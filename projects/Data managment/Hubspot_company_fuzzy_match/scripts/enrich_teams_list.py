"""Fill 'Fintrx wealth team id' and 'Wealth Team Parent CRD' on a HubSpot companies export by matching
each company to a FINTRX private wealth team.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/enrich_teams_list.py \
          --source hubspot-crm-exports-wealth-teams-2026-09-20.csv [--limit N] [--force]
Output: data/output/<source stem>-enriched.csv (original columns with E/F filled, plus trace columns).

Evidence per candidate team (name candidates from rapidfuzz against the cached team universe):
  domain_equal       row domain == team website domain      (team_info record, cached per team)
  city_equal         row City == team city
  parent_domain      reps using the row domain are registered under the team's parent firm
  link               Jev same-business score, 3 levels, with website, street, city in the state
Accept: domain_equal, or parent_domain with link >= 1.0, or city_equal with link >= 1.5.
Review: link >= 0.5. Two accepts on one row -> review. Everything else blank.
Rows that the firm pass put in review get possible_firm_crd / possible_firm_name for a human to judge.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import (DATA_FX, DATA_OUT, JEV_WORKERS, MATCHES, PROJECT, Eta, append_jsonl, extract_domain,  # noqa: E402
                    is_blank, load_source, log_error, paced, read_csv, read_jsonl, write_csv)
from lookup_domain import firms_for_domain, load_cache, save_cache  # noqa: E402
from match import UniverseIndex, load_universe, match_all  # noqa: E402
from match_teams import load_teams  # noqa: E402
from narrow import LEVELS  # noqa: E402
from normalize import normalize  # noqa: E402
from fintrx_sdk import FintrxAPIError, FintrxAuthError, FintrxClient  # noqa: E402
import jev  # noqa: E402

TEAM_INFO_DIR = DATA_FX / "team_info"
JEV_LOG = DATA_OUT / "jev_teams_list.jsonl"
COL_ID, COL_NAME, COL_DOMAIN, COL_CITY = "Record ID", "Company name", "Company Domain Name", "City"
COL_TEAM_ID, COL_PARENT_CRD = "Fintrx wealth team id", "Wealth Team Parent CRD"

# ---- thresholds ----
NAME_CUTOFF = 80.0
TOP = 3
REVIEW_MIN, ACCEPT_STRONG, ACCEPT_WITH_PARENT = 0.5, 1.5, 1.0

TRACE = ["fintrx_team_name", "fintrx_team_city", "fintrx_team_website", "fintrx_parent_name", "match_evidence",
         "match_confidence", "status", "fintrx_team_url", "alt_candidates", "possible_firm_crd", "possible_firm_name"]


TEAM_INFO_PACE = 1.0      # team_info returns 429 at the 0.25 s pace used elsewhere (2026-09-20)
BACKOFF = [5, 15, 30, 60, 120]


def team_info(c: FintrxClient, team_id: int) -> dict:
    p = TEAM_INFO_DIR / f"{team_id}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    for attempt in range(len(BACKOFF) + 1):
        try:
            r = c.request("GET", f"/private_wealth_teams/{team_id}/team_info")
            break
        except FintrxAPIError as e:
            if getattr(e, "status", None) == 429 and attempt < len(BACKOFF):
                time.sleep(BACKOFF[attempt])
                continue
            raise
    t = r.get("team") or {}
    TEAM_INFO_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")
    time.sleep(TEAM_INFO_PACE)
    return t


def decide(cand: dict) -> str:
    link = cand.get("link")
    if link is None:
        return "review"
    # a shared corporate website (raymondjames.com on every Raymond James team) must not accept on its own
    if cand["domain_equal"] and link >= REVIEW_MIN:
        return "accept"
    if cand["parent_domain"] and link >= ACCEPT_WITH_PARENT:
        return "accept"
    if cand["city_equal"] and link >= ACCEPT_STRONG:
        return "accept"
    if link >= REVIEW_MIN:
        return "review"
    return "reject"


def build_state(row: dict, cands: list[dict]) -> dict:
    return {"hubspot": {"name": row[COL_NAME], "city": row.get(COL_CITY) or "", "domain": row["_domain"]},
            "candidates": [{"idx": i, "team_name": c["team_name"], "website": c["website"], "street": c["street"],
                            "city": c["team_city"], "state": c["team_state"], "parent_firm": c["parent_name"],
                            "hubspot_domain_reps_belong_to_parent_firm": bool(c["parent_domain"])}
                           for i, c in enumerate(cands)]}


def build_questions(cands: list[dict]) -> dict:
    q = {}
    for i, _ in enumerate(cands):
        q[f"link_{i}"] = jev.score(
            {"question": f"Is the advisor team `candidates[{i}]` the same business as the company in `hubspot`?",
             "compare": [f"`candidates[{i}].team_name`", "`hubspot.name`"],
             "supporting": [f"`candidates[{i}].website` versus `hubspot.domain`",
                            f"`candidates[{i}].city` versus `hubspot.city`",
                            f"`candidates[{i}].hubspot_domain_reps_belong_to_parent_firm`"],
             "note": "Generic words (Wealth, Financial, Advisors, Group, Partners, LLC) are noise. A different website "
                     "and a different city together mean a different business even when the names match."},
            LEVELS)
    return q


def ask(row: dict, cands: list[dict]) -> dict:
    try:
        r = jev.ask(build_state(row, cands), build_questions(cands))
        return {"record_id": row[COL_ID], "model": r.get("model"), "answers": r["answers"], "items": [c["team_id"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        log_error("teams_list_jev", row[COL_ID], e)
        return {"record_id": row[COL_ID], "error": str(e)[:300], "items": [c["team_id"] for c in cands]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    src = PROJECT / args.source
    df = pd.read_csv(src, dtype=str).fillna("")
    if args.limit:
        df = df.head(args.limit)
    df["_domain"] = df[COL_DOMAIN].map(extract_domain)
    df.insert(0, "source_row", range(len(df)))
    rows = df.to_dict("records")
    print(f"{len(rows)} companies", flush=True)

    # 1. name candidates against the team universe (reuses the firm matcher over team rows)
    teams = load_teams()
    by_id = {t["item_id"]: t for t in teams}
    ux = UniverseIndex(teams)
    name_rows = match_all(df.rename(columns={COL_NAME: "Company name"}).assign(**{"Record ID": df[COL_ID], "State/Region (Global)": ""}),
                          ux, TOP, NAME_CUTOFF)
    by_row: dict[int, list[dict]] = {}
    for r in name_rows:
        by_row.setdefault(int(r["source_row"]), []).append(r)
    print(f"{len(by_row)} companies with a team-name candidate", flush=True)

    # 2. domain -> parent firms (reps typeahead), from the shared domain cache
    cache = load_cache()
    todo = sorted({r["_domain"] for r in rows if r["_domain"] and r["_domain"] not in cache})
    c = FintrxClient()
    if todo:
        print(f"{len(todo)} domains to look up", flush=True)
        for d in todo:
            try:
                cache[d] = firms_for_domain(c, d)
            except FintrxAuthError:
                raise
            except Exception as e:  # noqa: BLE001
                log_error("teams_list_domain", d, e)
                cache[d] = {"_error": 1}
            paced()
        save_cache(cache)
    fux = UniverseIndex(load_universe())
    firm_by_norm = {n: fux.rows[i]["item_id"] for n, i in fux.exact.items()}

    def parent_ids(domain: str) -> set[int]:
        out = set()
        for firm in (cache.get(domain) or {}):
            if firm.startswith("_"):
                continue
            i = firm_by_norm.get(normalize(firm))
            if i is not None:
                out.add(int(i))
        return out

    # 3. team_info per candidate, then flags
    need_ids = sorted({int(r["fintrx_item_id"]) for v in by_row.values() for r in v})
    print(f"{len(need_ids)} candidate teams to fetch, {sum(1 for i in need_ids if not (TEAM_INFO_DIR / f'{i}.json').exists())} not cached", flush=True)
    eta = Eta(len(need_ids), "team_info")
    info: dict[int, dict] = {}
    try:
        for i in need_ids:
            try:
                info[i] = team_info(c, i)
            except FintrxAuthError:
                raise
            except Exception as e:  # noqa: BLE001
                log_error("teams_list_info", i, e)
                info[i] = {}
            msg = eta.tick()
            if eta.done % 200 == 0:
                print(msg, flush=True)
    except FintrxAuthError as e:
        print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
        sys.exit(2)

    cands_by_row: dict[int, list[dict]] = {}
    for sr, v in by_row.items():
        row = rows[sr]
        pids = parent_ids(row["_domain"])
        for r in v:
            tid = int(r["fintrx_item_id"])
            t, ti = by_id[tid], info.get(tid) or {}
            site = extract_domain(ti.get("website"))
            city = ti.get("city") or t.get("city") or ""
            cands_by_row.setdefault(sr, []).append(dict(
                team_id=tid, team_name=t["name"], name_score=float(r["score"]), website=ti.get("website") or "",
                street=" ".join(x for x in (ti.get("address") or "", ti.get("address_2") or "") if x),
                team_city=city, team_state=ti.get("state_code") or t.get("state") or "",
                parent_name=ti.get("parent_name") or t.get("parent_firm_name") or "",
                parent_crd=ti.get("crd_id") or t.get("parent_crd"),
                domain_equal=bool(row["_domain"]) and row["_domain"] == site,
                city_equal=bool(row.get(COL_CITY)) and normalize(row[COL_CITY]) == normalize(city),
                parent_domain=bool(t.get("parent_firm_id")) and int(t["parent_firm_id"]) in pids))

    # 4. Jev on every row with candidates (cached by record id + candidate list)
    jcache = {} if args.force else {r["record_id"]: r for r in read_jsonl(JEV_LOG) if "answers" in r}
    for sr, cands in cands_by_row.items():
        rid = rows[sr][COL_ID]
        if rid in jcache and jcache[rid].get("items") != [c["team_id"] for c in cands]:
            del jcache[rid]
    need = [sr for sr in cands_by_row if rows[sr][COL_ID] not in jcache]
    print(f"{len(need)} rows need Jev", flush=True)
    with ThreadPoolExecutor(max_workers=JEV_WORKERS) as ex:
        for res in ex.map(lambda sr: ask(rows[sr], cands_by_row[sr]), need):
            jcache[res["record_id"]] = res
            append_jsonl(JEV_LOG, [res])

    # 5. decide and write
    firm_review = {}
    for r in read_csv(MATCHES):
        if r["row_outcome"] == "review" and r.get("crd_id"):
            rid = str(int(float(r["record_id"])))
            if rid not in firm_review or float(r["link2"] or 0) > float(firm_review[rid]["link2"] or 0):
                firm_review[rid] = r
    out, status = [], Counter()
    for sr, row in enumerate(rows):
        cands = cands_by_row.get(sr, [])
        ans = (jcache.get(row[COL_ID]) or {}).get("answers") or {}
        for i, cd in enumerate(cands):
            a = ans.get(f"link_{i}")
            cd["link"] = round(a["score"], 3) if a else None
            cd["decision"] = decide(cd)
        acc = [cd for cd in cands if cd["decision"] == "accept"]
        chosen, st = None, "no_candidate" if not cands else "no_match"
        if len(acc) == 1:
            chosen, st = acc[0], "accept"
        elif len(acc) > 1:
            st = "review_multiple_accepts"
        elif any(cd["decision"] == "review" for cd in cands):
            st = "review"
        status[st] += 1
        o = {k: v for k, v in row.items() if k not in ("source_row", "_domain")}
        o[COL_TEAM_ID] = str(chosen["team_id"]) if chosen else ""
        o[COL_PARENT_CRD] = str(chosen["parent_crd"]) if chosen and chosen.get("parent_crd") else ""
        o["fintrx_team_name"] = chosen["team_name"] if chosen else ""
        o["fintrx_team_city"] = chosen["team_city"] if chosen else ""
        o["fintrx_team_website"] = chosen["website"] if chosen else ""
        o["fintrx_parent_name"] = chosen["parent_name"] if chosen else ""
        o["match_evidence"] = "" if not chosen else ("website" if chosen["domain_equal"] else "domain reps under parent" if chosen["parent_domain"] else "name and city")
        o["match_confidence"] = chosen["link"] if chosen else ""
        o["status"] = st
        o["fintrx_team_url"] = f"https://platform.fintrx.com/private_wealth_group/{chosen['team_id']}" if chosen else ""
        o["alt_candidates"] = "; ".join(f"{cd['team_id']}:{cd['team_name']} ({cd['decision']}, link={cd['link']}, site={'=' if cd['domain_equal'] else '≠'}, city={'=' if cd['city_equal'] else '≠'})"
                                        for cd in cands if cd is not chosen)
        fr = firm_review.get(str(int(float(row[COL_ID]))))
        o["possible_firm_crd"] = fr["crd_id"] if fr else ""
        o["possible_firm_name"] = fr["matched_name"] if fr else ""
        out.append(o)
    dest = DATA_OUT / f"{src.stem}-enriched.csv"
    write_csv(dest, out, list(out[0].keys()))
    print(f"wrote {dest}: {len(out)} rows; status {dict(status)}")
    print("evidence for accepts:", dict(Counter(o["match_evidence"] for o in out if o["status"] == "accept")))


if __name__ == "__main__":
    main()
