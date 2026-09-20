"""Step 8 (explicit, separate): write accepted FINTRX ids onto HubSpot company records by Record ID.

Run:  python scripts/push_hubspot.py --dry-run [--limit N] [--only firm|team]
      python scripts/push_hubspot.py --limit 10          # real write, first 10 records
      python scripts/push_hubspot.py                     # real write, everything accepted
      python scripts/push_hubspot.py --overwrite         # also replace differing existing values

Reads matches.csv (firm accepts -> fintrx_firm_crd_id) and team_matches.csv (team accepts ->
fintrx_wealth_team_id + wealth_team_parent_crd). Reads the current HubSpot values first:
  equal     -> skipped, nothing written
  empty     -> written
  different -> reported as a conflict and NOT written unless --overwrite
Every decision is appended to data/output/hubspot_push_log.csv. Token: HUBSPOT_TOKEN in the root .env.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA_OUT, MATCHES, RAM_BRAIN, read_csv  # noqa: E402

TEAM_MATCHES = DATA_OUT / "team_matches.csv"
PUSH_LOG = DATA_OUT / "hubspot_push_log.csv"
API = "https://api.hubapi.com/crm/v3/objects/companies"
PROPS = ["fintrx_firm_crd_id", "fintrx_wealth_team_id", "wealth_team_parent_crd"]
BATCH = 100
PACE = 0.25


def load_token() -> str:
    env = RAM_BRAIN / ".env"
    for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip().startswith("HUBSPOT_TOKEN="):
            tok = line.split("=", 1)[1].strip().strip("'\"")
            if tok:
                return tok
    sys.exit("HUBSPOT_TOKEN not found in RAM_Brain/.env")


def api(token: str, path: str, body: dict) -> dict:
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="ignore")[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"HubSpot HTTP {e.code} on {path}: {detail}") from None
    raise RuntimeError("unreachable")


def _id(v) -> str:
    return str(int(float(v)))


def desired_values(only: str | None) -> dict[str, dict[str, str]]:
    """record_id -> {property: value} from the accepted firm and team matches."""
    want: dict[str, dict[str, str]] = {}
    if only in (None, "firm"):
        for r in read_csv(MATCHES):
            if r["row_outcome"] == "accept" and r["chosen"] == "True" and r.get("crd_id"):
                want.setdefault(_id(r["record_id"]), {})["fintrx_firm_crd_id"] = _id(r["crd_id"])
    if only in (None, "team"):
        for r in read_csv(TEAM_MATCHES):
            if r["row_outcome"] == "accept" and r["chosen"] == "True" and r.get("team_id"):
                d = want.setdefault(_id(r["record_id"]), {})
                d["fintrx_wealth_team_id"] = _id(r["team_id"])
                if r.get("parent_crd"):
                    d["wealth_team_parent_crd"] = _id(r["parent_crd"])
    return want


def read_current(token: str, ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        d = api(token, "/batch/read", {"inputs": [{"id": x} for x in chunk], "properties": PROPS + ["name"]})
        for o in d.get("results", []):
            out[o["id"]] = o.get("properties") or {}
        time.sleep(PACE)
    return out


def plan(want: dict[str, dict[str, str]], current: dict[str, dict], overwrite: bool) -> tuple[list[dict], list[dict]]:
    """Returns (updates, log_rows). updates: [{id, properties}] ready for batch/update."""
    updates, log = [], []
    for rid, props in want.items():
        cur = current.get(rid)
        if cur is None:
            log.append(dict(record_id=rid, name="", property="*", before="", after="", status="not_found"))
            continue
        to_write = {}
        for p, new in props.items():
            old = (cur.get(p) or "").strip()
            if old == new:
                status = "equal_skip"
            elif not old:
                status, to_write[p] = "write", new
            elif overwrite:
                status, to_write[p] = "overwrite", new
            else:
                status = "conflict_skip"
            log.append(dict(record_id=rid, name=cur.get("name", ""), property=p, before=old, after=new if status != "conflict_skip" else old, status=status))
        if to_write:
            updates.append({"id": rid, "properties": to_write})
    return updates, log


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="only the first N records (by record id order in the match files)")
    ap.add_argument("--only", choices=["firm", "team"], default=None)
    ap.add_argument("--overwrite", action="store_true", help="replace values that differ from ours")
    args = ap.parse_args()

    token = load_token()
    want = desired_values(args.only)
    ids = list(want)[: args.limit] if args.limit else list(want)
    want = {k: want[k] for k in ids}
    print(f"{len(want)} records with accepted ids to consider", flush=True)
    current = read_current(token, ids)
    updates, log = plan(want, current, args.overwrite)
    print("plan:", dict(Counter(r["status"] for r in log)))
    print(f"{len(updates)} records would be updated")
    for u in updates[:10]:
        print("  ", u["id"], current[u["id"]].get("name", "")[:30], u["properties"])
    if args.dry_run:
        print("dry run, nothing written")
        return
    written = 0
    for i in range(0, len(updates), BATCH):
        chunk = updates[i:i + BATCH]
        d = api(token, "/batch/update", {"inputs": chunk})
        written += len(d.get("results", []))
        if d.get("errors"):
            print("batch errors:", json.dumps(d["errors"])[:500], file=sys.stderr)
        time.sleep(PACE)
    stamp = datetime.now().isoformat(timespec="seconds")
    new = not PUSH_LOG.exists()
    with PUSH_LOG.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "record_id", "name", "property", "before", "after", "status"])
        if new:
            w.writeheader()
        for r in log:
            w.writerow(dict(r, timestamp=stamp))
    print(f"wrote {written} records to HubSpot; log appended to {PUSH_LOG}")


if __name__ == "__main__":
    main()
