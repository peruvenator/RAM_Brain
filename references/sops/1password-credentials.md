# 1Password Credentials for RAM Brain

*Set up 2026-09-19. All new RAM Brain credentials live in the 1Password vault "ReSolve" and are pulled at runtime through the 1Password CLI. Never write a key into a file, a script, or a chat.*

## What is in place

- 1Password CLI (`op`) installed via winget, version 2.39.0. Alias `op` is on PATH after a terminal restart.
- A 1Password service account with access to the ReSolve vault. Its token is stored as the Windows user environment variable `OP_SERVICE_ACCOUNT_TOKEN` on both of Rodrigo's machines (laptop and work desktop, set up 2026-09-19). It is not in Dropbox, the repo, or any file.
- Because the service account is used, no Windows Hello prompt appears. Scheduled tasks work the same way as interactive sessions.
- The legacy root `.env` still exists for older projects. It is not being ported. New projects use 1Password from day one.

## Naming convention in the vault

- One item per service, named after the service: `HubSpot`, `Tiingo`, `TypeSafe`, `Notion`.
- The key goes in a field called `credential`. Extra values get plain field names: `client_id`, `tenant_id`, `webhook_url`.
- That gives every secret a stable address: `op://ReSolve/<Item>/<field>`, for example `op://ReSolve/HubSpot/credential`.

## How a project uses a credential

### Option A: env-file template (preferred for anything with 2+ secrets)

Create a file called `op.env` in the project folder. It holds references, not values, so it is safe to commit. (Do not name it `.env.*`; the repo gitignore hides those.)

```
HUBSPOT_TOKEN=op://ReSolve/HubSpot/credential
TIINGO_API_KEY=op://ReSolve/Tiingo/credential
```

Run the script through `op run`, which resolves the references into environment variables for that process only:

```powershell
op run --env-file op.env -- python build_draft.py
op run --env-file op.env -- powershell -NoProfile -File run-weekly-scorecard.ps1
```

Scripts then read `os.environ["HUBSPOT_TOKEN"]` or `$env:HUBSPOT_TOKEN` as normal. Nothing else changes.

### Option B: one-off read inside a script

```powershell
$env:HUBSPOT_TOKEN = op read "op://ReSolve/HubSpot/credential"
```

```python
import subprocess
token = subprocess.run(["op", "read", "op://ReSolve/HubSpot/credential"],
                       capture_output=True, text=True, check=True).stdout.strip()
```

### Running Claude Code with secrets available

```powershell
op run --env-file op.env -- claude
```

Every tool call inside that session inherits the variables.

## Checks

```powershell
op whoami                      # should show User Type: SERVICE_ACCOUNT
op vault list                  # should list ReSolve
op item list --vault ReSolve   # item names only, never prints secrets
```

## Rules

- Never paste a key into Claude Code chat, a Slack message, or a Notion page.
- Never print a resolved secret to the terminal. `op run` masks them in output by default; keep it that way.
- If a token is rotated, update the field in 1Password. No file in the repo changes.
- Scheduled Windows tasks pick up `OP_SERVICE_ACCOUNT_TOKEN` automatically because it is a user-level variable. If a task runs under a different Windows account, set the variable for that account too.
- Do not add `OP_SERVICE_ACCOUNT_TOKEN` to any file. If it leaks, revoke the service account in 1Password and create a new one.
