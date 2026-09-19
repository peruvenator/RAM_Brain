#!/usr/bin/env python3
"""Live SDK smoke tests against the real FINTRX API (read-only).

Run from references/fintrx:  %USERPROFILE%/.venvs/fintrx/Scripts/python tests/test_live.py
Requires a valid token in 1Password (op://ReSolve/Fintrix). If stale: python capture_token.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fintrx_sdk.client import FintrxClient  # noqa: E402
from fintrx_sdk.auth import FintrxAuthError  # noqa: E402

PASS = []
FAIL = []


def check(name, fn):
    try:
        val = fn()
        PASS.append(name)
        print("PASS  %s" % name)
        return val
    except Exception as e:
        FAIL.append((name, str(e)[:200]))
        print("FAIL  %s -> %s" % (name, str(e)[:200]))
        return None


def main():
    c = FintrxClient()

    # 1. session
    h = check("health_check", c.health_check)
    if h is not None:
        assert h.get("is_logged_in") is True, "not logged in with stored credential"
    check("me", c.me)
    check("admin_permission", c.admin_permission)
    check("team_users", c.team_users)
    check("dashboard_statistics", c.dashboard_statistics)
    check("remaining_downloads", c.remaining_downloads)

    # 2. FO power search
    fo = check("fo_search page1", lambda: c.fo_search())
    if fo:
        invs = fo.get("investors", [])
        assert isinstance(invs, list), "investors missing"
        print("      FO investors page1: %d items, status=%s" % (len(invs), fo.get("status")))
    fo2 = check("fo_search_all 2 pages", lambda: list(c.fo_search_all(max_pages=2)))
    if fo2:
        print("      FO search_all: %d items over <=2 pages" % len(fo2))
    check("fo_contacts_search", lambda: c.fo_contacts_search())
    check("fo_transactions_search", lambda: c.fo_transactions_search())
    check("fo_companies_search", lambda: c.fo_companies_search())

    # 3. RIA power search + counts
    ria = check("ria_search page1", lambda: c.ria_search())
    if ria:
        invs = ria.get("investors", [])
        print("      RIA investors page1: %d items" % len(invs))
    counts = check("ria_counts", c.ria_counts)
    if counts:
        print("      RIA counts: %s" % counts)
    check("ria_contacts_search", lambda: c.ria_contacts_search())
    check("ria_teams_search", lambda: c.ria_teams_search())
    ria2 = check("ria_search_all 2 pages", lambda: list(c.ria_search_all(max_pages=2)))
    if ria2:
        print("      RIA search_all: %d items over <=2 pages" % len(ria2))

    # 4. options
    check("ria_options custodians", lambda: c.ria_options("custodians"))
    check("ria_options specialties", lambda: c.ria_options("specialties"))
    check("power_options investors", lambda: c.power_options("investors"))

    # 5. lists / notifications / news
    check("lists_folders", c.lists_folders)
    check("combined_lists", c.combined_lists)
    check("notifications_count", c.notifications_count)
    check("news", c.news)

    # 6. global typeahead
    gs = check("global_search 'Point72'", lambda: c.global_search("Point72", ["search_ria_entities"]))
    if gs:
        ents = gs["search_ria_entities"].get("entities", [])
        print("      global_search entities: %d" % len(ents))

    c.close()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    if FAIL:
        for name, err in FAIL:
            print("  FAILED %s: %s" % (name, err))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
