"""Step 3: resolve each Excel domain to FINTRX firm names through the reps typeahead.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/lookup_domain.py [--limit N]
Cache: data/fintrx/domain_cache.json (one call per unique domain, ever).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_DOMAIN, COL_DOMAIN, COL_NAME, COL_RECORD_ID, DOMAIN_CACHE,  # noqa: E402
                    Eta, extract_domain, load_source, log_error, paced, write_csv)
from match import UniverseIndex, load_universe  # noqa: E402
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

FIELDS = ["source_row", "record_id", "source_name", "domain", "matched_name", "fintrx_item_id",
          "rep_count", "method"]
MAP_CUTOFF = 95.0


def firms_for_domain(c: FintrxClient, domain: str) -> dict[str, int]:
    r = c.request("POST", "/global_search/search_ria_reps", form={"query": domain})
    counts: dict[str, int] = {}
    for rep in r.get("reps") or []:
        for f in rep.get("firms") or []:
            counts[f] = counts.get(f, 0) + 1
    return counts


def load_cache() -> dict:
    return json.loads(DOMAIN_CACHE.read_text(encoding="utf-8")) if DOMAIN_CACHE.exists() else {}


def save_cache(cache: dict) -> None:
    DOMAIN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DOMAIN_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def map_firm(ux: UniverseIndex, firm_name: str):
    i = ux.lookup_exact(firm_name)
    if i is None:
        hit = ux.best(firm_name, MAP_CUTOFF)
        i = hit[0] if hit else None
    return ux.rows[i]["item_id"] if i is not None else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    df = load_source(args.limit)
    df["_domain"] = df[COL_DOMAIN].map(extract_domain)
    domains = sorted({d for d in df["_domain"] if d})
    cache = load_cache()
    todo = [d for d in domains if d not in cache]
    print(f"{len(domains)} unique domains, {len(todo)} not cached", flush=True)
    if todo:
        c = FintrxClient()
        eta = Eta(len(todo), "domains")
        try:
            for n, d in enumerate(todo, 1):
                try:
                    cache[d] = firms_for_domain(c, d)
                except FintrxAuthError:
                    raise
                except Exception as e:  # noqa: BLE001
                    log_error("lookup_domain", d, e)
                    cache[d] = {"_error": 1}
                if n % 50 == 0:
                    save_cache(cache)
                    print(eta.tick(), flush=True)
                else:
                    eta.tick()
                paced()
        except FintrxAuthError as e:
            save_cache(cache)
            print(f"AUTH ERROR, refresh the token then rerun: {e}", file=sys.stderr)
            sys.exit(2)
        save_cache(cache)
    ux = UniverseIndex(load_universe())
    rows = []
    for s in df.to_dict("records"):
        d = s["_domain"]
        if not d:
            continue
        for firm, cnt in (cache.get(d) or {}).items():
            if firm.startswith("_"):
                continue
            item_id = map_firm(ux, firm)
            rows.append(dict(source_row=s["source_row"], record_id=s[COL_RECORD_ID], source_name=s[COL_NAME],
                             domain=d, matched_name=firm, fintrx_item_id=item_id, rep_count=cnt,
                             method="domain_reps" if item_id else "domain_unmapped"))
    write_csv(CAND_DOMAIN, rows, FIELDS)
    print(f"wrote {CAND_DOMAIN}: {len(rows)} domain candidates for {len({r['source_row'] for r in rows})} rows")


if __name__ == "__main__":
    main()
