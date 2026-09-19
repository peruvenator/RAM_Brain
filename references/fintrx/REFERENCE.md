# FINTRX SDK Reference

Condensed from Adam Butler's reverse-engineering notes (full text in `docs/`). Verified live
2026-09-19 on Rodrigo's seat. Read this whole file before writing code against the SDK.

## Contract

- Base: `https://platform.fintrx.com/v1/user/`
- Auth: headers `X-User-Token` + `X-User-Email`. A browser session, not a login. Expires; the
  SDK raises `FintrxAuthError` with refresh instructions when it does.
- Search endpoints: `POST`, form-urlencoded, one field `power_search=<json>`. Counts via
  `*_search_count` return `{"total_count": N}`. Every response ends `"status": "fetched"`.
- Pagination: `page` + `per_page` (50 default; keep it). `pagy.count` is the true total.
- Unknown payload keys are **ignored, not rejected**. A filtered count equal to the unfiltered
  baseline means the filter did nothing. Always compare against baseline.
- Server-side typos are load-bearing (`num_of_cliens_had_financial_planning_services_last_fiscal_yr`).

## Two universes, two id spaces

| Universe | Search | Detail | Contacts |
|---|---|---|---|
| RIA & Broker Dealers | `ria_search`, `ria_contacts_search`, `ria_teams_search`, `ria_counts` | `ria_firm(id)` → `GET /ria_investors/{id}` | `contact_detail(id)` → `/ria_contacts/{id}` |
| Family Offices | `fo_search`, `fo_contacts_search`, `fo_transactions_search`, `fo_companies_search` | `fo_investor(id)` → `GET /investors/{id}` (record under key `family_office`) | `fo_investor_contacts(id)`; `contact_detail` falls back to `/contacts/{id}` |

FINTRX item ids and CRD numbers are different things. Holdings endpoints key on **CRD**:
`ria_firm(item_id)["ria_investor"]["crd_id"]`.

## Method map

**Session**: `health_check`, `me`, `admin_permission`, `team_users`, `remaining_downloads`,
`enrichment_quota`, `dashboard_statistics`, `dashboard_widgets`, `recently_viewed`

**Typeahead**: `global_search(query[, categories])` across `search_ria_entities`, `search_ria_reps`,
`search_private_wealth_teams`, `search_contacts`, `search_previous_contacts`, `search_investors`,
`search_funded_companies`, `search_funded_properties`, `search_lists`

**RIA/BD search**: `ria_search(page, per_page, sort_direction, extra_filters)`, `ria_search_all()`
generator, `ria_contacts_search`, `ria_teams_search`, `ria_counts(extra_filters)` → `{firms, reps, teams}`,
`ria_options(name)` vocabularies (`custodians, specialties, firms_tamps_used, universities,
ria_investments, investors, ...`), `ria_companies_options_all()`, `saved_filters()`

**Firm roster**: `ria_firm_reps(primary_business_name)`. The filter matches the UPPERCASE
vocabulary string from `investors_options.primary_business_name`, which can differ in punctuation
from the display name. Zero results for a firm that has contacts means look up the exact
vocabulary string and retry. `ria_firm_contacts(id)` 404s; do not use.

**Firm detail**: `ria_firm(id)`, `ria_firm_sub(id, sub)` with subs `custodians_table, disclosures,
aum_accounts, notes, tasks, notable_changes, associated_tags, related_entities, private_fund,
ria_lists, mergers, ownerships/, custom_properties`. `office_locations` 404s; branch data is on
rep records (`branch_locations`). `entity_highlights(id)`.

**Rep detail**: `contact_detail(id)` ~70 fields: `email, office_phone_number, mobile_phone_number,
linkedin_profile_url, contact_crd_id, title_name, primary_location_full, branch_locations,
firm_tenure, industry_tenure, roles, ownership_percentage, investment_committee_member`.

**FO search**: `fo_search(search_value, page, per_page, sort_direction, extra_filters)`,
`fo_search_all()`, `fo_contacts_search`, `fo_transactions_search`, `fo_companies_search`,
`power_options(name)`.

**Transactions**: `direct_transactions`, `direct_transactions_statistics`, `transactions_heatmap(kind)`
(`investments_by_industry, total_amount_raised, employee_size, stage_of_investment`),
`funded_companies_locations`, `ma_transactions`, `ma_transactions_options`, `last_ma_transaction`.

**Lists (writes)**: `create_ria_list(name, type_list, ...)`, `add_entities_to_list(list_id, ids)`,
`lists_folders`, `combined_lists`, `team_lists`. No delete endpoint was ever captured; do not
delete lists programmatically.

**Anything else**: `request(method, path, form=..., params=...)` with `_power_form(payload)` for
search bodies. `reference(name)` for plain GET lookups (`user_tags, hobbies, universities, ...`).

## 13-F holdings

Only firms that file Form 13F (>$100M discretionary in 13(f) securities) have data: about 7,300 of
46,000. A zero is usually a **non-filer**, not a non-holder. Quarterly, 45 to 135 days stale.
Positions are the filer's; platform and omnibus positions roll up, so size is not conviction.
`put_call` is `PUT` / `CALL` / `None`; filter on `None` for real long exposure.

**Firm → holdings** (by CRD):
- `firm_holdings_statistics(crd)` → `number_of_holdings, last_quarter, total_assets, style_proportion`
- `firm_holdings(crd, type="ETF", page, per_page, sort_by, sort_direction, filter)` → one page.
  `type` in `ETF | Stock | ETN/ETD | CEF | Warrant`. Rows: `ticker, name_of_issuer, value,
  previous_value, shrs_or_prn_amt, per_of_portfolio, per_of_portfolio_variance, put_call,
  etf_style, etf_category, provider, open_position`
- `firm_holdings_all(crd, type)` → every row, auto-paginated
- Raw routes also under `/ria_investments/`: `all_categories_by_crd_id`, `investments_activity_by_crd_id`

**Ticker → firms** (power search on `ria_search` / `ria_counts` via `extra_filters`):

| Key | Value | Example |
|---|---|---|
| `ria_investments` | `["RSST"]` list of tickers, OR by default | RSST → 61 firms |
| `and_ria_investments` | `true` | RSST AND DBMF → 32 |
| `exclude_ria_investments` | `true`, scoped to 13-F filers | not RSST → 7,266 |
| `ria_investment_etf_category` | `["Systematic Trend"]` | → 475 |
| `ria_investment_etf_style` | `["Active"]` | |
| `thirteen_f_issuer` + `thirteenFAmountHeldIssuer` | `["DBMF"]` + `[min, max]` USD | DBMF ≥ $1M → 142 |
| `thirteen_f_issuer` + `perThirteenFAmountHeldIssuer` | `[min, max]` percent of portfolio | |
| `positions_issuer` + `selectedPositionsIssuer` + `positions_activity_type` | see below | Initiated DBMF → 54 |

Stepper filters need the `selected*` companion carrying the full option object, or they are
silently ignored (or 500):
```json
{"positions_issuer": ["DBMF"],
 "selectedPositionsIssuer": [{"id":"DBMF","name":"Imgp Dbi Managed Futures Strategy Etf (DBMF)","ticker":"DBMF","category":"ETF"}],
 "positions_activity_type": "Initiated New Position",
 "selectedPositionsActivityType": "Initiated New Position"}
```
`positions_activity_type`: `"Initiated New Position"` | `"Fully Exited Position"`.

**Ticker vocabulary is a whitelist.** `ria_options("ria_investments")` (2.4 MB, fetch once and
cache) lists 16,849 valid ids. A ticker absent from it returns the unfiltered baseline, which reads
as "everything matched". Validate tickers first. Options-list names are not payload keys
(vocabulary `etf_categories`, filter key `ria_investment_etf_category`).

Keys that look right and do nothing: `etf_tickers, holdings, current_holdings, etf_holdings,
holding_tickers, tickers, etf_style, etf_provider, number_of_holdings, has_investments`.

## Gotchas that produce wrong numbers silently

1. Filter count equals baseline (46,142 firms on 2026-09-19) → the key was ignored.
2. Ticker not in vocabulary → baseline, not zero.
3. Non-filer vs non-holder: check `firm_holdings_statistics(crd)["statistics"]["has_investments"]`.
4. `primary_business_name` filter needs the exact uppercase vocabulary string.
5. Multi-ticker lists are OR unless `and_ria_investments: true`.
6. Enrichment (rep detail with contact info) is US-only; Canadian firms appear only as funded companies.
7. Endowments & Foundations, Banks & Trusts are gated on this subscription.
8. `remaining_downloads()` and `users/bulk_users_conditions` show export quotas; the export
   execution endpoint was never captured.

## Rate discipline

Licensed seat. `per_page=50`, 0.25s between calls, no parallel workers, size with `*_count`
first. Thousands of lookups run for hours; build disk caching and resume into the calling project.

## Full notes

`docs/API_SDK_NOTES_v2.md` (endpoint families, payload shapes, UI routes) and
`docs/HOLDINGS_CAPABILITY.md` (every holdings route and filter key, with verified counts).
Grep them; do not load them whole.
