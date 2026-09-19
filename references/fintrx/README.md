# FINTRX SDK (Windows fork)

Python client for the FINTRX platform internal API, usable from any RAM_Brain project.
Forked from Adam Butler's `rs-sales-synthesis/fintrx_sdk_py` (macOS Keychain) on 2026-09-19;
this copy authenticates through 1Password and runs on Windows.

**Read `REFERENCE.md` before writing code against it.** It has the API contract, the method map,
the 13-F holdings section and the gotchas that silently corrupt results.

## When to use this vs. the FINTRX MCP connector

- **MCP connector** (available in Claude sessions): interactive lookups, screens, prospect lists,
  one firm's profile, anything conversational. No setup, no token.
- **This SDK**: bulk pagination over thousands of records, endpoints the connector does not expose
  (13-F holdings tables, filter vocabularies, list writes), reproducible scripts, unattended jobs.

## Setup (once per machine)

```powershell
uv venv $env:USERPROFILE\.venvs\fintrx -p 3.12
uv pip install --python $env:USERPROFILE\.venvs\fintrx\Scripts\python.exe -e "<path to>\RAM_Brain\references\fintrx"
```

Or install it into any project's own venv the same way (`uv pip install -e <this folder>`).
The venv lives outside Dropbox on purpose.

Requires the 1Password CLI with a **read + write** service account on the ReSolve vault
(see `references/sops/1password-credentials.md`). A read-only account breaks token capture.

## Credentials

FINTRX authenticates with a browser **session token**, not a login. It is captured from a
logged-in Chrome and stored on the 1Password item `Fintrix` (vault ReSolve) as fields
`credential` (the token) and `email`. Your username/password on the same item are for logging
into the browser; the SDK never uses them.

The SDK resolves the pair in this order:
1. `FINTRX_TOKEN` / `FINTRX_EMAIL` environment variables (set by `op run --env-file op.env`)
2. `op read op://ReSolve/Fintrix/credential` and `.../email`

### Refreshing the token (when the SDK raises FintrxAuthError)

1. Double-click `start-fintrx-chrome.cmd`. It opens a dedicated Chrome profile
   (`%USERPROFILE%\.fintrx-chrome`, outside Dropbox) with remote debugging on port 9222.
   Chrome 136+ refuses debugging on normal profiles, which is why it is separate.
2. First time only: log into platform.fintrx.com in that window. It stays logged in afterwards.
3. Run `%USERPROFILE%\.venvs\fintrx\Scripts\python capture_token.py`
   It reloads the page, reads the two headers off the traffic, writes them to 1Password and
   runs a health check. Nothing secret is printed.
4. Close the Chrome window if you like; the token lives in 1Password.

Manual fallback: F12 on any FINTRX page > Network > any `/v1/user/` request > copy
`X-User-Token` and `X-User-Email` into the `Fintrix` item's `credential` and `email` fields.

## Usage

```python
from fintrx_sdk import FintrxClient

c = FintrxClient()
c.health_check()                       # {"is_logged_in": true, ...}
c.ria_counts()                         # {'firms': 46142, 'reps': 802841, 'teams': 28586}
for firm in c.ria_search_all():        # generator, 50 per API call, be polite
    ...
c.global_search("Point72")             # typeahead across all categories
firm = c.ria_firm(164788)              # full record; CRD at ["ria_investor"]["crd_id"]
c.firm_holdings_statistics(283077)     # 13-F summary card by CRD
list(c.firm_holdings_all(283077))      # every ETF position, auto-paginated
```

Run scripts under `op run` so the token is injected per process:

```powershell
op run --env-file "<path to>\references\fintrx\op.env" -- python my_script.py
```

Without `op run` the SDK falls back to `op read`, which also works (two extra CLI calls at startup).

## Tests

```powershell
$py = "$env:USERPROFILE\.venvs\fintrx\Scripts\python.exe"
& $py -m unittest tests.test_auth -v      # offline, 6 checks
& $py tests\test_live.py                  # live read-only, 24 checks
& $py tests\test_live2.py                 # live read-only, 20 checks
```

All 50 passed on 2026-09-19 against Rodrigo's seat.

## Rate discipline

This is a licensed seat, not a scrape target. Keep `per_page=50`, pace calls (0.25s is the
convention), never run parallel workers, and size any bulk job with the `*_count` endpoints
first. A job in the tens of thousands of calls needs a daily cap and resume-on-failure; build
that in the project, not here.

## Files

| File | Purpose |
|---|---|
| `fintrx_sdk/client.py` | The client. One method per endpoint; `request()` for anything unwrapped |
| `fintrx_sdk/auth.py` | 1Password credential resolution and the Chrome capture |
| `capture_token.py` | One-command token refresh |
| `start-fintrx-chrome.cmd` | Launches the debug Chrome profile |
| `op.env` | 1Password references for `op run` (safe to commit; no values) |
| `REFERENCE.md` | API contract and gotchas, condensed for Claude |
| `docs/` | Adam's full reverse-engineering notes, verbatim; grep them, do not load whole |
| `tests/` | Offline auth tests and the live read-only suites |

## Upstream

Adam's original lives in `projects/Sales tools/rs-sales-synthesis/fintrx_sdk_py/`. This fork
diverges only in `auth.py` (1Password instead of Keychain), the removed `service` constructor
argument, and the added `firm_holdings*` methods. Endpoint changes discovered upstream can be
ported by copying `client.py` and re-applying those three edits.
