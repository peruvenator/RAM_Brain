# HubSpot Company Fuzzy Match

Enrich a 16,000+ row Excel list of company names with FINTRX data, then push the enriched fields into HubSpot.

## Goal

- Match each company name in the source Excel to a FINTRX RIA or family office record
- Pull enrichment fields from FINTRX (AUM, firm type, location, custodians, contacts, etc.)
- Produce a reviewable match file with confidence scores before anything touches HubSpot

## Layout

- `data/input/` -- source Excel file(s). Gitignored.
- `data/fintrx/` -- FINTRX exports or cached lookups used as the match universe. Gitignored.
- `data/output/` -- match results and enriched files. Gitignored.
- `scripts/` -- matching and enrichment scripts
- `notes/` -- working notes, decisions, field mappings

## Workflow

Design: `notes/2026-09-19-pipeline-design.md`. Plan: `notes/2026-09-19-pipeline-plan.md`.
Every step is idempotent, cached, and resumable. FINTRX steps run under `op run`; Jev steps read the
key through `references/typesafe-jev/jev.py`. Add `--limit 20` to any step for a smoke run.

```powershell
$PY = "$env:USERPROFILE\.venvs\fintrx\Scripts\python.exe"
$OPENV = "<RAM_Brain>\references\fintrx\op.env"
op run --env-file $OPENV -- & $PY scripts\pull_universe.py     # 1. 46k firm universe, ~25 min, once
& $PY scripts\match.py                                         # 2. rapidfuzz name candidates, ~10 min
op run --env-file $OPENV -- & $PY scripts\lookup_domain.py     # 3. domain -> firm via reps typeahead, ~2 h
& $PY scripts\narrow.py                                        # 4. Jev pass 1, keep plausible candidates
op run --env-file $OPENV -- & $PY scripts\fetch_details.py     # 5. detail record per kept firm (CRD), ~2 h
& $PY scripts\decide.py                                        # 6. Jev pass 2 + code rules
& $PY scripts\write_output.py                                  # 7. enriched xlsx + review.csv
# Wealth team pass (rows the firm pass did not accept):
op run --env-file $OPENV -- & $PY scripts\pull_teams.py        # T1. 28.6k private wealth teams, ~5 min, once
& $PY scripts\match_teams.py                                   # T2. rapidfuzz + Jev vs teams -> team_matches.csv
& $PY scripts\write_output.py                                  # rewrites the xlsx with Fintrx_wealth_team_id filled
& $PY -m unittest discover tests                                # offline tests
```

Outputs land in `data/output/`: `<source>-enriched.xlsx` (column C filled for accepted rows, three
trace columns appended), `review.csv` (everything else, with FINTRX links), `matches.csv` (one line
per candidate with every score and flag). Thresholds live at the top of `narrow.py` and `decide.py`.

## Status

- 2026-09-19: Project created.
- 2026-09-20: Full run complete on the 15,847-row export. 6,981 accepted (CRD filled), 2,409 review, 6,457 no match (416 blank names). Wealth team pass same day: 2,420 rows got a Fintrx_wealth_team_id (parent CRD alongside), 425 team review, 6,021 no team match. 9,401 of 15,847 rows identified in total. Output in `data/output/`. HubSpot push not yet built.
