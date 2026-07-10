"""Process scraped blog data into categorized blog-index.json."""
import json
import re
from collections import Counter

with open("scraped_blogs_raw.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# ── Strategy tag detection ──
STRATEGY_PATTERNS = {
    "Trend": [
        r"trend.follow", r"managed futures", r"RSST", r"RSBT",
        r"crisis alpha", r"CTA", r"momentum", r"systematic macro",
    ],
    "Carry": [
        r"carry", r"futures yield", r"RSSY", r"RSBY",
        r"roll yield", r"term structure", r"contango", r"backwardation",
    ],
    "Gold": [
        r"\bgold\b", r"RSGD", r"RSSX", r"precious metal",
    ],
    "Bitcoin": [
        r"bitcoin", r"\bBTC\b", r"crypto", r"RSSX",
    ],
    "Merger Arb": [
        r"merger arb", r"merger.arb", r"RSBA", r"RSMA",
        r"event.driven", r"deal spread",
    ],
    "Bonds": [
        r"RSSB", r"bonds plus", r"boosting bond", r"fixed income portfolio",
        r"rethinking fixed income", r"bonds still belong",
        r"liquidity bucket", r"bond return", r"inverted yield curve",
        r"interest rate environment",
    ],
    "Equities": [
        r"equity factor", r"100% stock", r"long.only active",
        r"equity exposure in managed futures", r"fresh perspective on long.only",
        r"EM investor", r"emerging market investor", r"anti.beta",
    ],
}

# ── Category assignment rules ──
# Each rule: (category_name, required_signals)
# A post gets a category if enough signals match

def detect_strategies(text):
    """Return list of strategy tags found in text."""
    text_lower = text.lower()
    found = []
    for strat, patterns in STRATEGY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                found.append(strat)
                break
    return found


def assign_categories(title, excerpt, body, wp_cats):
    """Assign topic categories based on content analysis."""
    text = f"{title} {excerpt} {body}".lower()
    title_lower = title.lower()
    cats = []

    # ── Foundations ──
    foundations_signals = [
        "what is return stacking" in text,
        "how-to guide" in title_lower,
        "checklist" in title_lower,
        "return stacking 101" in text,
        "diversification 2.0" in title_lower,
        "evolution of portfolio construction" in text,
        "core concept" in text,
        "visualizer" in title_lower,
        "three ways to use return stacking" in text,
        "lazy collateral" in title_lower,
        "reclaim core exposure" in title_lower,
        "diversification without compromise" in title_lower,
        "redefining risk management" in title_lower,
        "low return environment" in title_lower,
        "100% stock portfolio" in title_lower,
        "re-thinking" in title_lower and "60/40" in title_lower,
    ]
    if sum(foundations_signals) >= 1:
        cats.append("Foundations")

    # ── Strategy Spotlights ──
    spotlight_signals = [
        "trend following" in title_lower,
        "carry" in title_lower and "yield" in title_lower,
        "gold" in title_lower and ("stack" in title_lower or "opportunit" in title_lower or "hedge" in title_lower or "fringe" in title_lower),
        "bitcoin" in title_lower,
        "merger arb" in title_lower or "merger arbitrage" in text[:500],
        "managed futures" in title_lower,
        "commodities" in title_lower,
        "bonds still belong" in title_lower,
        "boosting bond" in title_lower,
        "filling the gap" in title_lower,
        "pent up energy" in title_lower,
        "em investors" in title_lower,
        "portable alpha with" in title_lower,
        "enhancing liquidity" in title_lower,
        "rethinking corporate bonds" in title_lower,
        "constrain equity exposure" in title_lower,
        "golden opportunities" in title_lower,
        "stacking for different objectives" in title_lower,
        "fast and slow diversification" in title_lower,
    ]
    if sum(spotlight_signals) >= 1:
        cats.append("Strategy Spotlights")

    # ── Portfolio Construction ──
    construction_signals = [
        "portfolio construction" in text[:1000],
        "60/40" in text[:500],
        "capital market assumptions" in title_lower,
        "how to guide" in title_lower,
        "100% stock portfolio" in title_lower,
        "bonds plus alternatives" in title_lower,
        "high interest rate" in title_lower,
        "inverted yield curve" in title_lower,
        "glide path" in title_lower,
        "retirement" in title_lower,
        "different objectives" in title_lower,
        "re-thinking the" in title_lower,
        "fresh perspective on long-only" in title_lower,
        "outperform" in title_lower and "benchmark" in title_lower,
        "reclaim core exposure" in title_lower,
        "fast and slow diversification" in title_lower,
        "don't skew it up" in title_lower or "skew" in title_lower,
    ]
    if sum(construction_signals) >= 1:
        cats.append("Portfolio Construction")

    # ── Leverage Explained ──
    leverage_signals = [
        "leverage" in title_lower,
        "margin" in title_lower,
        "volatility drag" in title_lower,
        "volatility is bad" in title_lower,
        "rebalance drag" in title_lower,
        "cost of leverage" in title_lower,
        "portable alpha" in title_lower and "case study" not in title_lower,
        "risks of leverage" in title_lower,
        "avoiding lice" in title_lower,
        "lazy collateral" in title_lower,
    ]
    if sum(leverage_signals) >= 1:
        cats.append("Leverage Explained")

    # ── Mechanics & Operations ──
    mechanics_signals = [
        "tax" in title_lower,
        "distribution" in title_lower,
        "tracking error" in title_lower,
        "cash drag" in title_lower,
        "liquidity" in title_lower,
        "fund distribution" in text[:500],
    ]
    if sum(mechanics_signals) >= 1:
        cats.append("Mechanics & Operations")

    # ── Practice Management ──
    practice_signals = [
        "financial advisor" in title_lower,
        "business risk" in title_lower,
        "practice management" in str(wp_cats).lower(),
        "behavioral alpha" in title_lower,
        "line-item risk" in text[:500] or "line item risk" in text[:500],
        "successful financial advisor" in title_lower,
        "immunize business risk" in title_lower,
    ]
    if sum(practice_signals) >= 1:
        cats.append("Practice Management")

    # ── Research & Case Studies ──
    research_signals = [
        "case study" in title_lower,
        "mystery" in title_lower and "factor" in title_lower,
        "randomly allocated" in title_lower,
        "excess returns" in title_lower and "structural" in title_lower,
        "delta" in title_lower and "pension" in title_lower,
        "potential return advantage" in title_lower,
        "em investors" in title_lower,
        "more than enough" in title_lower,
        "fresh perspective on long-only" in title_lower,
    ]
    if sum(research_signals) >= 1:
        cats.append("Research & Case Studies")

    # Fallback: if no category assigned, default to Foundations
    if not cats:
        cats.append("Foundations")

    return cats


def extract_keywords(title, excerpt, body):
    """Extract top keywords from the post content."""
    text = f"{title} {excerpt} {body[:2000]}".lower()

    # Domain-specific keywords to look for
    domain_terms = [
        "return stacking", "portable alpha", "managed futures", "trend following",
        "carry", "futures yield", "gold", "bitcoin", "merger arbitrage",
        "leverage", "volatility", "diversification", "correlation",
        "sharpe ratio", "drawdown", "risk-adjusted", "tracking error",
        "capital efficiency", "collateral", "margin", "rebalance",
        "60/40", "bonds", "equities", "alternatives", "inflation",
        "interest rate", "yield curve", "retirement", "glide path",
        "tax", "distributions", "liquidity", "cash drag",
        "behavioral", "line-item risk", "business risk", "practice management",
        "alpha", "beta", "skewness", "kurtosis", "variance drag",
        "ETF", "portfolio construction", "asset allocation",
        "risk premium", "factor", "momentum", "mean reversion",
        "emerging markets", "commodities", "TIPS", "real assets",
        "overlay", "notional", "exposure", "benchmark",
    ]

    found = []
    for term in domain_terms:
        if term.lower() in text:
            found.append(term)
    return found[:15]  # cap at 15 keywords


def extract_key_sentences(excerpt, body):
    """Extract 2-3 key sentences from the post."""
    sentences = []

    # Use excerpt as first key sentence
    if excerpt:
        sentences.append(excerpt.strip())

    # Extract from body: look for sentences with key phrases
    body_sentences = re.split(r'(?<=[.!?])\s+', body[:3000])
    key_phrases = [
        "return stacking", "the key", "importantly", "in other words",
        "the bottom line", "this means", "the result", "we find",
        "advisors should", "investors can", "the takeaway",
    ]

    for sent in body_sentences:
        if len(sent) < 40 or len(sent) > 300:
            continue
        sent_lower = sent.lower()
        for phrase in key_phrases:
            if phrase in sent_lower and sent.strip() not in sentences:
                sentences.append(sent.strip())
                break
        if len(sentences) >= 3:
            break

    return sentences[:3]


# ── Process all posts ──
index = []
for post in raw:
    title = post["title"]
    excerpt = post["excerpt"]
    body = post["body_preview"]
    url = post["url"]
    date = post["date"]
    wp_cats = post["wp_categories"]

    strategies = detect_strategies(f"{title} {excerpt} {body}")
    categories = assign_categories(title, excerpt, body, wp_cats)
    keywords = extract_keywords(title, excerpt, body)
    key_sentences = extract_key_sentences(excerpt, body)

    # Determine if featured/startHere
    start_here_titles = [
        "The Return Stacking How-To Guide",
        "Diversification 2.0 Understanding Return Stacking",
        "The Return Stacking Checklist",
    ]
    is_start_here = any(st.lower() in title.lower() for st in start_here_titles)

    entry = {
        "title": title,
        "url": url,
        "date": date,
        "categories": categories,
        "strategies": strategies,
        "startHere": is_start_here,
        "excerpt": excerpt,
        "keywords": keywords,
        "keySentences": key_sentences,
    }
    index.append(entry)

# Sort by date descending (newest first)
index.sort(key=lambda x: x["date"], reverse=True)

# Mark the 3 newest as featured
for i, entry in enumerate(index):
    entry["featured"] = i < 3

# Save
with open("blog-index.json", "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

# ── Print summary ──
print(f"Total posts: {len(index)}")
print()

# Category distribution
cat_counts = Counter()
for entry in index:
    for cat in entry["categories"]:
        cat_counts[cat] += 1
print("Category distribution:")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

print()

# Strategy distribution
strat_counts = Counter()
for entry in index:
    for strat in entry["strategies"]:
        strat_counts[strat] += 1
print("Strategy tag distribution:")
for strat, count in strat_counts.most_common():
    print(f"  {strat}: {count}")

print()

# Posts with no strategy tags
no_strat = [e for e in index if not e["strategies"]]
print(f"Posts with no strategy tags: {len(no_strat)}")
for e in no_strat:
    print(f"  - {e['title']}")

print()
print(f"Featured (latest 3):")
for e in index[:3]:
    print(f"  - [{e['date']}] {e['title']}")

print()
print(f"Start Here:")
for e in index:
    if e["startHere"]:
        print(f"  - {e['title']}")
