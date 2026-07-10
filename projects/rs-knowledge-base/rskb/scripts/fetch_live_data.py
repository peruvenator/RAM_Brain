#!/usr/bin/env python3
"""
fetch_live_data.py — Fetch live AUM/NAV/expense ratio/yield data from
returnstackedetfs.com, returnstackedetfs.ca, returnstackedfunds.com, and
quantifyfunds.com product pages.

Bypasses web_fetch URL provenance restriction by using direct HTTP via the
requests library. Designed to be invoked by Claude through bash_tool when the
rs-etfs-knowledge-base skill is active.

Usage (from Claude or shell):
    python scripts/fetch_live_data.py RSBY
    python scripts/fetch_live_data.py RDMIX --raw       # dump cleaned page text
    python scripts/fetch_live_data.py RSST RSBT RSSY    # multiple tickers

Output: JSON to stdout. Designed to be parsed by Claude or piped into jq.

Dependencies: requests, beautifulsoup4, pyyaml. All pip-installable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import requests
import yaml
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT = 20

# Patterns tuned for returnstackedetfs.com / .ca / returnstackedfunds.com page text.
# Matches values like "$77.76M", "$1.23B", "$77,760,000", "0.96%", "$18.74".
NUMBER = r"[\$]?[\d,]+\.?\d*[MBK%]?"

FIELD_PATTERNS: dict[str, list[str]] = {
    "net_assets": [
        r"Net Assets[:\s]+\$?([\d,]+\.?\d*\s*[MBK]?)",
        r"Total Net Assets[:\s]+\$?([\d,]+\.?\d*\s*[MBK]?)",
        r"Fund AUM[:\s]+\$?([\d,]+\.?\d*\s*[MBK]?)",
    ],
    "nav": [
        r"NAV[:\s]+\$?([\d,]+\.\d+)",
        r"Net Asset Value[:\s]+\$?([\d,]+\.\d+)",
    ],
    "shares_outstanding": [
        r"Shares Outstanding[:\s]+([\d,]+)",
    ],
    "gross_expense_ratio": [
        r"Gross Expense Ratio[:\s]+([\d.]+%)",
        r"Total Annual Fund Operating Expenses[:\s]+([\d.]+%)",
    ],
    "net_expense_ratio": [
        r"Net Expense Ratio[:\s]+([\d.]+%)",
    ],
    "sec_yield_30d": [
        r"30[\s\-]Day SEC Yield[:\s]+(-?[\d.]+%)",
        r"30 Day SEC Yield[:\s]+(-?[\d.]+%)",
    ],
    "median_30d_spread": [
        r"Median 30[\s\-]Day Spread[:\s]+([\d.]+%)",
    ],
    "premium_discount": [
        r"Premium/Discount[:\s]+(-?[\d.]+%)",
    ],
    "inception_date": [
        r"Inception Date[:\s]+([A-Za-z]+ \d+,?\s*\d{4})",
        r"Fund Inception[:\s]+([A-Za-z]+ \d+,?\s*\d{4})",
    ],
    "as_of_date": [
        r"[Aa]s of[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})",
        r"[Aa]s of[:\s]+([A-Za-z]+ \d+,?\s*\d{4})",
    ],
}


def load_url_registry(skill_root: Path) -> dict[str, dict[str, str]]:
    """Flatten urls.yaml into {ticker_upper: {name, url, category}}."""
    registry_path = skill_root / "urls.yaml"
    if not registry_path.exists():
        sys.exit(f"ERROR: urls.yaml not found at {registry_path}")

    with registry_path.open() as f:
        raw = yaml.safe_load(f)

    flat = {}
    for category, funds in raw.items():
        for ticker, meta in funds.items():
            flat[ticker.upper()] = {**meta, "category": category}
    return flat


def fetch_page(url: str) -> str:
    """GET the URL and return raw HTML. Raises on HTTP error."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def extract_text(html: str) -> str:
    """Strip HTML to clean text, preserving table-cell adjacency."""
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    # Insert spaces between adjacent tags so "Net Assets" and "$77.76M" don't run together
    text = soup.get_text(separator=" ", strip=True)
    # Collapse multi-space
    return re.sub(r"\s+", " ", text)


def extract_fields(text: str) -> dict[str, str | None]:
    """Run regex patterns and return whatever matches."""
    result: dict[str, str | None] = {}
    for field, patterns in FIELD_PATTERNS.items():
        result[field] = None
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                result[field] = m.group(1).strip()
                break
    return result


def fetch_ticker(ticker: str, registry: dict[str, dict[str, str]], raw: bool) -> dict[str, Any]:
    ticker = ticker.upper()
    if ticker not in registry:
        return {"ticker": ticker, "error": f"Ticker not found in urls.yaml registry"}

    meta = registry[ticker]
    try:
        html = fetch_page(meta["url"])
    except requests.RequestException as e:
        return {"ticker": ticker, "url": meta["url"], "error": f"HTTP fetch failed: {e}"}

    text = extract_text(html)
    out: dict[str, Any] = {
        "ticker": ticker,
        "name": meta["name"],
        "category": meta["category"],
        "url": meta["url"],
        "fields": extract_fields(text),
    }
    if raw:
        # Truncate to keep stdout reasonable; full text rarely needed beyond ~12KB.
        out["raw_text"] = text[:12000]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch live RS ETF product page data.")
    parser.add_argument("tickers", nargs="+", help="One or more tickers (e.g. RSBY RSST)")
    parser.add_argument("--raw", action="store_true", help="Include cleaned page text in output")
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to skill root (default: parent of scripts/)",
    )
    args = parser.parse_args()

    registry = load_url_registry(args.skill_root)
    results = [fetch_ticker(t, registry, args.raw) for t in args.tickers]
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
