# Automations Registry

Central inventory of all automated scripts. Future Claude sessions should read this file first.

## Shared Module

`C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\automation-helpers.ps1`

Every automation dot-sources this file to get `Send-SlackAlert`, `Log-NotionRun`, and `Update-InventoryStatus`. The calling script must define `$Config` with keys: `NotionToken`, `SlackWebhook`, `NotionRunsDbId`, `NotionInventoryDbId`. It must also define `$logFile` and a `Write-Log` function.

## Weekly Scorecard

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\run-weekly-scorecard.ps1` |
| Wrapper | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\run-weekly-scorecard.bat` |
| Schedule | Every Tuesday 5 AM (Windows Task Scheduler) |
| Shortcut | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\shortcuts\Run Weekly Scorecard.bat` |
| Description | Downloads CUs-RUs.xlsx from Dropbox, extracts AUM/Revenue/Units via Excel COM, pulls HubSpot CRM metrics (calls, emails, meetings, deals, SQLs, SALs), writes weekly entry to Notion "Weekly AUM Growth" DB, archives file. |

### Notion Databases

| Database | ID | Purpose |
|---|---|---|
| Weekly AUM Growth | `2d93037cb38a80ffba72d26282a7a544` | Weekly scorecard data entries |
| Automation Runs | `3023037cb38a815fb09fd3d2b6f71ae7` | Run history log (success/failure per run) |
| Automations Inventory | `3023037cb38a814bac81cb56a89af346` | Central inventory of all automations |

### Alerting

- **Slack**: Webhook posts to channel on failure only
- **Notion**: Every run (success or failure) logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run
