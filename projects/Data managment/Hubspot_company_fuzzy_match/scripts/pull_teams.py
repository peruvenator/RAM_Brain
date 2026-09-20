"""Team step 1: cache every FINTRX private wealth team to data/fintrx/teams.jsonl. Resumable.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/pull_teams.py [--max-pages N]
  or: python scripts/with_chrome_token.py scripts/pull_teams.py
Each line keeps the raw row under "raw" so fields can be re-flattened without another pull.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA_FX, append_jsonl, log_error, paced  # noqa: E402
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

TEAMS = DATA_FX / "teams.jsonl"
TEAMS_PROGRESS = DATA_FX / "teams.progress"


def parse_location(loc) -> tuple[str, str]:
    """'Gig Harbor, WA' -> ('Gig Harbor', 'WA'); anything else -> best effort."""
    if not isinstance(loc, str) or not loc.strip():
        return "", ""
    parts = [p.strip() for p in loc.split(",")]
    if len(parts) >= 2:
        return ", ".join(parts[:-1]), parts[-1]
    return parts[0], ""


def flatten(item: dict) -> dict:
    parent = item.get("parent_firm") or {}
    city, state = parse_location(item.get("location"))
    return {"team_id": int(item["id"]), "name": item.get("name"),
            "parent_firm_id": parent.get("id"), "parent_firm_name": parent.get("name"),
            "parent_crd": parent.get("crd_id"), "city": city, "state": state,
            "aum": item.get("aum"), "size": item.get("size"), "raw": item}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()
    page = 1
    if TEAMS_PROGRESS.exists():
        page = int(TEAMS_PROGRESS.read_text().strip() or 0) + 1
        print(f"resuming at page {page}")
    c = FintrxClient()
    seen_this_run: set[int] = set()
    try:
        while True:
            d = c.ria_teams_search(page=page, per_page=50)
            items = d.get("teams") or []
            if not items:
                print(f"page {page} empty, done")
                break
            rows = [flatten(it) for it in items]
            append_jsonl(TEAMS, rows)
            TEAMS_PROGRESS.write_text(str(page))
            new = {r["team_id"] for r in rows} - seen_this_run
            seen_this_run |= {r["team_id"] for r in rows}
            if page % 25 == 0:
                print(f"page {page}, {len(seen_this_run)} unique teams this run", flush=True)
            if not new and page > 10:
                print(f"page {page} returned only repeats, stopping (unstable sort past the end)")
                break
            if args.max_pages and page >= args.max_pages:
                break
            page += 1
            paced()
    except FintrxAuthError as e:
        print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        log_error("pull_teams", page, e)
        raise
    print(f"teams at {TEAMS}")


if __name__ == "__main__":
    main()
