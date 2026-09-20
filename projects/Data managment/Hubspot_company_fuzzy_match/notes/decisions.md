# Decisions

Format: [YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...

[2026-09-19] DECISION: Project created under projects/Data managment/Hubspot_company_fuzzy_match | REASONING: Enrich 16k+ HubSpot company names with FINTRX data for sales enablement | CONTEXT: Source Excel and FINTRX universe still to be loaded

# Open questions

- Which columns in the source Excel hold the company name, HubSpot record id, and any location or website fields that help disambiguate?
- Match universe: FINTRX bulk export, a saved FINTRX list, or live MCP lookups?
- Which FINTRX fields does sales actually want on the HubSpot company record?
- Confidence threshold for auto-accept vs review band.

[2026-09-19] DECISION: Pipeline runs entirely through the FINTRX Python SDK plus Jev; the FINTRX MCP connector is reserved for the leftover review band | REASONING: 15,847 rows means 20k+ lookups. The SDK is scriptable, cacheable, and resumable at zero Claude tokens per row; the MCP is interactive only and would cost dozens of sessions | CONTEXT: Spike 2026-09-19 confirmed bulk rows carry no CRD (detail call needed per accepted match), the reps typeahead resolves email domains to firm names, and the detail record carries website, street address, phone, legal and former names

[2026-09-19] DECISION: Two Jev passes, narrow before the detail fetch and confirm after | REASONING: The per-firm detail call is the slow step (~0.5 s each). Narrowing on universe fields first cuts detail calls from ~25k to ~17k. Jev cannot fetch a CRD; it only decides | CONTEXT: Cut points 0.5 / 1.5 on a 3-level Score per the TypeSafe entity-alignment cookbook; domain and phone equality computed in code, not asked of Jev

[2026-09-19] DECISION: FINTRX HubSpot sync ids are not used as a match key | REASONING: Sampled 1,000 firms; 316 carry a hubspot_id but only 2 appear in this Excel. The segment is the unsynced remainder | CONTEXT: Kept in the universe cache as a weak duplicate signal only

[2026-09-19] DECISION: Design spec lives at notes/2026-09-19-pipeline-design.md | REASONING: Project convention keeps working notes in notes/ | CONTEXT: Approved in chat before any code was written

[2026-09-19] DECISION: Keep the FINTRX caches (universe.jsonl, domain_cache.json, details/*.json, details.csv) in data/fintrx/ after the run | REASONING: Reusable for the later enrich step and any future FINTRX bulk job; licensed data stays inside the Dropbox project, gitignored, not shared outside the team | CONTEXT: Rodrigo confirmed in chat

[2026-09-20] DECISION: Thresholds for the first full run: rapidfuzz token_set cutoff 75, ranked on mean(token_set, token_sort), top 3; Jev pass 1 keep >= 0.5, max 3; pass 2 accept >= 1.5 with state agreeing or unknown, accept >= 0.75 with equal web domain, accept >= 1.25 with equal phone, review >= 0.5; two or more accepts on one row demote to review | REASONING: Cut points from the TypeSafe entity-alignment cookbook; domain is near-conclusive once Jev rules out shared-platform domains (custodians scored ~0.0), phone is weaker because affiliates share offices | CONTEXT: Full run 2026-09-20: 6,978 accept (6,337 via domain, 437 via phone, 204 via strong link), 2,401 review (2,261 review band, 140 multiple accepts), 6,468 no match (4,585 no kept candidate incl. 416 blank names, 1,883 all rejected). 100 Jev 500/NaN errors were re-asked cleanly. Raw answers cached, so re-thresholding is free.
