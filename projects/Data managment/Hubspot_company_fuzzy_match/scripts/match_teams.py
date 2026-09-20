"""Team step 2: match rows the firm pass did not accept against FINTRX private wealth teams.

Run:  python scripts/match_teams.py [--limit N] [--force]
Reads teams.jsonl, matches.csv (to skip accepted rows), cand_domain.csv (parent-firm evidence).
Name candidates via rapidfuzz, one Jev pass, code rules. Writes data/output/team_matches.csv.
Raw Jev answers cached in data/output/jev_teams.jsonl.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_DOMAIN, COL_DOMAIN, COL_NAME, COL_RECORD_ID, COL_STATE, DATA_FX,  # noqa: E402
                    DATA_OUT, JEV_WORKERS, MATCHES, Eta, append_jsonl, extract_domain, is_blank,
                    load_source, log_error, norm_state, read_csv, read_jsonl, write_csv)
from match import UniverseIndex, match_all  # noqa: E402
from narrow import LEVELS  # noqa: E402
import jev  # noqa: E402

TEAMS = DATA_FX / "teams.jsonl"
TEAM_MATCHES = DATA_OUT / "team_matches.csv"
JEV_TEAMS = DATA_OUT / "jev_teams.jsonl"

# ---- thresholds (logged in notes/decisions.md) ----
REVIEW_MIN = 0.5          # link below this -> reject
ACCEPT_STRONG = 1.5       # link at or above AND state confirmed equal -> accept
# (stricter than the firm pass: a team row has no website or phone to corroborate, so an unknown
#  state plus a common name is not enough; those go to review)
ACCEPT_WITH_PARENT = 1.0  # link at or above, and the row's domain reps belong to this team's parent firm -> accept

FIELDS = ["source_row", "record_id", "source_name", "team_id", "team_name", "parent_firm_id", "parent_firm_name",
          "parent_crd", "team_city", "team_state", "name_score", "state_equal", "parent_domain_match",
          "parent_rep_count", "link", "same_name", "decision", "row_outcome", "row_reason", "chosen"]


def load_teams() -> list[dict]:
    seen, out = set(), []
    for r in read_jsonl(TEAMS):
        if r["team_id"] in seen or is_blank(r.get("name")):
            continue
        seen.add(r["team_id"])
        out.append({"item_id": r["team_id"], "name": r["name"], "city": r.get("city"), "state": r.get("state"),
                    "parent_firm_id": r.get("parent_firm_id"), "parent_firm_name": r.get("parent_firm_name"),
                    "parent_crd": r.get("parent_crd")})
    if not out:
        sys.exit(f"teams empty, run pull_teams.py first ({TEAMS})")
    return out


def domain_parents(limit_rows: set[int] | None = None) -> dict[int, dict[int, int]]:
    """source_row -> {firm item_id: rep_count} from the domain lookup."""
    out: dict[int, dict[int, int]] = {}
    for r in read_csv(CAND_DOMAIN):
        if r["method"] != "domain_reps" or not r["fintrx_item_id"]:
            continue
        sr = int(r["source_row"])
        if limit_rows is not None and sr not in limit_rows:
            continue
        out.setdefault(sr, {})[int(float(r["fintrx_item_id"]))] = int(float(r["rep_count"] or 0))
    return out


def decide_candidate(link: float | None, state_equal, parent_match: bool) -> str:
    if link is None:
        return "review"
    if parent_match and link >= ACCEPT_WITH_PARENT:
        return "accept"
    if link >= ACCEPT_STRONG and state_equal is True:
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
    return {"hubspot": {"name": "" if is_blank(src.get(COL_NAME)) else str(src.get(COL_NAME)),
                        "state": norm_state(src.get(COL_STATE)), "domain": extract_domain(src.get(COL_DOMAIN))},
            "candidates": [{"idx": i, "team_name": c["team_name"], "city": c["team_city"] or "",
                            "state": c["team_state"] or "", "parent_firm": c["parent_firm_name"] or "",
                            "hubspot_domain_reps_belong_to_parent_firm": bool(c["parent_domain_match"])}
                           for i, c in enumerate(cands)]}


def build_questions(cands: list[dict]) -> dict:
    q = {}
    for i, _ in enumerate(cands):
        q[f"link_{i}"] = jev.score(
            {"question": f"Is the advisor team `candidates[{i}]` the same business as the company described in `hubspot`?",
             "compare": [f"`candidates[{i}].team_name`", "`hubspot.name`"],
             "supporting": [f"`candidates[{i}].state` versus `hubspot.state`",
                            f"`candidates[{i}].hubspot_domain_reps_belong_to_parent_firm` (true means people using "
                            f"the HubSpot company's email domain are registered under this team's parent firm)"],
             "note": "Treat LLC, Inc, Wealth Management, Advisors, Partners, Group and similar generic words as noise."},
            LEVELS)
        q[f"name_{i}"] = jev.noul(f"Does `candidates[{i}].team_name` name the same business as `hubspot.name`, "
                                  f"ignoring suffixes and generic industry words?")
    return q


def ask_row(sr: int, src: dict, cands: list[dict]) -> dict:
    try:
        r = jev.ask(build_state(src, cands), build_questions(cands))
        return {"source_row": sr, "model": r.get("model"), "answers": r["answers"], "usage": r.get("usage"),
                "items": [c["team_id"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        log_error("teams_jev", sr, e)
        return {"source_row": sr, "error": str(e)[:300], "items": [c["team_id"] for c in cands]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--cutoff", type=float, default=75.0)
    args = ap.parse_args()
    df = load_source(args.limit)
    accepted = {int(r["source_row"]) for r in read_csv(MATCHES) if r["row_outcome"] == "accept"}
    df = df[~df["source_row"].isin(accepted)]
    srcs = {int(s["source_row"]): s for s in df.to_dict("records")}
    teams = load_teams()
    by_id = {t["item_id"]: t for t in teams}
    ux = UniverseIndex(teams)
    print(f"{len(srcs)} rows not accepted by the firm pass vs {len(teams)} teams", flush=True)
    name_rows = match_all(df, ux, args.top, args.cutoff)
    parents = domain_parents(set(srcs))
    by_row: dict[int, list[dict]] = {}
    for r in name_rows:
        sr = int(r["source_row"])
        t = by_id[int(r["fintrx_item_id"])]
        pmap = parents.get(sr, {})
        pid = t.get("parent_firm_id")
        ss, ts = norm_state(srcs[sr].get(COL_STATE)), norm_state(t.get("state"))
        by_row.setdefault(sr, []).append(dict(
            team_id=t["item_id"], team_name=t["name"], parent_firm_id=pid, parent_firm_name=t.get("parent_firm_name"),
            parent_crd=t.get("parent_crd"), team_city=t.get("city"), team_state=ts, name_score=r["score"],
            state_equal=(ss == ts) if ss and ts else None,
            parent_domain_match=bool(pid) and int(pid) in pmap, parent_rep_count=pmap.get(int(pid), 0) if pid else 0))
    print(f"{len(by_row)} rows with team name candidates", flush=True)

    cache = {} if args.force else {r["source_row"]: r for r in read_jsonl(JEV_TEAMS) if "answers" in r}
    for sr, cands in by_row.items():
        if sr in cache and cache[sr].get("items") != [c["team_id"] for c in cands]:
            del cache[sr]
    need = [sr for sr in by_row if sr not in cache]
    print(f"{len(need)} rows need Jev", flush=True)
    eta = Eta(len(need), "jev_teams")
    with ThreadPoolExecutor(max_workers=JEV_WORKERS) as ex:
        for res in ex.map(lambda sr: ask_row(sr, srcs[sr], by_row[sr]), need):
            cache[res["source_row"]] = res
            append_jsonl(JEV_TEAMS, [res])
            msg = eta.tick()
            if eta.done % 200 == 0:
                print(msg, flush=True)

    out = []
    for sr, src in srcs.items():
        cands = by_row.get(sr, [])
        base = dict(source_row=sr, record_id=src[COL_RECORD_ID], source_name=src[COL_NAME])
        if not cands:
            out.append(dict(base, row_outcome="no_match", row_reason="no_team_candidate", decision="", chosen=False))
            continue
        ans = (cache.get(sr) or {}).get("answers") or {}
        for i, c in enumerate(cands):
            a, n = ans.get(f"link_{i}"), ans.get(f"name_{i}")
            c["link"] = round(a["score"], 3) if a else None
            c["same_name"] = round(n["noul"], 3) if n else ""
            c["decision"] = decide_candidate(c["link"], c["state_equal"], c["parent_domain_match"])
        outcome, chosen, reason = decide_row(cands)
        if not ans:
            outcome, chosen, reason = "review", None, "jev_error"
        for i, c in enumerate(cands):
            out.append(dict(base, **c, row_outcome=outcome, row_reason=reason, chosen=(i == chosen)))
    write_csv(TEAM_MATCHES, out, FIELDS)
    rows = {r["source_row"]: r["row_outcome"] for r in out}
    print(f"wrote {TEAM_MATCHES}: {len(out)} lines; row outcomes {dict(Counter(rows.values()))}")


if __name__ == "__main__":
    main()
