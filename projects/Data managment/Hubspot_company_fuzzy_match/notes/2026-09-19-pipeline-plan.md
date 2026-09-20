# HubSpot CRD Match Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill column C (`Fintrx Firm CRD ID`) of the 15,847-row HubSpot company Excel with FINTRX RIA CRDs, via a resumable, cached, zero-Claude-token pipeline.

**Architecture:** Seven small scripts in `scripts/`, each reading the previous step's file and its own cache, all sharing `common.py`. FINTRX calls go through the shared SDK under `op run`; Jev calls go through the shared `jev.py`. Decisions are computed in code from Jev scores plus exact-equality flags; every intermediate keeps source and match identifiers.

**Tech Stack:** Python 3.12 venv at `%USERPROFILE%\.venvs\fintrx` (pandas, openpyxl, rapidfuzz, numpy, fintrx_sdk installed), `references/typesafe-jev/jev.py`, 1Password CLI `op run`, unittest.

**Spec:** `notes/2026-09-19-pipeline-design.md`

## Global Constraints

- Never modify the source Excel. Read from the project root; write only to `data/output/`.
- `uv pip install` only, never `python -m pip install`. Never clear `UV_EXCLUDE_NEWER`.
- Fuzzy matching uses `rapidfuzz`. No hand-rolled similarity.
- Every match output carries source name, matched name, FINTRX id, score, and method.
- Below-threshold matches go to review, never into the enriched output.
- No HubSpot writes anywhere in this plan.
- FINTRX: `per_page=50`, 0.25 s pace, single worker, disk cache, resume. Run under
  `op run --env-file "<RAM_Brain>/references/fintrx/op.env" -- <venv python> scripts/<x>.py`.
- Jev: up to 6 threads, raw answers cached to JSONL, thresholds in one constants block.
- Data files (`*.csv`, `*.json`, `*.jsonl`, `*.xlsx`) are gitignored. Commit scripts, tests, notes.
- Commits end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

**Run alias used below** (PowerShell):
```powershell
$PY = "$env:USERPROFILE\.venvs\fintrx\Scripts\python.exe"
$OPENV = "c:\Users\rgord\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\references\fintrx\op.env"
# FINTRX scripts:  op run --env-file $OPENV -- & $PY scripts\<x>.py
# Everything else: & $PY scripts\<x>.py
```

---

## File structure

| File | Responsibility |
|---|---|
| `scripts/common.py` | Paths, Excel column names, domain and phone normalization, JSONL and CSV helpers, pacing, ETA, source loader, error log, Jev import path |
| `scripts/normalize.py` | Unchanged name normalizer |
| `scripts/pull_universe.py` | Step 1, FINTRX universe cache |
| `scripts/match.py` | Step 2, rapidfuzz name candidates (rewrite) |
| `scripts/lookup_domain.py` | Step 3, domain to firm via reps typeahead |
| `scripts/narrow.py` | Step 4, Jev pass 1, candidate narrowing |
| `scripts/fetch_details.py` | Step 5, per-firm detail cache and flatten |
| `scripts/decide.py` | Step 6, Jev pass 2 plus code rules |
| `scripts/write_output.py` | Step 7, enriched Excel and review CSV |
| `tests/test_common.py`, `tests/test_narrow.py`, `tests/test_decide.py`, `tests/test_write_output.py` | Offline unit tests |

---

### Task 1: Shared helpers

**Files:**
- Create: `scripts/common.py`
- Create: `tests/__init__.py` (empty), `tests/test_common.py`

**Interfaces:**
- Produces: `PROJECT, RAM_BRAIN, DATA_FX, DATA_OUT, SOURCE_XLSX, UNIVERSE, UNIVERSE_PROGRESS, DOMAIN_CACHE, DETAILS_DIR, DETAILS_CSV, CAND_NAME, CAND_DOMAIN, CAND_NARROWED, JEV1, JEV2, MATCHES, REVIEW, ERRORS` (Paths); `COL_*` strings; `extract_domain(value) -> str`; `phone_digits(value) -> str`; `norm_state(value) -> str`; `read_jsonl(path) -> list[dict]`; `append_jsonl(path, rows)`; `read_csv(path) -> list[dict]`; `write_csv(path, rows, fields)`; `paced()`; `class Eta(total)` with `.tick() -> str`; `load_source(limit=None) -> pandas.DataFrame` with column `source_row`; `log_error(step, key, err)`; `is_blank(v) -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_common.py
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import common


class DomainTests(unittest.TestCase):
    def test_strips_scheme_www_and_path(self):
        self.assertEqual(common.extract_domain("https://www.Intrua.com/about"), "intrua.com")

    def test_blank_and_nan(self):
        self.assertEqual(common.extract_domain(None), "")
        self.assertEqual(common.extract_domain(float("nan")), "")
        self.assertEqual(common.extract_domain("  "), "")

    def test_generic_domain_is_blank(self):
        self.assertEqual(common.extract_domain("gmail.com"), "")

    def test_subdomain_kept(self):
        self.assertEqual(common.extract_domain("advisors.lpl.com"), "advisors.lpl.com")


class PhoneTests(unittest.TestCase):
    def test_last_ten_digits(self):
        self.assertEqual(common.phone_digits("+1 617-720-4500"), "6177204500")
        self.assertEqual(common.phone_digits("12814912800"), "2814912800")
        self.assertEqual(common.phone_digits("(713) 355-9910"), "7133559910")

    def test_short_or_blank(self):
        self.assertEqual(common.phone_digits(None), "")
        self.assertEqual(common.phone_digits("555"), "")


class StateTests(unittest.TestCase):
    def test_upper_two_letter(self):
        self.assertEqual(common.norm_state(" tx "), "TX")
        self.assertEqual(common.norm_state("Texas"), "TX")
        self.assertEqual(common.norm_state(None), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `& $PY -m unittest tests.test_common -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'common'`

- [ ] **Step 3: Write common.py**

```python
"""Shared helpers for the HubSpot -> FINTRX CRD match pipeline."""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RAM_BRAIN = PROJECT.parents[1]            # projects/Data managment/<project> -> RAM_Brain
DATA_FX = PROJECT / "data" / "fintrx"
DATA_OUT = PROJECT / "data" / "output"
SOURCE_XLSX = PROJECT / "Hubspot-company-list-2026-09-18.xlsx"

UNIVERSE = DATA_FX / "universe.jsonl"
UNIVERSE_PROGRESS = DATA_FX / "universe.progress"
DOMAIN_CACHE = DATA_FX / "domain_cache.json"
DETAILS_DIR = DATA_FX / "details"
DETAILS_CSV = DATA_FX / "details.csv"
CAND_NAME = DATA_OUT / "cand_name.csv"
CAND_DOMAIN = DATA_OUT / "cand_domain.csv"
CAND_NARROWED = DATA_OUT / "cand_narrowed.csv"
JEV1 = DATA_OUT / "jev_pass1.jsonl"
JEV2 = DATA_OUT / "jev_pass2.jsonl"
MATCHES = DATA_OUT / "matches.csv"
REVIEW = DATA_OUT / "review.csv"
ERRORS = DATA_OUT / "errors.csv"

COL_RECORD_ID = "Record ID"
COL_NAME = "Company name"
COL_CRD = "Fintrx Firm CRD ID"
COL_PHONE = "Phone Number"
COL_STREET1 = "Street Address"
COL_STREET2 = "Street Address 2"
COL_STATE = "State/Region (Global)"
COL_DOMAIN = "Company Domain Name"

PACE_SECONDS = 0.25
JEV_WORKERS = 6
FINTRX_FIRM_URL = "https://platform.fintrx.com/ria_investor/{item_id}"

sys.path.insert(0, str(RAM_BRAIN / "references" / "typesafe-jev"))

GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com",
    "me.com", "live.com", "msn.com", "comcast.net", "att.net", "verizon.net",
    "sbcglobal.net", "protonmail.com", "linkedin.com", "facebook.com",
}

US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC",
}


def is_blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return str(v).strip() == ""


def extract_domain(value) -> str:
    """Registrable host from a URL or bare domain, lowercase; '' for blank or generic."""
    if is_blank(value):
        return ""
    s = str(value).strip().lower()
    s = re.sub(r"^[a-z]+://", "", s)
    s = s.split("/")[0].split("?")[0].split("#")[0]
    s = s.split("@")[-1]
    if s.startswith("www."):
        s = s[4:]
    s = s.strip(". ")
    if not s or "." not in s or s in GENERIC_DOMAINS:
        return ""
    return s


def phone_digits(value) -> str:
    """Last 10 digits of a phone number, or '' if fewer than 10."""
    if is_blank(value):
        return ""
    d = re.sub(r"\D", "", str(value))
    return d[-10:] if len(d) >= 10 else ""


def norm_state(value) -> str:
    if is_blank(value):
        return ""
    s = str(value).strip()
    if len(s) == 2:
        return s.upper()
    return US_STATES.get(s.lower(), s.upper())


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def paced() -> None:
    time.sleep(PACE_SECONDS)


class Eta:
    def __init__(self, total: int, label: str = ""):
        self.total, self.label, self.done, self.t0 = total, label, 0, time.time()

    def tick(self) -> str:
        self.done += 1
        el = time.time() - self.t0
        rate = self.done / el if el > 0 else 0
        left = (self.total - self.done) / rate if rate else 0
        return f"{self.label} {self.done}/{self.total} elapsed {el/60:.1f}m eta {left/60:.1f}m"


def load_source(limit: int | None = None):
    import pandas as pd
    df = pd.read_excel(SOURCE_XLSX)
    df.insert(0, "source_row", range(len(df)))
    if limit:
        df = df.head(limit)
    return df


def log_error(step: str, key, err) -> None:
    ERRORS.parent.mkdir(parents=True, exist_ok=True)
    new = not ERRORS.exists()
    with ERRORS.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "step", "key", "error"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), step, key, str(err)[:500]])
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `& $PY -m unittest tests.test_common -v`
Expected: 8 tests, OK

- [ ] **Step 5: Commit**

```bash
git add scripts/common.py tests/__init__.py tests/test_common.py
git commit -m "Hubspot CRD match: shared helpers" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Pull the FINTRX universe

**Files:**
- Create: `scripts/pull_universe.py`

**Interfaces:**
- Consumes: `common.UNIVERSE, UNIVERSE_PROGRESS, append_jsonl, paced`
- Produces: `data/fintrx/universe.jsonl`, one object per firm: `item_id:int, name, location, city, state, country, type_entity, aum_range, hubspot_id, synced_to_hubspot`. Later tasks call `load_universe()` from `match.py`.

- [ ] **Step 1: Write pull_universe.py**

```python
"""Step 1: cache every FINTRX RIA firm row to data/fintrx/universe.jsonl. Resumable.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/pull_universe.py [--max-pages N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import UNIVERSE, UNIVERSE_PROGRESS, append_jsonl, paced, log_error  # noqa: E402
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

EXTRA_FIELDS = ("city", "state", "country", "type_entity", "aum_range", "hubspot_id", "synced_to_hubspot")


def flatten(item: dict, extra: dict) -> dict:
    row = {"item_id": int(item["id"]), "name": item.get("name"), "location": item.get("location")}
    for k in EXTRA_FIELDS:
        row[k] = extra.get(k)
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    page = 1
    if UNIVERSE_PROGRESS.exists():
        page = int(UNIVERSE_PROGRESS.read_text().strip() or 0) + 1
        print(f"resuming at page {page}")
    c = FintrxClient()
    total_rows = 0
    try:
        while True:
            d = c.ria_search(page=page, per_page=50)
            items = d.get("investors") or []
            if not items:
                print(f"page {page} empty, done")
                break
            extra = d.get("extra_info") or {}
            rows = [flatten(it, extra.get(str(it["id"]), {}) or {}) for it in items]
            append_jsonl(UNIVERSE, rows)
            UNIVERSE_PROGRESS.write_text(str(page))
            total_rows += len(rows)
            if page % 25 == 0:
                print(f"page {page}, {total_rows} rows this run")
            if args.max_pages and page >= args.max_pages:
                break
            page += 1
            paced()
    except FintrxAuthError as e:
        print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        log_error("pull_universe", page, e)
        raise
    print(f"universe at {UNIVERSE}, last page {UNIVERSE_PROGRESS.read_text().strip()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke it on two pages**

Run: `op run --env-file $OPENV -- & $PY scripts\pull_universe.py --max-pages 2`
Expected: `universe at ...universe.jsonl, last page 2`; file has 100 lines with `item_id` and `state` keys.

- [ ] **Step 3: Delete the smoke output so the full run starts clean, then run the full pull in the background**

```powershell
Remove-Item data\fintrx\universe.jsonl, data\fintrx\universe.progress
op run --env-file $OPENV -- & $PY scripts\pull_universe.py
```
Expected: about 925 pages, roughly 8 to 10 minutes. Ends with `page N empty, done`.

- [ ] **Step 4: Commit**

```bash
git add scripts/pull_universe.py
git commit -m "Hubspot CRD match: universe pull with resume" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Name candidates with rapidfuzz

**Files:**
- Modify: `scripts/match.py` (full rewrite)

**Interfaces:**
- Consumes: `common.load_source, UNIVERSE, CAND_NAME, norm_state, write_csv, read_jsonl`, `normalize.normalize`
- Produces: `load_universe() -> list[dict]` (deduped by `item_id`), `UniverseIndex` with `.rows, .norm, .norm_agg, .exact: dict[str,int]` and `.lookup_exact(name) -> int | None`, `.best(name, cutoff) -> (idx, score) | None`; `data/output/cand_name.csv` with columns `source_row, record_id, source_name, candidate_rank, fintrx_item_id, matched_name, cand_city, cand_state, score, score_aggressive, method, state_match`.

- [ ] **Step 1: Write match.py**

```python
"""Step 2: rapidfuzz name candidates for every Excel row against the cached FINTRX universe.

Run:  python scripts/match.py [--limit N] [--top 3] [--cutoff 75]
No network. Output: data/output/cand_name.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NAME, COL_NAME, COL_RECORD_ID, COL_STATE, UNIVERSE,  # noqa: E402
                    is_blank, load_source, norm_state, read_jsonl, write_csv)
from normalize import normalize  # noqa: E402

FIELDS = ["source_row", "record_id", "source_name", "candidate_rank", "fintrx_item_id", "matched_name",
          "cand_city", "cand_state", "score", "score_aggressive", "method", "state_match"]
CHUNK = 500


def load_universe() -> list[dict]:
    seen, out = set(), []
    for r in read_jsonl(UNIVERSE):
        if r["item_id"] in seen or is_blank(r.get("name")):
            continue
        seen.add(r["item_id"])
        out.append(r)
    if not out:
        sys.exit(f"universe empty, run pull_universe.py first ({UNIVERSE})")
    return out


class UniverseIndex:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.norm = [normalize(r["name"]) for r in rows]
        self.norm_agg = [normalize(r["name"], aggressive=True) for r in rows]
        self.exact: dict[str, int] = {}
        for i, n in enumerate(self.norm):
            self.exact.setdefault(n, i)

    def lookup_exact(self, name) -> int | None:
        return self.exact.get(normalize(name))

    def best(self, name, cutoff: float = 95.0):
        hit = process.extractOne(normalize(name), self.norm, scorer=fuzz.token_set_ratio, score_cutoff=cutoff)
        return (hit[2], hit[1]) if hit else None


def candidate(src, rank, idx, score, s_agg, method, ux: UniverseIndex) -> dict:
    u = ux.rows[idx]
    return dict(source_row=src["source_row"], record_id=src[COL_RECORD_ID], source_name=src[COL_NAME],
                candidate_rank=rank, fintrx_item_id=u["item_id"], matched_name=u["name"],
                cand_city=u.get("city"), cand_state=norm_state(u.get("state")),
                score=round(float(score), 1), score_aggressive=round(float(s_agg), 1), method=method,
                state_match=bool(src["_state"]) and src["_state"] == norm_state(u.get("state")))


def match_all(df, ux: UniverseIndex, top: int, cutoff: float) -> list[dict]:
    srcs = df.to_dict("records")
    for s in srcs:
        s["_state"] = norm_state(s.get(COL_STATE))
        s["_norm"] = normalize(s.get(COL_NAME)) if not is_blank(s.get(COL_NAME)) else ""
        s["_agg"] = normalize(s.get(COL_NAME), aggressive=True) if s["_norm"] else ""
    out: list[dict] = []
    fuzzy = [s for s in srcs if s["_norm"] and s["_norm"] not in ux.exact]
    for s in srcs:
        if s["_norm"] and s["_norm"] in ux.exact:
            out.append(candidate(s, 1, ux.exact[s["_norm"]], 100.0, 100.0, "exact_normalized", ux))
    for start in range(0, len(fuzzy), CHUNK):
        block = fuzzy[start:start + CHUNK]
        sims = process.cdist([s["_norm"] for s in block], ux.norm, scorer=fuzz.token_set_ratio,
                             score_cutoff=cutoff, workers=-1, dtype=np.float32)
        k = min(top, sims.shape[1])
        part = np.argpartition(-sims, k - 1, axis=1)[:, :k]
        for bi, s in enumerate(block):
            idxs = part[bi]
            idxs = idxs[np.argsort(-sims[bi, idxs])]
            rank = 0
            for j in idxs:
                sc = float(sims[bi, j])
                if sc < cutoff:
                    continue
                rank += 1
                s_agg = fuzz.token_set_ratio(s["_agg"], ux.norm_agg[j]) if s["_agg"] else 0.0
                out.append(candidate(s, rank, int(j), sc, s_agg, "fuzzy_token_set", ux))
        print(f"fuzzy {min(start + CHUNK, len(fuzzy))}/{len(fuzzy)}", file=sys.stderr)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--cutoff", type=float, default=75.0)
    args = ap.parse_args()
    df = load_source(args.limit)
    ux = UniverseIndex(load_universe())
    print(f"{len(df)} source rows vs {len(ux.rows)} universe firms")
    rows = match_all(df, ux, args.top, args.cutoff)
    write_csv(CAND_NAME, rows, FIELDS)
    have = {r["source_row"] for r in rows}
    print(f"wrote {CAND_NAME}: {len(rows)} candidates, {len(have)} rows with >=1, "
          f"{len(df) - len(have)} rows with none")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run on 20 rows**

Run: `& $PY scripts\match.py --limit 20`
Expected: prints universe size ~46,000 and a candidate count. Open `data/output/cand_name.csv` and confirm Intrua maps to "Intrua Financial" and Newfound Research to "Newfound Research LLC".

- [ ] **Step 3: Run on all rows**

Run: `& $PY scripts\match.py`
Expected: finishes in under 15 minutes. Note the counts for the decisions log.

- [ ] **Step 4: Commit**

```bash
git add scripts/match.py
git commit -m "Hubspot CRD match: chunked rapidfuzz name candidates" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Domain candidates via the reps typeahead

**Files:**
- Create: `scripts/lookup_domain.py`

**Interfaces:**
- Consumes: `common.extract_domain, DOMAIN_CACHE, CAND_DOMAIN, load_source, paced, log_error`, `match.load_universe, UniverseIndex`, `FintrxClient.request`
- Produces: `data/fintrx/domain_cache.json` `{domain: {firm_name: rep_count}}`; `data/output/cand_domain.csv` with columns `source_row, record_id, source_name, domain, matched_name, fintrx_item_id, rep_count, method` where method is `domain_reps` or `domain_unmapped` (null id).

- [ ] **Step 1: Write lookup_domain.py**

```python
"""Step 3: resolve each Excel domain to FINTRX firm names through the reps typeahead.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/lookup_domain.py [--limit N]
Cache: data/fintrx/domain_cache.json (one call per unique domain, ever).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_DOMAIN, COL_DOMAIN, COL_NAME, COL_RECORD_ID, DOMAIN_CACHE,  # noqa: E402
                    Eta, extract_domain, load_source, log_error, paced, write_csv)
from match import UniverseIndex, load_universe  # noqa: E402
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

FIELDS = ["source_row", "record_id", "source_name", "domain", "matched_name", "fintrx_item_id",
          "rep_count", "method"]
MAP_CUTOFF = 95.0


def firms_for_domain(c: FintrxClient, domain: str) -> dict[str, int]:
    r = c.request("POST", "/global_search/search_ria_reps", form={"query": domain})
    counts: dict[str, int] = {}
    for rep in r.get("reps") or []:
        for f in rep.get("firms") or []:
            counts[f] = counts.get(f, 0) + 1
    return counts


def load_cache() -> dict:
    return json.loads(DOMAIN_CACHE.read_text(encoding="utf-8")) if DOMAIN_CACHE.exists() else {}


def save_cache(cache: dict) -> None:
    DOMAIN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DOMAIN_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def map_firm(ux: UniverseIndex, firm_name: str):
    i = ux.lookup_exact(firm_name)
    if i is None:
        hit = ux.best(firm_name, MAP_CUTOFF)
        i = hit[0] if hit else None
    return ux.rows[i]["item_id"] if i is not None else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    df = load_source(args.limit)
    df["_domain"] = df[COL_DOMAIN].map(extract_domain)
    domains = sorted({d for d in df["_domain"] if d})
    cache = load_cache()
    todo = [d for d in domains if d not in cache]
    print(f"{len(domains)} unique domains, {len(todo)} not cached")
    if todo:
        c = FintrxClient()
        eta = Eta(len(todo), "domains")
        try:
            for n, d in enumerate(todo, 1):
                try:
                    cache[d] = firms_for_domain(c, d)
                except FintrxAuthError:
                    raise
                except Exception as e:  # noqa: BLE001
                    log_error("lookup_domain", d, e)
                    cache[d] = {"_error": 1}
                if n % 50 == 0:
                    save_cache(cache)
                    print(eta.tick())
                else:
                    eta.tick()
                paced()
        except FintrxAuthError as e:
            save_cache(cache)
            print(f"AUTH ERROR, refresh the token then rerun: {e}", file=sys.stderr)
            sys.exit(2)
        save_cache(cache)
    ux = UniverseIndex(load_universe())
    rows = []
    for s in df.to_dict("records"):
        d = s["_domain"]
        if not d:
            continue
        for firm, cnt in (cache.get(d) or {}).items():
            if firm.startswith("_"):
                continue
            item_id = map_firm(ux, firm)
            rows.append(dict(source_row=s["source_row"], record_id=s[COL_RECORD_ID], source_name=s[COL_NAME],
                             domain=d, matched_name=firm, fintrx_item_id=item_id, rep_count=cnt,
                             method="domain_reps" if item_id else "domain_unmapped"))
    write_csv(CAND_DOMAIN, rows, FIELDS)
    print(f"wrote {CAND_DOMAIN}: {len(rows)} domain candidates for {len({r['source_row'] for r in rows})} rows")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run on 20 rows**

Run: `op run --env-file $OPENV -- & $PY scripts\lookup_domain.py --limit 20`
Expected: about 20 domains looked up, output shows Intrua, Newfound, Insight Wealth mapped with `domain_reps`. `mtyale.com` maps to Princeton Fund Advisors (a wrong-firm hint that pass 2 will reject).

- [ ] **Step 3: Run on all rows in the background**

Run: `op run --env-file $OPENV -- & $PY scripts\lookup_domain.py`
Expected: roughly 12k to 14k unique domains at ~0.45 s each, about 1.5 to 2 hours. Resumable.

- [ ] **Step 4: Commit**

```bash
git add scripts/lookup_domain.py
git commit -m "Hubspot CRD match: domain lookup via reps typeahead" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Narrow candidates with Jev pass 1

**Files:**
- Create: `scripts/narrow.py`
- Create: `tests/test_narrow.py`

**Interfaces:**
- Consumes: `common.*`, `read_csv(CAND_NAME)`, `read_csv(CAND_DOMAIN)`, `match.load_universe`, `jev.ask, jev.score, jev.noul`
- Produces: `merge_candidates(name_rows, domain_rows) -> dict[int, list[dict]]` keyed by `source_row`, each candidate `{item_id:int|None, matched_name, cand_city, cand_state, methods:str ("exact_normalized|domain_reps"), name_score:float, state_match:bool, rep_count:int}`; `auto_keep(cands) -> bool`; `build_questions(cands) -> dict`; `data/output/cand_narrowed.csv` with columns `source_row, record_id, source_name, fintrx_item_id, matched_name, cand_city, cand_state, methods, name_score, state_match, rep_count, link1, same_name1, kept, keep_reason`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_narrow.py
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import narrow


def nrow(sr, item, name, score, state_match, method="fuzzy_token_set"):
    return dict(source_row=str(sr), fintrx_item_id=str(item), matched_name=name, cand_city="X",
                cand_state="TX", score=str(score), method=method, state_match=str(state_match))


def drow(sr, item, name, cnt):
    return dict(source_row=str(sr), fintrx_item_id=str(item) if item else "", matched_name=name,
                rep_count=str(cnt), method="domain_reps" if item else "domain_unmapped")


class MergeTests(unittest.TestCase):
    def test_dedupes_same_item_and_joins_methods(self):
        m = narrow.merge_candidates([nrow(0, 11, "A Co", 100, True, "exact_normalized")], [drow(0, 11, "A Co", 5)])
        self.assertEqual(len(m[0]), 1)
        self.assertEqual(m[0][0]["methods"], "exact_normalized|domain_reps")
        self.assertEqual(m[0][0]["rep_count"], 5)

    def test_unmapped_domain_kept_with_none_id(self):
        m = narrow.merge_candidates([], [drow(3, None, "Mystery LLC", 2)])
        self.assertIsNone(m[3][0]["item_id"])


class AutoKeepTests(unittest.TestCase):
    def test_single_exact_with_state(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 100, True, "exact_normalized")], [])
        self.assertTrue(narrow.auto_keep(m[0]))

    def test_single_exact_without_state_needs_jev(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 100, False, "exact_normalized")], [])
        self.assertFalse(narrow.auto_keep(m[0]))

    def test_name_and_domain_agree(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 88, False)], [drow(0, 11, "A", 3)])
        self.assertTrue(narrow.auto_keep(m[0]))

    def test_two_candidates_needs_jev(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 100, True, "exact_normalized"), nrow(0, 12, "A2", 90, True)], [])
        self.assertFalse(narrow.auto_keep(m[0]))


class QuestionTests(unittest.TestCase):
    def test_two_questions_per_candidate(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 90, True), nrow(0, 12, "B", 80, False)], [])
        q = narrow.build_questions(m[0])
        self.assertEqual(set(q), {"link_0", "name_0", "link_1", "name_1"})
        self.assertEqual(q["link_0"]["type"], "score")
        self.assertEqual(len(q["link_0"]["criteria"]), 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `& $PY -m unittest tests.test_narrow -v`
Expected: FAIL, `No module named 'narrow'`

- [ ] **Step 3: Write narrow.py**

```python
"""Step 4: Jev pass 1. Merge name and domain candidates, keep the plausible ones before the
slow detail fetch.

Run:  python scripts/narrow.py [--limit N] [--force]
Reads data/output/cand_name.csv + cand_domain.csv. Writes data/output/cand_narrowed.csv.
Raw Jev answers cached in data/output/jev_pass1.jsonl (keyed by source_row).
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_DOMAIN, CAND_NAME, CAND_NARROWED, COL_DOMAIN, COL_NAME, COL_RECORD_ID,  # noqa: E402
                    COL_STATE, JEV1, JEV_WORKERS, Eta, append_jsonl, extract_domain, load_source,
                    log_error, norm_state, read_csv, read_jsonl, write_csv)
from match import load_universe  # noqa: E402
import jev  # noqa: E402

# ---- thresholds (logged in notes/decisions.md) ----
KEEP_MIN = 0.5        # link_state score at or above -> keep for the detail fetch
MAX_KEEP = 3

LEVELS = [
    "Different firms. The names refer to distinct businesses, or the same words point at a "
    "different company (for example a location that contradicts).",
    "Could be the same firm. The names are similar, one contains the other, they look like a "
    "parent and an affiliate or a renamed firm, or the evidence is too thin to tell.",
    "The same firm. The names identify the same business once legal suffixes, abbreviations and "
    "spelling variants are ignored, and nothing contradicts it.",
]

FIELDS = ["source_row", "record_id", "source_name", "fintrx_item_id", "matched_name", "cand_city",
          "cand_state", "methods", "name_score", "state_match", "rep_count", "link1", "same_name1",
          "kept", "keep_reason"]


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def merge_candidates(name_rows: list[dict], domain_rows: list[dict]) -> dict[int, list[dict]]:
    out: dict[int, dict] = {}

    def slot(sr: int, key):
        return out.setdefault(sr, {}).setdefault(key, dict(
            item_id=key if isinstance(key, int) else None, matched_name="", cand_city="", cand_state="",
            methods=[], name_score=0.0, state_match=False, rep_count=0))

    for r in name_rows:
        sr, item = int(r["source_row"]), _int(r["fintrx_item_id"])
        c = slot(sr, item)
        c.update(matched_name=r["matched_name"], cand_city=r.get("cand_city") or "",
                 cand_state=r.get("cand_state") or "", name_score=max(c["name_score"], float(r["score"])),
                 state_match=c["state_match"] or str(r.get("state_match")).lower() == "true")
        if r["method"] not in c["methods"]:
            c["methods"].append(r["method"])
    for r in domain_rows:
        sr, item = int(r["source_row"]), _int(r["fintrx_item_id"])
        key = item if item is not None else ("unmapped", r["matched_name"])
        c = slot(sr, key)
        c["matched_name"] = c["matched_name"] or r["matched_name"]
        c["rep_count"] += _int(r.get("rep_count")) or 0
        if r["method"] not in c["methods"]:
            c["methods"].append(r["method"])
    result = {}
    for sr, d in out.items():
        cands = list(d.values())
        for c in cands:
            c["methods"] = "|".join(c["methods"])
        cands.sort(key=lambda c: (-c["name_score"], -c["rep_count"]))
        result[sr] = cands
    return result


def auto_keep(cands: list[dict]) -> bool:
    """Skip Jev when there is exactly one candidate and either the normalized name is exact
    with a matching state, or name and domain independently point at the same firm."""
    if len(cands) != 1 or cands[0]["item_id"] is None:
        return False
    m = cands[0]["methods"].split("|")
    if "exact_normalized" in m and cands[0]["state_match"]:
        return True
    return "domain_reps" in m and any(x in m for x in ("exact_normalized", "fuzzy_token_set"))


def build_questions(cands: list[dict]) -> dict:
    q = {}
    for i, _ in enumerate(cands):
        q[f"link_{i}"] = jev.score(
            {"question": f"How does `candidates[{i}]` relate to the firm described in `hubspot`?",
             "compare": [f"`candidates[{i}].name`", "`hubspot.name`"],
             "supporting": [f"`candidates[{i}].state` versus `hubspot.state`",
                            f"whether `hubspot.domain` looks like it belongs to `candidates[{i}].name`"],
             "note": "Treat LLC, Inc, LP, Wealth Management, Advisors and similar generic words as noise."},
            LEVELS)
        q[f"name_{i}"] = jev.noul(
            f"Does `candidates[{i}].name` name the same business as `hubspot.name`, ignoring legal "
            f"suffixes and generic industry words?")
    return q


def build_state(src: dict, cands: list[dict]) -> dict:
    return {"hubspot": {"name": src.get(COL_NAME), "state": norm_state(src.get(COL_STATE)),
                        "domain": extract_domain(src.get(COL_DOMAIN))},
            "candidates": [{"idx": i, "name": c["matched_name"], "city": c["cand_city"],
                            "state": c["cand_state"], "type": c.get("type_entity") or ""}
                           for i, c in enumerate(cands)]}


def ask_row(sr: int, src: dict, cands: list[dict]) -> dict:
    try:
        r = jev.ask(build_state(src, cands), build_questions(cands))
        return {"source_row": sr, "model": r.get("model"), "answers": r["answers"],
                "usage": r.get("usage"), "items": [c["item_id"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        log_error("narrow_jev", sr, e)
        return {"source_row": sr, "error": str(e)[:300], "items": [c["item_id"] for c in cands]}


def apply_answers(cands: list[dict], ans: dict | None) -> None:
    for i, c in enumerate(cands):
        a = (ans or {}).get(f"link_{i}")
        n = (ans or {}).get(f"name_{i}")
        c["link1"] = round(a["score"], 3) if a else ""
        c["same_name1"] = round(n["noul"], 3) if n else ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="ignore the Jev cache")
    args = ap.parse_args()
    df = load_source(args.limit)
    srcs = {int(s["source_row"]): s for s in df.to_dict("records")}
    types = {u["item_id"]: u.get("type_entity") for u in load_universe()}
    merged = merge_candidates(read_csv(CAND_NAME), read_csv(CAND_DOMAIN))
    for cands in merged.values():
        for c in cands:
            c["type_entity"] = types.get(c["item_id"])
    cache = {} if args.force else {r["source_row"]: r for r in read_jsonl(JEV1)}

    need = [sr for sr, cands in merged.items() if sr in srcs and not auto_keep(cands) and sr not in cache]
    print(f"{len(srcs)} rows, {len(merged)} with candidates, {len(need)} need Jev pass 1")
    eta = Eta(len(need), "jev1")
    with ThreadPoolExecutor(max_workers=JEV_WORKERS) as ex:
        for res in ex.map(lambda sr: ask_row(sr, srcs[sr], merged[sr]), need):
            cache[res["source_row"]] = res
            append_jsonl(JEV1, [res])
            if eta.done % 200 == 0:
                print(eta.tick())
            else:
                eta.tick()

    rows = []
    for sr, src in srcs.items():
        cands = merged.get(sr, [])
        base = dict(source_row=sr, record_id=src[COL_RECORD_ID], source_name=src[COL_NAME])
        if not cands:
            rows.append(dict(base, kept=False, keep_reason="no_candidates"))
            continue
        if auto_keep(cands):
            apply_answers(cands, None)
            for c in cands:
                rows.append(dict(base, **c, kept=True, keep_reason="auto"))
            continue
        res = cache.get(sr) or {}
        apply_answers(cands, res.get("answers"))
        if "error" in res or "answers" not in res:
            for c in cands:
                rows.append(dict(base, **c, kept=False, keep_reason="jev_error"))
            continue
        ranked = sorted(cands, key=lambda c: -(c["link1"] or 0))
        kept_ids = {id(c) for c in ranked[:MAX_KEEP] if c["item_id"] is not None and (c["link1"] or 0) >= KEEP_MIN}
        for c in cands:
            k = id(c) in kept_ids
            rows.append(dict(base, **c, kept=k, keep_reason="jev1" if k else "below_keep_min"))
        if not kept_ids:
            rows[-1]["keep_reason"] = "no_plausible_candidate"
    for r in rows:
        r["fintrx_item_id"] = r.get("item_id", "")
    write_csv(CAND_NARROWED, rows, FIELDS)
    kept = {r["source_row"] for r in rows if r["kept"]}
    print(f"wrote {CAND_NARROWED}: {len(rows)} candidate rows, {len(kept)} rows with >=1 kept, "
          f"{sum(1 for r in rows if r['kept'])} kept candidates to fetch")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `& $PY -m unittest tests.test_narrow -v`
Expected: 7 tests OK

- [ ] **Step 5: Smoke on 20 rows (live Jev)**

Run: `& $PY scripts\narrow.py --limit 20`
Expected: prints rows needing Jev; `cand_narrowed.csv` shows `link1` values between 0 and 2, `kept` True for the obvious ones, Dakota's three lookalikes with low scores.

- [ ] **Step 6: Commit**

```bash
git add scripts/narrow.py tests/test_narrow.py
git commit -m "Hubspot CRD match: Jev pass 1 candidate narrowing" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Fetch firm details

**Files:**
- Create: `scripts/fetch_details.py`

**Interfaces:**
- Consumes: `read_csv(CAND_NARROWED)` rows with `kept == "True"`, `FintrxClient.ria_firm(id)`
- Produces: `data/fintrx/details/<item_id>.json` raw; `data/fintrx/details.csv` columns `item_id, crd_id, primary_business_name, legal_name, former_names, website_address, street1, street2, city, state, zip, phone, hubspot_id`; `flatten_detail(rec: dict) -> dict`.

- [ ] **Step 1: Write fetch_details.py**

```python
"""Step 5: fetch the FINTRX detail record for every kept candidate. Resumable by file existence.

Run:  op run --env-file <RAM_Brain>/references/fintrx/op.env -- python scripts/fetch_details.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NARROWED, DETAILS_CSV, DETAILS_DIR, Eta, load_source, log_error, paced,  # noqa: E402
                    read_csv, write_csv)
from fintrx_sdk import FintrxClient, FintrxAuthError  # noqa: E402

FIELDS = ["item_id", "crd_id", "primary_business_name", "legal_name", "former_names", "website_address",
          "street1", "street2", "city", "state", "zip", "phone", "hubspot_id"]
ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")


def flatten_detail(rec: dict) -> dict:
    loc = rec.get("location_address") or ""
    z = ZIP_RE.search(loc)
    fn = rec.get("former_names")
    if isinstance(fn, list):
        fn = "; ".join(str(x) for x in fn)
    return dict(
        item_id=rec.get("id"), crd_id=rec.get("crd_id"),
        primary_business_name=rec.get("primary_business_name"), legal_name=rec.get("legal_name"),
        former_names=fn, website_address=rec.get("website_address"),
        street1=rec.get("main_office_address_1"), street2=rec.get("main_office_address_2"),
        city=rec.get("office_city_name") or rec.get("ria_investor_data_main_office_city_name"),
        state=rec.get("main_office_state"), zip=z.group(1) if z else "",
        phone=rec.get("main_office_phone_number") or rec.get("main_office_fintrx_phone_number"),
        hubspot_id=rec.get("hubspot_id"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="only candidates for the first N source rows")
    args = ap.parse_args()
    rows = read_csv(CAND_NARROWED)
    if args.limit:
        keep_rows = set(str(x) for x in load_source(args.limit)["source_row"])
        rows = [r for r in rows if r["source_row"] in keep_rows]
    ids = sorted({int(float(r["fintrx_item_id"])) for r in rows if r["kept"] == "True" and r["fintrx_item_id"]})
    DETAILS_DIR.mkdir(parents=True, exist_ok=True)
    todo = [i for i in ids if not (DETAILS_DIR / f"{i}.json").exists()]
    print(f"{len(ids)} kept firms, {len(todo)} to fetch (~{len(todo) * 0.5 / 60:.0f} min)")
    if todo:
        c = FintrxClient()
        eta = Eta(len(todo), "details")
        try:
            for i in todo:
                try:
                    rec = c.ria_firm(i)
                    (DETAILS_DIR / f"{i}.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
                except FintrxAuthError:
                    raise
                except Exception as e:  # noqa: BLE001
                    log_error("fetch_details", i, e)
                if eta.done % 200 == 199:
                    print(eta.tick())
                else:
                    eta.tick()
                paced()
        except FintrxAuthError as e:
            print(f"AUTH ERROR, refresh the token then rerun to resume: {e}", file=sys.stderr)
            sys.exit(2)
    flat = []
    for i in ids:
        p = DETAILS_DIR / f"{i}.json"
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            flat.append(flatten_detail(rec.get("ria_investor") or rec))
    write_csv(DETAILS_CSV, flat, FIELDS)
    print(f"wrote {DETAILS_CSV}: {len(flat)} firms, {sum(1 for f in flat if f['crd_id'])} with CRD")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke on 20 rows**

Run: `op run --env-file $OPENV -- & $PY scripts\fetch_details.py --limit 20`
Expected: ~20 files under `data/fintrx/details/`, `details.csv` shows CRD 281554 with website `https://www.intrua.com/` for Intrua.

- [ ] **Step 3: Commit**

```bash
git add scripts/fetch_details.py
git commit -m "Hubspot CRD match: resumable detail fetch" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Decide with Jev pass 2 plus code rules

**Files:**
- Create: `scripts/decide.py`
- Create: `tests/test_decide.py`

**Interfaces:**
- Consumes: `read_csv(CAND_NARROWED)` kept rows, `read_csv(DETAILS_CSV)`, `load_source`, `jev`
- Produces: `compute_flags(src, det) -> dict(domain_equal, phone_equal, state_equal, zip_equal)`; `decide_candidate(link: float | None, flags) -> str`; `decide_row(cands) -> (outcome, chosen_index | None, reason)`; `data/output/matches.csv` with one line per kept candidate, columns `source_row, record_id, source_name, fintrx_item_id, matched_name, crd_id, legal_name, website_address, street1, city, state, zip, phone, methods, name_score, link1, link2, same_name2, same_street2, domain_equal, phone_equal, state_equal, zip_equal, decision, row_outcome, row_reason, chosen`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_decide.py
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import decide


class FlagTests(unittest.TestCase):
    def test_domain_phone_state_zip(self):
        src = {"Company Domain Name": "intrua.com", "Phone Number": "12814912800",
               "State/Region (Global)": "TX", "_zip": ""}
        det = {"website_address": "https://www.intrua.com/", "phone": "(281) 491-2800", "state": "TX", "zip": "77098"}
        f = decide.compute_flags(src, det)
        self.assertTrue(f["domain_equal"]); self.assertTrue(f["phone_equal"]); self.assertTrue(f["state_equal"])
        self.assertIsNone(f["zip_equal"])

    def test_missing_state_is_none(self):
        f = decide.compute_flags({"Company Domain Name": "", "Phone Number": "", "State/Region (Global)": None},
                                 {"website_address": "", "phone": "", "state": "TX", "zip": ""})
        self.assertIsNone(f["state_equal"]); self.assertFalse(f["domain_equal"])


class RuleTests(unittest.TestCase):
    F = dict(domain_equal=False, phone_equal=False, state_equal=True, zip_equal=None)

    def test_domain_with_moderate_link_accepts(self):
        self.assertEqual(decide.decide_candidate(1.1, dict(self.F, domain_equal=True)), "accept")

    def test_domain_with_low_link_reviews(self):
        self.assertEqual(decide.decide_candidate(0.6, dict(self.F, domain_equal=True)), "review")

    def test_strong_link_same_state_accepts(self):
        self.assertEqual(decide.decide_candidate(1.7, self.F), "accept")

    def test_strong_link_other_state_reviews(self):
        self.assertEqual(decide.decide_candidate(1.7, dict(self.F, state_equal=False)), "review")

    def test_low_link_rejects(self):
        self.assertEqual(decide.decide_candidate(0.3, self.F), "reject")

    def test_missing_link_reviews(self):
        self.assertEqual(decide.decide_candidate(None, self.F), "review")


class RowTests(unittest.TestCase):
    def test_single_accept_wins(self):
        self.assertEqual(decide.decide_row([{"decision": "accept"}, {"decision": "reject"}]), ("accept", 0, "single_accept"))

    def test_two_accepts_demote(self):
        self.assertEqual(decide.decide_row([{"decision": "accept"}, {"decision": "accept"}])[0], "review")

    def test_only_reviews(self):
        self.assertEqual(decide.decide_row([{"decision": "review"}])[0], "review")

    def test_all_rejects(self):
        self.assertEqual(decide.decide_row([{"decision": "reject"}]), ("no_match", None, "all_rejected"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `& $PY -m unittest tests.test_decide -v`
Expected: FAIL, `No module named 'decide'`

- [ ] **Step 3: Write decide.py**

```python
"""Step 6: Jev pass 2 on detail records plus code rules. One line per kept candidate.

Run:  python scripts/decide.py [--limit N] [--force]
Reads cand_narrowed.csv + details.csv. Writes data/output/matches.csv. Raw answers: jev_pass2.jsonl.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NARROWED, COL_DOMAIN, COL_NAME, COL_PHONE, COL_RECORD_ID, COL_STATE,  # noqa: E402
                    COL_STREET1, COL_STREET2, DETAILS_CSV, JEV2, JEV_WORKERS, Eta, append_jsonl,
                    extract_domain, is_blank, load_source, log_error, norm_state, phone_digits,
                    read_csv, read_jsonl, write_csv)
from narrow import LEVELS  # noqa: E402
import jev  # noqa: E402

# ---- thresholds (logged in notes/decisions.md) ----
REVIEW_MIN = 0.5        # link_state below this -> reject
ACCEPT_STRONG = 1.5     # link_state at or above, with state agreeing or unknown -> accept
ACCEPT_WITH_KEY = 1.0   # link_state at or above, with domain or phone equal -> accept

FIELDS = ["source_row", "record_id", "source_name", "fintrx_item_id", "matched_name", "crd_id", "legal_name",
          "website_address", "street1", "city", "state", "zip", "phone", "methods", "name_score", "link1",
          "link2", "same_name2", "same_street2", "domain_equal", "phone_equal", "state_equal", "zip_equal",
          "decision", "row_outcome", "row_reason", "chosen"]


def compute_flags(src: dict, det: dict) -> dict:
    sd, dd = extract_domain(src.get(COL_DOMAIN)), extract_domain(det.get("website_address"))
    sp, dp = phone_digits(src.get(COL_PHONE)), phone_digits(det.get("phone"))
    ss, ds = norm_state(src.get(COL_STATE)), norm_state(det.get("state"))
    sz, dz = str(src.get("_zip") or "").strip()[:5], str(det.get("zip") or "").strip()[:5]
    return dict(domain_equal=bool(sd) and sd == dd,
                phone_equal=bool(sp) and sp == dp,
                state_equal=(ss == ds) if ss and ds else None,
                zip_equal=(sz == dz) if sz and dz else None)


def decide_candidate(link: float | None, flags: dict) -> str:
    if link is None:
        return "review"
    if (flags["domain_equal"] or flags["phone_equal"]) and link >= ACCEPT_WITH_KEY:
        return "accept"
    if link >= ACCEPT_STRONG and flags["state_equal"] in (True, None):
        return "accept"
    if link >= REVIEW_MIN:
        return "review"
    return "reject"


def decide_row(cands: list[dict]):
    acc = [i for i, c in enumerate(cands) if c["decision"] == "accept"]
    if len(acc) == 1:
        return "accept", acc[0], "single_accept"
    if len(acc) > 1:
        return "review", None, "multiple_accepts"
    if any(c["decision"] == "review" for c in cands):
        return "review", None, "review_band"
    return "no_match", None, "all_rejected"


def build_state(src: dict, cands: list[dict]) -> dict:
    street = " ".join(str(src.get(k)) for k in (COL_STREET1, COL_STREET2) if not is_blank(src.get(k)))
    return {"hubspot": {"name": src.get(COL_NAME), "street": street, "state": norm_state(src.get(COL_STATE)),
                        "domain": extract_domain(src.get(COL_DOMAIN))},
            "candidates": [{"idx": i, "name": c["matched_name"], "legal_name": c.get("legal_name") or "",
                            "former_names": c.get("former_names") or "", "website": c.get("website_address") or "",
                            "street": " ".join(x for x in (c.get("street1") or "", c.get("street2") or "") if x),
                            "city": c.get("city") or "", "state": c.get("state") or ""}
                           for i, c in enumerate(cands)]}


def build_questions(cands: list[dict]) -> dict:
    q = {}
    for i, _ in enumerate(cands):
        q[f"link_{i}"] = jev.score(
            {"question": f"Is `candidates[{i}]` the same firm as the one described in `hubspot`?",
             "compare": [f"`candidates[{i}].name`, `.legal_name`, `.former_names`", "`hubspot.name`"],
             "supporting": [f"`candidates[{i}].street` and `.state` versus `hubspot.street` and `hubspot.state`",
                            f"`candidates[{i}].website` versus `hubspot.domain`"],
             "note": "Legal suffixes and generic words are noise. A custodian, broker-dealer or platform that "
                     "merely shares a website with many advisors is not the same firm."},
            LEVELS)
        q[f"name_{i}"] = jev.noul(f"Does `candidates[{i}].name` or `.legal_name` or `.former_names` name the "
                                  f"same business as `hubspot.name`, ignoring suffixes and generic words?")
        q[f"street_{i}"] = jev.noul(f"Do `candidates[{i}].street` and `hubspot.street` describe the same street "
                                    f"address, allowing for abbreviations and suite numbers? Answer no if either is blank.")
    return q


def ask_row(sr: int, src: dict, cands: list[dict]) -> dict:
    try:
        r = jev.ask(build_state(src, cands), build_questions(cands))
        return {"source_row": sr, "model": r.get("model"), "answers": r["answers"], "usage": r.get("usage"),
                "items": [c["fintrx_item_id"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        log_error("decide_jev", sr, e)
        return {"source_row": sr, "error": str(e)[:300], "items": [c["fintrx_item_id"] for c in cands]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    df = load_source(args.limit)
    srcs = {int(s["source_row"]): s for s in df.to_dict("records")}
    details = {str(d["item_id"]): d for d in read_csv(DETAILS_CSV)}
    narrowed = read_csv(CAND_NARROWED)
    by_row: dict[int, list[dict]] = {}
    for r in narrowed:
        sr = int(r["source_row"])
        if sr not in srcs:
            continue
        if r["kept"] == "True" and r["fintrx_item_id"]:
            det = details.get(str(int(float(r["fintrx_item_id"]))))
            if det:
                by_row.setdefault(sr, []).append(dict(r, **{k: v for k, v in det.items() if k != "item_id"}))
    cache = {} if args.force else {r["source_row"]: r for r in read_jsonl(JEV2)}
    need = [sr for sr in by_row if sr not in cache]
    print(f"{len(srcs)} rows, {len(by_row)} with kept candidates, {len(need)} need Jev pass 2")
    eta = Eta(len(need), "jev2")
    with ThreadPoolExecutor(max_workers=JEV_WORKERS) as ex:
        for res in ex.map(lambda sr: ask_row(sr, srcs[sr], by_row[sr]), need):
            cache[res["source_row"]] = res
            append_jsonl(JEV2, [res])
            if eta.done % 200 == 0:
                print(eta.tick())
            else:
                eta.tick()

    out = []
    for sr, src in srcs.items():
        cands = by_row.get(sr, [])
        base = dict(source_row=sr, record_id=src[COL_RECORD_ID], source_name=src[COL_NAME])
        if not cands:
            out.append(dict(base, row_outcome="no_match", row_reason="no_kept_candidate", decision="", chosen=False))
            continue
        ans = (cache.get(sr) or {}).get("answers") or {}
        for i, c in enumerate(cands):
            a, n, s = ans.get(f"link_{i}"), ans.get(f"name_{i}"), ans.get(f"street_{i}")
            c["link2"] = round(a["score"], 3) if a else None
            c["same_name2"] = round(n["noul"], 3) if n else ""
            c["same_street2"] = round(s["noul"], 3) if s else ""
            c.update(compute_flags(src, c))
            c["decision"] = decide_candidate(c["link2"], c)
        outcome, chosen, reason = decide_row(cands)
        if not ans:
            outcome, chosen, reason = "review", None, "jev_error"
        for i, c in enumerate(cands):
            out.append(dict(base, **c, row_outcome=outcome, row_reason=reason, chosen=(i == chosen)))
    write_csv(MATCHES, out, FIELDS)
    rows = {r["source_row"]: r["row_outcome"] for r in out}
    from collections import Counter
    print(f"wrote {MATCHES}: {len(out)} lines; row outcomes {dict(Counter(rows.values()))}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `& $PY -m unittest tests.test_decide -v`
Expected: 12 tests OK

- [ ] **Step 5: Smoke on 20 rows (live Jev)**

Run: `& $PY scripts\decide.py --limit 20`
Expected: Intrua, Newfound, Insight Wealth accept with `domain_equal=True`; Mount Yale candidate (Princeton Fund Advisors) rejects or reviews; Dakota lookalikes review or reject.

- [ ] **Step 6: Commit**

```bash
git add scripts/decide.py tests/test_decide.py
git commit -m "Hubspot CRD match: Jev pass 2 and decision rules" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Write the enriched Excel and review file

**Files:**
- Create: `scripts/write_output.py`
- Create: `tests/test_write_output.py`

**Interfaces:**
- Consumes: `read_csv(MATCHES)`, `SOURCE_XLSX`, `read_csv(CAND_NARROWED)` for context on no-match rows
- Produces: `fill_workbook(src_path, out_path, accepted: dict[int, dict]) -> int` (rows filled); `data/output/Hubspot-company-list-2026-09-18-enriched.xlsx`; `data/output/review.csv`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_write_output.py
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import openpyxl
import write_output


class FillTests(unittest.TestCase):
    def test_fills_column_c_and_leaves_rest(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "s.xlsx"; out = Path(d) / "o.xlsx"
            wb = openpyxl.Workbook(); ws = wb.active
            ws.append(["Record ID", "Company name", "Fintrx Firm CRD ID", "Phone Number"])
            ws.append([1, "Intrua", None, "555"]); ws.append([2, "Nobody", None, "666"])
            wb.save(src)
            n = write_output.fill_workbook(src, out, {0: dict(crd_id="281554", matched_name="Intrua Financial",
                                                              methods="exact_normalized", link2="1.9")})
            self.assertEqual(n, 1)
            ws2 = openpyxl.load_workbook(out).active
            self.assertEqual(ws2["C2"].value, 281554)
            self.assertIsNone(ws2["C3"].value)
            self.assertEqual(ws2["D3"].value, "666")
            self.assertEqual(ws2["E1"].value, "fintrx_match_name")
            self.assertEqual(ws2["E2"].value, "Intrua Financial")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `& $PY -m unittest tests.test_write_output -v`
Expected: FAIL, `No module named 'write_output'`

- [ ] **Step 3: Write write_output.py**

```python
"""Step 7: enriched Excel (column C filled for accepted rows) plus review.csv for everything else.

Run:  python scripts/write_output.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NARROWED, COL_CRD, DATA_OUT, FINTRX_FIRM_URL, MATCHES, REVIEW,  # noqa: E402
                    SOURCE_XLSX, read_csv, write_csv)

EXTRA_HEADERS = ["fintrx_match_name", "fintrx_match_method", "fintrx_match_confidence"]
REVIEW_FIELDS = ["source_row", "record_id", "source_name", "row_outcome", "row_reason", "fintrx_item_id",
                 "matched_name", "crd_id", "legal_name", "website_address", "street1", "city", "state", "methods",
                 "name_score", "link1", "link2", "same_name2", "same_street2", "domain_equal", "phone_equal",
                 "state_equal", "decision", "fintrx_url"]


def fill_workbook(src_path: Path, out_path: Path, accepted: dict[int, dict]) -> int:
    wb = openpyxl.load_workbook(src_path)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    col_c = headers.index(COL_CRD) + 1
    first_extra = len(headers) + 1
    for j, h in enumerate(EXTRA_HEADERS):
        ws.cell(row=1, column=first_extra + j, value=h)
    n = 0
    for sr, m in accepted.items():
        r = sr + 2
        crd = m.get("crd_id")
        if not crd:
            continue
        ws.cell(row=r, column=col_c, value=int(float(crd)))
        ws.cell(row=r, column=first_extra, value=m.get("matched_name"))
        ws.cell(row=r, column=first_extra + 1, value=m.get("methods"))
        ws.cell(row=r, column=first_extra + 2, value=m.get("link2"))
        n += 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return n


def main() -> None:
    matches = read_csv(MATCHES)
    accepted = {int(r["source_row"]): r for r in matches if r["row_outcome"] == "accept" and r["chosen"] == "True"}
    out_xlsx = DATA_OUT / f"{SOURCE_XLSX.stem}-enriched.xlsx"
    n = fill_workbook(SOURCE_XLSX, out_xlsx, accepted)
    outcomes = {}
    for r in matches:
        outcomes[int(r["source_row"])] = r["row_outcome"]
    review = []
    for r in matches:
        if r["row_outcome"] == "accept":
            continue
        row = dict(r)
        row["fintrx_url"] = FINTRX_FIRM_URL.format(item_id=int(float(r["fintrx_item_id"]))) if r.get("fintrx_item_id") else ""
        review.append(row)
    review_rows = {int(r["source_row"]) for r in review}
    for r in read_csv(CAND_NARROWED):
        sr = int(r["source_row"])
        if outcomes.get(sr) == "accept" or sr in review_rows or r["kept"] == "True":
            continue
        row = dict(r, row_outcome=outcomes.get(sr, "no_match"), row_reason=r["keep_reason"], decision="",
                   fintrx_url=FINTRX_FIRM_URL.format(item_id=int(float(r["fintrx_item_id"]))) if r.get("fintrx_item_id") else "")
        review.append(row)
    review.sort(key=lambda r: (int(r["source_row"]), r.get("matched_name") or ""))
    write_csv(REVIEW, review, REVIEW_FIELDS)
    print(f"wrote {out_xlsx}: {n} rows filled")
    print(f"wrote {REVIEW}: {len(review)} lines for {len({r['source_row'] for r in review})} rows")
    print("row outcomes:", dict(Counter(outcomes.values())))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `& $PY -m unittest tests.test_write_output -v`
Expected: 1 test OK

- [ ] **Step 5: Smoke end to end on the 20-row outputs**

Run: `& $PY scripts\write_output.py`
Expected: an enriched xlsx in `data/output/` with column C filled for the accepted rows among the first 20, and `review.csv` listing the rest with FINTRX links.

- [ ] **Step 6: Commit**

```bash
git add scripts/write_output.py tests/test_write_output.py
git commit -m "Hubspot CRD match: enriched Excel and review output" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Full run, README, and decisions

**Files:**
- Modify: `README.md` (replace "Workflow (planned)" and "Status")
- Modify: `notes/decisions.md` (append thresholds and run counts)

- [ ] **Step 1: Run the full pipeline in order**

```powershell
# FINTRX (under op run), each resumable:
op run --env-file $OPENV -- & $PY scripts\pull_universe.py      # done in Task 2 if it completed
op run --env-file $OPENV -- & $PY scripts\lookup_domain.py      # ~1.5-2 h
# local:
& $PY scripts\match.py                                          # ~10-15 min
& $PY scripts\narrow.py                                         # Jev, ~10-20 min
op run --env-file $OPENV -- & $PY scripts\fetch_details.py      # ~2-2.5 h
& $PY scripts\decide.py                                         # Jev, ~10-20 min
& $PY scripts\write_output.py
```
Expected: each prints its counts. Record accept / review / no_match totals.

- [ ] **Step 2: Spot-check 15 accepted and 15 review rows by eye** in `matches.csv` and `review.csv`. If a pattern of wrong accepts appears, raise `ACCEPT_STRONG` or require `state_equal is True`, rerun `decide.py` (cached Jev answers make this free), and note the change.

- [ ] **Step 3: Update README.md workflow and status**

Replace the "Workflow (planned)" section with the seven commands above and the "Status" line with the run date and counts.

- [ ] **Step 4: Append to notes/decisions.md**

```
[YYYY-MM-DD] DECISION: Thresholds: rapidfuzz cutoff 75 top 3; Jev pass 1 keep >= 0.5 max 3; pass 2 accept >= 1.5 with state agreeing or unknown, accept >= 1.0 with domain or phone equal, review >= 0.5 | REASONING: cut points from the TypeSafe entity-alignment cookbook, key equality computed in code | CONTEXT: full run on <date>: <accept> accepted, <review> review, <no_match> no match
```

- [ ] **Step 5: Commit**

```bash
git add README.md notes/decisions.md
git commit -m "Hubspot CRD match: full run results and README" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
