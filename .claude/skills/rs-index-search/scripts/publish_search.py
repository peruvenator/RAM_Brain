"""Publish the shared search engine into every index widget repo.

    python publish_search.py            # copy files + sync cores, report
    python publish_search.py --check    # report only; exit 1 if anything is stale

Each widget repo carries its own copy of the engine in a search/ folder so
it builds and tests on any machine with nothing but that repo:

    search/search-core.js        the core (namespace placeholder)
    search/search-synonyms.json  the shared concept groups
    search/sync_search_core.py   splices the core into the widget source
    search/test_search.js        the regression runner
    search/README.md             what the folder is and who owns it

The skill stays the only place to EDIT these files. This script copies them
into every repo in WIDGETS and re-renders the core inside each widget's
source file. Afterwards: rebuild Research Articles, regenerate the Product
Articles embed, run every widget's tests, then commit and push each repo.
"""
import argparse
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = SKILL.parents[2]                         # RAM_Brain
SITE = ROOT / "projects" / "return-stacked-website"

# (repo folder, widget source file, JS namespace)
WIDGETS = [
    (SITE / "Blog_Indexing_LP", "research-articles.template.html", "rsRes"),
    (SITE / "Product_Blog_Index", "product-articles.html", "rsArt"),
    (SITE / "Literature_PDF_Index", "literature-option-d.html", "rsLit"),
]

FILES = {
    "search-core.js": SKILL / "assets" / "search-core.js",
    "search-synonyms.json": SKILL / "assets" / "search-synonyms.json",
    "sync_search_core.py": HERE / "sync_search_core.py",
    "test_search.js": HERE / "test_search.js",
}

README = """# search/ (generated copy, do not edit here)

This folder is the widget's copy of the shared Return Stacked index search
engine. It makes the repo self-contained: the build and the search tests use
only these files.

| File | Purpose |
|---|---|
| `search-core.js` | Search functions (stemmer, typo tolerance, synonym expansion, any-word fallback). Rendered into the widget between the `RS-SEARCH-CORE-START` / `RS-SEARCH-CORE-END` comments. |
| `search-synonyms.json` | Concept groups shared by every index widget (tax / taxes / taxation, cta / managed futures, ...). |
| `sync_search_core.py` | Re-renders the core inside the widget source. `--check` reports whether it is current. |
| `test_search.js` | Regression runner: `node search/test_search.js search-tests.json` from the repo root. |

The master copy is maintained by ReSolve (the `rs-index-search` skill) and
published into the Research Articles, Product Articles and Literature repos
together, so all three widgets search the same way. If you need a change to
search behaviour or to the synonym list, ask Rodrigo rather than editing these
files: a local edit is overwritten by the next publish.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = False
    for repo, source, ns in WIDGETS:
        if not repo.is_dir():
            print(f"skip {repo.name}: folder not found")
            continue
        dest = repo / "search"
        changed = []
        if not args.check:
            dest.mkdir(exist_ok=True)
        for name, src in FILES.items():
            target = dest / name
            if target.exists() and filecmp.cmp(src, target, shallow=False):
                continue
            changed.append(name)
            if not args.check:
                shutil.copyfile(src, target)
        readme = dest / "README.md"
        if not readme.exists() or readme.read_text(encoding="utf-8") != README:
            changed.append("README.md")
            if not args.check:
                readme.write_text(README, encoding="utf-8", newline="\n")
        cmd = [sys.executable, str(HERE / "sync_search_core.py"), str(repo / source), "--ns", ns]
        if args.check:
            cmd.append("--check")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if changed:
            stale = True
        if r.returncode != 0:
            stale = True
        verb = "stale" if args.check else "updated"
        print(f"{repo.name}: search/ {verb}: {', '.join(changed) if changed else 'none'} | {r.stdout.strip() or r.stderr.strip()}")
    if not args.check:
        print("\nNext: python build_research_widget.py (Blog_Indexing_LP); regenerate the Product Articles embed;"
              " run node search/test_search.js search-tests.json in each repo; commit and push each repo.")
    sys.exit(1 if (args.check and stale) else 0)


if __name__ == "__main__":
    main()
