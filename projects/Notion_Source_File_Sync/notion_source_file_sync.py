"""
Notion Source File Sync
=======================
Queries the Runs database for entries where "Ready For Approval" = "Approved".
Downloads the Sources file(s) and re-uploads them to the linked Publications
page's "Source files" field via the Notion File Upload API.

Designed to run once per execution (called by Task Scheduler via wrapper).
Exit codes: 0 = success, 1 = failure
"""

import os
import sys
import json
import math
import time
import requests
from pathlib import Path
from datetime import datetime

# ─── CONFIGURATION ───────────────────────────────────────────────────────────

# .env lives at RAM_Brain root (two levels up from projects/Notion_Source_File_Sync)
ENV_PATH = Path(__file__).parent.parent.parent / ".env"

# Database IDs
RUNS_DATABASE_ID = "2f63037cb38a8060908ce6e1ae5aeeeb"

# Property names
RUNS_APPROVAL_PROP = "Ready For Approval"
RUNS_SOURCES_PROP = "Sources"
RUNS_PAGE_RELATION_PROP = "Page"
PUBLICATIONS_SOURCE_FILES_PROP = "Source files"

# Approval value that triggers the sync
TRIGGER_VALUE = "Approved"

# Local temp directory for downloaded files
TEMP_DIR = Path(__file__).parent / "temp_downloads"

# Processed tracker file (to avoid re-processing)
PROCESSED_FILE = Path(__file__).parent / "processed_runs.json"

# ─── ENV LOADING ─────────────────────────────────────────────────────────────

def load_env(env_path: Path) -> dict:
    """Load key=value pairs from a .env file."""
    env = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip()
    return env


# Load token
env_vars = load_env(ENV_PATH)
NOTION_TOKEN = env_vars.get("NOTION_API_KEY", os.environ.get("NOTION_API_KEY", ""))
NOTION_VERSION = "2022-06-28"

# ─── NOTION API HELPERS ──────────────────────────────────────────────────────

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def log(msg: str):
    """Print timestamped log message to stdout (captured by PS wrapper)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def notion_get(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def notion_post(url: str, payload: dict) -> dict:
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def notion_patch(url: str, payload: dict) -> dict:
    resp = requests.patch(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


# ─── PROCESSED RUNS TRACKER ─────────────────────────────────────────────────

def load_processed() -> set:
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("processed", []))
    return set()


def save_processed(processed: set):
    with open(PROCESSED_FILE, "w") as f:
        json.dump({
            "processed": list(processed),
            "last_updated": datetime.now().isoformat()
        }, f, indent=2)


# ─── CORE LOGIC ──────────────────────────────────────────────────────────────

def query_approved_runs() -> list:
    """Query the Runs database for entries where Ready For Approval = Approved."""
    url = f"https://api.notion.com/v1/databases/{RUNS_DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": RUNS_APPROVAL_PROP,
            "select": {"equals": TRIGGER_VALUE},
        },
    }
    results = []
    has_more = True
    start_cursor = None

    while has_more:
        if start_cursor:
            payload["start_cursor"] = start_cursor
        data = notion_post(url, payload)
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return results


def get_sources_files(run_page: dict) -> list:
    props = run_page.get("properties", {})
    sources_prop = props.get(RUNS_SOURCES_PROP, {})
    return sources_prop.get("files", [])


def get_linked_publication_ids(run_page: dict) -> list:
    props = run_page.get("properties", {})
    page_relation = props.get(RUNS_PAGE_RELATION_PROP, {})
    relations = page_relation.get("relation", [])
    return [r["id"] for r in relations]


def get_run_title(run_page: dict) -> str:
    title_prop = run_page.get("properties", {}).get("Name", {})
    if title_prop.get("title"):
        return "".join(t.get("plain_text", "") for t in title_prop["title"])
    return run_page["id"][:8]


def download_file(file_entry: dict) -> tuple:
    """Download a file. Returns (local_path, filename, content_type) or None."""
    TEMP_DIR.mkdir(exist_ok=True)

    file_type = file_entry.get("type")
    if file_type == "file":
        url = file_entry["file"]["url"]
    elif file_type == "external":
        url = file_entry["external"]["url"]
    else:
        log(f"  Unknown file type: {file_type}")
        return None

    filename = file_entry.get("name", "unknown_file")
    log(f"  Downloading: {filename}")

    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    local_path = TEMP_DIR / filename

    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    file_size = local_path.stat().st_size
    log(f"  Downloaded: {filename} ({file_size:,} bytes)")
    return (local_path, filename, content_type)


def upload_file_to_notion(local_path: Path, filename: str, content_type: str) -> str:
    """Upload via Notion File Upload API. Returns file_upload ID.
    Uses single-part for files <= 20MB, multi-part for larger files."""
    file_size = local_path.stat().st_size
    SINGLE_PART_LIMIT = 20 * 1024 * 1024  # 20 MB
    PART_SIZE = 10 * 1024 * 1024  # 10 MB per part

    auth_headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
    }

    if file_size <= SINGLE_PART_LIMIT:
        # ── Single-part upload ──
        log(f"  Creating single-part upload for: {filename} ({file_size:,} bytes)")
        create_resp = requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers={**auth_headers, "Content-Type": "application/json"},
            json={"mode": "single_part"},
        )
        create_resp.raise_for_status()
        upload_obj = create_resp.json()
        upload_id = upload_obj["id"]
        upload_url = upload_obj["upload_url"]

        log(f"  Uploading file contents...")
        with open(local_path, "rb") as f:
            send_resp = requests.post(
                upload_url,
                headers=auth_headers,
                files={"file": (filename, f, content_type)},
            )
        send_resp.raise_for_status()
        result = send_resp.json()

        if result.get("status") == "uploaded":
            log(f"  Upload successful: {upload_id}")
            return upload_id
        else:
            raise Exception(f"Upload failed with status: {result.get('status')}")

    else:
        # ── Multi-part upload ──
        num_parts = math.ceil(file_size / PART_SIZE)
        log(f"  Creating multi-part upload for: {filename} ({file_size:,} bytes, {num_parts} parts)")

        create_resp = requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers={**auth_headers, "Content-Type": "application/json"},
            json={
                "mode": "multi_part",
                "number_of_parts": num_parts,
                "filename": filename,
                "content_type": content_type,
            },
        )
        create_resp.raise_for_status()
        upload_obj = create_resp.json()
        upload_id = upload_obj["id"]

        # Send each part with retry logic and delay
        with open(local_path, "rb") as f:
            for part_num in range(1, num_parts + 1):
                chunk = f.read(PART_SIZE)
                if not chunk:
                    break
                log(f"  Uploading part {part_num}/{num_parts} ({len(chunk):,} bytes)...")
                send_url = f"https://api.notion.com/v1/file_uploads/{upload_id}/send"

                # Retry with exponential backoff
                max_retries = 3
                for attempt in range(max_retries):
                    send_resp = requests.post(
                        send_url,
                        headers=auth_headers,
                        data={"part_number": str(part_num)},
                        files={"file": (filename, chunk, content_type)},
                    )
                    if send_resp.status_code == 503 or send_resp.status_code == 429:
                        wait = 2 ** (attempt + 1)
                        log(f"  Rate limited (HTTP {send_resp.status_code}), retrying in {wait}s...")
                        time.sleep(wait)
                        continue
                    send_resp.raise_for_status()
                    break
                else:
                    send_resp.raise_for_status()  # raise last error

                # Pause between parts to avoid rate limits
                if part_num < num_parts:
                    time.sleep(1.5)

        # Complete the multi-part upload
        log(f"  Completing multi-part upload...")
        complete_resp = requests.post(
            f"https://api.notion.com/v1/file_uploads/{upload_id}/complete",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        complete_resp.raise_for_status()
        result = complete_resp.json()

        if result.get("status") == "uploaded":
            log(f"  Multi-part upload successful: {upload_id}")
            return upload_id
        else:
            raise Exception(f"Multi-part upload failed with status: {result.get('status')}")


def attach_file_to_publication(publication_page_id: str, file_upload_id: str, filename: str):
    """Attach uploaded file to Publication's Source files property."""
    log(f"  Attaching to Publication: {publication_page_id}")

    # Get existing files
    page = notion_get(f"https://api.notion.com/v1/pages/{publication_page_id}")
    existing_files = page.get("properties", {}).get(PUBLICATIONS_SOURCE_FILES_PROP, {}).get("files", [])

    # Build file list: preserve external files, add new upload
    final_files = []
    for existing in existing_files:
        if existing.get("type") == "external":
            final_files.append({
                "type": "external",
                "external": {"url": existing["external"]["url"]},
                "name": existing.get("name", ""),
            })
        # Note: existing Notion-hosted files can't be re-referenced in a PATCH.
        # They will be replaced. This is a known Notion API limitation.

    final_files.append({
        "type": "file_upload",
        "file_upload": {"id": file_upload_id},
        "name": filename,
    })

    notion_patch(
        f"https://api.notion.com/v1/pages/{publication_page_id}",
        {"properties": {PUBLICATIONS_SOURCE_FILES_PROP: {"files": final_files}}},
    )
    log(f"  Attached successfully")


def process_run(run_page: dict) -> bool:
    """Process a single approved Run. Returns True if successful."""
    run_title = get_run_title(run_page)
    log(f"Processing Run: {run_title}")

    source_files = get_sources_files(run_page)
    if not source_files:
        log(f"  No Sources files found - skipping")
        return True

    pub_ids = get_linked_publication_ids(run_page)
    if not pub_ids:
        log(f"  No linked Publication page found - skipping")
        return True

    for file_entry in source_files:
        try:
            result = download_file(file_entry)
            if result is None:
                continue

            local_path, filename, content_type = result
            file_upload_id = upload_file_to_notion(local_path, filename, content_type)

            for pub_id in pub_ids:
                attach_file_to_publication(pub_id, file_upload_id, filename)

            # Clean up
            local_path.unlink(missing_ok=True)

        except Exception as e:
            log(f"  ERROR processing file {file_entry.get('name', '?')}: {e}")
            return False

    return True


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    if not NOTION_TOKEN:
        log(f"ERROR: NOTION_API_KEY not found. Checked .env at: {ENV_PATH}")
        sys.exit(1)

    log("=" * 50)
    log("Notion Source File Sync - starting")
    log(f"Trigger: '{RUNS_APPROVAL_PROP}' = '{TRIGGER_VALUE}'")
    log(f"Source: '{RUNS_SOURCES_PROP}' -> Target: '{PUBLICATIONS_SOURCE_FILES_PROP}'")

    processed = load_processed()
    synced_count = 0
    error_count = 0

    try:
        approved_runs = query_approved_runs()
    except Exception as e:
        log(f"ERROR querying Runs database: {e}")
        sys.exit(1)

    new_runs = [r for r in approved_runs if r["id"] not in processed]

    if not new_runs:
        log("No new approved Runs to process.")
        log("Sync complete.")
        sys.exit(0)

    log(f"Found {len(new_runs)} new approved Run(s) to process.")

    for run in new_runs:
        success = process_run(run)
        if success:
            processed.add(run["id"])
            save_processed(processed)
            synced_count += 1
            log(f"  Marked as processed: {run['id'][:8]}...")
        else:
            error_count += 1
            log(f"  FAILED: {run['id'][:8]}...")

    # Summary
    log("=" * 50)
    log(f"Sync complete. Synced: {synced_count}, Errors: {error_count}")

    if error_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
