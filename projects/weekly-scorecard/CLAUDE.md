# Weekly Scorecard Automation

Automated weekly scorecard for Return Stacked ETFs. Runs every Tuesday at 5:00 AM via Windows Task Scheduler.

## What It Does

1. Downloads the CUs-RUs.xlsx from Dropbox
2. Extracts AUM and revenue data from Excel
3. Updates HubSpot CRM with current figures
4. Logs the run to a Notion database
5. Archives the file

## Key Files

- `run-weekly-scorecard.ps1` -- Main automation script (self-contained, no LLM dependencies)
- `run-weekly-scorecard.bat` -- Thin wrapper for Task Scheduler
- `automation-helpers.ps1` -- Shared functions (Slack alerts, Notion run logging)
- `.env` -- Secrets (HubSpot token, Notion tokens, Slack webhook). NOT in git.
- `extract_excel.ps1` -- Excel data extraction helper
- `Hubspot_CRM_object_list.txt` -- Reference list of HubSpot CRM objects
- `shortcuts/Run Weekly Scorecard.bat` -- Manual run shortcut with pause

## Scheduled Task

- **Task name:** RS Weekly Scorecard
- **Schedule:** Every Tuesday at 5:00 AM
- **Managed via:** Windows Task Scheduler (schtasks)

## Secrets

All secrets are loaded from `.env` via `$PSScriptRoot`. Required keys:
- `HUBSPOT_TOKEN`
- `NOTION_TOKEN`
- `NOTION_DB_ID`
- `NOTION_RUNS_DB_ID`
- `NOTION_INVENTORY_DB_ID`
- `SLACK_WEBHOOK`
