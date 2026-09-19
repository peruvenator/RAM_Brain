#!/usr/bin/env python3
"""Live SDK smoke tests against the real FINTRX API (read-only).

Run from references/fintrx:  %USERPROFILE%/.venvs/fintrx/Scripts/python tests/test_live2.py
Requires a valid token in 1Password (op://ReSolve/Fintrix). If stale: python capture_token.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fintrx_sdk.client import FintrxClient  # noqa: E402

PASS = []
FAIL = []


def check(name, fn):
    try:
        val = fn()
        PASS.append(name)
        print("PASS  %s" % name)
        return val
    except Exception as e:
        FAIL.append((name, str(e)[:180]))
        print("FAIL  %s -> %s" % (name, str(e)[:180]))
        return None


def main():
    c = FintrxClient()
    check("health", c.health_check)

    # RIA firm detail (find a firm id from search first)
    ria = check("ria_search", lambda: c.ria_search())
    if ria:
        invs = ria.get("investors", [])
        if invs:
            fid = invs[0]["id"]
            check("ria_firm %d" % fid, lambda: c.ria_firm(fid))
            check("ria_firm custodians", lambda: c.ria_firm_sub(fid, "custodians_table"))
            check("ria_firm disclosures", lambda: c.ria_firm_sub(fid, "disclosures"))
            check("ria_firm aum_accounts", lambda: c.ria_firm_sub(fid, "aum_accounts"))
            check("ria_firm notes", lambda: c.ria_firm_sub(fid, "notes"))
            check("ria_firm notable_changes", lambda: c.ria_firm_sub(fid, "notable_changes"))
            check("ria_firm related_entities", lambda: c.ria_firm_sub(fid, "related_entities"))
            check("entity_highlights", lambda: c.entity_highlights(fid))

    # contacts + affinity: get contacts from contacts_search
    rc = check("ria_contacts_search", lambda: c.ria_contacts_search())
    if rc:
        contacts = rc.get("contacts") or []
        if contacts:
            cid = contacts[0]["id"]
            check("contact_detail %d" % cid, lambda: c.contact_detail(cid))

    # direct transactions
    check("direct_transactions", c.direct_transactions)
    check("direct_transactions_statistics", c.direct_transactions_statistics)
    check("transactions_heatmap industry", lambda: c.transactions_heatmap("investments_by_industry"))
    check("funded_companies_locations", c.funded_companies_locations)
    check("ma_transactions", c.ma_transactions)
    check("ma_transactions_options", c.ma_transactions_options)
    check("last_ma_transaction", c.last_ma_transaction)

    # saved filters
    check("saved_filters", c.saved_filters)

    c.close()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for name, err in FAIL:
        print("  FAILED %s: %s" % (name, err))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
