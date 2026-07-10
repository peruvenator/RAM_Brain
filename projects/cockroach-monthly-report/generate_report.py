"""
generate_report.py -- Monthly performance summary for the Cockroach Carry strategy.

Reads the daily returns time series synced from S3, computes a standard set of
performance statistics, formats a summary, and posts it to Slack.

Self-contained: no LLM/MCP dependencies. Config via the CONFIG block + .env.

Usage:
    python generate_report.py            # compute + post to Slack
    python generate_report.py --dry-run  # compute + print, do NOT post
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ── Config ───────────────────────────────────────────────────────────────────
CONFIG = {
    # Source data (S3-synced local folder)
    "returns_csv": r"C:\Users\RodrigoGordillo\S3_Data\backtest-sims\portfolio_returns\cockroach_carry\live\strategy\returns.csv",

    # Which return column to headline. Options in this file:
    #   gross, net, net_fees, net_fees_tax (+ *_adj variants)
    "return_column": "net_fees",

    # Display
    "strategy_name": "Cockroach Carry",
    "recipient_name": "team",          # who this report is for (used in message text)

    # Trading days per year for annualization
    "trading_days": 252,

    # Warn if the latest data point is older than this many days vs today
    "staleness_days": 7,
}

TRADING_DAYS = CONFIG["trading_days"]


# ── Data loading ─────────────────────────────────────────────────────────────
def load_returns(path: str, column: str) -> pd.Series:
    df = pd.read_csv(path, parse_dates=["date"])
    if column not in df.columns:
        raise ValueError(
            f"Column '{column}' not found. Available: {list(df.columns)}"
        )
    s = df.set_index("date")[column].sort_index()
    s = s.dropna()
    return s


# ── Metrics ──────────────────────────────────────────────────────────────────
def compound(returns: pd.Series) -> float:
    """Total compounded return over the series."""
    if len(returns) == 0:
        return float("nan")
    return float((1.0 + returns).prod() - 1.0)


def annualized_return(returns: pd.Series) -> float:
    if len(returns) == 0:
        return float("nan")
    total = (1.0 + returns).prod()
    years = len(returns) / TRADING_DAYS
    if years <= 0:
        return float("nan")
    return float(total ** (1.0 / years) - 1.0)


def annualized_vol(returns: pd.Series) -> float:
    if len(returns) < 2:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS))


def sharpe(returns: pd.Series, rf: float = 0.0) -> float:
    """Sharpe with a constant annual risk-free rate (default 0)."""
    if len(returns) < 2:
        return float("nan")
    excess_daily = returns - rf / TRADING_DAYS
    mu = excess_daily.mean() * TRADING_DAYS
    sigma = returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    if sigma == 0:
        return float("nan")
    return float(mu / sigma)


def max_drawdown(returns: pd.Series) -> float:
    if len(returns) == 0:
        return float("nan")
    curve = (1.0 + returns).cumprod()
    peak = curve.cummax()
    dd = curve / peak - 1.0
    return float(dd.min())


def trailing_window(returns: pd.Series, months: int) -> pd.Series:
    end = returns.index.max()
    start = end - pd.DateOffset(months=months)
    return returns[returns.index > start]


def latest_full_month(returns: pd.Series):
    """Return (label, monthly_return) for the most recent month present in data."""
    monthly = (1.0 + returns).groupby(returns.index.to_period("M")).prod() - 1.0
    last_period = monthly.index.max()
    return str(last_period), float(monthly.loc[last_period])


def ytd(returns: pd.Series) -> float:
    last_year = returns.index.max().year
    yr = returns[returns.index.year == last_year]
    return compound(yr)


def compute_stats(returns: pd.Series) -> dict:
    last_date = returns.index.max()
    month_label, month_ret = latest_full_month(returns)
    return {
        "last_date": last_date,
        "first_date": returns.index.min(),
        "n_obs": len(returns),
        "month_label": month_label,
        "month_return": month_ret,
        "ytd": ytd(returns),
        "trailing_3m": compound(trailing_window(returns, 3)),
        "trailing_12m": compound(trailing_window(returns, 12)),
        "ann_return_3y": annualized_return(trailing_window(returns, 36)),
        "cagr_inception": annualized_return(returns),
        "vol_12m": annualized_vol(trailing_window(returns, 12)),
        "vol_inception": annualized_vol(returns),
        "sharpe_inception": sharpe(returns),
        "max_drawdown": max_drawdown(returns),
    }


# ── Formatting ───────────────────────────────────────────────────────────────
def pct(x: float, dp: int = 2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x * 100:+.{dp}f}%"


def num(x: float, dp: int = 2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:.{dp}f}"


def build_message(stats: dict, cfg: dict, stale: bool) -> str:
    name = cfg["strategy_name"]
    col = cfg["return_column"]
    lines = [
        f":bar_chart: *{name} -- Monthly Performance Report*",
        f"_Return series: `{col}` | Data through {stats['last_date'].date()}_",
        "",
        f"*{stats['month_label']} (latest month):*  {pct(stats['month_return'])}",
        f"*YTD:*  {pct(stats['ytd'])}",
        f"*Trailing 3M:*  {pct(stats['trailing_3m'])}",
        f"*Trailing 12M:*  {pct(stats['trailing_12m'])}",
        "",
        "*Risk / long-run:*",
        f"  - 3Y annualized: {pct(stats['ann_return_3y'])}",
        f"  - Since-inception CAGR: {pct(stats['cagr_inception'])}",
        f"  - 12M vol (annualized): {pct(stats['vol_12m'])}",
        f"  - Since-inception vol: {pct(stats['vol_inception'])}",
        f"  - Since-inception Sharpe: {num(stats['sharpe_inception'])}",
        f"  - Max drawdown (inception): {pct(stats['max_drawdown'])}",
        "",
        f"_{stats['n_obs']:,} daily obs from {stats['first_date'].date()}._",
    ]
    if stale:
        lines.insert(
            2,
            f":warning: *Data may be stale* -- latest point is "
            f"{stats['last_date'].date()}, more than {cfg['staleness_days']} days old.",
        )
    return "\n".join(lines)


# ── Slack ────────────────────────────────────────────────────────────────────
def post_to_slack(text: str, webhook: str) -> None:
    resp = requests.post(webhook, json={"text": text}, timeout=30)
    resp.raise_for_status()


# ── .env loader ──────────────────────────────────────────────────────────────
def load_env() -> None:
    """Load .env from this project dir first, then the repo root .env."""
    here = Path(__file__).resolve().parent
    candidates = [here / ".env", here.parents[1] / ".env"]
    for env_path in candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            # Don't let the repo root override a project-level value
            if key and key not in os.environ:
                os.environ[key] = val


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Cockroach Carry monthly report")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute and print, do not post to Slack")
    args = parser.parse_args()

    load_env()

    csv_path = CONFIG["returns_csv"]
    if not os.path.exists(csv_path):
        print(f"ERROR: returns file not found: {csv_path}", file=sys.stderr)
        return 1

    returns = load_returns(csv_path, CONFIG["return_column"])
    stats = compute_stats(returns)

    today = pd.Timestamp.today().normalize()
    stale = (today - stats["last_date"]).days > CONFIG["staleness_days"]

    message = build_message(stats, CONFIG, stale)
    print(message)
    print()

    if args.dry_run:
        print("[dry-run] Not posting to Slack.")
        return 0

    webhook = os.environ.get("SLACK_WEBHOOK")
    if not webhook:
        print("ERROR: SLACK_WEBHOOK not set in environment/.env", file=sys.stderr)
        return 1

    post_to_slack(message, webhook)
    print("Posted to Slack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
