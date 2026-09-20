# HubSpot Company Fuzzy Match -- Working Instructions

## What this is

Match ~16,000 company names from an Excel export to FINTRX records and enrich them for HubSpot. Sales enablement project: the enriched fields let the Return Stacked sales team prioritize and segment advisors.

## Rules

- Source Excel lives in `data/input/`. Never modify it in place. Write all results to `data/output/`.
- Excel, CSV, and JSON data files are gitignored. Scripts and notes are committed.
- Use `uv pip install` for any package, never `python -m pip install`. Never clear `UV_EXCLUDE_NEWER`.
- Fuzzy matching uses `rapidfuzz`. Do not hand-roll string similarity.
- Every match output must carry: source name, matched name, FINTRX id, score, and match method. No silent merges.
- Anything below the confidence threshold goes to a review file, not into the enriched output.
- HubSpot writes are a separate script and a separate explicit step. Never combine matching and CRM updates in one run.
- Log meaningful decisions (thresholds, field mappings, universe scope) in `notes/decisions.md` and in the root `decisions/log.md`.

## FINTRX access

- MCP tools: `fintrx_search_ria_firms`, `fintrx_lookup_ria_entity`, `fintrx_search_fo_firms`, `fintrx_lookup_family_office_entity`, and the `fintrx_get_ria_investor_*` family for enrichment fields.
- For 16k rows, prefer a bulk FINTRX export or a saved FINTRX list (`fintrx_get_list_records`) as the match universe over per-row MCP lookups. Per-row lookups are for the ambiguous band only.

## HubSpot access

- Object: companies. Check `discover_hubspot_schema` and `get_properties` before assuming property names.
- `HUBSPOT_TOKEN` in root `.env` for scripted writes.

## Jev (TypeSafe)

- Use Jev for the "is candidate X the same firm as source Y" decision on the ambiguous band. See `references/typesafe-jev/REFERENCE.md` and `COOKBOOKS.md`. Use the existing `jev.py` client.

## Scripts

- `scripts/normalize.py` -- name normalization helpers (shared)
- `scripts/match.py` -- fuzzy match source names against the FINTRX universe, write scored candidates
- `scripts/enrich.py` -- join FINTRX fields onto confirmed matches (to build)
- `scripts/push_hubspot.py` -- write enriched fields to HubSpot companies (to build, run only on explicit request)
