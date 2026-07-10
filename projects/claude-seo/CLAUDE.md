# Claude SEO

SEO analysis skill for Claude Code. Installed project-locally from [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) v1.8.2.

## Skill Location

- Skills: `.claude/skills/seo/` and `.claude/skills/seo-*/`
- Agents: `.claude/agents/seo-*.md`
- Extensions: DataForSEO, Firecrawl, Banana (image gen)

## Commands

| Command | What it does |
|---------|-------------|
| `/seo audit <url>` | Full site audit with parallel subagent delegation |
| `/seo page <url>` | Deep single-page analysis |
| `/seo technical <url>` | Technical SEO audit (9 categories) |
| `/seo content <url>` | E-E-A-T and content quality |
| `/seo schema <url>` | Schema.org markup detection and validation |
| `/seo images <url>` | Image optimization analysis |
| `/seo sitemap <url>` | Analyze existing XML sitemap |
| `/seo sitemap generate` | Generate new sitemap |
| `/seo geo <url>` | AI Overviews / GEO optimization |
| `/seo plan <type>` | Strategic SEO planning (saas, local, ecommerce, publisher, agency) |
| `/seo local <url>` | Local SEO analysis |
| `/seo maps [command]` | Maps intelligence (geo-grid, GBP, reviews, competitors) |
| `/seo hreflang <url>` | International SEO audit |
| `/seo backlinks <url>` | Backlink profile analysis |
| `/seo google [command]` | Google APIs (GSC, PageSpeed, CrUX, Indexing, GA4) |
| `/seo google report [type]` | Generate PDF/HTML report with charts |
| `/seo programmatic <url>` | Programmatic SEO analysis |
| `/seo competitor-pages <url>` | Competitor comparison page generation |
| `/seo firecrawl [command] <url>` | Full-site crawling via Firecrawl |
| `/seo dataforseo [command]` | Live SEO data via DataForSEO |

## Google API Setup

1. Drop your Google Search Console and GA4 API credential JSON files into this folder (`projects/claude-seo/`)
2. Run `/seo google setup` to configure credential paths
3. The `.gitignore` in this folder excludes `*.json` to prevent committing secrets

## Credential Tiers

The tool works at 4 levels of authentication:
- **No credentials**: PageSpeed Insights (public API, no key needed)
- **API key only**: PageSpeed + CrUX data
- **OAuth (Search Console)**: + GSC queries, URL inspection, Indexing API
- **OAuth (GA4)**: + organic traffic analysis

## Known Issues

- **WeasyPrint** (PDF report generation) requires GTK/Pango system libraries on Windows. If you need PDF reports via `/seo google report`, install GTK3 for Windows: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows
- HTML reports work without WeasyPrint

## Updating

To update to a newer version:
1. Clone the repo: `git clone --depth 1 https://github.com/AgriciDaniel/claude-seo.git /tmp/claude-seo-update`
2. Copy updated files over the existing `.claude/skills/seo*` and `.claude/agents/seo-*.md`
3. Re-run `pip install -r requirements.txt` if dependencies changed
