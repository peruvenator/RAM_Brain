"""Splice the shared search core into an index widget.

    python sync_search_core.py TARGET --ns rsArt [--check]

TARGET is the widget's design source (the template for a built widget, the
single HTML file for a hand-maintained one). The file must already contain
the two marker lines

    // RS-SEARCH-CORE-START
    // RS-SEARCH-CORE-END

inside its <script>; everything between them is replaced with the core
from ../assets/search-core.js, with __NS__ replaced by the widget's JS
namespace (rsRes, rsArt, rsLit, ...) and __SYNONYM_GROUPS__ replaced by
the groups in ../assets/search-synonyms.json. Indentation follows the
start marker line.

--check exits 1 (without writing) if the target's block differs from the
rendered core, so a build can refuse to ship a stale copy.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "assets" / "search-core.js"
SYNONYMS = HERE.parent / "assets" / "search-synonyms.json"
START = "// RS-SEARCH-CORE-START"
END = "// RS-SEARCH-CORE-END"
FORBIDDEN = re.compile(r"[&<>]")


def load_groups():
    data = json.loads(SYNONYMS.read_text(encoding="utf-8"))
    groups = []
    for group in data["groups"]:
        phrases = [p.strip().lower() for p in group if p and p.strip()]
        for p in phrases:
            if re.search(r"[&<>\"'\\]", p):
                sys.exit(f"synonym phrase {p!r} contains a forbidden character")
        if phrases:
            groups.append(phrases)
    return groups


def render(ns, indent):
    core = CORE.read_text(encoding="utf-8")
    lines = core.splitlines()
    if not lines or lines[0].strip() != START or lines[-1].strip() != END:
        sys.exit("search-core.js must start with the START marker line and end with the END marker line")
    body = lines[1:-1]
    # The asset is written with a two-space indent; re-indent to the target.
    body = [(indent + ln[2:]) if ln.startswith("  ") else (indent + ln if ln.strip() else "") for ln in body]
    groups = load_groups()
    literal = "[\n" + ",\n".join(indent + "  " + json.dumps(g, ensure_ascii=False) for g in groups) + "\n" + indent + "]"
    text = "\n".join(body)
    text = text.replace("__SYNONYM_GROUPS__", literal).replace("__NS__", ns)
    if "__" in text and re.search(r"__[A-Z_]+__", text):
        sys.exit("unfilled placeholder in the rendered core")
    bad = sorted(set(FORBIDDEN.findall(text)))
    if bad:
        sys.exit(f"rendered core contains forbidden characters {bad}")
    return text, len(groups)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--ns", required=True, help="JS namespace prefix, e.g. rsArt")
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if stale")
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", args.ns):
        sys.exit("--ns must be an identifier prefix such as rsArt")

    target = Path(args.target)
    src = target.read_text(encoding="utf-8")
    crlf = "\r\n" in src
    src = src.replace("\r\n", "\n")
    starts = [m for m in re.finditer(r"^([ \t]*)" + re.escape(START) + r"[ \t]*$", src, flags=re.M)]
    ends = [m for m in re.finditer(r"^[ \t]*" + re.escape(END) + r"[ \t]*$", src, flags=re.M)]
    if len(starts) != 1 or len(ends) != 1:
        sys.exit(f"{target}: expected exactly one START and one END marker line (found {len(starts)} / {len(ends)}). "
                 "Add both lines inside the widget script where the search functions go, then re-run.")
    s, e = starts[0], ends[0]
    if e.start() < s.end():
        sys.exit("END marker precedes START marker")
    indent = s.group(1)
    rendered, ngroups = render(args.ns, indent)
    current = src[s.end() + 1:e.start()].rstrip("\n")
    if current == rendered:
        print(f"{target.name}: search core up to date ({args.ns}, {ngroups} synonym groups)")
        return
    if args.check:
        print(f"{target.name}: search core is STALE; run sync_search_core.py without --check")
        sys.exit(1)
    out = src[:s.end()] + "\n" + rendered + "\n" + src[e.start():]
    if crlf:
        out = out.replace("\n", "\r\n")
    target.write_text(out, encoding="utf-8", newline="")
    print(f"{target.name}: search core written ({args.ns}, {ngroups} synonym groups, {len(rendered):,} chars)")


if __name__ == "__main__":
    main()
