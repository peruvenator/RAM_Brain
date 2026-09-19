# FINTRX Internal API — SDK Foundation Notes (v2) — CANONICAL REFERENCE

**This is the authoritative reference for the FINTRX web API and the Python SDK that wraps it.**
All programmatic access to FINTRX goes through `fintrx_sdk_py/fintrx_sdk/client.py`
(`FintrxClient`). See the project root `README.md` for quickstart, tests, and rules of the road.
Do not interface with FINTRX via the browser, MCP, or any licensed-API channel — those are
deprecated/unsupported paths.

**Base:** `https://platform.fintrx.com/v1/user/`
**Auth:** custom headers `X-User-Token: <session token>` + `X-User-Email: <account email>`.
(NOT Bearer; NOT cookie. Verified: plain HTTPS GET with these two headers returns 200 + `is_logged_in:true`.)
Storage: macOS Keychain service `FINTRX_API_TOKEN`, JSON blob `{"token":..., "email":...}`.
Capture path: CDP `Network.requestWillBeSent` on any `/v1/user/` request; values never printed/logged.


## Confirmed request formats

### Power search (Family Offices) — POST, form-urlencoded body `power_search=<json>`
`POST /v1/user/power_search/investors_search`
```json
{"status":"","search_value":"","sort_investors_direction":"desc","page":1,"per_page":50}
```
- Response: `{investors:[...], extra_info:{id:{aum_range,country,state,city,type_entity,...}}, pagy:{vars:{page,items,...}}, status:"fetched"}`
- Sibling endpoints: `contacts_search` (sort key `sort_contacts_direction`), `transactions_search`, `funded_companies_search`
- Count variant: `*_search_count` (same payload; returns `{total_count, status}`)

### Power search (RIA & Broker Dealers) — same envelope under `ria_power_search/`
- `POST /v1/user/ria_power_search/investors_search` → `{investors:[{id,name,location,photo,fraudulent}], extra_info, pagy}`
- `POST /v1/user/ria_power_search/contacts_search` → `{contacts:[{id,ria_contact_id,team_aum,name,ria_contact_crd_id,email,phone,title,photo,linkedin_url,firm_tenure,...}], extra_info, pagy}`
- `POST /v1/user/ria_power_search/teams_search` → `{teams:[{id,parent_firm:{name,id,crd_id,photo},name,aum,location,size,favorite,photo,client_types,...}], pagy}`
- Counts: `entities_count_search/`, `contacts_search_count/`, `teams_search_count/` → `{total_count,status}`
- Baseline payload keys (RIA): `location`, `num_of_cliens_had_financial_planning_services_last_fiscal_yr[]`, `exclude_..._fiscal_yr`, `hide_undisclosed_amounts`, `changed`, sort, page, per_page. (Note server-side typo "cliens" — preserve as-is.)

### Options endpoints (filter vocabularies; all GET)
- power_search: `investors_options`, `contacts_options`, `transactions_options`, `scores_options`, `team_relationships_options`, `custom_properties?from_search=true`, `last_keywords`
- ria_power_search: `investors_options` (counties, zip_code, countries, cities, states, metro_area_names, area_codes, owner_type, types_of_organization, distribution_channels, independent_broker_dealer, acquiring/acquired_firm_names, contact_regulatory_organizations, primary_business_name), `custodians_options`, `specialties_options`, `firms_accolades_options`, `contacts_accolades_options`, `contact_achievement_options`, `investment_utilized_options`, `firms_tamps_used_options`, `clients_served_options`, `network_affiliations_options`, `referral_network_options`, `universities_options`, `private_wealth_team_options`, `ria_investments_options`
- `ria_companies_options?page=N` is paginated (pagy scaffold, 10,000/page)

### Filter categories in the UI (RIA search, "All Filters" tab)
Keyword Search, Contact & Rep Location, Contact & Rep Info, Wealth Teams, Historical Acquisitions,
Firm Location, Firm Info, Accounts & AUM, Clients, Current Holdings (13-F), Investment Preferences,
Asset Breakdown, Custodian Information, Private Funds Advised, Your Favorites/Tags/Custom Properties, HubSpot.
Filter drawer = `.power-search-container`; filter name search box: `input[placeholder="Search filter names..."]`.

## Global search (typeahead) — POST `/v1/user/global_search/<category>`, form body `query=<term>`
Categories: search_ria_entities, search_ria_reps, search_private_wealth_teams, search_contacts,
search_previous_contacts, search_investors, search_funded_companies, search_funded_properties, search_lists.

## Session/user endpoints (GET unless noted)
`users/health_check`, `users/admin_permission`, `users` (own profile), `users/team_users`,
`teammates/index`, `users/remaining_downloads`, `users/enrichment_quota_limit`, `users/time_zones`,
`users/permission_shares`, `users/bulk_users_conditions`, `users/profile_settings_warnings`,
`dashboard/selected_widgets`, `dashboard/number_statistics`, `dashboard/recently_viewed`,
`app_notifications/notifications_count`, `user_prompt/get_messages` (POST), `answer_hub/suggestions`,
`types/note_types`, `lists_folders`, `combined_lists`, `combined_lists/team_lists` (POST), `news`,
`previously_enrichment`, `previously_enrichment/historical_statistics`, `notifications_settings`,
`custom_properties/my_custom_properties`, `custom_properties/ai_fields`, `user_tags`, `hobbies`,
`societal_affiliations`, `universities`, `cities/cities_for_affinity`, `contacts/team_contacts`,
`investors/team_entities`, `fintegra/test_connection` (POST), `integrations/paragon_project_id`.

## Notifications
`GET app_notifications`, `app_notifications/fintrx_updates`, `app_notifications/shares`,
`PUT app_notifications/update_last_time_seen_notifications`.

## UI routes
`/` Dashboard, `/power_search` FO search, `/ria_power_search` RIA search, `/news`, `/lists_and_folders`,
`/data_enrichment`, `/relationshiphub`, `/recently_viewed`, `/notification_center`, `/profile_settings`.
Sidebar flyout categories: Family Offices, RIAs & Broker Dealers, Wealth Teams (href TBD),
Endowments & Foundations + Banks & Trusts (gated: REQUEST ACCESS).

## Key counts on this subscription (2026-08-28)
Firms 45,891 · Reps 798,042 · Wealth Teams 28,576 · FO 4,595 · FO Contacts 30,125 ·
Transactions 41,969 · Companies/Properties 30,925.

## SDK plumbing notes
- `per_page: 50` default; pagination via `page` + `pagy.vars` metadata.
- Payload is `application/x-www-form-urlencoded` with a single field `power_search=<urlencoded json>`
  (Content-Type may appear as multipart/form-data in extraInfo; the SPA sends urlencoded — verify in SDK tests).
- Response envelope always ends `"status":"fetched"` (or `total_count`+`fetched` for counts).
- CDP gotchas: response bodies must be fetched on `Network.loadingFinished` (not `responseReceived`);
  only ONE CDP client per target may enable Network domains reliably (pause the harness before probing).
- Keychain: `security add-generic-password -a adambutler -s FINTRX_API_TOKEN -w <json> -U`.

---

## SDK method → endpoint map (complete, as of 2026-08-28)

### Session & user
| SDK method | Endpoint | Notes |
|---|---|---|
| `health_check()` | `GET /users/health_check` | `is_logged_in` flag — call first to validate Keychain credential |
| `me()` | `GET /users` | own profile record |
| `admin_permission()` | `GET /users/admin_permission` | |
| `team_users()` | `GET /users/team_users` | teammates with seats/permissions |
| `remaining_downloads()` | `GET /users/remaining_downloads` | download quota message + count |
| `enrichment_quota()` | `GET /users/enrichment_quota_limit` | |
| `dashboard_statistics()` | `GET /dashboard/number_statistics` | rolling 365-day team stats |
| `dashboard_widgets()` | `GET /dashboard/selected_widgets` | |
| `recently_viewed()` | `GET /dashboard/recently_viewed` | |

### Global typeahead
| SDK method | Endpoint |
|---|---|
| `global_search(query[, categories])` | `POST /global_search/{category}` (form `query=<term>`) for each of: `search_ria_entities`, `search_ria_reps`, `search_private_wealth_teams`, `search_contacts`, `search_previous_contacts`, `search_investors`, `search_funded_companies`, `search_funded_properties`, `search_lists` |

### Family Office power search
| SDK method | Endpoint | Payload keys |
|---|---|---|
| `fo_search(search_value, page, per_page, sort_direction, extra_filters)` | `POST /power_search/investors_search` | `status, search_value, sort_investors_direction, page, per_page` + filters |
| `fo_search_all(...)` | same, auto-paginated generator (honors `pagy.vars.pages`) | |
| `fo_contacts_search(page, per_page, extra_filters)` | `POST /power_search/contacts_search` | `sort_contacts_direction` variant |
| `fo_transactions_search(page, per_page)` | `POST /power_search/transactions_search` | |
| `fo_companies_search(page, per_page)` | `POST /power_search/funded_companies_search` | |
| `power_options(name)` | `GET /power_search/{name}_options` | `investors`, `contacts`, `transactions`, `scores`, `team_relationships`, `custom_properties`, `last_keywords` |

Response shapes: `investors` + `extra_info` (aum_range, country/state/city, type_entity per id) + `pagy`;
`contacts` items carry `id, first_name, last_name, email, photo, linkedin_url`;
`transactions` items carry `id, investment_date, total_raised`;
`funded_companies` items carry `id, name, state, clearbit_money_raised, logo, type(company|property), sector, country_name`.

### RIA & Broker Dealer power search
| SDK method | Endpoint | Notes |
|---|---|---|
| `ria_search(page, per_page, sort_direction, extra_filters)` | `POST /ria_power_search/investors_search` | baseline keys incl. server typo `num_of_cliens_...` — preserved exactly |
| `ria_search_all(...)` | same, auto-paginated generator | |
| `ria_contacts_search(page, per_page, extra_filters)` | `POST /ria_power_search/contacts_search` | reps with email/title/CRD/firm_tenure; `extra_info` maps id → `entity_name`, `ria_investor_id` |
| `ria_teams_search(page, per_page, extra_filters)` | `POST /ria_power_search/teams_search` | Wealth Teams tab; items carry `parent_firm{id,name,crd_id,photo}`, `aum`, `size`, `client_types` |
| `ria_counts(extra_filters)` | `POST /ria_power_search/entities_count_search/`, `contacts_search_count/`, `teams_search_count/` | returns `{'firms','reps','teams'}` |
| `ria_options(name, page)` | `GET /ria_power_search/{name}_options` | `custodians, specialties, firms_accolades, contacts_accolades, contact_achievement, investment_utilized, firms_tamps_used, clients_served, network_affiliations, referral_network, universities, private_wealth_team, ria_investments, investors, scores, team_relationships` |
| `ria_companies_options_all()` | `GET /ria_power_search/ria_companies_options?page=N` | 10,000/page, auto-paginated |
| `saved_filters()` | `GET /ria_power_search/saved_search_filters` | |

### Entity detail
| SDK method | Endpoint |
|---|---|
| `ria_firm(id)` | `GET /ria_investors/{id}` |
| `ria_firm_sub(id, sub)` | `GET /ria_investors/{id}/{sub}` — verified subs: `custodians_table`, `disclosures`, `aum_accounts`, `notes`, `tasks`, `notable_changes`, `associated_tags`, `related_entities`, `relationship_path_teammates`, `relationship_path_contacts`, `ownerships/`, `private_fund`, `ria_lists`, `mergers`, `family_office_id`, `custom_properties`. **`office_locations` 404s** (2026-08-28) — branch data comes from rep records (`branch_locations` on `ria_contacts/{id}`) and the branch_* filter vocabularies in `contacts_options` |
| `ria_firm_contacts(id)` | `GET /ria_investors/{id}/contacts` — **404s in practice; do not use** |
| `ria_firm_reps(primary_business_name)` | `POST /ria_power_search/contacts_search` with filter `{"primary_business_name": ["<exact FINTRX business name>"]}` — **the working firm-roster mechanism** (verified 2026-08-28: SteelPeak → exactly its 38 contacts; `extra_info` carries `ria_investor_id` + `team_connection`). Composes with `search_value` for person-in-firm lookup: `{"primary_business_name": ["<firm>"], "search_value": "<surname>"}` → the reps at that firm matching the surname. **Gotcha (2026-08-30):** the filter matches the string in the `investors_options.primary_business_name` vocabulary, which is UPPERCASE and can differ in punctuation from the display name (e.g. `FOGUTH WEALTH MANAGEMENT, LLC.` with trailing period vs display `Foguth Wealth Management, LLC`). If the display-name filter returns 0 for a firm that has contacts, look up the exact string in the vocabulary (case-insensitive contains) and retry |
| `fo_investor(id)` | `GET /investors/{id}` — Family Office record, nested under the **`family_office`** key (not `investor`) |
| `fo_investor_contacts(id)` | `GET /investors/{id}/contacts` — FO contact roster (verified: ArchBridge → 21 contacts with emails; titles under `title_name`) |
| `entity_highlights(id)` | `GET /highlights/{id}/ria_investor_highlights` |
| `contact_detail(id)` | `GET /ria_contacts/{id}` (RIA reps — ~70 fields) with fallback `GET /contacts/{id}` (FO contacts) on 404/500 |
| `contact_affinity(cid, teammate_id)` | `GET /contacts/{cid}/teammate_affinity_score/{teammate_id}` |

`ria_contacts/{id}` field highlights: `email`, `office_phone_number`, `mobile_phone_number`,
`linkedin_profile_url`, `contact_crd_id`, `title_name`, `primary_location_full`, `branch_locations`,
`hq_location`, `firm_tenure`, `industry_tenure`, `roles`, `ownership_percentage`,
`investment_committee_member`, `producing_advisor`, CRM sync fields.

### Direct transactions & M&A
| SDK method | Endpoint |
|---|---|
| `direct_transactions()` | `GET /transactions/direct_transactions` |
| `direct_transactions_statistics()` | `GET /transactions/direct_transactions_statistics` |
| `transactions_heatmap(kind)` | `GET /transactions/heatmap_{kind}` — kinds: `investments_by_industry`, `total_amount_raised`, `employee_size`, `stage_of_investment` |
| `funded_companies_locations()` | `GET /transactions/funded_companies_locations` (GeoJSON FeatureCollection) |
| `ma_transactions(params)` | `GET /ma_transactions/` |
| `ma_transactions_options()` | `GET /ma_transactions/ma_transactions_options` |
| `last_ma_transaction()` | `GET /ma_transactions/last_ma_transaction` |

### Lists (write ops)
| SDK method | Endpoint | Payload |
|---|---|---|
| `create_ria_list(name, type_list, include_entities, include_reps[, entity_ids])` | `POST /ria_lists` | form `ria_list={"name","type_list","layout_id","save_results_from_entities","save_results_from_reps"}` → `{"status":"ok","ria_list":{...}}` |
| `add_entities_to_list(list_id, entity_ids)` | `POST /ria_lists/add_entities_to_list` | form `ria_listships={"item_type":"entities","item_ids":[...],"ria_list_id"}` → `{"status":"added","list_is_updating":true}` |
| `lists_folders()` | `GET /lists_folders` | |
| `combined_lists()` | `GET /combined_lists` | `lists[]` incl. team lists |
| `team_lists()` | `POST /combined_lists/team_lists` | form filter |
| list content (UI-captured; not yet wrapped) | `POST /ria_lists/{id}/entities2`, `/contacts2`, `/entities_count2`, `/contacts_counts2` | form `page, per_page, filter, extra_columns[]` |
| list delete | **no captured endpoint** — do not attempt programmatically | |

### News, notifications, enrichment, reference
| SDK method | Endpoint |
|---|---|
| `news(params)` | `GET /news` |
| `notifications()` / `notifications_count()` | `GET /app_notifications` · `GET /app_notifications/notifications_count` |
| `mark_notifications_seen()` | `PUT /app_notifications/update_last_time_seen_notifications` |
| `enrichment_history()` / `enrichment_statistics()` | `GET /previously_enrichment` · `GET /previously_enrichment/historical_statistics` |
| `reference(name)` | `GET /{name}` — e.g. `user_tags`, `hobbies`, `societal_affiliations`, `universities`, `cities/cities_for_affinity`, `contacts/team_contacts`, `investors/team_entities`, `types/note_types` |

### Export-related (read-only parts captured)
| SDK method | Endpoint |
|---|---|
| `remaining_downloads()` | `GET /users/remaining_downloads` (1000 downloads / 69 days on this seat) |
| `reference("users/bulk_users_conditions")` | `GET /users/bulk_users_conditions` (exports_allowed_per_period=1000, ria_exports=100000) |
| `reference("users/export_permissions")` | `GET /users/export_permissions` (`can_export: true`) |
| (UI-captured) | `GET /ria_list_export_templates` — export-template picker; **the execution POST is not yet captured** |

### Verification status
- `fintrx_sdk_py/tests/test_live.py` — 24 checks, all passing (session, FO search+pagination, RIA search+counts, options, lists read, notifications, news, typeahead).
- `fintrx_sdk_py/tests/test_live2.py` — 20 checks, all passing (firm detail + 6 sub-resources, highlights, contact detail, direct transactions, heatmaps, M&A, saved filters).
- `fintrx_sdk_py/tests/test_write_list.py` — real create + add-entities verified (`{"status":"added"}`), sandbox list cleaned up.

