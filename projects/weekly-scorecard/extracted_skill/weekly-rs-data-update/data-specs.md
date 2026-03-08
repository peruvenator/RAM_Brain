# Data Extraction Specifications

## Excel File: CUs-RUs.xlsx

Source: `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG\CUs-RUs.xlsx`

### Cell References

| Metric | Source | Format |
|---|---|---|
| AUM | Cell `AD6` | Express in millions (e.g., if cell = 523000000, output = 523) |
| Units Outstanding | Last non-empty value in column `Q` | Whole number |
| RW Units Outstanding | Last non-empty value in column `R` | Whole number |
| Revenue (Fwd 12 mth) | Cell `AE19` | Full dollar amount (e.g., 5624008) |

### Calculated Fields

**% Revenue top ETF:**
```
MAX(U14:AA14) / AE19
```
Find the single highest value in the range U14 through AA14, divide by cell AE19.

**% Revenue top 3 ETFs:**
```
SUM(TOP_3(U14:AA14)) / AE19
```
Sort values in U14:AA14 descending, sum the top 3, divide by cell AE19.

## HubSpot — Top Firm Revenue (current snapshot, NOT date-filtered)

Query contacts sorted by `total_revenue__assets_invested` descending, filtering for value > 0 and **excluding contact ID `36400025260` (Kent Boss)**.

**% Revenue top 1 Firm:**
```
TOP_1_contact.total_revenue__assets_invested / AE19
```

**% Revenue top 3 Firms:**
```
SUM(TOP_3_contacts.total_revenue__assets_invested) / AE19
```

## BTGD Revenue (web API, NOT date-filtered)

Fetch AUM of ETF ticker BTGD from: `https://api.stockanalysis.com/api/symbol/e/BTGD/overview`

Parse the `data.aum` field (e.g., `"$77.67M"`) → convert to raw number → multiply by **0.001**.

```
BTGD_Revenue = AUM_raw * 0.001
```

## HubSpot Date Range

Compute dynamically relative to the current date to capture the **previous complete calendar week** (Monday–Friday):
- **Monday**: The Monday of the **prior calendar week** — NOT the most recent Monday. For example, if today is Friday Feb 6, 2026, the prior calendar week's Monday is **Jan 26**, not Feb 2.
  - Formula: subtract enough days to reach the Monday **before** this week's Monday. In other words, go back to this week's Monday, then subtract 7 more days.
- **Saturday**: The Saturday immediately following that Monday (i.e., Monday + 5 days)
- Format: ISO 8601 timestamps in UTC (e.g., `2026-01-26T00:00:00Z`)
- Apply `GTE` for Monday, `LT` for Saturday

## Notion Scorecard Field Mapping

When creating the scorecard entry, map values to these database fields (verify exact property names via Notion MCP fetch):

| Computed Value | Notion Field Name |
|---|---|
| AUM (millions) | AUM ($ Millions) |
| Units Outstanding | Units Outstanding |
| RW Units Outstanding | RW Units Outstanding |
| Revenue | Revenue (Fwd 12 mth) |
| % Revenue top ETF | % Revenue top ETF |
| % Revenue top 3 ETFs | % Revenue top 3 ETFs |
| Calls count | Calls |
| Emails count | Emails |
| Meetings count | Meetings |
| New deals count | New Deals |
| Closed deals count | Closed Deals |
| SQL count | SQLs |
| SAL count | SALs |
| Redemptions count | Redemptions |
| Deal advancements count | Deal Advancements |
| % Revenue top 1 Firm | % Revenue top 1 Firm |
| % Revenue top 3 Firms | % Revenue top 3 Firms |
| BTGD Revenue | BTGD Revenue |
