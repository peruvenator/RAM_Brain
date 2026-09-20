"""Step 1: cache every FINTRX RIA firm row to data/fintrx/universe.jsonl. Resumable.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/pull_universe.py [--max-pages N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import UNIVERSE, UNIVERSE_PROGRESS, append_jsonl, paced, log_error  # noqa: E402
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

EXTRA_FIELDS = ("city", "state", "country", "type_entity", "aum_range", "hubspot_id", "synced_to_hubspot")


def flatten(item: dict, extra: dict) -> dict:
    row = {"item_id": int(item["id"]), "name": item.get("name"), "location": item.get("location")}
    for k in EXTRA_FIELDS:
        row[k] = extra.get(k)
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    page = 1
    if UNIVERSE_PROGRESS.exists():
        page = int(UNIVERSE_PROGRESS.read_text().strip() or 0) + 1
        print(f"resuming at page {page}")
    c = FintrxClient()
    total_rows = 0
    try:
        while True:
            d = c.ria_search(page=page, per_page=50)
            items = d.get("investors") or []
            if not items:
                print(f"page {page} empty, done")
                break
            extra = d.get("extra_info") or {}
            rows = [flatten(it, extra.get(str(it["id"]), {}) or {}) for it in items]
            append_jsonl(UNIVERSE, rows)
            UNIVERSE_PROGRESS.write_text(str(page))
            total_rows += len(rows)
            if page % 25 == 0:
                print(f"page {page}, {total_rows} rows this run", flush=True)
            if args.max_pages and page >= args.max_pages:
                break
            page += 1
            paced()
    except FintrxAuthError as e:
        print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        log_error("pull_universe", page, e)
        raise
    print(f"universe at {UNIVERSE}, last page {UNIVERSE_PROGRESS.read_text().strip()}")


if __name__ == "__main__":
    main()
