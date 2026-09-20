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
RAM_BRAIN = PROJECT.parents[2]            # <project> -> Data managment -> projects -> RAM_Brain
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
