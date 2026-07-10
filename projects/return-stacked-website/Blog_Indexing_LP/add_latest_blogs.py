"""Add the two newest blog posts and make them positions 1-2 of Latest Posts.

Latest Posts renders filter(f==true) in array order, sliced to 3. So we insert
the two new dated posts at the top of the dated-post block (after the evergreen
foundational/Start Here entries) and recompute `featured` = the 3 newest by date.

Updates blog-index.json, blog-data-slim.json, and the inline var POSTS in
blog-landing-page.html. Idempotent (matches by URL slug).
"""
import json
import re

INDEX = "blog-index.json"
SLIM = "blog-data-slim.json"
HTML = "blog-landing-page.html"

# Newest first so featured array order = date order.
NEW = [
    {
        "title": "Is Now the Right Time to Add My Stack?",
        "url": "https://www.returnstacked.com/is-now-the-right-time-to-add-my-stack/",
        "date": "2026-05-11",
        "categories": ["Portfolio Construction"],
        "strategies": [],
        "startHere": False,
        "excerpt": "A framework for managing timing risk when adding a stack: stacking versus funding approaches, timing luck, and three practical ways to phase in implementation.",
        "keywords": ["return stacking", "market timing", "implementation", "diversification", "managed futures", "capital efficiency", "correlation"],
        "keySentences": [],
        "featured": True,
    },
    {
        "title": "What's the Optimal Stack?",
        "url": "https://www.returnstacked.com/whats-the-optimal-stack/",
        "date": "2026-04-14",
        "categories": ["Portfolio Construction", "Research & Case Studies"],
        "strategies": [],
        "startHere": False,
        "excerpt": "Bootstrap analysis of optimal return stacking allocations, why the mathematically ideal stack is behaviorally unsustainable, and practical blends using tracking error constraints.",
        "keywords": ["return stacking", "portfolio construction", "diversification", "tracking error", "managed futures", "merger arbitrage", "gold", "risk management"],
        "keySentences": [],
        "featured": True,
    },
]


def slug(url):
    return url.rstrip("/").rsplit("/", 1)[-1].lower()


def to_slim(e):
    return {
        "t": e["title"], "u": e["url"], "d": e["date"],
        "c": e["categories"], "s": e["strategies"],
        "e": e["excerpt"], "k": " ".join(e["keywords"]),
        "f": e["featured"], "sh": e["startHere"],
    }


with open(INDEX, encoding="utf-8") as f:
    index = json.load(f)

# Drop any prior copies of the new URLs (idempotent)
new_slugs = {slug(e["url"]) for e in NEW}
index = [e for e in index if slug(e["url"]) not in new_slugs]

# Insert the new posts right before the first dated entry (i.e. after the
# evergreen foundational/Start Here block, which all carry date == "").
insert_at = next((i for i, e in enumerate(index) if e.get("date")), len(index))
index = index[:insert_at] + NEW + index[insert_at:]

# Recompute featured = the 3 newest by date.
for e in index:
    e["featured"] = False
dated = sorted([e for e in index if e.get("date")], key=lambda x: x["date"], reverse=True)
for e in dated[:3]:
    e["featured"] = True

with open(INDEX, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

slim = [to_slim(e) for e in index]
with open(SLIM, "w", encoding="utf-8") as f:
    json.dump(slim, f, ensure_ascii=False)

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

print(f"Total posts now: {len(index)}")
print("Latest Posts (featured, array order = what renders):")
for e in [x for x in index if x["featured"]][:3]:
    print(f"  - [{e['date']}] {e['title']}")
print("HTML var POSTS updated:", replaced)
