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

[2026-09-20] DECISION: Exact normalized-name candidates always pass Jev pass 1 into the detail fetch (keep_reason exact_name), and both Jev caches are validated against the candidate id list before reuse | REASONING: 465 exact-name hits were dropped in pass 1 on a stale HubSpot state alone; pass 2 has the website to settle them (13 became accepts, 377 confirmed different firms). The cache bug: answers are indexed by candidate position, so inserting a candidate shifted cached answers onto the wrong firms and silently cost 32 accepts until caught by comparing counts | CONTEXT: Final first-run counts 6,981 accept, 2,409 review (140 multiple accepts, mostly parent/affiliate pairs sharing a website), 6,457 no match. Root decisions/log.md entry updated to match.

[2026-09-20] DECISION: Add a wealth team pass. Rows the firm pass did not accept are matched against the 28,586 FINTRX private wealth teams; accepted team matches fill a new column Fintrx_wealth_team_id (plus team name, parent CRD, confidence) and leave column C untouched | REASONING: Spot check showed Konvergent Wealth Partners is a FINTRX wealth team under Integrated Partners, not a firm, and about 1,800 non-accepted rows show the same pattern (domain reps all under one parent RIA). Teams have no CRD of their own, so the team id is the honest identifier and the parent CRD is recorded alongside | CONTEXT: Team pass evidence is name (rapidfuzz), state, and whether the row domain reps belong to the team parent firm; accept >= 1.5 with state agreeing or unknown, >= 1.0 with parent-domain agreement. FINTRX session token expired 2026-09-20 and the 1Password write is refused for the service account, so scripts run via scripts/with_chrome_token.py which captures the token from the debug Chrome per process

[2026-09-20] DECISION: Team pass accept rule: link >= 1.0 when the row's domain reps belong to the team's parent firm; link >= 1.5 only with a confirmed equal state (unknown state goes to review, unlike the firm pass) | REASONING: Team rows carry no website or phone, so name plus unknown state is too thin; 21 generic-name accepts moved to review under the stricter rule | CONTEXT: Team pass results 2026-09-20: 2,420 accepted (1,999 via parent-domain agreement, 421 via name and state), 425 review (11 multiple accepts), 6,021 no match (1,190 with no team candidate at all). Konvergent Wealth Partners -> team 54668 under Integrated Partners CRD 284656. Combined with the firm pass, 9,401 of 15,847 rows now carry a FINTRX identifier.
