# Skill: Advisor Guide

Generate a branded "Advisor's Guide to Client Conversations" document for Return Stacked.

## When to Use

When the user asks to create, update, or regenerate an advisor guide for any Return Stacked brand line.

## How It Works

The full workflow, content format reference, and brand rules are documented in `projects/advisor-guide-tool/CLAUDE.md`. **Read that file before doing anything.** It is the single source of truth for this skill.

## Quick Reference

### Create a new guide

Follow the phased workflow in the project CLAUDE.md:

1. **Intake** -- ask the 5 intake questions (brand line, topic, cover style, images, source materials) one at a time
2. **Write** -- collaborate on content in the established voice/style
3. **Notion handoff** -- output clean Markdown for team editing in Notion
4. **Generate** -- translate finalized content to YAML, run the generator, deliver HTML
5. **Iterate** -- make adjustments as needed

### Regenerate an existing guide

```bash
cd projects/advisor-guide-tool
python generator/generate_guide.py content/<topic-slug>.yaml
```

Output lands in `projects/advisor-guide-tool/Advisor_Guide_Output/`.

### Brand lines

| Brand | logo_family key | Footer URL |
|-------|----------------|------------|
| Return Stacked ETFs (US) | `RS_ETF_Logos` | www.returnstackedetfs.com |
| Return Stacked ETFs Canada | `RS_ETF_Canada_Logos` | www.returnstackedetfs.ca |
| Return Stacked Funds | `RS_Funds_Logos` | www.returnstackedfunds.com |
| Return Stacked Portfolio Solutions | `RS_Portfolio_Solutions_logos` | www.returnstacked.com |

## Key Files

| Path | Purpose |
|------|---------|
| `projects/advisor-guide-tool/CLAUDE.md` | Full workflow and rules (read this first) |
| `projects/advisor-guide-tool/generator/generate_guide.py` | Main generator |
| `projects/advisor-guide-tool/generator/brand_config.py` | Brand constants |
| `projects/advisor-guide-tool/generator/templates/base.css` | Master stylesheet |
| `projects/advisor-guide-tool/content/` | YAML content files |
| `projects/advisor-guide-tool/Advisor_Guide_Output/` | Generated HTML output |
| `projects/advisor-guide-tool/Original_guides/` | Reference PDFs |

## Dependencies

- Python 3 with `pyyaml` (`pip install pyyaml`)
- Brand assets in `references/brand-assets/return-stacked/` (fonts, logos, backdrops)
