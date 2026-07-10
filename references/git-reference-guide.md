# Git & GitHub Reference Guide
> Created for Rodrigo Gordillo — February 2026

---

## Part 1: Glossary — Git & GitHub Terminology

### The Basics

**Git** — A version control system that runs on your computer. It tracks every change
you make to your files, like an unlimited "undo" history. Git works locally — you
don't need the internet to use it.

**GitHub** — A website (owned by Microsoft) that hosts your Git repositories online.
Think of it as "Google Drive for code" but with superpowers: version history,
collaboration tools, and access control. Git is the engine; GitHub is the garage
where you park your car so others can see it.

**Repository (repo)** — A project folder that Git is tracking. It contains your files
plus a hidden `.git` folder that stores the entire change history. Every project you
work on becomes its own repository.

**Local repo** — The repository on YOUR computer.

**Remote repo** — The copy of your repository on GitHub (or another server). When you
hear "push to remote" it means "upload my changes to GitHub."

### Working With Files

**Working directory** — The files you can see and edit in your project folder right now.
This is just your normal folder — Git watches it for changes.

**Staging area (index)** — A "loading dock" between your working directory and a commit.
When you run `git add`, you're moving changes to the staging area, saying "I want to
include these in my next snapshot." This gives you control over exactly what goes
into each commit.

**Commit** — A snapshot of your project at a point in time. Every commit has:
- A unique ID (a long hash like `a1b2c3d`)
- A message you write describing what changed
- A timestamp
- A pointer to the previous commit

Think of commits like save points in a video game. You can always go back to any one.

**Commit message** — The short description you write when you commit.
Example: `"Add PDF export to compliance report generator"`

### Syncing With GitHub

**Clone** — Download a complete copy of a remote repo to your computer, including its
entire history. This is how your team members will get your projects.
```
git clone https://github.com/peruvenator/my-project.git
```

**Push** — Upload your local commits to GitHub. Your changes aren't on GitHub until
you push.
```
git push
```

**Pull** — Download and merge changes from GitHub into your local repo. This is how
you get changes your teammates made.
```
git pull
```

**Fetch** — Download changes from GitHub but DON'T merge them yet. Like checking
your mailbox without opening the letters. Useful when you want to review changes
before integrating them.

### Branching (For Later — When Collaborating)

**Branch** — A parallel version of your project. The default branch is called `main`.
You can create branches to work on features without affecting the main code.
Think of it like making a copy of a document to experiment on, with the ability
to merge your experiments back into the original.

**Main (or master)** — The primary branch. This is the "official" version of your code.
Older repos use `master`; newer ones use `main`. They're the same concept.

**Merge** — Combine changes from one branch into another. When your experiment on a
branch works out, you merge it back into `main`.

**Pull request (PR)** — A GitHub feature (not a Git feature) where you ask to merge
your branch into another branch. It creates a page where teammates can review your
changes, leave comments, and approve the merge. This is the core of team collaboration
on GitHub.

**Merge conflict** — When two people change the same line in the same file, Git can't
automatically decide which version to keep. It asks you to manually resolve the
conflict by choosing which changes to keep.

### Files Git Should Ignore

**.gitignore** — A special file that tells Git "never track these files." You list
patterns of files to exclude: log files, cached files, generated output, secrets, etc.
This keeps your repo clean and safe.

### Other Terms You'll Hear

**Fork** — A personal copy of someone else's repository on GitHub. Used in open-source:
you fork a project, make changes, then submit a pull request to the original.

**HEAD** — A pointer to your current position in the commit history. Usually points to
the latest commit on your current branch.

**Diff** — The difference between two versions of a file. Shows what was added (green)
and removed (red).

**Stash** — Temporarily shelve changes you've made so you can work on something else,
then come back to them later. Like putting papers in a drawer.

**Tag** — A named bookmark for a specific commit. Often used for releases
(e.g., `v1.0`, `v2.3`).

**Origin** — The default name for your remote repository on GitHub. When you see
`origin/main`, it means "the main branch on GitHub."

---

## Part 2: Git Hygiene — Best Practices for Your Workflow

### The Golden Rules

1. **Commit often, push regularly.** Small, frequent commits are better than one giant
   commit. Each commit should represent one logical change.

2. **Write meaningful commit messages.** Your future self (and teammates) will thank you.

3. **Never commit secrets.** API keys, passwords, tokens — use `.gitignore` to block
   them. If you accidentally commit a secret, consider it compromised and rotate it.

4. **Pull before you push** (when collaborating). Always get the latest changes from
   GitHub before pushing yours to avoid conflicts.

### Your Daily Workflow (Solo Projects)

```
1. Start your work session
   └── git pull                    # Get any changes (habit, even for solo work)

2. Make your changes
   └── Edit files normally

3. Review what changed
   └── git status                  # See which files changed
   └── git diff                    # See exactly what changed line-by-line

4. Stage your changes
   └── git add file1.py file2.py   # Stage specific files
   └── git add .                   # Or stage everything (if you're sure)

5. Commit with a good message
   └── git commit -m "Add PDF export feature to report generator"

6. Push to GitHub
   └── git push

7. Repeat steps 2-6 as you work
```

### Your Workflow (Team Projects — For Later)

```
1. Create a branch for your work
   └── git checkout -b feature/add-export-button

2. Make changes, commit (same as solo steps 2-5)

3. Push your branch
   └── git push -u origin feature/add-export-button

4. Open a Pull Request on GitHub
   └── Teammates review your code

5. After approval, merge into main
   └── Done via GitHub's interface

6. Clean up
   └── git checkout main
   └── git pull
   └── git branch -d feature/add-export-button
```

### Commit Message Guidelines

**Format:**
```
<action verb> <what changed>

Optional: longer description if needed
```

**Good examples:**
- `Add weekly scorecard PDF generation`
- `Fix date parsing bug in extract_excel.ps1`
- `Update compliance template for SEC 2025 requirements`
- `Remove unused logging code from report generator`
- `Refactor guide generator to support multiple brands`

**Bad examples:**
- `update` (too vague — update what?)
- `fix stuff` (what stuff?)
- `WIP` (work in progress — commit when the work IS the progress)
- `asdfasdf` (we've all been there, but don't)

**Verb cheat sheet:**
| Verb | When to use it |
|------|---------------|
| Add | Brand new feature or file |
| Fix | Bug fix |
| Update | Improve existing feature |
| Remove | Delete code or files |
| Refactor | Restructure code without changing behavior |
| Rename | Rename files or variables |
| Move | Relocate files |
| Document | Add/update documentation |

### How Often Should You Commit?

Commit when you've completed a **logical unit of work**:
- "I finished writing the function that parses Excel data" → commit
- "I fixed the bug where dates were off by one day" → commit
- "I added the new template file" → commit
- "I changed one typo in line 42" → probably fine to bundle with the next commit

**Don't wait until the end of the day** to commit everything in one giant lump.
If something goes wrong, you want small save points to roll back to.

### When to Push

- **At minimum:** End of every work session (so your work is backed up on GitHub)
- **Ideally:** After every few commits
- **Always:** Before you close your laptop or stop working for the day

### Quick Reference — Common Commands

| What you want to do | Command |
|---|---|
| See what changed | `git status` |
| See line-by-line changes | `git diff` |
| Stage files for commit | `git add <files>` |
| Stage everything | `git add .` |
| Commit staged changes | `git commit -m "your message"` |
| Push to GitHub | `git push` |
| Pull latest from GitHub | `git pull` |
| See commit history | `git log --oneline` |
| Undo changes to a file (before staging) | `git checkout -- <file>` |
| Unstage a file (keep changes) | `git reset HEAD <file>` |
| See which branch you're on | `git branch` |
| Create and switch to new branch | `git checkout -b <branch-name>` |
| Switch to existing branch | `git checkout <branch-name>` |
| Clone a repo | `git clone <url>` |

---

## Part 3: How Your Team Will Use This Repo

All projects live in a single **monorepo** on GitHub:

```
https://github.com/peruvenator/Project_Repository_RAM_RS
```

### For teammates to get the full repo:
```bash
git clone https://github.com/peruvenator/Project_Repository_RAM_RS.git
```
This downloads every project and the shared `references/brand-assets/` folders. They only
need to do this once.

### For teammates to get your latest updates:
```bash
cd Project_Repository_RAM_RS
git pull
```

### For teammates to contribute changes back:
They create a branch, make changes, push, and open a Pull Request for your
review. You approve or request changes. This keeps you in control of what goes
into the main version.

### What's NOT in the repo
The `.gitignore` excludes generated output, large binaries (PDF, PPTX, XLSX,
etc.), secrets (`.env` files), and intermediate artifacts. These stay in Dropbox
only. If a teammate needs those files, they get them via Dropbox sync — not git.

---

## Part 4: Sparse Checkout — Getting Only the Projects You Need

The full repo includes every project plus shared brand assets. If a teammate only
needs one or two projects, they can use **sparse checkout** to download just those
folders (plus `references/brand-assets/` so relative paths work).

### First-time setup (clone with sparse checkout):
```bash
# 1. Clone the repo without checking out files
git clone --no-checkout https://github.com/peruvenator/Project_Repository_RAM_RS.git
cd Project_Repository_RAM_RS

# 2. Enable sparse checkout
git sparse-checkout init --cone

# 3. Choose which folders to include
#    Always include references/brand-assets so shared asset paths resolve
git sparse-checkout set references/brand-assets projects/advisor-guide-tool

# 4. Check out the files
git checkout main
```

Now your working directory only contains `references/brand-assets/` and
`projects/advisor-guide-tool/`. All git commands (pull, push, branch, commit) work
normally — they just ignore files outside your sparse set.

### Add more projects later:
```bash
git sparse-checkout add RS_Portfolio_widget
```

### See what's currently included:
```bash
git sparse-checkout list
```

### Go back to the full repo:
```bash
git sparse-checkout disable
```

### Important notes:
- **Root files** (CLAUDE.md, .gitignore, Git_Reference_Guide.md, etc.) are always
  included — sparse checkout only filters directories.
- **Always include `references/brand-assets/`** if your project references shared brand assets.
- Sparse checkout is purely local — it doesn't affect the remote repo or other
  team members.

---

*Last updated: February 28, 2026*
