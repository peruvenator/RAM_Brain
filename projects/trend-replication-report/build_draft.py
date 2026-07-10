#!/usr/bin/env python3
"""build_draft.py -- Generate a clean, unbranded draft for compliance review.

Runs build_report.py (which produces a simple HTML with text + embedded charts),
captures the output as trend-replication-draft.html, then restores the branded
trend-replication-analysis.html untouched.

Usage:
    python build_draft.py
"""

import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
BRANDED = HERE / "trend-replication-analysis.html"
DRAFT = HERE / "trend-replication-draft.html"
BACKUP = HERE / "_trend-replication-analysis.html.bak"

# Back up the current branded file
if BRANDED.exists():
    shutil.copy2(BRANDED, BACKUP)
    print("Backed up branded HTML.")

# Run build_report.py to regenerate the raw/clean HTML
print("Running build_report.py...")
subprocess.run(["python", "build_report.py"], cwd=HERE, check=True)

# Copy the raw output to the draft file
shutil.copy2(BRANDED, DRAFT)
print(f"Draft saved: {DRAFT.name}")

# Restore the branded file
if BACKUP.exists():
    shutil.copy2(BACKUP, BRANDED)
    BACKUP.unlink()
    print("Branded HTML restored.")

print("\nDone. Open trend-replication-draft.html to review and edit.")
print("When edits are complete, bring the draft back and run the update workflow.")
