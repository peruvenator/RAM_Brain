"""Step 4: Jev pass 1. Merge name and domain candidates, keep the plausible ones before the
slow detail fetch.

Run:  python scripts/narrow.py [--limit N] [--force]
Reads data/output/cand_name.csv + cand_domain.csv. Writes data/output/cand_narrowed.csv.
Raw Jev answers cached in data/output/jev_pass1.jsonl (keyed by source_row).
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_DOMAIN, CAND_NAME, CAND_NARROWED, COL_DOMAIN, COL_NAME, COL_RECORD_ID,  # noqa: E402
                    COL_STATE, JEV1, JEV_WORKERS, Eta, append_jsonl, extract_domain, is_blank,
                    load_source, log_error, norm_state, read_csv, read_jsonl, write_csv)
from match import load_universe  # noqa: E402
import jev  # noqa: E402

# ---- thresholds (logged in notes/decisions.md) ----
KEEP_MIN = 0.5        # link_state score at or above -> keep for the detail fetch
MAX_KEEP = 3

LEVELS = [
    "Different firms. The names refer to distinct businesses, or the same words point at a "
    "different company (for example a location that contradicts).",
    "Could be the same firm. The names are similar, one contains the other, they look like a "
    "parent and an affiliate or a renamed firm, or the evidence is too thin to tell.",
    "The same firm. The names identify the same business once legal suffixes, abbreviations and "
    "spelling variants are ignored, and nothing contradicts it.",
]

FIELDS = ["source_row", "record_id", "source_name", "fintrx_item_id", "matched_name", "cand_city",
          "cand_state", "methods", "name_score", "state_match", "rep_count", "link1", "same_name1",
          "kept", "keep_reason"]


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def merge_candidates(name_rows: list[dict], domain_rows: list[dict]) -> dict[int, list[dict]]:
    out: dict[int, dict] = {}

    def slot(sr: int, key):
        return out.setdefault(sr, {}).setdefault(key, dict(
            item_id=key if isinstance(key, int) else None, matched_name="", cand_city="", cand_state="",
            methods=[], name_score=0.0, state_match=False, rep_count=0))

    for r in name_rows:
        sr, item = int(r["source_row"]), _int(r["fintrx_item_id"])
        c = slot(sr, item)
        c.update(matched_name=r["matched_name"], cand_city=r.get("cand_city") or "",
                 cand_state=r.get("cand_state") or "", name_score=max(c["name_score"], float(r["score"])),
                 state_match=c["state_match"] or str(r.get("state_match")).lower() == "true")
        if r["method"] not in c["methods"]:
            c["methods"].append(r["method"])
    for r in domain_rows:
        sr, item = int(r["source_row"]), _int(r["fintrx_item_id"])
        key = item if item is not None else ("unmapped", r["matched_name"])
        c = slot(sr, key)
        c["matched_name"] = c["matched_name"] or r["matched_name"]
        c["rep_count"] += _int(r.get("rep_count")) or 0
        if r["method"] not in c["methods"]:
            c["methods"].append(r["method"])
    result = {}
    for sr, d in out.items():
        cands = list(d.values())
        for c in cands:
            c["methods"] = "|".join(c["methods"])
        cands.sort(key=lambda c: (-c["name_score"], -c["rep_count"]))
        result[sr] = cands
    return result


def auto_keep(cands: list[dict]) -> bool:
    """Skip Jev when there is exactly one candidate and either the normalized name is exact
    with a matching state, or name and domain independently point at the same firm."""
    if len(cands) != 1 or cands[0]["item_id"] is None:
        return False
    m = cands[0]["methods"].split("|")
    if "exact_normalized" in m and cands[0]["state_match"]:
        return True
    return "domain_reps" in m and any(x in m for x in ("exact_normalized", "fuzzy_token_set"))


def build_questions(cands: list[dict]) -> dict:
    q = {}
    for i, _ in enumerate(cands):
        q[f"link_{i}"] = jev.score(
            {"question": f"How does `candidates[{i}]` relate to the firm described in `hubspot`?",
             "compare": [f"`candidates[{i}].name`", "`hubspot.name`"],
             "supporting": [f"`candidates[{i}].state` versus `hubspot.state`",
                            f"whether `hubspot.domain` looks like it belongs to `candidates[{i}].name`"],
             "note": "Treat LLC, Inc, LP, Wealth Management, Advisors and similar generic words as noise."},
            LEVELS)
        q[f"name_{i}"] = jev.noul(
            f"Does `candidates[{i}].name` name the same business as `hubspot.name`, ignoring legal "
            f"suffixes and generic industry words?")
    return q


def _s(v) -> str:
    """JSON-safe string: pandas NaN becomes '' (Jev rejects NaN in the state)."""
    return "" if is_blank(v) else str(v)


def build_state(src: dict, cands: list[dict]) -> dict:
    return {"hubspot": {"name": _s(src.get(COL_NAME)), "state": norm_state(src.get(COL_STATE)),
                        "domain": extract_domain(src.get(COL_DOMAIN))},
            "candidates": [{"idx": i, "name": c["matched_name"], "city": c["cand_city"],
                            "state": c["cand_state"], "type": c.get("type_entity") or ""}
                           for i, c in enumerate(cands)]}


def ask_row(sr: int, src: dict, cands: list[dict]) -> dict:
    try:
        r = jev.ask(build_state(src, cands), build_questions(cands))
        return {"source_row": sr, "model": r.get("model"), "answers": r["answers"],
                "usage": r.get("usage"), "items": [c["item_id"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        log_error("narrow_jev", sr, e)
        return {"source_row": sr, "error": str(e)[:300], "items": [c["item_id"] for c in cands]}


def apply_answers(cands: list[dict], ans: dict | None) -> None:
    for i, c in enumerate(cands):
        a = (ans or {}).get(f"link_{i}")
        n = (ans or {}).get(f"name_{i}")
        c["link1"] = round(a["score"], 3) if a else ""
        c["same_name1"] = round(n["noul"], 3) if n else ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="ignore the Jev cache")
    args = ap.parse_args()
    df = load_source(args.limit)
    srcs = {int(s["source_row"]): s for s in df.to_dict("records")}
    types = {u["item_id"]: u.get("type_entity") for u in load_universe()}
    merged = merge_candidates(read_csv(CAND_NAME), read_csv(CAND_DOMAIN))
    for cands in merged.values():
        for c in cands:
            c["type_entity"] = types.get(c["item_id"])
    # cached errors are re-asked on the next run; a later good answer wins because it is appended last
    cache = {} if args.force else {r["source_row"]: r for r in read_jsonl(JEV1) if "answers" in r}

    need = [sr for sr, cands in merged.items() if sr in srcs and not auto_keep(cands) and sr not in cache]
    print(f"{len(srcs)} rows, {len(merged)} with candidates, {len(need)} need Jev pass 1", flush=True)
    eta = Eta(len(need), "jev1")
    with ThreadPoolExecutor(max_workers=JEV_WORKERS) as ex:
        for res in ex.map(lambda sr: ask_row(sr, srcs[sr], merged[sr]), need):
            cache[res["source_row"]] = res
            append_jsonl(JEV1, [res])
            msg = eta.tick()
            if eta.done % 200 == 0:
                print(msg, flush=True)

    rows = []
    for sr, src in srcs.items():
        cands = merged.get(sr, [])
        base = dict(source_row=sr, record_id=src[COL_RECORD_ID], source_name=src[COL_NAME])
        if not cands:
            rows.append(dict(base, kept=False, keep_reason="no_candidates"))
            continue
        if auto_keep(cands):
            apply_answers(cands, None)
            for c in cands:
                rows.append(dict(base, **c, kept=True, keep_reason="auto"))
            continue
        res = cache.get(sr) or {}
        apply_answers(cands, res.get("answers"))
        if "error" in res or "answers" not in res:
            for c in cands:
                rows.append(dict(base, **c, kept=False, keep_reason="jev_error"))
            continue
        ranked = sorted(cands, key=lambda c: -(c["link1"] or 0))
        kept_ids = {id(c) for c in ranked[:MAX_KEEP] if c["item_id"] is not None and (c["link1"] or 0) >= KEEP_MIN}
        for c in cands:
            k = id(c) in kept_ids
            rows.append(dict(base, **c, kept=k, keep_reason="jev1" if k else "below_keep_min"))
        if not kept_ids:
            rows[-1]["keep_reason"] = "no_plausible_candidate"
    for r in rows:
        r["fintrx_item_id"] = r.get("item_id", "")
    write_csv(CAND_NARROWED, rows, FIELDS)
    kept = {r["source_row"] for r in rows if r["kept"]}
    print(f"wrote {CAND_NARROWED}: {len(rows)} candidate rows, {len(kept)} rows with >=1 kept, "
          f"{sum(1 for r in rows if r['kept'])} kept candidates to fetch")


if __name__ == "__main__":
    main()
