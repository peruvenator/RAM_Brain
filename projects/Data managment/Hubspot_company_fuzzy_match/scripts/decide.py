"""Step 6: Jev pass 2 on detail records plus code rules. One line per kept candidate.

Run:  python scripts/decide.py [--limit N] [--force]
Reads cand_narrowed.csv + details.csv. Writes data/output/matches.csv. Raw answers: jev_pass2.jsonl.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NARROWED, COL_DOMAIN, COL_NAME, COL_PHONE, COL_RECORD_ID, COL_STATE,  # noqa: E402
                    COL_STREET1, COL_STREET2, DETAILS_CSV, JEV2, JEV_WORKERS, MATCHES, Eta, append_jsonl,
                    extract_domain, is_blank, load_source, log_error, norm_state, phone_digits,
                    read_csv, read_jsonl, write_csv)
from narrow import LEVELS  # noqa: E402
import jev  # noqa: E402

# ---- thresholds (logged in notes/decisions.md) ----
REVIEW_MIN = 0.5        # link_state below this -> reject
ACCEPT_STRONG = 1.5     # link_state at or above, with state agreeing or unknown -> accept
ACCEPT_WITH_KEY = 1.0   # link_state at or above, with domain or phone equal -> accept

FIELDS = ["source_row", "record_id", "source_name", "fintrx_item_id", "matched_name", "crd_id", "legal_name",
          "website_address", "street1", "city", "state", "zip", "phone", "methods", "name_score", "link1",
          "link2", "same_name2", "same_street2", "domain_equal", "phone_equal", "state_equal", "zip_equal",
          "decision", "row_outcome", "row_reason", "chosen"]


def compute_flags(src: dict, det: dict) -> dict:
    sd, dd = extract_domain(src.get(COL_DOMAIN)), extract_domain(det.get("website_address"))
    sp, dp = phone_digits(src.get(COL_PHONE)), phone_digits(det.get("phone"))
    ss, ds = norm_state(src.get(COL_STATE)), norm_state(det.get("state"))
    sz, dz = str(src.get("_zip") or "").strip()[:5], str(det.get("zip") or "").strip()[:5]
    return dict(domain_equal=bool(sd) and sd == dd,
                phone_equal=bool(sp) and sp == dp,
                state_equal=(ss == ds) if ss and ds else None,
                zip_equal=(sz == dz) if sz and dz else None)


def decide_candidate(link: float | None, flags: dict) -> str:
    if link is None:
        return "review"
    if (flags["domain_equal"] or flags["phone_equal"]) and link >= ACCEPT_WITH_KEY:
        return "accept"
    if link >= ACCEPT_STRONG and flags["state_equal"] in (True, None):
        return "accept"
    if link >= REVIEW_MIN:
        return "review"
    return "reject"


def decide_row(cands: list[dict]):
    acc = [i for i, c in enumerate(cands) if c["decision"] == "accept"]
    if len(acc) == 1:
        return "accept", acc[0], "single_accept"
    if len(acc) > 1:
        return "review", None, "multiple_accepts"
    if any(c["decision"] == "review" for c in cands):
        return "review", None, "review_band"
    return "no_match", None, "all_rejected"


def build_state(src: dict, cands: list[dict]) -> dict:
    street = " ".join(str(src.get(k)) for k in (COL_STREET1, COL_STREET2) if not is_blank(src.get(k)))
    return {"hubspot": {"name": src.get(COL_NAME), "street": street, "state": norm_state(src.get(COL_STATE)),
                        "domain": extract_domain(src.get(COL_DOMAIN))},
            "candidates": [{"idx": i, "name": c["matched_name"], "legal_name": c.get("legal_name") or "",
                            "former_names": c.get("former_names") or "", "website": c.get("website_address") or "",
                            "street": " ".join(x for x in (c.get("street1") or "", c.get("street2") or "") if x),
                            "city": c.get("city") or "", "state": c.get("state") or ""}
                           for i, c in enumerate(cands)]}


def build_questions(cands: list[dict]) -> dict:
    q = {}
    for i, _ in enumerate(cands):
        q[f"link_{i}"] = jev.score(
            {"question": f"Is `candidates[{i}]` the same firm as the one described in `hubspot`?",
             "compare": [f"`candidates[{i}].name`, `.legal_name`, `.former_names`", "`hubspot.name`"],
             "supporting": [f"`candidates[{i}].street` and `.state` versus `hubspot.street` and `hubspot.state`",
                            f"`candidates[{i}].website` versus `hubspot.domain`"],
             "note": "Legal suffixes and generic words are noise. A custodian, broker-dealer or platform that "
                     "merely shares a website with many advisors is not the same firm."},
            LEVELS)
        q[f"name_{i}"] = jev.noul(f"Does `candidates[{i}].name` or `.legal_name` or `.former_names` name the "
                                  f"same business as `hubspot.name`, ignoring suffixes and generic words?")
        q[f"street_{i}"] = jev.noul(f"Do `candidates[{i}].street` and `hubspot.street` describe the same street "
                                    f"address, allowing for abbreviations and suite numbers? Answer no if either is blank.")
    return q


def ask_row(sr: int, src: dict, cands: list[dict]) -> dict:
    try:
        r = jev.ask(build_state(src, cands), build_questions(cands))
        return {"source_row": sr, "model": r.get("model"), "answers": r["answers"], "usage": r.get("usage"),
                "items": [c["fintrx_item_id"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        log_error("decide_jev", sr, e)
        return {"source_row": sr, "error": str(e)[:300], "items": [c["fintrx_item_id"] for c in cands]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    df = load_source(args.limit)
    srcs = {int(s["source_row"]): s for s in df.to_dict("records")}
    details = {str(d["item_id"]): d for d in read_csv(DETAILS_CSV)}
    narrowed = read_csv(CAND_NARROWED)
    by_row: dict[int, list[dict]] = {}
    for r in narrowed:
        sr = int(r["source_row"])
        if sr not in srcs:
            continue
        if r["kept"] == "True" and r["fintrx_item_id"]:
            det = details.get(str(int(float(r["fintrx_item_id"]))))
            if det:
                by_row.setdefault(sr, []).append(dict(r, **{k: v for k, v in det.items() if k != "item_id"}))
    cache = {} if args.force else {r["source_row"]: r for r in read_jsonl(JEV2)}
    need = [sr for sr in by_row if sr not in cache]
    print(f"{len(srcs)} rows, {len(by_row)} with kept candidates, {len(need)} need Jev pass 2", flush=True)
    eta = Eta(len(need), "jev2")
    with ThreadPoolExecutor(max_workers=JEV_WORKERS) as ex:
        for res in ex.map(lambda sr: ask_row(sr, srcs[sr], by_row[sr]), need):
            cache[res["source_row"]] = res
            append_jsonl(JEV2, [res])
            msg = eta.tick()
            if eta.done % 200 == 0:
                print(msg, flush=True)

    out = []
    for sr, src in srcs.items():
        cands = by_row.get(sr, [])
        base = dict(source_row=sr, record_id=src[COL_RECORD_ID], source_name=src[COL_NAME])
        if not cands:
            out.append(dict(base, row_outcome="no_match", row_reason="no_kept_candidate", decision="", chosen=False))
            continue
        ans = (cache.get(sr) or {}).get("answers") or {}
        for i, c in enumerate(cands):
            a, n, s = ans.get(f"link_{i}"), ans.get(f"name_{i}"), ans.get(f"street_{i}")
            c["link2"] = round(a["score"], 3) if a else None
            c["same_name2"] = round(n["noul"], 3) if n else ""
            c["same_street2"] = round(s["noul"], 3) if s else ""
            c.update(compute_flags(src, c))
            c["decision"] = decide_candidate(c["link2"], c)
        outcome, chosen, reason = decide_row(cands)
        if not ans:
            outcome, chosen, reason = "review", None, "jev_error"
        for i, c in enumerate(cands):
            out.append(dict(base, **c, row_outcome=outcome, row_reason=reason, chosen=(i == chosen)))
    write_csv(MATCHES, out, FIELDS)
    rows = {r["source_row"]: r["row_outcome"] for r in out}
    print(f"wrote {MATCHES}: {len(out)} lines; row outcomes {dict(Counter(rows.values()))}")


if __name__ == "__main__":
    main()
