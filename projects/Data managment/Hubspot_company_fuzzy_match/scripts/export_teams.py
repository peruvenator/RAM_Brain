"""Export every identified wealth team to data/output/wealth_teams.csv with the FINTRX parent company.

Run:  python scripts/export_teams.py
fintrx_parent_company comes from the team record's parent_firm block (FINTRX's own parent name).
parent_company_by_crd is the firm name from the cached firm detail record with the same CRD, when we
have one, and parent_name_agrees says whether the two agree after normalization. Exact-CRD join, no fuzzy.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA_FX, DATA_OUT, DETAILS_CSV, read_csv, read_jsonl, write_csv  # noqa: E402
from normalize import normalize  # noqa: E402

TEAMS = DATA_FX / "teams.jsonl"
TEAM_MATCHES = DATA_OUT / "team_matches.csv"
OUT = DATA_OUT / "wealth_teams.csv"
FIELDS = ["record_id", "hubspot_company", "Fintrx_wealth_team_id", "fintrx_team_name", "fintrx_team_parent_crd",
          "fintrx_parent_company", "fintrx_parent_firm_id", "parent_company_by_crd", "parent_name_agrees",
          "team_city", "team_state", "team_size", "team_aum", "match_confidence", "match_evidence", "fintrx_team_url",
          "fintrx_parent_url"]


def main() -> None:
    teams = {r["team_id"]: r for r in read_jsonl(TEAMS)}
    by_crd = {}
    for d in read_csv(DETAILS_CSV):
        if d.get("crd_id"):
            by_crd.setdefault(str(int(float(d["crd_id"]))), d)
    rows = []
    for r in read_csv(TEAM_MATCHES):
        if r["row_outcome"] != "accept" or r["chosen"] != "True":
            continue
        t = teams.get(int(float(r["team_id"])), {})
        crd = str(int(float(r["parent_crd"]))) if r.get("parent_crd") else ""
        det = by_crd.get(crd)
        parent = t.get("parent_firm_name") or r.get("parent_firm_name") or ""
        by_crd_name = (det or {}).get("primary_business_name") or ""
        agrees = "" if not det else (normalize(parent) == normalize(by_crd_name) or normalize(parent) == normalize((det or {}).get("legal_name") or ""))
        rows.append(dict(
            record_id=str(int(float(r["record_id"]))), hubspot_company=r["source_name"],
            Fintrx_wealth_team_id=str(int(float(r["team_id"]))), fintrx_team_name=r["team_name"],
            fintrx_team_parent_crd=crd, fintrx_parent_company=parent, fintrx_parent_firm_id=t.get("parent_firm_id") or "",
            parent_company_by_crd=by_crd_name, parent_name_agrees=agrees,
            team_city=t.get("city") or "", team_state=t.get("state") or "", team_size=t.get("size") or "",
            team_aum=t.get("aum") or "", match_confidence=r["link"],
            match_evidence="domain reps under parent firm" if r["parent_domain_match"] == "True" else "name and state",
            fintrx_team_url=f"https://platform.fintrx.com/private_wealth_group/{int(float(r['team_id']))}",
            fintrx_parent_url=f"https://platform.fintrx.com/ria_investor/{t['parent_firm_id']}" if t.get("parent_firm_id") else ""))
    rows.sort(key=lambda x: (x["fintrx_parent_company"], x["fintrx_team_name"]))
    write_csv(OUT, rows, FIELDS)
    n_chk = sum(1 for x in rows if x["parent_company_by_crd"])
    n_ok = sum(1 for x in rows if x["parent_name_agrees"] is True)
    print(f"wrote {OUT}: {len(rows)} teams, {len({x['fintrx_parent_company'] for x in rows})} distinct parents; "
          f"{n_chk} cross-checked by CRD, {n_ok} agree, {n_chk - n_ok} differ")


if __name__ == "__main__":
    main()
