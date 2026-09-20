"""Fill 'Fintrx wealth team ID' and 'Wealth Team (Fintrx)' on a HubSpot contacts export, keyed by the
contact's FINTRX rep CRD. Exact lookups only, no fuzzy matching, no Jev.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/enrich_contacts_teams.py \
          --source "hubspot-crm-exports-financial-advisors-u-s-all-2026-09-20.csv" [--limit N]
Output: data/output/<source stem>-teams-enriched.csv (all original columns, the two target columns
filled, plus trace columns). Cache: data/fintrx/contact_teams_cache.json keyed by CRD.

Team choice when a contact sits on several teams, in order:
  1. the team whose name matches the contact's Company Name
  2. a team we identified for the companies list (data/output/wealth_teams.csv)
  3. the team whose name matches the pre-filled 'Wealth Team (Fintrx)' value
  otherwise the two columns stay blank, status=multiple_teams, and all teams are listed in all_teams.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA_FX, DATA_OUT, PROJECT, Eta, is_blank, log_error, paced, read_csv  # noqa: E402
from normalize import normalize  # noqa: E402
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

CACHE = DATA_FX / "contact_teams_cache.json"
WEALTH_TEAMS = DATA_OUT / "wealth_teams.csv"
COL_CRD = "Fintrx Contact CRD ID"
COL_TEAM_ID = "Fintrx wealth team ID"
COL_TEAM_NAME = "Wealth Team (Fintrx)"
COL_COMPANY = "Company Name"
COL_RECORD = "Record ID"
BATCH = 100


def _crd(v) -> str:
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return ""


def fetch_batch(c: FintrxClient, crds: list[str]) -> dict[str, dict]:
    """CRD -> {contact_id, name, hubspot_id, teams:[{team_id, team_name, parent_crd}]} for one batch."""
    out: dict[str, dict] = {}
    page = 1
    while True:
        d = c.ria_contacts_search(page=page, per_page=BATCH,
                                  extra_filters={"contacts_contact_crd_id": crds, "selectContactsContactCrdId": crds})
        rows = d.get("contacts") or []
        extra = d.get("extra_info") or {}
        for r in rows:
            e = extra.get(str(r["id"])) or {}
            crd = _crd(r.get("ria_contact_crd_id"))
            if not crd:
                continue
            teams = [{"team_id": t.get("team_id"), "team_name": t.get("team_name"), "parent_crd": t.get("parent_crd")}
                     for t in (e.get("pwt_teams") or [])]
            rec = {"contact_id": r["id"], "name": r.get("name"), "hubspot_id": e.get("hubspot_id"),
                   "primary_firm": e.get("entity_name"), "teams": teams}
            if crd in out:                      # a CRD mapping to two FINTRX contact records: keep the union of teams
                seen = {t["team_id"] for t in out[crd]["teams"]}
                out[crd]["teams"] += [t for t in teams if t["team_id"] not in seen]
            else:
                out[crd] = rec
        if len(rows) < BATCH:
            break
        page += 1
        paced()
    return out


def choose_team(teams: list[dict], company: str, prev_name: str, identified: set[str]) -> tuple[dict | None, str]:
    if not teams:
        return None, "no_team"
    if len(teams) == 1:
        return teams[0], "single_team"
    cn = normalize(company) if not is_blank(company) else ""
    if cn:
        hit = [t for t in teams if normalize(t["team_name"] or "") == cn]
        if len(hit) == 1:
            return hit[0], "multiple_teams_company_name"
    hit = [t for t in teams if str(t["team_id"]) in identified]
    if len(hit) == 1:
        return hit[0], "multiple_teams_identified"
    pn = normalize(prev_name) if not is_blank(prev_name) else ""
    if pn:
        hit = [t for t in teams if normalize(t["team_name"] or "") == pn]
        if len(hit) == 1:
            return hit[0], "multiple_teams_prev_name"
    return None, "multiple_teams"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="contacts CSV, relative to the project folder")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    src = PROJECT / args.source
    df = pd.read_csv(src, dtype=str)
    if args.limit:
        df = df.head(args.limit)
    df["_crd"] = df[COL_CRD].map(_crd)
    crds = sorted({c for c in df["_crd"] if c})
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = [c for c in crds if c not in cache]
    print(f"{len(df)} contacts, {len(crds)} unique CRDs, {len(todo)} not cached", flush=True)
    if todo:
        c = FintrxClient()
        eta = Eta((len(todo) + BATCH - 1) // BATCH, "batches")
        try:
            for i in range(0, len(todo), BATCH):
                chunk = todo[i:i + BATCH]
                try:
                    got = fetch_batch(c, chunk)
                except FintrxAuthError:
                    raise
                except Exception as e:  # noqa: BLE001
                    log_error("contact_teams", chunk[0], e)
                    got = {}
                for crd in chunk:
                    cache[crd] = got.get(crd, {"contact_id": None, "name": None, "hubspot_id": None, "primary_firm": None,
                                               "teams": [], "not_found": crd not in got})
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                CACHE.write_text(json.dumps(cache), encoding="utf-8")
                print(eta.tick(), flush=True)
                paced()
        except FintrxAuthError as e:
            print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
            sys.exit(2)

    identified = {r["Fintrx_wealth_team_id"] for r in read_csv(WEALTH_TEAMS)}
    out_rows, status = [], Counter()
    for rec in df.to_dict("records"):
        info = cache.get(rec["_crd"]) or {}
        teams = info.get("teams") or []
        prev_id, prev_name = rec.get(COL_TEAM_ID), rec.get(COL_TEAM_NAME)
        chosen, st = choose_team(teams, rec.get(COL_COMPANY), prev_name, identified)
        if not rec["_crd"]:
            st = "no_crd"
        elif info.get("not_found"):
            st = "crd_not_in_fintrx"
        status[st] += 1
        row = {k: v for k, v in rec.items() if k != "_crd"}
        row[COL_TEAM_ID] = str(chosen["team_id"]) if chosen else ""
        row[COL_TEAM_NAME] = chosen["team_name"] if chosen else ""
        row["fintrx_team_parent_crd"] = str(chosen["parent_crd"]) if chosen and chosen.get("parent_crd") else ""
        row["fintrx_contact_id"] = info.get("contact_id") or ""
        row["fintrx_primary_firm"] = info.get("primary_firm") or ""
        row["status"] = st
        row["all_teams"] = "; ".join(f"{t['team_id']}:{t['team_name']}" for t in teams) if len(teams) > 1 else ""
        row["hubspot_prev_team_id"] = "" if is_blank(prev_id) else prev_id
        row["hubspot_prev_team_name"] = "" if is_blank(prev_name) else prev_name
        row["prev_name_changed"] = bool(chosen) and not is_blank(prev_name) and normalize(prev_name) != normalize(chosen["team_name"] or "")
        hs = info.get("hubspot_id")
        row["fintrx_synced_hubspot_id"] = hs or ""
        row["synced_id_matches_record"] = "" if not hs else str(hs) == _crd(rec.get(COL_RECORD))
        out_rows.append(row)
    out = DATA_OUT / f"{src.stem}-teams-enriched.csv"
    pd.DataFrame(out_rows).to_csv(out, index=False)
    filled = sum(1 for r in out_rows if r[COL_TEAM_ID])
    print(f"wrote {out}: {len(out_rows)} rows, {filled} with a team id; status {dict(status)}")
    print(f"pre-filled names changed: {sum(1 for r in out_rows if r['prev_name_changed'])}; "
          f"FINTRX sync id matches HubSpot record id: {sum(1 for r in out_rows if r['synced_id_matches_record'] is True)}")


if __name__ == "__main__":
    main()
