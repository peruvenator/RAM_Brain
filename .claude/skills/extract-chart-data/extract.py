"""
Extract embedded chart/visualization data from web pages.

Usage:
    python extract.py <URL> [--output path/to/output.json]

Handles: Google Charts, Chart.js, Highcharts, wpDataCharts (WordPress),
         generic JS data arrays.

Also extracts figure titles ("Figure N: ...") and disclaimers
("Source: ...") from surrounding HTML and maps them to each chart.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)


# ── Pattern definitions ──────────────────────────────────────────────────

CHART_PATTERNS = {
    "wpDataCharts_render_data": {
        "description": "wpDataCharts render_data (WordPress DataTables plugin)",
        "pattern": r"wpDataCharts\[(\d+)\]\s*=\s*\{[^}]*render_data:\s*(\{\"columns\"[\s\S]*?\})\s*,\s*\n",
    },
    "google_charts_arrayToDataTable": {
        "description": "Google Charts arrayToDataTable",
        "pattern": r"arrayToDataTable\s*\(\s*(\[[\s\S]*?\])\s*\)",
    },
    "google_charts_addRows": {
        "description": "Google Charts addRows",
        "pattern": r"\.addRows\s*\(\s*(\[[\s\S]*?\])\s*\)",
    },
    "google_charts_DataTable_constructor": {
        "description": "Google Charts DataTable with data object",
        "pattern": r"new\s+google\.visualization\.DataTable\s*\(\s*(\{[\s\S]*?\})\s*\)",
    },
    "chartjs_datasets": {
        "description": "Chart.js datasets",
        "pattern": r"datasets\s*:\s*(\[[\s\S]*?\])\s*[,}]",
    },
    "chartjs_data_labels": {
        "description": "Chart.js labels array",
        "pattern": r"labels\s*:\s*(\[[\s\S]*?\])\s*,",
    },
    "highcharts_series": {
        "description": "Highcharts series data",
        "pattern": r"series\s*:\s*(\[[\s\S]*?\])\s*[,}]",
    },
    "generic_date_value_array": {
        "description": "Date-value pairs in JS array",
        "pattern": r"\[\s*(\[\s*(?:new Date|Date\.parse|['\"](?:19|20)\d{2})[\s\S]*?\])\s*\]",
    },
}

FALLBACK_PATTERNS = {
    "large_numeric_array": {
        "description": "Large numeric array (50+ elements)",
        "pattern": r"(?:data|values|series|points|rows)\s*[:=]\s*(\[(?:\s*[\[\{][\s\S]*?){50,}\])",
    },
    "json_script_block": {
        "description": "JSON data in script type=application/json",
        "tag_type": "application/json",
    },
    "json_ld_data": {
        "description": "JSON-LD structured data",
        "tag_type": "application/ld+json",
    },
}


def fetch_page(url):
    """Fetch full HTML via requests (no truncation unlike WebFetch)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_scripts(html):
    """Extract all inline script contents from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    scripts = []

    for tag in soup.find_all("script"):
        script_type = tag.get("type", "").lower()
        content = tag.string or ""

        if not content.strip():
            src = tag.get("src", "")
            if src:
                scripts.append({"type": "external", "src": src, "content": ""})
            continue

        scripts.append({
            "type": script_type or "text/javascript",
            "src": None,
            "content": content,
        })

    return scripts, soup


def extract_figure_metadata(soup):
    """Extract figure titles and disclaimers from HTML.

    Scans the page for:
    - Figure titles: "Figure N: ..." in <strong>, <b>, <h2>-<h4>, or <p> tags
    - Disclaimers: "Source: ..." text in <em>, <i>, <p>, or <span> tags
      that appear after each figure title

    Returns a list of dicts ordered by page position:
        [{"figure_num": 1, "title": "Figure 1: ...", "disclaimer": "Source: ..."}, ...]
    """
    figures = []

    # Find all figure title elements
    title_elements = []
    for el in soup.find_all(string=re.compile(r"Figure\s+\d+\s*:", re.IGNORECASE)):
        parent = el.parent if isinstance(el, NavigableString) else el
        full_text = parent.get_text(strip=True)
        num_match = re.search(r"Figure\s+(\d+)\s*:\s*(.*)", full_text, re.IGNORECASE)
        if num_match:
            fig_num = int(num_match.group(1))
            # Avoid duplicate entries from nested tags
            if title_elements and title_elements[-1]["figure_num"] == fig_num:
                # Keep the longer/more complete version
                if len(full_text) > len(title_elements[-1]["full_text"]):
                    title_elements[-1] = {
                        "figure_num": fig_num,
                        "title": num_match.group(0).strip(),
                        "full_text": full_text,
                        "element": parent,
                    }
            else:
                title_elements.append({
                    "figure_num": fig_num,
                    "title": num_match.group(0).strip(),
                    "full_text": full_text,
                    "element": parent,
                })

    # Deduplicate by figure number
    seen_nums = set()
    unique_titles = []
    for t in title_elements:
        if t["figure_num"] not in seen_nums:
            seen_nums.add(t["figure_num"])
            unique_titles.append(t)

    # For each figure title, find the nearest disclaimer that follows it
    # Disclaimers typically start with "Source:" and are in <em> or <p> tags
    # Walk up to <p> level to capture the full disclaimer text (often split
    # across multiple <em>/<span> children within a single <p>)
    disclaimer_elements = []
    seen_p_ids = set()
    for el in soup.find_all(string=re.compile(r"Source\s*:", re.IGNORECASE)):
        parent = el.parent if isinstance(el, NavigableString) else el
        # Walk up to <p> to get the full disclaimer paragraph
        p = parent
        while p and p.name not in ("p", "div", "body", None):
            p = p.parent
        if p and p.name == "p":
            p_id = id(p)
            if p_id in seen_p_ids:
                continue  # Already captured this paragraph
            seen_p_ids.add(p_id)
            text = p.get_text(strip=True)
        else:
            text = parent.get_text(strip=True)
        if len(text) > 20:  # Filter out trivial matches
            disclaimer_elements.append({"text": text, "element": p or parent})

    # Map disclaimers to figures by page order
    # Strategy: for each figure, find the next disclaimer that comes after it
    # in document order
    def element_position(el):
        """Get approximate position of element in document."""
        pos = 0
        for i, tag in enumerate(soup.descendants):
            if tag is el:
                return i
            pos = i
        return pos

    title_positions = [
        (element_position(t["element"]), t) for t in unique_titles
    ]
    disclaimer_positions = [
        (element_position(d["element"]), d) for d in disclaimer_elements
    ]

    for title_pos, title_info in sorted(title_positions):
        # Find the next disclaimer after this title
        disclaimer_text = ""
        for disc_pos, disc_info in sorted(disclaimer_positions):
            if disc_pos > title_pos:
                disclaimer_text = disc_info["text"]
                break

        figures.append({
            "figure_num": title_info["figure_num"],
            "title": title_info["title"],
            "disclaimer": disclaimer_text,
        })

    return figures


def search_patterns(scripts, patterns):
    """Search scripts for chart data patterns. Returns list of matches."""
    matches = []

    for script in scripts:
        content = script["content"]
        if not content:
            continue

        for name, spec in patterns.items():
            if "tag_type" in spec:
                if script["type"] == spec["tag_type"]:
                    matches.append({
                        "pattern_name": name,
                        "description": spec["description"],
                        "raw_match": content.strip(),
                        "script_type": script["type"],
                    })
                continue

            for m in re.finditer(spec["pattern"], content):
                if name == "wpDataCharts_render_data" and m.lastindex >= 2:
                    chart_id = m.group(1)
                    raw = m.group(2)
                    matches.append({
                        "pattern_name": name,
                        "description": f"{spec['description']} (chart #{chart_id})",
                        "raw_match": raw,
                        "chart_id": chart_id,
                        "script_type": script["type"],
                    })
                else:
                    raw = m.group(1) if m.lastindex else m.group(0)
                    matches.append({
                        "pattern_name": name,
                        "description": spec["description"],
                        "raw_match": raw,
                        "script_type": script["type"],
                        "context": content[max(0, m.start() - 100):m.end() + 100],
                    })

    return matches


def try_parse_js_array(raw):
    """Try to parse a JavaScript array/object literal as JSON."""
    cleaned = raw
    cleaned = re.sub(r"new\s+Date\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", r'"\1"', cleaned)

    def date_constructor_to_str(m):
        parts = [int(x.strip()) for x in m.group(1).split(",")]
        if len(parts) >= 3:
            y, mo, d = parts[0], parts[1] + 1, parts[2]
            return f'"{y:04d}-{mo:02d}-{d:02d}"'
        return m.group(0)

    cleaned = re.sub(r"new\s+Date\s*\(([^)]+)\)", date_constructor_to_str, cleaned)
    cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    cleaned = re.sub(r"(?<=[{,\n])\s*(\w+)\s*:", r' "\1":', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def summarize_data(parsed):
    """Generate a human-readable summary of parsed data."""
    if isinstance(parsed, list):
        if len(parsed) == 0:
            return "Empty array"
        first = parsed[0]
        if isinstance(first, list):
            ncols = len(first)
            return f"Table: {len(parsed)} rows x {ncols} columns. Header: {first}"
        elif isinstance(first, dict):
            keys = list(first.keys())
            return f"Array of {len(parsed)} objects. Keys: {keys[:5]}"
        else:
            return f"Array of {len(parsed)} values. First: {first}, Last: {parsed[-1]}"
    elif isinstance(parsed, dict):
        keys = list(parsed.keys())
        return f"Object with keys: {keys[:10]}"
    return f"Type: {type(parsed).__name__}"


def main():
    parser = argparse.ArgumentParser(
        description="Extract chart data from web pages"
    )
    parser.add_argument("url", help="URL to fetch and extract data from")
    parser.add_argument("--output", "-o", help="Save extracted data to JSON file")
    parser.add_argument(
        "--raw-scripts", action="store_true",
        help="Also dump all inline scripts to stdout (for debugging)",
    )
    args = parser.parse_args()

    # Fetch
    print(f"Fetching: {args.url}")
    html = fetch_page(args.url)
    print(f"HTML size: {len(html):,} bytes")

    # Extract scripts and parse HTML
    scripts, soup = extract_scripts(html)
    inline_scripts = [s for s in scripts if s["content"]]
    external_scripts = [s for s in scripts if s["type"] == "external"]
    print(f"Found {len(inline_scripts)} inline scripts, {len(external_scripts)} external scripts")

    # Extract figure titles and disclaimers
    figures = extract_figure_metadata(soup)
    if figures:
        print(f"\nFound {len(figures)} figure(s) with metadata:")
        for fig in figures:
            print(f"  Figure {fig['figure_num']}: {fig['title'][:80]}")
            if fig["disclaimer"]:
                print(f"    Disclaimer: {fig['disclaimer'][:100]}...")

    if args.raw_scripts:
        print("\n" + "=" * 80)
        print("RAW INLINE SCRIPTS")
        print("=" * 80)
        for i, s in enumerate(inline_scripts):
            print(f"\n--- Script {i+1} (type={s['type']}, {len(s['content']):,} chars) ---")
            print(s["content"][:2000])
            if len(s["content"]) > 2000:
                print(f"... [{len(s['content']) - 2000:,} more chars]")

    # Search for chart patterns
    print("\nSearching for chart data patterns...")
    matches = search_patterns(scripts, CHART_PATTERNS)

    if not matches:
        print("No specific chart patterns found. Trying fallback patterns...")
        matches = search_patterns(scripts, FALLBACK_PATTERNS)

    if not matches:
        print("\nNo chart data patterns found in inline scripts.")
        print("\nPossible reasons:")
        print("  - Data is loaded via external .js file (check external scripts below)")
        print("  - Data is fetched via AJAX/API call (use chrome-cdp network inspection)")
        print("  - Data is server-rendered into SVG/canvas (no extractable data)")
        if external_scripts:
            print(f"\nExternal scripts that might contain data:")
            for s in external_scripts:
                print(f"  {s['src']}")
        sys.exit(0)

    # Process matches and map to figure metadata
    results = []
    print(f"\nFound {len(matches)} chart data match(es):")
    for i, match in enumerate(matches):
        print(f"\n--- Match {i+1}: {match['description']} ---")

        parsed = try_parse_js_array(match["raw_match"])
        if parsed is not None:
            summary = summarize_data(parsed)
            print(f"  Parsed successfully: {summary}")

            result = {
                "pattern": match["pattern_name"],
                "description": match["description"],
                "data": parsed,
                "summary": summary,
            }

            # Map figure metadata: match chart index to figure index
            if i < len(figures):
                fig = figures[i]
                result["title"] = fig["title"]
                result["disclaimer"] = fig["disclaimer"]
                print(f"  Title: {fig['title']}")
                if fig["disclaimer"]:
                    print(f"  Disclaimer: {fig['disclaimer'][:100]}...")
            elif match.get("chart_id"):
                # Try to extract y-axis title from chart options as fallback
                vaxis_title = (
                    parsed.get("options", {}).get("vAxis", {}).get("title", "")
                    if isinstance(parsed, dict) else ""
                )
                if vaxis_title:
                    result["title"] = vaxis_title
                    print(f"  Title (from vAxis): {vaxis_title}")

            results.append(result)
        else:
            excerpt = match["raw_match"][:500]
            print(f"  Could not auto-parse. Raw excerpt:")
            print(f"  {excerpt}")
            if len(match["raw_match"]) > 500:
                print(f"  ... [{len(match['raw_match']) - 500} more chars]")
            result = {
                "pattern": match["pattern_name"],
                "description": match["description"],
                "raw": match["raw_match"],
            }
            if i < len(figures):
                result["title"] = figures[i]["title"]
                result["disclaimer"] = figures[i]["disclaimer"]
            results.append(result)

    # Save output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nSaved to {output_path}")

    return results


if __name__ == "__main__":
    main()
