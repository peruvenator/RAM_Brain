"""FINTRX API client (platform.fintrx.com/v1/user).

Feature-parity client for the web UI surface discovered by CDP capture:
  - power search (Family Offices + RIA/BD): investors/contacts/teams/transactions/companies
  - counts for every search family
  - filter option vocabularies (auto-paginated where the server paginates)
  - global typeahead search across all categories
  - session/user endpoints (health, permissions, quotas, dashboard)
  - lists & folders, notifications, news, enrichment history
  - 13-F holdings by firm CRD (ria_investments/*)

All calls require the session credential pair (X-User-Token / X-User-Email),
resolved by fintrx_sdk.auth.load_credential() from the environment or 1Password.
"""
from __future__ import annotations

import json
import time
from typing import Any, Iterator

import httpx

from .auth import load_credential, FintrxAuthError

BASE = "https://platform.fintrx.com"
API = BASE + "/v1/user"


class FintrxAPIError(RuntimeError):
    def __init__(self, status: int, url: str, body: str):
        super().__init__("HTTP %d on %s: %s" % (status, url, body[:200]))
        self.status = status
        self.url = url
        self.body = body


class FintrxClient:
    def __init__(self, timeout: float = 30.0, max_retries: int = 3, per_page: int = 50):
        self._timeout = timeout
        self._max_retries = max_retries
        self._per_page = per_page
        self._cred = None
        self._http: httpx.Client | None = None

    # -- auth ---------------------------------------------------------------
    def _ensure_cred(self) -> dict:
        if self._cred is None:
            self._cred = load_credential()
        return self._cred

    def refresh_auth(self) -> None:
        """Drop the cached credential and HTTP client; next call re-reads 1Password."""
        self._cred = None
        if self._http:
            self._http.close()
            self._http = None
        self._ensure_cred()

    def _client(self) -> httpx.Client:
        if self._http is None:
            cred = self._ensure_cred()
            self._http = httpx.Client(
                base_url=API,
                headers={
                    "X-User-Token": cred["token"],
                    "X-User-Email": cred["email"],
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
        return self._http

    # -- core request -------------------------------------------------------
    def request(self, method: str, path: str, *, form: dict | None = None,
                params: dict | None = None) -> Any:
        c = self._client()
        url = path if path.startswith("http") else path
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                if form is not None:
                    r = c.request(method, url, data=form, params=params)
                else:
                    r = c.request(method, url, params=params)
            except httpx.HTTPError as e:
                last_exc = e
                time.sleep(min(2 ** attempt, 8))
                continue
            if r.status_code in (401, 403):
                raise FintrxAuthError(
                    "HTTP %d on %s: the FINTRX session token is expired or invalid. "
                    "Refresh it: run start-fintrx-chrome.cmd, log in, then "
                    "auth_bridge_capture()." % (r.status_code, str(r.url)))
            if r.status_code >= 500:
                last_exc = FintrxAPIError(r.status_code, str(r.url), r.text)
                time.sleep(min(2 ** attempt, 8))
                continue
            if r.status_code >= 400:
                raise FintrxAPIError(r.status_code, str(r.url), r.text)
            if not r.content:
                return None
            ctype = r.headers.get("content-type", "")
            if "json" in ctype:
                return r.json()
            return r.text
        raise last_exc  # type: ignore[misc]

    # -- low-level helpers ----------------------------------------------------
    @staticmethod
    def _power_form(payload: dict) -> dict:
        """Encode a power_search payload the way the SPA does."""
        import json as _json
        from urllib.parse import quote
        return {"power_search": _json.dumps(payload, separators=(",", ":"))}

    # -- session / user -------------------------------------------------------
    def health_check(self) -> dict:
        return self.request("GET", "/users/health_check")

    def me(self) -> dict:
        return self.request("GET", "/users")

    def admin_permission(self) -> dict:
        return self.request("GET", "/users/admin_permission")

    def team_users(self) -> list:
        return self.request("GET", "/users/team_users")

    def remaining_downloads(self) -> dict:
        return self.request("GET", "/users/remaining_downloads")

    def enrichment_quota(self) -> dict:
        return self.request("GET", "/users/enrichment_quota_limit")

    def dashboard_statistics(self) -> dict:
        return self.request("GET", "/dashboard/number_statistics")

    def dashboard_widgets(self) -> dict:
        return self.request("GET", "/dashboard/selected_widgets")

    def recently_viewed(self) -> dict:
        return self.request("GET", "/dashboard/recently_viewed")

    # -- global typeahead search ----------------------------------------------
    def global_search(self, query: str, categories: list[str] | None = None) -> dict:
        """Run the dashboard typeahead across one or all categories."""
        cats = categories or [
            "search_ria_entities", "search_ria_reps", "search_private_wealth_teams",
            "search_contacts", "search_previous_contacts", "search_investors",
            "search_funded_companies", "search_funded_properties", "search_lists",
        ]
        out = {}
        for cat in cats:
            out[cat] = self.request("POST", "/global_search/" + cat,
                                    form={"query": query})
        return out

    # -- power search: Family Offices ------------------------------------------
    def fo_search(self, search_value: str = "", page: int = 1, per_page: int | None = None,
                  sort_direction: str = "desc", extra_filters: dict | None = None) -> dict:
        payload = {"status": "", "search_value": search_value,
                   "sort_investors_direction": sort_direction,
                   "page": page, "per_page": per_page or self._per_page}
        if extra_filters:
            payload.update(extra_filters)
        return self.request("POST", "/power_search/investors_search",
                            form=self._power_form(payload))

    def fo_search_all(self, search_value: str = "", per_page: int | None = None,
                      max_pages: int | None = None) -> Iterator[dict]:
        """Iterate every matching Family Office (auto-pagination)."""
        page = 1
        while True:
            data = self.fo_search(search_value=search_value, page=page, per_page=per_page)
            items = data.get("investors", [])
            if not items:
                return
            yield from items
            total_pages = (data.get("pagy") or {}).get("vars", {}).get("pages")
            if total_pages and page >= total_pages:
                return
            if max_pages and page >= max_pages:
                return
            page += 1

    def fo_contacts_search(self, page: int = 1, per_page: int | None = None,
                           extra_filters: dict | None = None) -> dict:
        payload = {"status": "", "search_value": "",
                   "sort_contacts_direction": "desc",
                   "page": page, "per_page": per_page or self._per_page}
        if extra_filters:
            payload.update(extra_filters)
        return self.request("POST", "/power_search/contacts_search",
                            form=self._power_form(payload))

    def fo_transactions_search(self, page: int = 1, per_page: int | None = None) -> dict:
        payload = {"status": "", "search_value": "", "page": page,
                   "per_page": per_page or self._per_page}
        return self.request("POST", "/power_search/transactions_search",
                            form=self._power_form(payload))

    def fo_companies_search(self, page: int = 1, per_page: int | None = None) -> dict:
        payload = {"status": "", "search_value": "", "page": page,
                   "per_page": per_page or self._per_page}
        return self.request("POST", "/power_search/funded_companies_search",
                            form=self._power_form(payload))

    # -- power search: RIA & Broker Dealers --------------------------------------
    def ria_search(self, page: int = 1, per_page: int | None = None,
                   sort_direction: str = "desc", extra_filters: dict | None = None) -> dict:
        payload = {"location": "",
                   "num_of_cliens_had_financial_planning_services_last_fiscal_yr": [],
                   "exclude_num_of_cliens_had_financial_planning_services_last_fiscal_yr": False,
                   "hide_undisclosed_amounts": False, "changed": False,
                   "sort_investors_direction": sort_direction,
                   "page": page, "per_page": per_page or self._per_page}
        if extra_filters:
            payload.update(extra_filters)
        return self.request("POST", "/ria_power_search/investors_search",
                            form=self._power_form(payload))

    def ria_search_all(self, per_page: int | None = None,
                       max_pages: int | None = None) -> Iterator[dict]:
        page = 1
        while True:
            data = self.ria_search(page=page, per_page=per_page)
            items = data.get("investors", [])
            if not items:
                return
            yield from items
            total_pages = (data.get("pagy") or {}).get("vars", {}).get("pages")
            if total_pages and page >= total_pages:
                return
            if max_pages and page >= max_pages:
                return
            page += 1

    def ria_contacts_search(self, page: int = 1, per_page: int | None = None,
                            extra_filters: dict | None = None) -> dict:
        payload = {"location": "",
                   "num_of_cliens_had_financial_planning_services_last_fiscal_yr": [],
                   "exclude_num_of_cliens_had_financial_planning_services_last_fiscal_yr": False,
                   "hide_undisclosed_amounts": False, "changed": False,
                   "sort_contacts_direction": "desc",
                   "per_page": per_page or self._per_page, "page": page}
        if extra_filters:
            payload.update(extra_filters)
        return self.request("POST", "/ria_power_search/contacts_search",
                            form=self._power_form(payload))

    def ria_firm_reps(self, primary_business_name: str, page: int = 1,
                      per_page: int | None = None) -> dict:
        """Rep roster for ONE firm: contacts_search scoped by the
        primary_business_name filter (exact FINTRX business name, e.g.
        "Steelpeak Wealth, LLC"). Verified 2026-08-28: returns exactly the
        firm's contacts; extra_info carries ria_investor_id + team_connection.
        Use this instead of /ria_investors/{id}/contacts, which 404s."""
        return self.ria_contacts_search(
            page=page, per_page=per_page,
            extra_filters={"primary_business_name": [primary_business_name]})

    def ria_teams_search(self, page: int = 1, per_page: int | None = None,
                         extra_filters: dict | None = None) -> dict:
        payload = {"location": "",
                   "num_of_cliens_had_financial_planning_services_last_fiscal_yr": [],
                   "exclude_num_of_cliens_had_financial_planning_services_last_fiscal_yr": False,
                   "hide_undisclosed_amounts": False, "changed": False,
                   "page": page, "per_page": per_page or self._per_page}
        if extra_filters:
            payload.update(extra_filters)
        return self.request("POST", "/ria_power_search/teams_search",
                            form=self._power_form(payload))

    # -- counts ---------------------------------------------------------------
    def ria_counts(self, extra_filters: dict | None = None) -> dict:
        base = {"location": "",
                "num_of_cliens_had_financial_planning_services_last_fiscal_yr": [],
                "exclude_num_of_cliens_had_financial_planning_services_last_fiscal_yr": False,
                "hide_undisclosed_amounts": False, "changed": False}
        if extra_filters:
            base.update(extra_filters)
        out = {}
        out["firms"] = self.request(
            "POST", "/ria_power_search/entities_count_search/",
            form=self._power_form(base)).get("total_count")
        contacts_payload = dict(base, sort_contacts_direction="desc",
                                per_page=self._per_page, page=1)
        out["reps"] = self.request(
            "POST", "/ria_power_search/contacts_search_count/",
            form=self._power_form(contacts_payload)).get("total_count")
        teams_payload = dict(base)
        out["teams"] = self.request(
            "POST", "/ria_power_search/teams_search_count/",
            form=self._power_form(teams_payload)).get("total_count")
        return out

    # -- options (filter vocabularies) ------------------------------------------
    def ria_options(self, name: str, page: int | None = None) -> dict:
        path = "/ria_power_search/%s_options" % name
        params = {"page": page} if page else None
        return self.request("GET", path, params=params)

    def ria_companies_options_all(self) -> list:
        """Auto-paginate the 10k-per-page companies options endpoint."""
        out: list = []
        page = 1
        while True:
            data = self.ria_options("ria_companies", page=page)
            companies = data.get("companies", [])
            if not companies:
                return out
            out.extend(companies)
            pagy = data.get("pagy") or {}
            pages = (pagy.get("vars") or {}).get("pages") or (pagy.get("metadata") or {}).get("pages")
            if pages and page >= pages:
                return out
            if page > 50:  # safety bound
                return out
            page += 1

    def power_options(self, name: str) -> dict:
        return self.request("GET", "/power_search/%s_options" % name)

    # -- lists & folders ---------------------------------------------------------
    def lists_folders(self) -> dict:
        return self.request("GET", "/lists_folders")

    def combined_lists(self) -> dict:
        return self.request("GET", "/combined_lists")

    def team_lists(self) -> dict:
        return self.request("POST", "/combined_lists/team_lists", form={})

    # -- notifications / news / enrichment ----------------------------------------
    def notifications(self) -> dict:
        return self.request("GET", "/app_notifications")

    def notifications_count(self) -> dict:
        return self.request("GET", "/app_notifications/notifications_count")

    def mark_notifications_seen(self) -> dict:
        return self.request("PUT", "/app_notifications/update_last_time_seen_notifications")

    def news(self, params: dict | None = None) -> dict:
        return self.request("GET", "/news", params=params)

    def enrichment_history(self) -> dict:
        return self.request("GET", "/previously_enrichment")

    def enrichment_statistics(self) -> dict:
        return self.request("GET", "/previously_enrichment/historical_statistics")

    # -- misc reference -----------------------------------------------------------
    def reference(self, name: str) -> Any:
        return self.request("GET", "/" + name)


    # -- entity detail (RIA firm) -------------------------------------------------
    def ria_firm(self, item_id: int) -> dict:
        return self.request("GET", "/ria_investors/%d" % item_id)

    def ria_firm_sub(self, item_id: int, sub: str, params: dict | None = None) -> Any:
        """Any /ria_investors/{id}/<sub> resource: contacts, custodians_table,
        disclosures, aum_accounts, private_fund, ownerships, office_locations,
        related_entities, notes, tasks, notable_changes, associated_tags,
        relationship_path_teammates, ria_lists, mergers, family_office_id, custom_properties."""
        return self.request("GET", "/ria_investors/%d/%s" % (item_id, sub), params=params)

    def ria_firm_contacts(self, item_id: int, per_page: int | None = None,
                          sort_by: str = "network") -> dict:
        return self.ria_firm_sub(item_id, "contacts",
                                 params={"sort_by": sort_by, "per_page": per_page or self._per_page})

    def entity_highlights(self, item_id: int, kind: str = "ria_investor") -> dict:
        return self.request("GET", "/highlights/%d/%s_highlights" % (item_id, kind))

    def contact_detail(self, contact_id: int) -> dict:
        """Full rep/contact record. RIA reps live under /ria_contacts/{id};
        /contacts/{id} is the Family Office contact route (may 404/500 for RIA ids)."""
        try:
            return self.request("GET", "/ria_contacts/%d" % contact_id)
        except FintrxAPIError as e:
            if e.status in (404, 500):
                return self.request("GET", "/contacts/%d" % contact_id)
            raise

    def fo_investor(self, item_id: int) -> dict:
        """Family Office record: GET /investors/{id}. The FO body is nested
        under the 'family_office' key (NOT 'investor'). FO contact roster:
        GET /investors/{id}/contacts."""
        return self.request("GET", "/investors/%d" % item_id)

    def fo_investor_contacts(self, item_id: int) -> dict:
        return self.request("GET", "/investors/%d/contacts" % item_id)

    def contact_affinity(self, contact_id: int, teammate_id: int) -> dict:
        return self.request("GET", "/contacts/%d/teammate_affinity_score/%d" % (contact_id, teammate_id))

    # -- direct transactions ---------------------------------------------------------
    def direct_transactions(self) -> dict:
        return self.request("GET", "/transactions/direct_transactions")

    def direct_transactions_statistics(self) -> dict:
        return self.request("GET", "/transactions/direct_transactions_statistics")

    def transactions_heatmap(self, kind: str) -> dict:
        """kind in: investments_by_industry, total_amount_raised, employee_size, stage_of_investment"""
        return self.request("GET", "/transactions/heatmap_%s" % kind)

    def funded_companies_locations(self) -> dict:
        return self.request("GET", "/transactions/funded_companies_locations")

    def ma_transactions(self, params: dict | None = None) -> Any:
        return self.request("GET", "/ma_transactions/", params=params)

    def ma_transactions_options(self) -> dict:
        return self.request("GET", "/ma_transactions/ma_transactions_options")

    def last_ma_transaction(self) -> dict:
        return self.request("GET", "/ma_transactions/last_ma_transaction")

    # -- saved filters ------------------------------------------------------------------
    def saved_filters(self) -> dict:
        return self.request("GET", "/ria_power_search/saved_search_filters")

    # -- write operations -----------------------------------------------------------------
    def create_ria_list(self, name: str, type_list: str = "ria_prospects",
                        include_entities: bool = True, include_reps: bool = True,
                        entity_ids: list[int] | None = None) -> dict:
        """Create a list; optionally add entity ids in the same call the UI makes."""
        payload = {"name": name, "type_list": type_list, "layout_id": "",
                   "save_results_from_entities": include_entities,
                   "save_results_from_reps": include_reps}
        out = self.request("POST", "/ria_lists", form={"ria_list": json.dumps(payload)})
        if entity_ids and out and out.get("ria_list", {}).get("id"):
            list_id = out["ria_list"]["id"]
            self.add_entities_to_list(list_id, entity_ids)
        return out

    def add_entities_to_list(self, list_id: int, entity_ids: list[int]) -> dict:
        payload = {"item_type": "entities", "item_ids": entity_ids, "ria_list_id": list_id}
        return self.request("POST", "/ria_lists/add_entities_to_list",
                            form={"ria_listships": json.dumps(payload)})

    # -- helpers ------------------------------------------------------------------------------
    def delete_list_attempt(self, list_id: int) -> list[tuple[str, str, Any]]:
        """Try known delete variants; returns [(method, path, result_or_error)]."""
        results = []
        for method, path in (("DELETE", "/ria_lists/%d" % list_id),):
            try:
                results.append((method, path, self.request(method, path)))
            except Exception as e:
                results.append((method, path, str(e)[:120]))
        return results

    # -- 13-F holdings (keyed by firm CRD, not FINTRX item id) -------------------------------
    # Get the CRD from ria_firm(item_id)["ria_investor"]["crd_id"]. Only ~16% of firms file
    # 13-F; a non-filer returns has_investments: false, which is not the same as "holds nothing".
    def firm_holdings_statistics(self, crd: int | str) -> dict:
        """Summary card: number_of_holdings, last_quarter, total_assets, style split."""
        return self.request("GET", "/ria_investments/statistics", params={"crd_id": crd})

    def firm_holdings(self, crd: int | str, type: str = "ETF", page: int = 1,
                      per_page: int | None = None, sort_by: str = "value",
                      sort_direction: str = "desc", filter: str | None = None) -> dict:
        """One page of a firm's 13-F positions. type: ETF | Stock | ETN/ETD | CEF | Warrant.

        Rows carry ticker, value, previous_value, shrs_or_prn_amt, per_of_portfolio,
        put_call (PUT/CALL/None; filter on None for real long exposure), etf_style,
        etf_category, provider. pagy.count is the true position count.
        """
        params = {"crd_id": crd, "type": type, "page": page,
                  "per_page": per_page or self._per_page,
                  "sort_by": sort_by, "sort_direction": sort_direction}
        if filter:
            params["filter"] = filter
        return self.request("GET", "/ria_investments/investments_by_crd_id", params=params)

    def firm_holdings_all(self, crd: int | str, type: str = "ETF", pace: float = 0.25,
                          **kw) -> Iterator[dict]:
        """Every row of firm_holdings(), auto-paginated, one API call per 50 rows."""
        page = 1
        while True:
            d = self.firm_holdings(crd, type=type, page=page, **kw)
            rows = d.get("ria_investments") or []
            yield from rows
            count = (d.get("pagy") or {}).get("count") or 0
            if not rows or page * (kw.get("per_page") or self._per_page) >= count:
                return
            page += 1
            time.sleep(pace)

    def close(self) -> None:
        if self._http:
            self._http.close()
            self._http = None

    def __enter__(self) -> "FintrxClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
