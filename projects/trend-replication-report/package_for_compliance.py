#!/usr/bin/env python3
"""Package the Trend Replication Report and supporting files for compliance review.

Usage:
    python package_for_compliance.py

Produces:
    Trend_Replication_3Y_Analysis_YYYY-MM-DD.zip

Contents:
    - Trend Replication Program - 3-Year Analysis.html  (the report)
    - Trend Replication - Audit Workbook.html           (audit trail)
    - build_report.py                                    (source code)
    - build_audit.py                                     (audit workbook generator)
    - trend-data.csv                                     (raw input data)
    - README.txt                                         (explains each file)
"""

import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
DATE_STR = datetime.now().strftime("%Y-%m-%d")
ZIP_NAME = f"Trend_Replication_3Y_Analysis_{DATE_STR}.zip"
ZIP_PATH = HERE / ZIP_NAME


def run_script(name):
    print(f"Running {name}...")
    result = subprocess.run(
        [sys.executable, str(HERE / name)],
        cwd=str(HERE),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr[-500:]}")
        sys.exit(1)
    # Print last 2 lines of stdout
    lines = result.stdout.strip().splitlines()
    for line in lines[-2:]:
        print(f"  {line}")


def build_readme():
    return f"""\
Trend Replication Program - 3-Year Analysis
============================================
Compliance Review Package
Generated: {datetime.now().strftime('%B %d, %Y')}

CONTENTS
--------

1. Trend Replication Program - 3-Year Analysis.html
   The report itself. Open in any web browser.
   Contains 13 figures, full-period statistics, quarterly tracking detail,
   ex-post optimization analysis, technical glossary, index definitions,
   and important disclosures.

2. Trend Replication - Audit Workbook.html
   Detailed audit trail of every computation in the report.
   Shows formulas, Python code, Lo (2002) autocorrelation adjustment
   at each lag, naive vs. adjusted tracking error reconciliation,
   and optimization details. Open in any web browser.

3. build_report.py
   The Python script that generates the report from raw data.
   All computations, chart generation, and HTML templating are
   contained in this single file.

4. build_audit.py
   The Python script that generates the audit workbook.
   Replicates all key computations independently and presents
   them in an auditable format.

5. trend-data.csv
   Raw input data. Daily index levels for:
   - SG Trend Index (NEIXCTAT excess return basis)
   - Top Down Small (Constrained Universe) - Net
   - Top Down Medium (Full Universe) - Net
   - Bottom Up - Net
   - Blend (15/15/70) - Net
   Date range: Feb 08, 2023 through Feb 06, 2026 (754 trading days)

HOW TO REPRODUCE
----------------
Install Python 3.10+ and the following packages:
    pip install pandas numpy matplotlib scipy

Then run:
    python build_report.py     # generates the report HTML
    python build_audit.py      # generates the audit workbook HTML

Both scripts read trend-data.csv and produce self-contained HTML files
with all charts and data embedded inline (no external dependencies).

METHODOLOGY NOTES
-----------------
- Tracking error uses the Lo (2002) autocorrelation adjustment with
  a Bartlett kernel and 21 lags. See the audit workbook for full detail.
- Reference: Lo, Andrew W. "The Statistics of Sharpe Ratios."
  Financial Analysts Journal 58(4), 2002: 36-52.
- All model returns are net of estimated trading costs and a 0.95%
  annual expense ratio.
- The SG Trend Index is shown on an excess return basis.

CONTACT
-------
ReSolve Asset Management
"""


def main():
    # Step 1: Generate the raw report HTML
    run_script("build_report.py")

    # Step 2: Apply ReSolve branded paged layout
    run_script("reformat_html.py")

    # Step 3: Generate the audit workbook
    run_script("build_audit.py")

    # Step 4: Verify all files exist
    files_to_package = {
        "Trend Replication Program - 3-Year Analysis.html": HERE / "trend-replication-analysis.html",
        "Trend Replication - Audit Workbook.html": HERE / "trend-replication-audit.html",
        "build_report.py": HERE / "build_report.py",
        "build_audit.py": HERE / "build_audit.py",
        "trend-data.csv": HERE / "trend-data.csv",
    }

    for display_name, path in files_to_package.items():
        if not path.exists():
            print(f"ERROR: {display_name} not found at {path}")
            sys.exit(1)

    # Step 4: Build README
    readme_text = build_readme()

    # Step 5: Create ZIP
    print(f"\nPackaging into {ZIP_NAME}...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for display_name, path in files_to_package.items():
            zf.write(path, display_name)
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  + {display_name} ({size_mb:.1f} MB)")
        zf.writestr("README.txt", readme_text)
        print(f"  + README.txt")

    zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\nDone: {ZIP_PATH.name} ({zip_size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
