"""Step 5: fetch the FINTRX detail record for every kept candidate. Resumable by file existence.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/fetch_details.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NARROWED, DETAILS_CSV, DETAILS_DIR, Eta, load_source, log_error, paced,  # noqa: E402
                    read_csv, write_csv)
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

FIELDS = ["item_id", "crd_id", "primary_business_name", "legal_name", "former_names", "website_address",
          "street1", "street2", "city", "state", "zip", "phone", "hubspot_id"]
ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")


def flatten_detail(rec: dict) -> dict:
    loc = rec.get("location_address") or ""
    z = ZIP_RE.search(loc)
    fn = rec.get("former_names")
    if isinstance(fn, list):
        fn = "; ".join(str(x) for x in fn)
    return dict(
        item_id=rec.get("id"), crd_id=rec.get("crd_id"),
        primary_business_name=rec.get("primary_business_name"), legal_name=rec.get("legal_name"),
        former_names=fn, website_address=rec.get("website_address"),
        street1=rec.get("main_office_address_1"), street2=rec.get("main_office_address_2"),
        city=rec.get("office_city_name") or rec.get("ria_investor_data_main_office_city_name"),
        state=rec.get("main_office_state"), zip=z.group(1) if z else "",
        phone=rec.get("main_office_phone_number") or rec.get("main_office_fintrx_phone_number"),
        hubspot_id=rec.get("hubspot_id"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="only candidates for the first N source rows")
    args = ap.parse_args()
    rows = read_csv(CAND_NARROWED)
    if args.limit:
        keep_rows = set(str(x) for x in load_source(args.limit)["source_row"])
        rows = [r for r in rows if r["source_row"] in keep_rows]
    ids = sorted({int(float(r["fintrx_item_id"])) for r in rows if r["kept"] == "True" and r["fintrx_item_id"]})
    DETAILS_DIR.mkdir(parents=True, exist_ok=True)
    todo = [i for i in ids if not (DETAILS_DIR / f"{i}.json").exists()]
    print(f"{len(ids)} kept firms, {len(todo)} to fetch (~{len(todo) * 0.5 / 60:.0f} min)", flush=True)
    if todo:
        c = FintrxClient()
        eta = Eta(len(todo), "details")
        try:
            for i in todo:
                try:
                    rec = c.ria_firm(i)
                    (DETAILS_DIR / f"{i}.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
                except FintrxAuthError:
                    raise
                except Exception as e:  # noqa: BLE001
                    log_error("fetch_details", i, e)
                msg = eta.tick()
                if eta.done % 200 == 0:
                    print(msg, flush=True)
                paced()
        except FintrxAuthError as e:
            print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
            sys.exit(2)
    flat = []
    for i in ids:
        p = DETAILS_DIR / f"{i}.json"
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            flat.append(flatten_detail(rec.get("ria_investor") or rec))
    write_csv(DETAILS_CSV, flat, FIELDS)
    print(f"wrote {DETAILS_CSV}: {len(flat)} firms, {sum(1 for f in flat if f['crd_id'])} with CRD")


if __name__ == "__main__":
    main()
