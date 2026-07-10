# Notion Source File Sync — Claude.md

## Conversation Summary

This automation was born out of a broader conversation about improving templates and workflows in the **Publications List [M&S]** Notion database.

### Template Improvements (Preceding Context)

Rodrigo wanted each new page created from a Publications template to display an inline table showing the current page's own properties. We explored several approaches:

1. **Self-referencing inline database view**: Added a "This Page" self-relation property to Publications List [M&S], then created a Notion database automation ("When page is added → set This Page to Trigger page") so every new page automatically links to itself. Templates can then include an inline linked view filtered to "This Page contains This page."

2. **Gallery vs Table view**: Explored displaying properties vertically via Gallery view, but Notion forces the title to always show on Gallery cards — no way to hide it.

3. **@Property mentions**: Considered using `@Property` mentions in templates for a cleaner single-record display. These are display-only (can't edit inline) but visually clean. Rodrigo opted for the inline database approach.

4. **Batch template updates**: Updated the top section of templates (Final Published Files heading, inline database views, For Approval section, Final URLs section) across multiple templates via the Notion API. The API can insert inline linked database views structurally, but **cannot** configure view filters or column visibility — those must be set manually in the Notion UI per template. Tested on RAM Written Content Template (2026) and RS Presentation Slides (2025).

### The File Sync Problem

Under "Final Published Files," Rodrigo needed approved source files from the **Runs** database to automatically appear in the linked Publications page's **Source files** field. We explored:

- **Notion automations**: Can't move/copy file attachments between databases.
- **Rollups**: Can pull files via a relation, but can't filter by a property value (e.g., "Ready For Approval = Approved").
- **Inline filtered views**: Already in use — shows Runs data live, but doesn't populate the actual Source files property.
- **API script (this automation)**: Downloads files from Runs and re-uploads them to Publications via the Notion File Upload API.

## What This Automation Does

Monitors the **Runs** database (`2f63037cb38a8060908ce6e1ae5aeeeb`) for entries where **"Ready For Approval" = "Approved"**. For each newly approved Run:

1. Downloads the **Sources** file(s) from the Run page (via Notion's temporary file URLs)
2. Re-uploads each file to Notion using the **File Upload API** — uses single-part upload for files ≤ 20 MB, multi-part upload (with retry logic and rate-limit backoff) for larger files
3. Attaches the uploaded file to the linked **Publications List [M&S]** page's **"Source files"** field (found via the "Page" relation on the Run)
4. Tracks processed Run IDs in `processed_runs.json` to avoid duplicates

## Architecture

```
run-source-file-sync.bat          ← Windows Task Scheduler entry point
  └─ run-source-file-sync.ps1     ← PowerShell wrapper (logging, alerting)
       ├─ automation-helpers.ps1   ← Shared module (Log-NotionRun, Send-SlackAlert, Update-InventoryStatus)
       └─ notion_source_file_sync.py  ← Core Python script (Notion API calls, file transfer)
```

## Schedule

- **Frequency**: Daily at 1:00 AM ET
- **Method**: Windows Task Scheduler
- **Task name**: Source File Sync

## Key Configuration

| Item | Value |
|---|---|
| Runs Database ID | `2f63037cb38a8060908ce6e1ae5aeeeb` |
| Trigger property | Ready For Approval = "Approved" |
| Source field (Runs) | Sources |
| Target field (Publications) | Source files |
| Relation field (Runs → Pub) | Page |
| .env location | `RAM_Brain\.env` (variable: **`NOTION_API_KEY`** — not NOTION_TOKEN) |
| Automation Runs DB | `3023037cb38a815fb09fd3d2b6f71ae7` |
| Automations Inventory DB | `3023037cb38a814bac81cb56a89af346` |
| Automation name in Notion | "Source File Sync" |

## Test Results (2026-03-17)

Successfully tested end-to-end:

1. **rdmix_monthly** (65 MB source_files.zip) → 7-part upload → attached to *RDMIX 2026-02 Monthly Performance Report (Internal Use Only)* ✅
2. **rs_monthly** (49 MB source_files.zip) → 5-part upload → attached to *RS US Email: ETF Monthly Commentary 2026-02* ✅

### Issues encountered and resolved during testing:

- **Wrong API key**: Initial test used `NOTION_TOKEN` which didn't have access to the Runs database. Fixed by switching to `NOTION_API_KEY` in .env (a different integration with broader permissions).
- **Files over 20 MB**: First attempt failed because the source_files.zip files were 49-65 MB, exceeding Notion's single-part upload limit. Added multi-part upload support (10 MB chunks).
- **Rate limiting (503 errors)**: Multi-part uploads sent too fast hit Notion's rate limits. Added 1.5s delay between parts and exponential backoff retry logic (up to 3 retries per part).

## Setup Completed

- [x] Script files written to `RAM_Brain\projects\Notion_Source_File_Sync\`
- [x] Notion Automations Inventory entry created ("Source File Sync")
- [x] `automations-registry.md` updated with Source File Sync section
- [x] End-to-end test passed
- [x] Windows Task Scheduler task configured (Daily at 1:00 AM)

## Remaining Setup

Set up Windows Task Scheduler:
1. Create Basic Task → **"Source File Sync"**
2. Trigger: **Daily at 1:00 AM**
3. Action: Start a program → `run-source-file-sync.bat`
4. Start in: `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\Notion_Source_File_Sync\`
5. Check **"Run whether user is logged on or not"**

## Known Limitations

- **File property replacement**: When writing to "Source files" on a Publications page, the Notion API replaces the entire file list. Existing Notion-hosted files in that field will be overwritten. External URL files are preserved.
- **Temporary URLs**: Notion file download URLs expire after ~1 hour. The script downloads immediately upon detection.
- **Multi-part uploads**: Files are uploaded in 10 MB chunks. Each part has retry logic with exponential backoff for rate limiting. Files up to 5 GB are supported (Notion's workspace limit for paid plans).
- **Processed tracker**: If a Run needs re-processing, remove its ID from `processed_runs.json`.

## File Inventory

| File | Purpose |
|---|---|
| `notion_source_file_sync.py` | Core sync logic (Python) — reads `NOTION_API_KEY` from shared .env |
| `run-source-file-sync.ps1` | PowerShell wrapper with Notion/Slack logging — reads `NOTION_TOKEN` for logging helpers |
| `run-source-file-sync.bat` | Task Scheduler launcher |
| `Claude.md` | This file — conversation context and documentation |
| `processed_runs.json` | Auto-generated tracker of synced Run IDs |
| `logs/` | Auto-generated directory for per-run log files |
| `temp_downloads/` | Temporary directory for file transfers (auto-cleaned) |

## Important Notes for Future Claude Sessions

- The Python script reads **`NOTION_API_KEY`** from `.env` (not `NOTION_TOKEN`). The PS1 wrapper reads `NOTION_TOKEN` for the shared automation-helpers logging functions. These are two different integrations.
- The `.env` file is at `RAM_Brain\.env` (two levels up from the project folder).
- Source files from the Runs database are typically large zip files (50-65 MB), so multi-part upload is essential.
