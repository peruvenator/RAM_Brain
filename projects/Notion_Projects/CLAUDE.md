# Notion Projects

Parent project for one-off and recurring improvements to the ReSolve Notion workspace. Each subproject lives in its own folder with a CLAUDE.md describing the specific task.

## Purpose

The Notion databases (Publications List, Runs, Channels, etc.) have accumulated data quality gaps and missing automations over time. This project is a home for targeted scripts and workflows that clean up, enrich, or extend those databases.

## Conventions

- Each subproject gets its own folder under `projects/Notion_Projects/`
- Each subproject has a `CLAUDE.md` with scope, target database, and key configuration
- Scripts use `NOTION_API_KEY` from `RAM_Brain/.env` unless otherwise noted (this is the integration with broader permissions)
- Test on a small batch before running against the full database
- Log results so we can audit what changed

## Related Projects

- `projects/Notion_Source_File_Sync/` -- automated file sync from Runs to Publications (daily cron)

## Key Notion Databases

| Database | ID |
|---|---|
| Publications List [M&S] | `60b55bf9-54ce-476c-a050-167034bd1346` |
| Data source (collection) | `collection://e8717675-3685-4d87-b1f8-f5317da846c1` |
| Runs | `2f63037cb38a8060908ce6e1ae5aeeeb` |
| Automation Runs | `3023037cb38a815fb09fd3d2b6f71ae7` |
| Automations Inventory | `3023037cb38a814bac81cb56a89af346` |
