"""One-off: seed assets/search-synonyms.json from the Research Articles
file plus the literature / product groups. Kept for the record; edit the
JSON directly from now on."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / "projects/return-stacked-website/Blog_Indexing_LP/search-synonyms.json"
OUT = HERE.parent / "assets/search-synonyms.json"

groups = json.loads(SRC.read_text(encoding="utf-8"))["groups"]
extra = [
    ["white paper", "whitepaper", "research paper", "paper"],
    ["one pager", "one-pager", "onepager", "one page", "primer", "overview"],
    ["presentation", "deck", "slides", "slide deck"],
    ["product brief", "fact sheet", "factsheet", "brief"],
    ["quarterly commentary", "commentary", "quarterly", "quarterly update", "market update"],
    ["client conversation", "talking points", "client guide", "advisor guide"],
    ["international", "intl", "developed markets", "ex us", "non us"],
    ["case study", "case studies", "worked example"],
]
readme = (
    "Shared search concept groups for every Return Stacked index widget "
    "(Research Articles, Product Articles, Literature). Each group is a list "
    "of phrases that mean the same thing. When an item's searchable text "
    "(title, summary, keywords, tags) contains ANY phrase of a group, the "
    "words of EVERY phrase in that group are added to that item's search "
    "terms, so a search for one phrasing finds items that use another. "
    "Phrase matching is word-by-word; the last word may carry a suffix "
    "('tax' also fires on 'taxes' and 'taxation'). Keep phrases lowercase "
    "and never use the characters & < > or quotes in them. Applied (a) at "
    "runtime inside every widget's search core (sync_search_core.py renders "
    "this file into the script; re-run the sync for each widget after "
    "editing) and (b) at build time by the Research Articles build, which "
    "also sees each post's key sentences. Do NOT add ETF tickers as trigger "
    "phrases: on the Literature page a ticker must never surface Manager "
    "Research rows (compliance)."
)
OUT.write_text(json.dumps({"_readme": readme, "groups": groups + extra}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(groups) + len(extra)} groups written to {OUT}")
