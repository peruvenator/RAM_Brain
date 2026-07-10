"""Scrape all 62 Return Stacked blog posts and extract structured data."""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

URLS = [
    "https://www.returnstacked.com/if-youre-a-successful-financial-advisor-you-got-lucky/",
    "https://www.returnstacked.com/return-stacking%ef%b8%8f-strategy-for-a-low-return-environment/",
    "https://www.returnstacked.com/avoiding-lice-the-right-and-wrong-ways-to-use-leverage-in-long-term-investing/",
    "https://www.returnstacked.com/return-stacking-a-fresh-perspective-on-long-only-active-u-s-equity-strategies/",
    "https://www.returnstacked.com/behavioral-alpha-how-return-stacking-can-help-investors-avoid-line-item-risk/",
    "https://www.returnstacked.com/the-potential-return-advantage-of-stacking-managed-futures-on-equities/",
    "https://www.returnstacked.com/portable-alpha-with-managed-futures-a-diversification-overlay/",
    "https://www.returnstacked.com/the-rebalance-drag-myth-in-leveraged-etfs-what-advisors-need-to-know/",
    "https://www.returnstacked.com/deltas-pension-miracle-a-portable-alpha-case-study/",
    "https://www.returnstacked.com/stacking-in-high-interest-rate-environments/",
    "https://www.returnstacked.com/return-stacking-how-to-guide/",
    "https://www.returnstacked.com/the-risks-of-leverage/",
    "https://www.returnstacked.com/bonds-plus-alternatives-and-chill/",
    "https://www.returnstacked.com/tracking-error-return-stacking-versus-replacement/",
    "https://www.returnstacked.com/stacking-the-odds-in-retirement/",
    "https://www.returnstacked.com/return-stacking-and-the-cost-of-leverage/",
    "https://www.returnstacked.com/return-stacking-in-an-inverted-yield-curve-environment/",
    "https://www.returnstacked.com/portable-alpha/",
    "https://www.returnstacked.com/return-stacking-and-taxes/",
    "https://www.returnstacked.com/the-return-stacking-visualizer/",
    "https://www.returnstacked.com/the-glide-path-re-imagined-part-2/",
    "https://www.returnstacked.com/capital-market-assumptions-when-return-stacking/",
    "https://www.returnstacked.com/the-glide-path-re-imagined/",
    "https://www.returnstacked.com/more-than-enough-is-too-much/",
    "https://www.returnstacked.com/can-randomly-allocated-portfolios-generate-excess-returns/",
    "https://www.returnstacked.com/tips-versus-commodities-just-return-stacking/",
    "https://www.returnstacked.com/financial-advisors-immunize-business-risk-from-bear-markets-inflation-regimes/",
    "https://www.returnstacked.com/cash-drag-liquidity-needs-and-return-stacking/",
    "https://www.returnstacked.com/a-mystery-equity-factor/",
    "https://www.returnstacked.com/the-return-stacking-checklist/",
    "https://www.returnstacked.com/return-stacking-and-volatility-drag/",
    "https://www.returnstacked.com/volatility-is-bad-for-your-wealth/",
    "https://www.returnstacked.com/excess-returns-through-a-structural-edge/",
    "https://www.returnstacked.com/diversification-without-compromise-three-ways-to-use-return-stacking-in-a-portfolio/",
    "https://www.returnstacked.com/dont-skew-it-up-return-stacking-for-smoother-returns/",
    "https://www.returnstacked.com/return-stacking-turning-lazy-collateral-into-opportunity/",
    "https://www.returnstacked.com/trend-following-through-turmoil-why-the-best-protection-comes-after-the-first-punch/",
    "https://www.returnstacked.com/diversification-2-0-understanding-return-stacking-and-the-evolution-of-portfolio-construction/",
    "https://www.returnstacked.com/reclaim-core-exposure-with-return-stacking/",
    "https://www.returnstacked.com/re-thinking-the-40-in-60-40-how-return-stacking-may-enhance-portfolio-diversification/",
    "https://www.returnstacked.com/diversification-2-0-redefining-risk-management-with-return-stacking/",
    "https://www.returnstacked.com/using-a-gold-stack-to-hedge-u-s-home-equity-bias/",
    "https://www.returnstacked.com/gold-bitcoin-from-fringe-to-foundational/",
    "https://www.returnstacked.com/carry-the-yield-ride-the-trend-a-strategic-partnership/",
    "https://www.returnstacked.com/a-different-way-to-outperform-benchmarks/",
    "https://www.returnstacked.com/rethinking-corporate-bonds-swapping-credit-risk-for-merger-arbitrage/",
    "https://www.returnstacked.com/boosting-bond-returns-return-stacking-for-enhancing-liquidity-buckets/",
    "https://www.returnstacked.com/were-all-em-investors-now/",
    "https://www.returnstacked.com/pent-up-energy-carry-managed-futures-why-now/",
    "https://www.returnstacked.com/should-we-constrain-equity-exposure-in-managed-futures-when-stacking-on-equities/",
    "https://www.returnstacked.com/building-a-100-stock-portfolio-using-return-stacking/",
    "https://www.returnstacked.com/the-key-business-risk-metric-i-use-financial-advisors-dont/",
    "https://www.returnstacked.com/stacking-for-different-objectives-part-3-inflation-hedging/",
    "https://www.returnstacked.com/return-stacking-and-fund-distributions-how-structure-drives-tax-drag/",
    "https://www.returnstacked.com/stacking-for-different-objectives-part-1-anti-beta/",
    "https://www.returnstacked.com/stacking-for-different-objectives-part-2-absolute-return/",
    "https://www.returnstacked.com/return-stacking-with-fast-and-slow-diversification-a-framework-for-market-volatility/",
    "https://www.returnstacked.com/golden-opportunities-enhancing-traditional-portfolios-with-a-gold-futures-stack/",
    "https://www.returnstacked.com/boosting-bonds-stacking-merger-arbitrage-to-enhance-fixed-income-portfolios/",
    "https://www.returnstacked.com/filling-the-gap-enhancing-traditional-stock-and-bond-portfolios-with-a-managed-futures-stack/",
    "https://www.returnstacked.com/why-bonds-still-belong-rethinking-fixed-income-in-modern-portfolios/",
    "https://www.returnstacked.com/margin-management-in-return-stacking/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_post(url):
    """Fetch a single blog post and extract structured data."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Title
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "").strip()
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else ""

        # Meta description
        excerpt = ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            excerpt = og_desc.get("content", "").strip()
        if not excerpt:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            excerpt = meta_desc.get("content", "").strip() if meta_desc else ""

        # Publication date
        date = ""
        date_meta = soup.find("meta", property="article:published_time")
        if date_meta:
            date = date_meta.get("content", "")[:10]
        if not date:
            time_el = soup.find("time")
            if time_el and time_el.get("datetime"):
                date = time_el["datetime"][:10]

        # Article body text
        body_text = ""
        article = soup.find("article") or soup.find("div", class_="entry-content") or soup.find("div", class_="et_pb_post_content")
        if article:
            for tag in article.find_all(["script", "style", "nav", "footer", "aside"]):
                tag.decompose()
            body_text = article.get_text(separator=" ", strip=True)

        # Fallback: try main content area
        if len(body_text) < 200:
            main = soup.find("main") or soup.find("div", id="main-content")
            if main:
                for tag in main.find_all(["script", "style", "nav", "footer", "aside", "header"]):
                    tag.decompose()
                body_text = main.get_text(separator=" ", strip=True)

        # Clean body text
        body_text = re.sub(r'\s+', ' ', body_text).strip()

        # Extract first ~3000 chars of body for analysis
        body_preview = body_text[:3000]

        # WordPress categories from page
        categories_found = []
        cat_links = soup.select('a[rel="category tag"], a[rel="tag"]')
        for cl in cat_links:
            cat_text = cl.get_text(strip=True)
            if cat_text:
                categories_found.append(cat_text)

        return {
            "url": url,
            "title": title,
            "date": date,
            "excerpt": excerpt,
            "body_preview": body_preview,
            "body_length": len(body_text),
            "wp_categories": list(set(categories_found)),
            "status": "ok"
        }
    except Exception as e:
        return {
            "url": url,
            "title": "",
            "date": "",
            "excerpt": "",
            "body_preview": "",
            "body_length": 0,
            "wp_categories": [],
            "status": f"error: {str(e)}"
        }


def main():
    print(f"Scraping {len(URLS)} blog posts...")
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_post, url): url for url in URLS}
        for i, future in enumerate(as_completed(future_to_url), 1):
            result = future.result()
            results.append(result)
            status = "OK" if result["status"] == "ok" else result["status"]
            print(f"  [{i}/{len(URLS)}] {status}: {result['title'][:60]}...")

    # Sort by URL to match original order
    url_order = {url: i for i, url in enumerate(URLS)}
    results.sort(key=lambda r: url_order.get(r["url"], 999))

    # Save raw scraped data
    with open("scraped_blogs_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\nDone. {ok_count}/{len(results)} scraped successfully.")
    print(f"Saved to scraped_blogs_raw.json")

    # Print summary
    for r in results:
        if r["status"] != "ok":
            print(f"  FAILED: {r['url']} -- {r['status']}")


if __name__ == "__main__":
    main()
