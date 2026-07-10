"""Add curated landing-page/podcast entries to the corpus and set the
Start Here trio. Updates blog-index.json (full), blog-data-slim.json (slim),
and the inline `var POSTS = [...]` line in blog-landing-page.html.

Start Here order (renders first card large):
  1. What is Return Stacking for Outperformance
  2. What is Return Stacking for Diversification
  3. Avoiding LICE (existing entry, flag flipped)

Idempotent: re-running won't create duplicates (matches by URL slug).
"""
import json
import re

INDEX = "blog-index.json"
SLIM = "blog-data-slim.json"
HTML = "blog-landing-page.html"

# New entries to prepend, in array order. Full-record form.
NEW = [
    {
        "title": "What is Return Stacking for Outperformance",
        "url": "https://www.returnstacked.com/what-is-return-stacking-for-outperformance/",
        "date": "",
        "categories": ["Foundations"],
        "strategies": [],
        "startHere": True,
        "excerpt": "How return stacking layers diversifying alternatives on top of a traditional stock and bond portfolio in pursuit of outperformance, without giving up core market exposure.",
        "keywords": ["return stacking", "portable alpha", "capital efficiency", "outperformance", "diversification", "alpha", "portfolio construction"],
        "keySentences": [],
        "featured": False,
    },
    {
        "title": "What is Return Stacking for Diversification",
        "url": "https://www.returnstacked.com/what-is-return-stacking",
        "date": "",
        "categories": ["Foundations"],
        "strategies": [],
        "startHere": True,
        "excerpt": "An introduction to return stacking: adding diversifying alternative investments on top of traditional stocks and bonds without reducing core allocations.",
        "keywords": ["return stacking", "diversification", "portable alpha", "capital efficiency", "portfolio construction", "correlation"],
        "keySentences": [],
        "featured": False,
    },
    {
        "title": "Investing in Gold",
        "url": "https://www.returnstacked.com/investing-in-gold",
        "date": "",
        "categories": ["Strategy Spotlights"],
        "strategies": ["Gold"],
        "startHere": False,
        "excerpt": "A guide to gold as a portfolio diversifier and inflation hedge, its history and valuation, and how a gold stack can be used within return stacking.",
        "keywords": ["gold", "diversification", "inflation", "real assets", "return stacking", "hedge"],
        "keySentences": [],
        "featured": False,
    },
    {
        "title": "Managed Futures Trend Following",
        "url": "https://www.returnstacked.com/managed-futures-trend-following",
        "date": "",
        "categories": ["Strategy Spotlights"],
        "strategies": ["Trend"],
        "startHere": False,
        "excerpt": "A guide to managed futures and trend following: history, theory, performance characteristics, and how a trend stack fits into portfolio construction.",
        "keywords": ["trend following", "managed futures", "crisis alpha", "momentum", "diversification", "return stacking"],
        "keySentences": [],
        "featured": False,
    },
    {
        "title": "Managed Futures Yield (Carry)",
        "url": "https://www.returnstacked.com/managed-futures-yield-carry",
        "date": "",
        "categories": ["Strategy Spotlights"],
        "strategies": ["Carry"],
        "startHere": False,
        "excerpt": "A guide to carry strategies in managed futures: theory, history, implementation, and applications to return stacking for portfolio enhancement.",
        "keywords": ["carry", "futures yield", "managed futures", "term structure", "return stacking", "diversification"],
        "keySentences": [],
        "featured": False,
    },
    {
        "title": "Merger Arbitrage",
        "url": "https://www.returnstacked.com/merger-arbitrage",
        "date": "",
        "categories": ["Strategy Spotlights"],
        "strategies": ["Merger Arb"],
        "startHere": False,
        "excerpt": "A guide to merger arbitrage: how the strategy profits from deal spreads in M&A, its performance characteristics, and its role in return stacking.",
        "keywords": ["merger arbitrage", "event driven", "deal spread", "diversification", "return stacking", "alternatives"],
        "keySentences": [],
        "featured": False,
    },
    {
        "title": "Managed Futures - Why Now! Positioning, Energy, De-Dollarization, and Portfolio Blind Spots",
        "url": "https://www.returnstacked.com/podcasts/managed-futures-why-now",
        "date": "",
        "categories": ["Strategy Spotlights"],
        "strategies": ["Trend"],
        "startHere": False,
        "excerpt": "ReSolve co-founders on why managed futures matter in today's macro environment: positioning, commodities, de-dollarization, and making the strategy behaviorally palatable through return stacking.",
        "keywords": ["managed futures", "trend following", "commodities", "diversification", "return stacking"],
        "keySentences": [],
        "featured": False,
    },
]

START_HERE_TRIO = ["what-is-return-stacking-for-outperformance",
                   "what-is-return-stacking", "avoiding-lice"]


def slug(url):
    return url.rstrip("/").rsplit("/", 1)[-1].lower()


def to_slim(e):
    return {
        "t": e["title"], "u": e["url"], "d": e["date"],
        "c": e["categories"], "s": e["strategies"],
        "e": e["excerpt"], "k": " ".join(e["keywords"]),
        "f": e["featured"], "sh": e["startHere"],
    }


# ---- Update FULL index ----
with open(INDEX, encoding="utf-8") as f:
    index = json.load(f)

# Reset all startHere, then drop any prior copies of our new URLs
new_slugs = {slug(e["url"]) for e in NEW}
for e in index:
    e["startHere"] = False
index = [e for e in index if slug(e["url"]) not in new_slugs]
index = NEW + index

# Flag the Start Here trio (outperformance + diversification already True in NEW;
# avoiding-lice is an existing entry)
for e in index:
    if slug(e["url"]) == "avoiding-lice" or "avoiding-lice" in e["url"].lower():
        e["startHere"] = True

with open(INDEX, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

# ---- Update SLIM (mirror of index, short keys) ----
slim = [to_slim(e) for e in index]
with open(SLIM, "w", encoding="utf-8") as f:
    json.dump(slim, f, ensure_ascii=False)

# ---- Update inline var POSTS in HTML ----
with open(HTML, encoding="utf-8") as f:
    lines = f.readlines()

posts_json = json.dumps(slim, ensure_ascii=False)
replaced = False
for i, ln in enumerate(lines):
    if ln.lstrip().startswith("var POSTS ="):
        indent = ln[:len(ln) - len(ln.lstrip())]
        lines[i] = f"{indent}var POSTS = {posts_json};\n"
        replaced = True
        break
if not replaced:
    raise SystemExit("ERROR: could not find 'var POSTS =' line in HTML")

with open(HTML, "w", encoding="utf-8") as f:
    f.writelines(lines)

# ---- Report ----
sh = [e for e in index if e["startHere"]]
print(f"Total posts now: {len(index)}")
print(f"Start Here ({len(sh)}), in render order:")
for e in [x for x in index if x["startHere"]][:3]:
    print(f"  - {e['title']}")
print(f"Featured/Latest (f=true): {sum(1 for e in index if e['featured'])}")
print("HTML var POSTS updated:", replaced)
