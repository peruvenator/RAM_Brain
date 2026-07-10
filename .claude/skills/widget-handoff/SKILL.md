# Skill: Widget Handoff

Generate a complete developer handoff package for any HTML widget project.

## When to Use

When the user has finished building or modifying an HTML widget locally and is ready to hand it off to the web developer for deployment. Invoke with `/widget-handoff` or when the user says "create a handoff" or "prepare the deploy package."

## How It Works

This skill is discovery-based. It figures out the project from context rather than assuming specific file names. Follow these steps in order.

---

### Step 1: Understand the project

Explore the current working directory to figure out:

- **What is this widget?** Read `CLAUDE.md` or `README.md` for the widget name, purpose, and target site
- **Is there a build script?** Look for `build_widget.py`, `build.py`, `Makefile`, `package.json` (check for a `build` script), or similar. If found, it must be run before packaging
- **What are the deploy output files?** These are the files that go to the server. Look for:
  - HTML files described as "embed," "web," or "production" versions (not local test files)
  - JS files that are separately uploaded (e.g., an extracted widget JS file)
  - PHP plugin files in a `backend/` folder
  - Any file the CLAUDE.md explicitly says "goes to" a server path
- **Where do these files go?** Look for deployment destinations in CLAUDE.md (server paths, WP directories, CDN paths)
- **What branch are we on?** Run `git branch --show-current`. This may affect which output files are active
- **Are there any integration requirements?** Things like WordPress shortcodes, server-side config injections, environment variables, or third-party service IDs the developer needs to wire up

If `CLAUDE.md` is missing or sparse, use `README.md`, `git log`, and directory structure to fill in the gaps.

---

### Step 1b: Confirm Divi prep has passed

If this widget is going onto the returnstacked.com or any Divi/WordPress site, confirm that `/website-widget-divi-prep` has been run and passed in this session. If it hasn't, run it now before continuing. Do not package a widget that hasn't cleared the Divi prep audit.

### Step 2: Run the build (if applicable)

If a build script was found:
- Run it now
- Report success or stop and surface the error
- Never proceed to packaging from a failed build

If no build script exists (direct-edit HTML project), skip this step and note it in the handoff doc.

---

### Step 3: Identify what changed

Run:
```
git log --oneline -8
git status
```

Summarize changes in plain English — what the developer will see differently, not what lines changed. For example: "Added a new chart tab," not "inserted 40 lines in `renderTabs()`."

If the user passed args to the skill (e.g., `/widget-handoff "added share link feature"`), incorporate that description.

---

### Step 4: Write HANDOFF.md

Write a `HANDOFF.md` file in the project root. Structure:

```
# [Widget Name] — Developer Handoff
Branch: [branch] | Date: [today]

## Overview
[1-2 sentences: what this widget is, where it lives on the site]
Questions: Rodrigo Gordillo

## Files to Deploy
| File | Destination | Notes |
|------|-------------|-------|
| ...  | ...         | ...   |

## What Changed
- [plain English bullet per change]

## Developer Action Items
1. [concrete, actionable step]
2. [include any required code blocks inline]
...

## Testing Checklist
- [ ] [specific thing to verify, derived from what changed]
- [ ] Open browser console — no JS errors on load
- [ ] [environment-specific checks, e.g., logged-in vs logged-out behavior]

## Integration Notes
[Only include what's relevant to this deployment: shortcodes, config injections, API keys, CDN version pins, etc. Include code blocks where needed.]

## Not in This Build
[Anything explicitly NOT done yet that the developer should not attempt. Pull from CLAUDE.md "Pending" or "Remaining Work" sections.]
```

Keep every section tight. The developer should be able to read this in 5 minutes and execute without asking questions.

---

### Step 5: Package the zip

Create a zip containing:
- `HANDOFF.md`
- All deploy output files identified in Step 1

Name it: `[widget-name]-handoff-[YYYY-MM-DD].zip`

Use PowerShell:
```powershell
Compress-Archive -Path HANDOFF.md, file1, file2 -DestinationPath "widget-name-handoff-2026-06-30.zip" -Force
```

Place the zip in the project root. Tell the user the filename so they can send it to the developer.

---

## Args

Optional — pass a short description of what changed:
```
/widget-handoff "added share link, removed intake form"
```
This seeds the "What Changed" section.
