# RS Knowledge Base — Project

Authoring and iteration workspace for the Return Stacked® product knowledge base. The deployable skill bundle is built from `rskb/` and shared as `rs-etfs-knowledge-base.zip` for upload via Organization settings → Skills.

## Current state

- **Latest deployment artifact:** `rs-etfs-knowledge-base.zip` (24 files, ~59KB) at the project root and mirrored to `Downloads RG/rs-etfs-knowledge-base.zip`. Folder-at-root structure ready for org-wide skill provisioning.
- **Source of truth for ETF Management sections:** April 2026 prospectus at https://www.returnstackedetfs.com/wp-content/uploads/pdf/return-PRO.pdf
- **Snapshot date for time-sensitive numbers:** late April 2026 (refresh per `rskb/SKILL.md` Live Data Refresh Protocol).

## Timeline

- **2026-04-28** — Initial KB delivered as `RS-ETF-knowledge.zip` (in Downloads RG). Sourced from returnstackedetfs.com, returnstackedetfs.ca, returnstackedfunds.com, quantifyfunds.com.
- **2026-04-29** — Per-fund Management sections in `etfs-us/*.md` and `overview.md` rewritten verbatim against the April 2026 prospectus. Section header changed from "Sponsor structure" to prospectus-canonical "Management". "Futures Trading Advisor" → "Futures Advisor".
- **2026-04-29** — Reconciled v2 from parallel work session: added `urls.yaml`, `scripts/fetch_live_data.py`, and a Live Data Refresh Protocol section in `SKILL.md`. v2's ETF/overview .md files were stale (pre-prospectus) and intentionally NOT pulled in.
- **2026-04-29** — Built deployment zip; copied to Downloads RG for upload.

## Coverage

- 7 U.S. ETFs: RSST, RSBT, RSSB, RSSY, RSBY, RSBA, RSSX
- 2 Canadian ETFs: RGBM, RGBM.U
- 1 mutual fund (3 share classes): RDMIX / RDMAX / RDMCX
- 3 partner (Quantify) funds: BTGD, ISBG, ISSB
- 5 concept files: return stacking 101, trend replication, carry/yield, merger arbitrage, glossary
- RDMIX predecessor-fund compliance language captured

## Folder layout

- `rskb/` — canonical KB content
- `rskb/SKILL.md` — skill front matter, routing, **Live Data Refresh Protocol**, mirror of urls.yaml
- `rskb/urls.yaml` — canonical product page URLs (URL registry source of truth)
- `rskb/scripts/fetch_live_data.py` — Python helper using requests + BeautifulSoup. Works on `quantifyfunds.com`; ReSolve domains (`.com`, `.ca`, `.funds`) hit SiteGround captcha so direct bash HTTP fetch isn't viable there.
- `rskb/README.md` — file map and source-of-truth conventions
- `rskb/update-process.md` — refresh cadence + deployment options + open design questions
- `rskb/etfs-us/` — 7 product files; Management sections are prospectus-verbatim with per-fund variations
- `rskb/etfs-canada/` — RGBM and RGBM.U
- `rskb/mutual-funds/` — RDMIX (covers all 3 share classes)
- `rskb/partner-funds/` — BTGD, ISBG, ISSB (Quantify)
- `rskb/concepts/` — concept-level explainers
- `rskb/overview.md` — lineup table + per-fund Management table

## Key facts to preserve across sessions

### Why web_fetch fails for live data without setup

`web_fetch` only accepts URLs that arrived via user message or prior search results, not URLs read from skill files. Workaround in `SKILL.md` Live Data Refresh Protocol:
1. Look up canonical URL in `urls.yaml`
2. Run `web_search "{ticker} returnstackedetfs.com"` to establish provenance
3. `web_fetch` the URL (now permitted)
4. Extract fields and cite the page's "as of" date

Direct bash HTTP fetch hits SiteGround captcha on all three ReSolve-controlled domains, so bash isn't a fallback there. It is fine for `quantifyfunds.com` (no bot-protection).

### Per-fund Management variations (verbatim from prospectus)

| Ticker | Sub-adviser line for RAM | Futures Advisor | Cayman Sub | Tidal punctuation |
|---|---|---|---|---|
| RSST | "investment sub-adviser" (NOT non-discretionary — anomaly) | Yes | Yes | Tidal Investments LLC |
| RSBT | "non-discretionary investment sub-adviser" | Yes | Yes | Tidal Investments LLC |
| RSBY | "non-discretionary investment sub-adviser" | Yes | Yes | Tidal Investments LLC |
| RSSY | "non-discretionary investment sub-adviser" | Yes | Yes | Tidal Investments LLC |
| RSSX | "non-discretionary investment sub-adviser" | Yes | Yes | Tidal Investments**,** LLC (with comma) |
| RSBA | "non-discretionary investment sub-adviser" (uses singular "Investment Sub-Adviser" header) | None | No | Tidal Investments LLC ("Tidal" or the "Adviser") |
| RSSB | "non-discretionary investment sub-adviser" | None | No | Tidal Investments LLC ("Tidal" or the "Adviser") |

### Why RSBA and RSSB have no Cayman / Futures Advisor

- RSSB: holds no commodity futures; no Cayman Subsidiary, no Futures Advisor.
- RSBA: holds Treasury futures only (not commodity futures); does not require CTA/Cayman.

## Open items (pick up here)

1. **Compliance verify RSST anomaly** — confirm with **Marissa Ciancio** whether RAM as plain "investment sub-adviser" (vs non-discretionary, like every other Return Stacked® US ETF) is intentional or a prospectus typo. A note is already inline in `etfs-us/rsst.md`.
2. **Open design questions** in `rskb/update-process.md`:
   - ~~Live data fetching~~ — RESOLVED via Live Data Refresh Protocol.
   - **Compliance modes** — split skill into client-facing (approved-language-only + mandatory disclosures) vs internal (full positioning context)?
   - **Personas file** — add voice guidance per principal (Adam, Mike, Corey, Rodrigo)?
   - **Stale-data self-flag** — should the skill warn when snapshot is older than N days?
3. **Decide deployment model** — Option 1 (skill, recommended), Option 2 (Notion + Project knowledge), Option 3 (hybrid Notion + sync script). Currently shipping as Option 1 via the org-wide zip.
4. **Test the skill** — once provisioned to the team, verify trigger phrases fire on tickers, sponsor names, and product-page URLs. Test sample content tasks (product brief, FAQ, comparison).
5. **Add CHANGELOG.md** under `rskb/` once the cadence stabilizes.

## When ready to deploy as the user's local skill

If/when this also gets installed in the local Claude Code skills folder (vs only org-wide):

- Copy `rskb/` to `.claude/skills/rs-etfs-knowledge-base/`
- Verify trigger phrases in `SKILL.md` description fire correctly
- Move this project folder to `archives/` (keep for history)
- Update `skills-backlog.md` to mark this skill as built

## Compliance reviewer

- **Marissa Ciancio** owns RDMIX predecessor-fund disclosure language. Any change to that block needs her sign-off.
- Marissa also owns the open RSST sub-adviser-language question above.

## Related files outside this folder

- `Downloads RG/RS-ETF-knowledge.zip` — original delivery (2026-04-28)
- `Downloads RG/rs-etfs-knowledge-base_2.zip` — v2 with live-data additions
- `Downloads RG/rs-etfs-knowledge-base.zip` — current deployment artifact (mirror of project root zip)
- `skills-backlog.md` — tracks "RS ETF knowledge base" as in-progress
