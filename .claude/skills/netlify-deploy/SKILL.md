---
name: netlify-deploy
description: Use when Rodrigo wants a project pushed, published, or deployed to Netlify — creating a new site, connecting a GitHub repo for auto-deploy, updating a live site, or password-protecting one.
---

# Netlify Deploy

Publish a project to Netlify under Rodrigo's account. Facts verified 2026-07-10 (rs-portfolio-builder setup).

## Account facts

- Netlify team: **"rodrigo-gordillo's team"** (Pro, card on file). Login: email `rodrigo.gordillo@investresolve.com` (not OAuth).
- GitHub org **resolve-lab** is connected via the Netlify GitHub App, but access is granted **per repo**: github.com/apps/netlify → Configure → resolve-lab → Select repositories → add the repo → Update access.
- Live precedents: `rs-sales-thermometer`, `rs-portfolio-builder` (password `rstacked`). Name new sites `rs-<project>`; names are globally unique.

## Choose the mode

- **Git-connected (default for anything the team will iterate on):** separate private repo under resolve-lab; every push to `main` auto-deploys.
- **CLI direct deploy (quick one-off, no repo):** `netlify deploy --prod --dir <folder>`. One-time setup: `npm install -g netlify-cli` then `netlify login` (browser OAuth, Rodrigo present). Never touch the quarantine env vars.

## Git-connected recipe

1. **Separate repo, never the monorepo.** Create `resolve-lab/<name>` (private) — `gh` CLI may not be installed; if absent, Rodrigo creates the repo at github.com and you `git remote add origin`. `git init -b main` inside the project folder, add the project path to RAM_Brain's `.gitignore` with the standard `# <Project> (separate repo: resolve-lab/<name>)` comment block.
2. **Only expose a `deploy/` dir.** Have the build script write `deploy/index.html` directly (add a `DEPLOY_FILE` output beside the normal one, like build_builder_widget.py) — a manual copy step will eventually be forgotten. Source, data, and CLAUDE.md stay unreachable from the web. `netlify.toml` at repo root:
   ```toml
   [build]
     publish = "deploy"
   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```
   No build command — Netlify serves committed files as-is.
3. **Publish-safety check before first push:** the built HTML must contain zero `localhost`/`127.0.0.1` references and no dev-only API endpoints (grep it). Scan for secrets before pushing.
4. Grant the Netlify GitHub App access to the new repo (see Account facts), then in app.netlify.com: Add new project → GitHub → **switch the account dropdown from peruvenator to resolve-lab** → pick the repo → confirm publish dir `deploy`, empty build command → Deploy.
5. Verify: fetch the live URL (HTTP 200, expected content marker, no localhost), then load it in a browser and exercise one real interaction.

## The stale-deploy trap (most likely future mistake)

**Netlify never runs local Python/build scripts.** The live site updates only when the committed build output changes. Update loop, always in this order:

```
rebuild (writes deploy/index.html) → run project tests → git add -A && commit && push
```

Pushing source edits without rebuilding leaves the live site silently stale. Never hand-edit `deploy/index.html`.

## Password protection (Pro feature)

UI only (not in CLI): project → Project configuration → General → Visitor access → Configure password protection → **Basic protection** + password + **All deploys** → Save.
Verify both ways: anonymous fetch returns 401 with no content leak; the password unlocks the widget in a browser.

## Gotchas

| Symptom | Reality |
|---|---|
| "Upgrade to Pro" card-entry modal blocks selecting a private resolve-lab repo | Private **org-owned** repos need Pro **with a card on file**. Rodrigo must enter card details himself — never fill payment fields. |
| Repo missing in Netlify's list | Per-repo GitHub App access not granted yet (Account facts), or account dropdown still on peruvenator. |
| Deep links like `app.netlify.com/start/...` bounce to the generic start page | Walk the UI: Add new project → GitHub → org → repo. |
| Scripted `el.click()` on Netlify buttons does nothing / popup blocked | SPA needs trusted input events — use chrome-cdp `clickxy` at element coords. |
| Site name taken | Names are global across all Netlify users; suffix with `-rs` or similar. |

## After deploying

Update the project README (live URL, deploy loop, "password protected — ask Rodrigo") and save/refresh a project memory so the next session doesn't re-derive the setup.
