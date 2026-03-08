"""Disclosures and glossary page HTML builder."""

import html
from datetime import date


def build_glossary(terms):
    """Build a glossary section.

    Args:
        terms: List of dicts with 'term' and 'definition' keys.

    Returns:
        HTML string.
    """
    if not terms:
        return ""

    items = []
    for entry in terms:
        term = html.escape(entry.get("term", ""))
        defn = html.escape(entry.get("definition", ""))
        items.append(
            f'<div class="glossary-term">{term}</div>'
            f'<div class="glossary-definition">{defn}</div>'
        )

    return f'''<div class="glossary-heading">Glossary</div>
{"".join(items)}'''


def build_disclosures(legal_text="", glossary_terms=None, logo_family=None, year=None):
    """Build the full disclosures page content.

    Args:
        legal_text: The legal disclaimer text (can contain newlines for paragraphs).
        glossary_terms: Optional list of glossary dicts.
        logo_family: Logo family key to determine business name for copyright.
        year: Copyright year (defaults to current year).

    Returns:
        HTML string for the disclosures content area.
    """
    if year is None:
        year = date.today().year

    glossary_html = build_glossary(glossary_terms or [])

    paragraphs = []
    if legal_text:
        for para in legal_text.strip().split("\n\n"):
            para = para.strip()
            if para:
                paragraphs.append(
                    f'<p class="disclosures-text">{html.escape(para)}</p>'
                )

    # Build copyright using the correct business name for the silo
    if logo_family:
        from generator import brand_config
        business_name = brand_config.get_business_name(logo_family)
    else:
        business_name = "Return Stacked\u00ae Portfolio Solutions"

    copyright_html = (
        f'<p class="copyright">'
        f'\u00a9 {html.escape(business_name)}, {year}. All rights reserved.'
        f'</p>'
    )

    return f'''{glossary_html}
<div class="disclosures-heading">Disclosures</div>
{"".join(paragraphs)}
{copyright_html}'''
