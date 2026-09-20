"""Company name normalization shared by match and enrich scripts."""
import re
import unicodedata

# Suffixes and filler words that add noise to firm-name matching.
_STRIP_TOKENS = {
    "llc", "l.l.c", "inc", "inc.", "incorporated", "ltd", "ltd.", "limited",
    "lp", "l.p", "llp", "l.l.p", "plc", "co", "co.", "corp", "corp.",
    "corporation", "company", "the", "and", "&", "of", "group", "holdings",
    "partners", "wealth", "management", "advisors", "advisers", "advisory",
    "capital", "financial", "investment", "investments", "services",
    "associates", "asset", "assets", "planning", "counsel", "counselors",
}

_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize(name: str, aggressive: bool = False) -> str:
    """Return a lowercase, punctuation-free form of a firm name.

    aggressive=True also drops generic industry words (wealth, capital, etc.).
    Use the light form for the primary score and the aggressive form as a
    secondary signal, since dropping words can collapse distinct firms.
    """
    if not isinstance(name, str):
        return ""
    s = strip_accents(name).lower()
    s = s.replace("&", " and ")
    s = _PUNCT.sub(" ", s)
    tokens = s.split()
    light = {"llc", "inc", "incorporated", "ltd", "limited", "lp", "llp", "plc",
             "corp", "corporation", "co", "company", "the"}
    drop = _STRIP_TOKENS if aggressive else light
    tokens = [t for t in tokens if t not in drop]
    return _WS.sub(" ", " ".join(tokens)).strip()


if __name__ == "__main__":
    for n in ["The Smith & Jones Wealth Management, LLC", "Acme Capital Advisors Inc."]:
        print(repr(n), "->", repr(normalize(n)), "|", repr(normalize(n, aggressive=True)))
