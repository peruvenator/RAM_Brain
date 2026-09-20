"""Step 7: enriched Excel (column C filled for accepted rows) plus review.csv for everything else.

Run:  python scripts/write_output.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NARROWED, COL_CRD, DATA_OUT, FINTRX_FIRM_URL, MATCHES, REVIEW,  # noqa: E402
                    SOURCE_XLSX, read_csv, write_csv)

EXTRA_HEADERS = ["fintrx_match_name", "fintrx_match_method", "fintrx_match_confidence"]
REVIEW_FIELDS = ["source_row", "record_id", "source_name", "row_outcome", "row_reason", "fintrx_item_id",
                 "matched_name", "crd_id", "legal_name", "website_address", "street1", "city", "state", "methods",
                 "name_score", "link1", "link2", "same_name2", "same_street2", "domain_equal", "phone_equal",
                 "state_equal", "decision", "fintrx_url"]


def _url(item_id) -> str:
    try:
        return FINTRX_FIRM_URL.format(item_id=int(float(item_id)))
    except (TypeError, ValueError):
        return ""


def fill_workbook(src_path: Path, out_path: Path, accepted: dict[int, dict]) -> int:
    wb = openpyxl.load_workbook(src_path)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    col_c = headers.index(COL_CRD) + 1
    first_extra = len(headers) + 1
    for j, h in enumerate(EXTRA_HEADERS):
        ws.cell(row=1, column=first_extra + j, value=h)
    n = 0
    for sr, m in accepted.items():
        r = sr + 2
        crd = m.get("crd_id")
        if not crd:
            continue
        ws.cell(row=r, column=col_c, value=int(float(crd)))
        ws.cell(row=r, column=first_extra, value=m.get("matched_name"))
        ws.cell(row=r, column=first_extra + 1, value=m.get("methods"))
        ws.cell(row=r, column=first_extra + 2, value=m.get("link2"))
        n += 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return n


def main() -> None:
    matches = read_csv(MATCHES)
    accepted = {int(r["source_row"]): r for r in matches if r["row_outcome"] == "accept" and r["chosen"] == "True"}
    out_xlsx = DATA_OUT / f"{SOURCE_XLSX.stem}-enriched.xlsx"
    n = fill_workbook(SOURCE_XLSX, out_xlsx, accepted)
    outcomes = {int(r["source_row"]): r["row_outcome"] for r in matches}
    review = []
    for r in matches:
        if r["row_outcome"] == "accept":
            continue
        review.append(dict(r, fintrx_url=_url(r.get("fintrx_item_id"))))
    review_rows = {int(r["source_row"]) for r in review}
    for r in read_csv(CAND_NARROWED):
        sr = int(r["source_row"])
        if outcomes.get(sr) == "accept" or sr in review_rows or r["kept"] == "True":
            continue
        review.append(dict(r, row_outcome=outcomes.get(sr, "no_match"), row_reason=r["keep_reason"], decision="",
                           fintrx_url=_url(r.get("fintrx_item_id"))))
    review.sort(key=lambda r: (int(r["source_row"]), r.get("matched_name") or ""))
    write_csv(REVIEW, review, REVIEW_FIELDS)
    print(f"wrote {out_xlsx}: {n} rows filled")
    print(f"wrote {REVIEW}: {len(review)} lines for {len({r['source_row'] for r in review})} rows")
    print("row outcomes:", dict(Counter(outcomes.values())))


if __name__ == "__main__":
    main()
