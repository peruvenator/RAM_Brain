# Cockroach Carry Monthly Report

Automated monthly performance summary for the Cockroach Carry strategy. Pulls the
S3-synced daily returns series, computes performance stats, and posts a summary to
Slack for the team.

> Note: originally framed as an email automation. Delivery is via Slack (incoming
> webhook). To switch to email later, swap `post_to_slack()` in `generate_report.py`
> for an MS365/SMTP send.

## What It Does

1. Reads the daily returns CSV synced from S3
2. Computes monthly / YTD / trailing / since-inception performance + risk stats
3. Formats a summary and posts it to Slack (with a stale-data warning if needed)

## Source Data

- `C:\Users\RodrigoGordillo\S3_Data\backtest-sims\portfolio_returns\cockroach_carry\live\strategy\returns.csv`
- Daily returns, columns: `date, gross, net, net_fees, net_fees_tax` + `*_adj` variants
- Headline column is configurable in `generate_report.py` (`CONFIG["return_column"]`, default `net_fees`)

## Key Files

- `generate_report.py` -- Core: load CSV, compute stats, build + post message (self-contained Python)
- `run-cockroach-report.ps1` -- Wrapper: .env load, logging, Slack failure alert
- `run-cockroach-report.bat` -- Task Scheduler wrapper (quotes the spaced path)
- `.env.example` -- Config template (copy to `.env`)
- `logs/` -- Per-run logs (auto-pruned after 180 days)

## Run It

```
# Compute + print, do NOT post (good for iterating)
python generate_report.py --dry-run

# Compute + post to Slack
python generate_report.py

# Full wrapped run (what Task Scheduler calls)
.\run-cockroach-report.bat
```

## Config

Edit the `CONFIG` block at the top of `generate_report.py`:
- `return_column` -- which return series to headline (default `net_fees`)
- `strategy_name`, `recipient_name` -- message text
- `staleness_days` -- warn if data is older than this

## Secrets

- `SLACK_WEBHOOK` -- loaded from project `.env` first, then repo-root `.env` (which already has it).
  Set a project-level webhook only if you want a dedicated channel/recipient.

## Scheduling (not yet set up)

Intended cadence: **monthly**. Not yet registered in Task Scheduler. To add it,
mirror the existing cron jobs (see root `MEMORY.md` "Cron Jobs"):
- Task name suggestion: `Cockroach Monthly Report`
- Run `run-cockroach-report.bat` via `Register-ScheduledTask` (PowerShell, monthly trigger)
- Use the `cmd.exe /c ""path""` quoting pattern to survive the spaces in the path

## Open Items

- Confirm headline return column (`net_fees` vs `net_fees_tax` vs `gross`)
- Confirm Slack target (shared channel vs dedicated webhook for the specific team member)
- Decide day-of-month + time for the schedule, then register the task
