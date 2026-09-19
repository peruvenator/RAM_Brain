# FINTRX — Current Holdings (13-F) / ETF Holdings Capability

**Status: FULLY CAPABLE — both directions work.** Firm → holdings, and ticker → firms.
Investigated 2026-08-31. All findings verified live against `platform.fintrx.com/v1/user`.
Read-only throughout (GETs + search/count POSTs). 144 live API calls used.

---

## 0. TL;DR

| Capability | Verdict |
|---|---|
| Pull a firm's full 13-F holdings (ETF + Stock, with $ value, shares, % of portfolio, QoQ delta) | ✅ `GET /ria_investments/investments_by_crd_id` |
| Search FINTRX for **every firm holding a given ticker** | ✅ power-search key **`ria_investments: ["RSST"]`** |
| AND / OR / NOT across multiple tickers | ✅ `and_ria_investments`, `exclude_ria_investments` |
| Filter by position size ($ or % of portfolio) | ✅ `thirteen_f_issuer` + `thirteenFAmountHeldIssuer` |
| Find firms that **just opened / fully exited** a position | ✅ `positions_issuer` + `positions_activity_type` |
| Filter by ETF category / style / provider-behaviour | ✅ `ria_investment_etf_category`, `..._etf_style`, `..._etf_investor`, `..._early_adopter` |
| "My ETF Alignment" / "My ETF Matchup" (us vs. named competitors) | ⚠️ Endpoints exist; **blocked until `users/etf_settings` is configured** (a write op — not performed) |
| Family Office (FO) side holdings | ❌ No 13-F data. FO records carry only `tracked_investments_count` (private/direct deals) |

**Headline numbers (2026 Q2 filings, this subscription):**

- FINTRX firm universe: **45,965**. Firms with any 13-F holdings data: **7,327** (15.9%).
- Firms holding **≥1 Return Stacked ETF: 79**.
- Firms holding **RSST: 61** · RSSB 39 · RSBT 20 · RSSX 15 · RSSY 13 · RSBA 13.
- Firms holding **DBMF: 301** · CTA 229 · BTAL 85 · WTMF 82 · FMF 81 · KMLM 54 · PFIX 48 · TFPN 15 · HFND 13 · MFUT 11 · AHLT 10.
- Firms holding **any** of 8 competitor managed-futures ETFs: **481**.
- Firms holding **both RSST and DBMF: 32**.
- **Prime prospect list: 222 firms** holding >$1M of a competitor managed-futures ETF and **zero** Return Stacked tickers.

---

## 1. Coverage caveats (read before trusting any count)

1. **13-F only.** Data is sourced from SEC Form 13F. Only institutional managers with
   **>$100M in 13(f)-listed securities** under *discretionary* management must file.
   Only **7,327 of 45,965** FINTRX firms (15.9%) have any holdings data at all.
   A firm returning zero is usually a *non-filer*, not a non-holder.
2. **Quarterly lag.** Latest quarter observed is **2026 Q2** (`statistics.last_quarter = {year:2026, quarter:2}`).
   13-F is due 45 days after quarter end, so data is 45–135 days stale.
3. **Discretionary only.** Assets held in non-discretionary / advisory-only accounts and
   assets custodied but not reported by the adviser are invisible. Large wirehouse and
   broker-dealer platforms (Merrill, LPL, Raymond James) show up because of their advisory
   arms, and their positions reflect aggregated house holdings, not one advisor's book.
4. **Beneficial-ownership quirks.** 13-F reports positions of the *filer*; sub-advised,
   omnibus and platform positions roll up to the filer, so a single row can represent
   thousands of end clients. Position size ≠ conviction.
5. **Derivatives are included and flagged.** `put_call` is `PUT` / `CALL` / `null`.
   Hedge-fund rows are frequently options, not shares — Point72's largest "ETF holding"
   is a **PUT** on IWM. Filter on `put_call = null` if you want real long exposure.
6. **The ticker vocabulary is a whitelist.** `etf_tickers` has 5,713 entries and
   `ria_investments` has 16,849. All six live Return Stacked ETFs are present.
   **RSBX is NOT in the vocabulary** (nor RSCS/RSMB/RSEM/RSEQ) — a ticker absent from
   the vocabulary silently returns the unfiltered baseline count, which reads as
   "everything matched". **Always validate a ticker against the vocabulary first.**

---

## 2. Endpoint map — firm → holdings

All holdings endpoints are keyed by **CRD**, not by the FINTRX `item_id`.
Get CRD from `GET /ria_investors/{item_id}` → `ria_investor.crd_id`.
Example used throughout: **Point72 = item_id 164788, CRD 283077**.

### 2.1 `GET /ria_investments/statistics?crd_id={crd}` ✅ (1 call, cheap)

The summary card. This is the "183 ETFs held" number from the UI.

```json
{"statistics": {
  "number_of_holdings": 183,
  "top_provider_name": "BlackRock",
  "top_etf_category_name": "Small Cap Blend",
  "style_proportion": {"passive":"780964123.0","passive_percentage":"86.4885...",
                       "active":"122004200.0","active_percentage":"13.5114...","total":"902968323.0"},
  "last_quarter": {"year": 2026, "quarter": 2},
  "total_assets": "90675333456.0",
  "should_calculate_charts": true,
  "has_investments": true,
  "early_adopter": true,
  "has_etf_settings": false
}, "status": "fetched"}
```

A non-filer returns `number_of_holdings: false, has_investments: false` and nulls throughout
(verified on BNY Mellon Securities, CRD 231).

### 2.2 `GET /ria_investments/investments_by_crd_id` ✅ — **the holdings table**

Params: `crd_id`, `type` (`ETF` | `Stock` | `ETN/ETD` | `CEF` | `Warrant`),
`page`, `per_page` (50 default), `sort_by=value`, `sort_direction=desc`,
`filter=` (free-text ticker/issuer search *within* the firm's holdings).

Real row (Point72, `type=ETF`):

```json
{"name_of_issuer":"Ishares Russell 2000 Etf (IWM)","put_call":"PUT",
 "title_of_class":"RUSSELL 2000 ETF","value":426969495,"previous_value":106764000,
 "previous_shrs_or_prn_amt":430500,"shrs_or_prn_amt":1421100,
 "per_of_portfolio":0.47087722617219374,"per_of_portfolio_variance":"increase",
 "per_of_shrs_or_prn":230.10452961672473,"sector":"","category":"ETF",
 "user_ticker":null,"competitor_ticker":null,"ticker":"IWM",
 "etf_style":"Passive","etf_category":"Small Blend","ratio_text":null,"split_date":null,
 "provider":"BlackRock","provider_logo_url":"https://...","per_of_value":299.918975,
 "open_position":false}
```

Response envelope: `{ria_investments:[...], sectors, pagy, types, top_categories,
providers, newly_options, styles, status}`. `pagy.count` is the true position count.

Point72: **184 ETF positions, 2,787 Stock positions**.
`per_page` is honoured; 184 ETF rows = 4 pages at 50/page.

`user_ticker` / `competitor_ticker` are **populated only when `users/etf_settings` is configured** —
see §5. Today they are always `null`.

Verified spot-checks (`filter=RSST`, `type=ETF`), all 2026 Q2:

| Firm | item_id | CRD | Total holdings | RSST position | % of portfolio | QoQ |
|---|---|---|---|---|---|---|
| Continuum Wealth Advisors | 160079 | 152895 | 54 | $17,776,748 (543,798 sh) | 5.999% | increase |
| SPC | 155552 | 110692 | 753 | $7,041,583 (215,405 sh) | 0.177% | increase |
| True Wealth Design | 158927 | 143194 | 120 | $249,981 (7,647 sh) | 0.060% | decrease |

### 2.3 Other verified `/ria_investments/*` routes (all `?crd_id=`)

| Route | Returns |
|---|---|
| `all_categories_by_crd_id` | Category rollup: `[{category, shrs_or_prn_amt, sum_value}]` — e.g. Continuum: Large Blend $87.4M, Options Trading $42.6M, Commodities Focused $22.3M |
| `investments_activity_by_crd_id` | Facet lists + `has_investments`, `has_my_etfs` |
| `investments_alignment_by_crd_id` | Alignment scores (needs `etf_settings`) |
| `competitive_landscape` | `{competitive_breakdown: []}` — **empty without `etf_settings`** |
| `bar_chart_data`, `pie_chart_data`, `etf_amounts_by_quarter`, `etf_by_provider_chart`, `etf_category_trends`, `etf_trends_pie_chart_data` | Chart series for the profile UI |
| `GET /separately_managed_accounts/statistics?crd_id=` | SMA block: `{estimated_sma_assets, most_used_asset_type, most_used_asset_type_value, preference, has_sma, sma_custodians_count}` — *unrelated to 13-F* |

### 2.4 404'd / dead ends

`GET /ria_investments`, `/ria_investments/`, `/ria_investments/index`, `/holdings`, `/etfs`,
`/table`, `/list`, `/charts`, `/investments` — **all 404**. There is no un-scoped holdings
collection; every route is CRD-scoped.
`/ria_investors/{id}/...` has **no** holdings sub-resource — holdings live entirely under
the `/ria_investments/` namespace, keyed by CRD.
`GET /highlights/164788/ria_investor_highlights` → `{"highlights":[],"highlight_enabled":true}` — no ETF block.

---

## 3. The search filter — ticker → firms  ⭐ THE MONEY CAPABILITY

**Endpoints:** `POST /ria_power_search/entities_count_search/` (counts, cheap — use for sizing)
and `POST /ria_power_search/investors_search` (rows). Body is form-urlencoded
`power_search=<json>`, i.e. `c._power_form(payload)`.

**Baseline (no filter): `total_count = 45965`.**

> ⚠️ **Silent-failure trap.** An unrecognised payload key is *ignored*, not rejected — the
> endpoint returns the 45,965 baseline. A result equal to baseline means **the filter did
> nothing**, not "everything matched". Always compare against baseline.

### 3.1 Verified filter keys

Extracted authoritatively from the SPA bundle
(`application-B_S_eHei.js`, `field:` declarations) and each validated live.

| Payload key | Value shape | Verified example → count |
|---|---|---|
| **`ria_investments`** | `["RSST"]` (list of tickers; ticker == option `id`) | RSST → **61** |
| `and_ria_investments` | `true` — turns the list into AND | `["RSST","DBMF"] + and` → **32** |
| `exclude_ria_investments` | `true` — NOT, *within the 13-F universe* | `["RSST"] + exclude` → **7266** |
| `ria_investments_sector` (+ `exclude_`, `and_`) | `["Technology"]` | → 6636 |
| `ria_investments_industry` (+ `exclude_`) | `["Airlines"]` | → 1913 |
| `ria_investment_etf_category` (+ `exclude_`, `and_`) | `["Systematic Trend"]` | → **475** |
| `ria_investment_etf_style` (+ `exclude_`) | `["Active"]` | → 4539 |
| `ria_investment_etf_investor` (+ `exclude_`) | `["Yes"]` | → 5822 |
| `ria_investment_early_adopter` (+ `exclude_`) | `["Yes"]` | → 2515 |
| `thirteen_f_issuer` + `thirteenFAmountHeldIssuer` | `["DBMF"]` + `[min,max]` USD | DBMF any → 301; **≥$1M → 142** |
| `thirteen_f_issuer` + `perThirteenFAmountHeldIssuer` | `[min,max]` percent of portfolio | (same pattern, % basis) |
| `positions_issuer` + `selectedPositionsIssuer` + `positions_activity_type` | see §3.3 | Initiated DBMF → **54** |
| `totalHoldings` | `[min,max]` range | position-count range |

**Multi-ticker default is OR.** `["RSST","RSBT"]` → 63 (vs 61 + 20 separately ⇒ 18 overlap).
Add `and_ria_investments: true` for AND.

`exclude_ria_investments: true` is scoped to firms that *have* holdings data, which is how
the 13-F universe size is derived: `61 (hold RSST) + 7266 (don't) = 7327`.

### 3.2 Keys that do NOT exist (all returned baseline 45,965)

`etf_tickers`, `etf_investments`, `holdings`, `current_holdings`, `etf_holdings`,
`thirteen_f_holdings`, `securities`, `holding_tickers`, `investments`, `tickers`,
`etf_categories`, `etf_provider`, `etf_parent_categories`, `etf_style`, `etf_investor`,
`all_etf_categories`, `top_etf_categories`, `number_of_holdings`, `has_investments`,
`thirteen_f_type`, `thirteen_f_sector`, `newly_added_investments`, `etf_total`.

Note the trap: the **options-endpoint list names are not the payload keys.** The vocabulary
comes back under `etf_categories`, but the filter key is `ria_investment_etf_category`.

### 3.3 The stepper filters need a `selected*` companion object

"Recent Open/Closed Positions", "Top 10 Holding" and "Change In Holdings Over Time" are
`complex` filters: the wire payload carries **both** the plain key and a `selected*`
companion holding the full option object. Sending only the plain key is silently ignored;
sending only `top_issuer` yields **HTTP 500**.

Option object shape (from `ria_investments_options`):
`{"id":"DBMF","name":"Imgp Dbi Managed Futures Strategy Etf (DBMF)","ticker":"DBMF","category":"ETF"}`

**Recent Open/Closed Positions — verified working:**

```json
{"positions_issuer": ["DBMF"],
 "selectedPositionsIssuer": [{"id":"DBMF","name":"Imgp Dbi Managed Futures Strategy Etf (DBMF)",
                              "ticker":"DBMF","category":"ETF"}],
 "positions_activity_type": "Initiated New Position",
 "selectedPositionsActivityType": "Initiated New Position"}
```

`positions_activity_type` enum: `"Initiated New Position"` | `"Fully Exited Position"`.

Verified results:

| Query | Count |
|---|---|
| Initiated a new **RSST** position | **14** |
| Initiated a new **DBMF** position | 54 |
| Initiated DBMF / CTA / KMLM | **98** |
| **Fully exited** DBMF | 28 |
| Fully exited DBMF / CTA / KMLM | **53** |

**Other stepper filters (keys confirmed in the bundle, companion object required, not fully validated):**

- *Change In Holdings Over Time*: `holding_change_issuer` (single) + `holding_change_direction`
  (`"Increased"` | `"Decreased"`) + `perHoldingChangeAmount` `[0..100]` + `holdingChangeTimeRange`
  (`"1 Quarter"`…`"4 Quarters"`).
- *Top 10 Holding*: `top_issuer` (single) + `top_holding_position`
  (`"1 Position ($)"`…`"10 Positions ($)"`). Returns 500 without the companion object.
- *Historical ETF Movement by Style / Category*: `etf_style_change_stepper_{style,direction,time}`,
  `etf_category_change_stepper_{category,direction,time}` + `etfCategoryChangeStepperAmount`.
- *Holdings by Sector / Product Type*: `thirteen_f_sector` + `thirteenFAmountHeld`,
  `thirteen_f_type` + `thirteenFAmountHeldType` (+ `per...` percent variants).
- *Equity/Debt*: `ria_investment_sh_prn` (+ `exclude_`).
- *Put or Call*: `put_call_issuer`.
- *ETF Provider + Amount*: `etf_provider` + `etfAmountHeldIssuer` / `etfPercentageValue`.

---

## 4. Filter vocabularies

`GET /ria_power_search/ria_investments_options/` — **2.4 MB**, fetch once and cache.

| Key | Size | Sample |
|---|---|---|
| `etf_tickers` | 5,713 | `["SVIX","TXXD",...]` |
| `etf_investments` | 5,713 | `{"id":"RSST","name":"Return Stacked(R) Us Stocks & Managed Futures Etf (RSST)","ticker":"RSST","category":"ETF"}` |
| `ria_investments` | 16,849 | ETFs + single stocks + SPACs; `id` == ticker |
| `etf_categories` | 112 | `Systematic Trend`, `Multistrategy`, `Options Trading`, … |
| `etf_provider` | 155 | `KraneShares`, `Simplify Asset Management`, `BlackRock`, … (**no "Return Stacked" entry**) |
| `etf_parent_categories` | 12 | `Fixed Income`, `Large Cap Blend`, … |
| `ria_investments_type` | 5 | `CEF`, `ETN/ETD`, `ETF`, `Stock`, `Warrant` |
| `ria_investments_sector` | 11 | `Technology`, `Basic Materials`, … |
| `ria_investments_industry` | 149 | `Airlines`, `Aerospace & Defense`, … |

**Managed futures is called `Systematic Trend`.** `"Managed Futures"` is not a valid category
and returns baseline.

**Return Stacked tickers present:** RSST ✅ RSSY ✅ RSSB ✅ RSSX ✅ RSBT ✅ RSBA ✅ · **RSBX ❌**
**Competitors present:** DBMF ✅ KMLM ✅ CTA ✅ MFUT ✅ FMF ✅ WTMF ✅ TFPN ✅ AHLT ✅ HFND ✅ PFIX ✅ BTAL ✅
**Absent (mutual funds, not ETFs — out of 13-F ETF scope):** BLNDX, RDMIX, AQMIX, QMHIX, ABYIX, RYMFX, DRRIX

Other useful vocab: `GET /ria_power_search/investment_utilized_options` → 16 broad asset
classes (`Alternative Investments`, `Commodities`, …) — this is the **ADV self-reported**
"Investment Preferences" filter, unrelated to 13-F and available for all 45,965 firms.

---

## 5. "My ETFs" — the feature built for exactly our use case (currently OFF)

FINTRX has a first-class **ETF issuer** mode. You register your own tickers and named
competitors, and the platform then:

- populates `user_ticker` / `competitor_ticker` on every holdings row;
- fills `ria_investments/competitive_landscape` (today `{"competitive_breakdown":[]}`);
- enables **"My ETF Alignment"** (`etf_investment_alignment`, `etf_investment_for_alignment`)
  — score firms by fit to our funds;
- enables **"My ETF Matchup"** (`user_etf_investment_win_lose`,
  `competitor_etf_investment_win_lose`, `etf_win_lose_relation`) — *"firms where DBMF is
  beating RSST"*, i.e. a head-to-head displacement target list;
- surfaces `has_my_etfs` / `has_etf_settings` flags on the profile endpoints.

**Current state: `GET /users/etf_settings` → `{"etf_settings": [], ...}`** and
`GET /user_etf_settings/my_etf_custom_properties` → `{"properties":{}}`.
`statistics.has_etf_settings = false` on every firm.

Turning this on is a **write operation and was deliberately not performed.** It is the
single highest-leverage configuration change available — recommend enabling it (via the UI
or with explicit approval) with RSST/RSSY/RSSB/RSSX/RSBT/RSBA as "my ETFs" and
DBMF/CTA/KMLM/WTMF/FMF/TFPN/AHLT/MFUT as competitors.

---

## 6. Family Office side — no 13-F

`GET /investors/{id}` (ArchBridge = 10190) carries only `tracked_investments_count` and
`tracked_real_estate_investments_count` (both 0), which are **private/direct deal counts**,
not securities holdings. There is no ETF or 13-F data on the FO side. 13-F holdings are an
RIA/BD-only capability.

---

## 7. Verified lead lists (2026 Q2)

### 7.1 Firms holding any Return Stacked ETF — 79 total, top 15 by AUM

| item_id | Firm | Location | AUM |
|---|---|---|---|
| 153092 | UBS Financial Services Inc. | Weehawken, NJ | $915.8B |
| 155850 | Envestnet PMC | Berwyn, PA | $614.9B |
| 153087 | Commonwealth Financial Network | Waltham, MA | $212.7B |
| 158057 | Cambridge Investment Research Advisors | Fairfield, IA | $138.7B |
| 156418 | Wealth Enhancement Advisory Services | Plymouth, MN | $122.2B |
| 153102 | MML Investors Services | Springfield, MA | $115.6B |
| 159416 | Mercer Global Advisors | Denver, CO | $84.4B |
| 164204 | World Investment Advisors | Lincroft, NJ | $71.6B |
| 159616 | Betterment | New York, NY | $69.5B |
| 154645 | Orion Portfolio Solutions | Omaha, NE | $64.8B |
| 155235 | MAI Capital Management | Cleveland, OH | $52.1B |
| 160427 | CWM, LLC | Omaha, NE | $50.6B |
| 164702 | AE Wealth Management | Topeka, KS | $49.8B |
| 164777 | Steward Partners Investment Advisory | Stamford, CT | $36.7B |
| 153199 | J.P. Morgan Alternative Asset Management | New York, NY | $29.7B |

Payload: `{"ria_investments":["RSST","RSSY","RSSB","RSSX","RSBT","RSBA"]}`

### 7.2 Prime prospects — 222 firms, >$1M in a competitor managed-futures ETF, **zero** Return Stacked. Top 15 by AUM

| item_id | Firm | Location | AUM |
|---|---|---|---|
| 159690 | Morgan Stanley | Purchase, NY | $1,961.9B |
| 153078 | Merrill Lynch, Pierce, Fenner & Smith | New York, NY | $1,781.6B |
| 164107 | Captrust | Raleigh, NC | $1,236.7B |
| 153061 | LPL Financial LLC | Fort Mill, SC | $819.1B |
| 153193 | Wells Fargo Advisors | Saint Louis, MO | $671.4B |
| 152983 | Raymond James & Associates | St Petersburg, FL | $501.0B |
| 159603 | Raymond James Financial Services Advisors | St Petersburg, FL | $390.0B |
| 155899 | AQR Capital Management | Greenwich, CT | $311.7B |
| 154290 | First Trust Advisors LP | Wheaton, IL | $309.2B |
| 153663 | Creative Planning | Overland Park, KS | $295.6B |
| 153764 | Cetera Investment Advisers | Schaumburg, IL | $256.8B |
| 159164 | Hightower Advisors | Chicago, IL | $198.6B |
| 163685 | Global Retirement Partners | San Rafael, CA | $169.6B |
| 154195 | OneDigital | Overland Park, KS | $155.4B |
| 155172 | New York Life Investment Management | New York, NY | $120.7B |

Payload:
```json
{"thirteen_f_issuer": ["DBMF","CTA","KMLM","WTMF","FMF","TFPN","AHLT","MFUT"],
 "thirteenFAmountHeldIssuer": [1000000, 2000000000],
 "exclude_ria_investments": true,
 "ria_investments": ["RSST","RSSY","RSSB","RSSX","RSBT","RSBA"],
 "sort_investors_by": "total_aum", "sort_investors_direction": "desc",
 "page": 1, "per_page": 100}
```

> Sanity note: the top of this list is dominated by wirehouses and mega-platforms whose
> 13-F aggregates thousands of advisors. For an advisor-level prospecting list, add an AUM
> ceiling and/or `distribution_channels: ["Independent RIA"]`.

### 7.3 Other ready-made segments

| Segment | Payload | Count |
|---|---|---|
| Hold any Systematic Trend ETF | `ria_investment_etf_category:["Systematic Trend"]` | 475 |
| …and hold **no** RS ticker | + `exclude_ria_investments` + 6 RS tickers | **425** |
| Hold both RSST **and** DBMF (displacement risk) | `ria_investments:["RSST","DBMF"], and_ria_investments:true` | 32 |
| Just **opened** a competitor MF position (buying now) | `positions_activity_type:"Initiated New Position"` | 98 |
| Just **exited** a competitor MF position (in play) | `positions_activity_type:"Fully Exited Position"` | 53 |
| Just opened an **RSST** position (onboard/thank) | same, `positions_issuer:["RSST"]` | 14 |
| Flagged ETF adopters / early adopters | `ria_investment_etf_investor:["Yes"]` / `..._early_adopter:["Yes"]` | 5,822 / 2,515 |

---

## 8. Integration recommendation

### 8.1 Add a **holdings sweep** stage — do not bolt this onto per-firm enrich

The enrich stage is per-firm and expensive. The holdings capability is a *set* operation:
one search call returns every firm holding a ticker. Build a separate scheduled stage.

**Cost: ~15 calls per full sweep**, versus ~7,300 calls to enumerate the 13-F universe firm-by-firm.

```
holdings_sweep (quarterly, ~1 week after each 13-F deadline: mid-Feb/May/Aug/Nov)
  1. GET /ria_power_search/ria_investments_options/     -> cache; validate our + competitor
                                                          tickers exist (guards RSBX-class bugs)
  2. For each segment below: POST entities_count_search/ (size), then investors_search
     (rows, per_page=100, paginate on pagy)
       a. holders_ours        : ria_investments = [6 RS tickers]                  (~79)
       b. holders_competitors : ria_investments = [8 competitor tickers]          (~481)
       c. prime_prospects     : thirteen_f_issuer=[competitors] + >$1M
                                + exclude_ria_investments=[RS tickers]            (~222)
       d. new_ours            : positions_issuer=[RS] + "Initiated New Position"  (~14)
       e. churn_ours          : positions_issuer=[RS] + "Fully Exited Position"
       f. in_play             : positions_issuer=[competitors] + "Fully Exited"   (~53)
  3. Diff against last quarter's snapshot -> NEW HOLDER / GREW / SHRANK / EXITED events
  4. Emit to the lead pipeline; reconcile item_id against HubSpot
```

### 8.2 Enrich stage — attach position detail only to firms that matter

Per firm, **2–3 calls**:

```
GET /ria_investors/{item_id}                       -> crd_id            (skip if cached)
GET /ria_investments/statistics?crd_id={crd}       -> number_of_holdings, total_assets,
                                                      last_quarter, style_proportion
GET /ria_investments/investments_by_crd_id?crd_id={crd}&type=ETF&filter=RSST&per_page=50
                                                   -> exact $ value, shares, % of portfolio,
                                                      QoQ direction
```

Cache `item_id → crd_id` permanently (it never changes) to drop this to 2 calls.
Run it only on segments (a)+(c)+(d) — roughly 300 firms, ~600–900 calls per quarter.

### 8.3 Highest-value scoring signals now available

- `per_of_portfolio` + `per_of_portfolio_variance` → **conviction and direction**.
  Continuum Wealth at 6.0% of portfolio in RSST and *increasing* is a reference-client /
  case-study candidate; True Wealth Design at 0.06% and *decreasing* is a churn risk.
- `positions_activity_type` → **timing**. A firm that just exited DBMF is in-market *this
  quarter*; that is the single best trigger in the dataset.
- `and_ria_investments` on (ours, competitor) → **displacement battleground** (32 firms).
- `ria_investment_early_adopter` → 2,515 firms with a demonstrated appetite for new ETFs.

### 8.4 Recommended actions, in priority order

1. **Enable `users/etf_settings`** with our 6 tickers and 8 competitors (write op — needs
   approval). Unlocks Alignment, Matchup and `competitive_landscape`, which are purpose-built
   for an ETF issuer's sales team. Nothing else on this list comes close in leverage.
2. **Ship the quarterly holdings sweep** (§8.1). ~15 calls buys the full customer + prospect
   graph, refreshed every quarter.
3. **Validate every ticker against the vocabulary before querying** and assert
   `count != 45965`. Both failure modes are silent.
4. **Work the 53 "just exited a competitor" firms first**, then the 425 Systematic-Trend
   holders with no RS exposure.
5. Add an AUM ceiling / `distribution_channels` filter to prospect lists so wirehouse
   aggregates don't crowd out addressable advisors.

---

## 9. Method notes

- Capture corpus (`fintrx_api/capture/api_calls.jsonl`, 2,402 records) yielded the
  `/ria_investments/statistics?crd_id=` CRD-keying and the `etf_*` column family on
  `ria_lists/{id}/entities2` (`etf_total`, `active_etf`, `passive_etf`, `etf_investor`,
  `etf_categories_info`, `last_13_f_filing_date`, `number_of_holdings`), but contained no
  holdings-table XHR — the original browse never opened a 13-F-filing firm.
- The full `/ria_investments/*` route family was recovered by arming CDP `Network.enable`
  and loading `platform.fintrx.com/ria_investor/164788` — read-only, no API budget consumed.
- Payload keys were recovered authoritatively from the SPA bundle
  `https://dphzoid7hdhvq.cloudfront.net/vite/assets/application-B_S_eHei.js` (23 MB) by
  grepping `field:` / `exclude:` / `and:` declarations, then each was validated live against
  `entities_count_search/`. This beat black-box guessing, which failed on 22 of 22 attempts
  for the non-obvious keys.
- The Keychain token (`FINTRX_API_TOKEN`) had expired (`is_logged_in:false`, 401). Refreshed
  via the documented auth bridge against the running `~/.fintrx-sdk-profile` debug Chrome,
  whose session had persisted. Token never printed or written to disk.
- No FINTRX write operations were performed: no lists created or modified, no exports, no
  `etf_settings` changes.
