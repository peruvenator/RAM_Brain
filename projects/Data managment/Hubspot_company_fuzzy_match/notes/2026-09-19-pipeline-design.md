# Pipeline design: fill FINTRX Firm CRD ID on the HubSpot company list

Approved in chat 2026-09-19. Supersedes the "Workflow (planned)" section of README.md.

## Goal

Fill column C (`Fintrx Firm CRD ID`) of `Hubspot-company-list-2026-09-18.xlsx` (15,847 rows) with the
FINTRX RIA firm CRD, using name first, web domain second, and street address plus state as
tie-breakers. Produce a reviewable output. Nothing writes to HubSpot.

## Constraints established by the spike (see notes/decisions.md)

- Bulk FINTRX firm search returns id, name, city, state, AUM range, entity type. No CRD, website,
  or street address. Those live on the per-firm detail record (`ria_firm(id)`), one call each.
- FINTRX cannot be searched by street address. The reps typeahead (`/global_search/search_ria_reps`)
  matches on email domain and returns each rep's firm names, so domain lookup is scriptable.
- The firm-name typeahead is weak; rapidfuzz against the cached universe is the name engine.
- Jev never fetches or extracts. It decides. Two Jev passes: narrow candidates before the slow
  detail fetch, confirm with website and address after.
- Licensed seat: `per_page=50`, 0.25 s pace, one worker, disk cache, resume on failure.
- All FINTRX scripts run under `op run --env-file references/fintrx/op.env`. Jev key via `jev.py`.

## Data flow

```
Excel (A Record ID, B Company name, E/F street, H state, J domain)
  |
  v
[1] pull_universe.py  -> data/fintrx/universe.jsonl            (46k firms, once, ~8 min)
  |
  v
[2] match.py          -> data/output/cand_name.csv             (rapidfuzz top 3 per row)
[3] lookup_domain.py  -> data/output/cand_domain.csv           (reps typeahead per unique domain)
  |
  v
[4] narrow.py         -> data/output/cand_narrowed.csv         (Jev pass 1 on universe fields)
  |
  v
[5] fetch_details.py  -> data/fintrx/details/<item_id>.json    (resumable, the slow step)
                      -> data/fintrx/details.csv               (flattened fields)
  |
  v
[6] decide.py         -> data/output/matches.csv               (Jev pass 2 + code rules)
  |
  v
[7] write_output.py   -> data/output/<excel name>-enriched.xlsx (column C filled)
                      -> data/output/review.csv                (middle band, with FINTRX links)
```

Every intermediate file keeps `source_row`, `record_id`, `source_name`, `fintrx_item_id`,
`matched_name`, `method`, and the raw scores. No silent merges.

## Components

### [1] pull_universe.py
- `ria_search_all()` paged at 50. Writes one JSON line per firm: `item_id, name, city, state,
  country, type_entity, aum_range, hubspot_id, synced_to_hubspot`.
- Progress file `data/fintrx/universe.progress` holds the last completed page; rerun resumes.
- Stops when a page returns no items.

### [2] match.py (rewrite of the existing script)
- Loads Excel and universe. Normalizes with `normalize.py` (light form for scoring, aggressive form
  as secondary signal).
- Exact normalized-name hit: one candidate, `method=exact_normalized`, score 100.
- Otherwise `rapidfuzz.process.extract` with `token_set_ratio`, top 3, cutoff 75.
- Adds `state_match` (Excel column H vs universe state, 2-letter compare) as a boolean column.
- Rows with an empty name produce no candidates.

### [3] lookup_domain.py
- Extracts the registrable domain from column J (strip scheme, `www.`, path; lowercase).
- Skips webmail and generic domains (gmail, yahoo, outlook, hotmail, aol, icloud, and a short list
  in a constant). Skips blanks.
- One typeahead call per unique domain, cached in `data/fintrx/domain_cache.json` keyed by domain.
- Collapses reps to firm-name counts. Maps each firm name to a universe `item_id` by exact
  normalized name, then rapidfuzz best hit at or above 95 as fallback; unmapped names are kept
  with a null id and `method=domain_unmapped` so they show up in review rather than vanish.
- Output columns: `source_row, record_id, domain, matched_name, fintrx_item_id, rep_count,
  method=domain_reps`.

### [4] narrow.py (Jev pass 1)
- Merges name and domain candidates per row into one candidate set (dedupe by item_id).
- **Auto-keep without Jev**: exactly one candidate, and (`method=exact_normalized` with
  `state_match`) or (name candidate and domain candidate are the same item). These skip Jev.
- Everything else goes to Jev, one request per row, all candidates in one `state`:
  `{"hubspot": {"name", "state", "domain"}, "candidates": [{"idx", "name", "city", "state", "type"}]}`.
  Per candidate: one Score `link_state` with 3 levels (different firm / could be, related or
  ambiguous / same firm), one Noul `same_name`. Questions point at `candidates[idx]`.
- Keeps candidates with `link_state >= 0.5`, max 3, ordered by score. Rows with none kept go
  straight to review with `reason=no_plausible_candidate`.
- Raw Jev answers appended to `data/output/jev_pass1.jsonl` with the model version. Rerunning
  reads the cache first.

### [5] fetch_details.py
- Input: union of item_ids kept by [4]. One `ria_firm(id)` call each, 0.25 s pace, one worker.
- Raw record saved to `data/fintrx/details/<item_id>.json`; skip if the file exists (resume).
- Flattens to `details.csv`: `item_id, crd_id, primary_business_name, legal_name, former_names,
  website_address, main_office_address_1, main_office_address_2, office_city_name,
  main_office_state, zip (parsed from location_address), main_office_phone_number, hubspot_id`.
- Prints an ETA every 200 calls. `FintrxAuthError` stops the run with the refresh instructions;
  resume picks up where it stopped.

### [6] decide.py (Jev pass 2 + code rules)
- Per row, per kept candidate. Computed in code first (Jev is bad at string equality):
  `domain_equal` (Excel domain vs registrable domain of `website_address`), `phone_equal`
  (digits only, last 10), `state_equal`, `zip_equal` when both present.
- Jev, one request per row with all candidates in `state`:
  `{"hubspot": {"name", "street", "state", "domain"}, "candidates": [{"idx", "name", "legal_name",
  "former_names", "website", "street", "city", "state"}]}`.
  Per candidate: Score `link_state` (same 3 levels), Nouls `same_name`, `same_street`.
- Decision per candidate, in code:
  - `accept` if `domain_equal` or `phone_equal`, and `link_state >= 1.0` (domain or phone is
    near-conclusive; Jev just guards against a shared-domain parent like a custodian).
  - `accept` if `link_state >= 1.5` and (`state_equal` or state missing on either side).
  - `review` if `link_state >= 0.5`.
  - `reject` otherwise.
- Row outcome: the single accepted candidate wins. Two or more accepted candidates demote the
  row to review with `reason=multiple_accepts`. Zero accepted, any review: review. Else no match.
- Raw answers to `data/output/jev_pass2.jsonl`. Thresholds live in one constants block at the
  top of the file, logged in decisions.md.

### [7] write_output.py
- Copies the source Excel to `data/output/<name>-enriched.xlsx`, fills column C for accepted
  rows only, leaves everything else untouched, and adds columns `fintrx_match_name`,
  `fintrx_match_method`, `fintrx_match_confidence` at the far right for traceability.
- `review.csv`: one line per row-candidate in the review band with Excel fields, FINTRX fields,
  scores, reason, and `https://platform.fintrx.com/ria_investor/<item_id>`.
- Prints the count table: accepted, review, no candidate, blank name.

## Shared helpers
- `scripts/common.py`: paths, Excel column constants, domain extraction, phone normalization,
  JSONL read/write, a `paced()` wrapper that sleeps 0.25 s, ETA printing, `sys.path` setup for
  `references/typesafe-jev/jev.py`.
- `scripts/normalize.py`: unchanged.

## Error handling
- FINTRX: `FintrxAuthError` aborts with the refresh instructions from the SDK README. Other
  HTTP errors retry inside the SDK; after that the item is logged to `data/output/errors.csv`
  and skipped, never silently dropped.
- Jev: `jev.py` retries 429/529/5xx. A hard failure logs the row and continues; the row lands in
  review with `reason=jev_error`.
- Every step is idempotent and reads its own cache before calling anything.

## Testing
- Offline unit tests in `tests/`: domain extraction, phone normalization, candidate merge and
  dedupe, the decision rules in [6] with hand-built score tables, Excel write leaves other
  columns byte-identical.
- Live smoke: `--limit 20` flag on every script, run end to end on the first 20 Excel rows,
  inspect the review and enriched output by eye before the full run.
- Full run happens only after the smoke output looks right.

## Runtime and cost estimate
- FINTRX calls: ~925 universe, ~5k domain, ~16k to 18k details. About 3 to 4 hours unattended.
- Jev: ~10k to 20k requests across both passes, roughly 5M to 10M input tokens, under $1.
- Claude tokens per row: zero.

## Out of scope
- HubSpot writes (`push_hubspot.py`, later, on explicit request).
- Family office universe (no CRD there).
- Enrichment fields beyond CRD (later `enrich.py`).
