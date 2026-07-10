# Daily/Weekly Calendar Briefing

Sends Slack messages with upcoming calendar events pulled from Microsoft 365 via Graph API.

## What It Does

- **Daily (8 PM ET every day):** Tomorrow's calendar events
- **Weekly (8 PM ET Sundays):** Full Mon-Fri schedule for the coming week
- Filters out "Deep Work Block" entries automatically
- Logs every run to Notion (Automation Runs DB)

## Key Files

- `run-briefing.ps1` -- Main script, accepts `-Mode daily` or `-Mode weekly`
- `run-daily-briefing.bat` -- Task Scheduler wrapper for daily mode
- `run-weekly-briefing.bat` -- Task Scheduler wrapper for weekly mode
- `.env` -- Secrets (MS365 client credentials, Slack webhook, Notion tokens). NOT in git.
- `logs/` -- Timestamped log files

## Scheduled Tasks

| Task Name | Schedule | Wrapper |
|---|---|---|
| Daily Calendar Briefing | Every day at 8:00 PM | `run-daily-briefing.bat` |
| Weekly Calendar Briefing | Every Sunday at 8:00 PM | `run-weekly-briefing.bat` |

## Secrets

All secrets loaded from `.env`. Required keys:
- `MS365_CLIENT_ID`
- `MS365_TENANT_ID`
- `MS365_CLIENT_SECRET`
- `MS365_USER_EMAIL`
- `SLACK_WEBHOOK`
- `NOTION_TOKEN`
- `NOTION_RUNS_DB_ID`
- `NOTION_INVENTORY_DB_ID`

## Dependencies

- Dot-sources `../weekly-scorecard/automation-helpers.ps1` for `Send-SlackAlert` and `Log-NotionRun`
- Requires Azure app registration with `Calendars.Read` application permission
