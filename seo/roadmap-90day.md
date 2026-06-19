# 90-Day SEO Roadmap — bestwiets.com

**Starting state (week 0):** 180 indexable URLs, sitemap submitted, GSC verified, NL/DE/BE country pages live, 28 cluster articles, Tidio live chat, full schema (Product/Article/FAQ/Breadcrumb).

**Reality check up front:** SEO is **time + crawl + authority**. Nothing you do in the next 90 days will produce a sudden ranking spike on head terms like "wiet kopen". What it *can* do: drive measurable indexation, generate the first impressions/clicks on long-tail keywords, and lay a backlink base. I've kept the projections honest — they're ranges, not promises.

---

## Month 1 — Foundation + crawl (weeks 1–4)

### Week 1 — Verify indexation is happening

| Day | Action | Owner |
|---|---|---|
| 1 | Resubmit `sitemap.xml` in GSC (forces a refresh) | You |
| 1 | URL-Inspect 5 priority pages, click "Request indexing": `/`, `/shop`, `/be`, `/fr`, `/de/cannabis-kaufen-deutschland` | You |
| 2 | Set up Bing Webmaster Tools (mirror of GSC; verifies → submits sitemap) | You |
| 3 | Run PageSpeed Insights on `/`, `/shop`, `/product/gelato-41`. Note CWV scores. | You / me |
| 4 | Verify Tidio is appearing on real bestwiets.com (in your dashboard → Live Visitors) | You |
| 5–7 | Daily: check GSC → Pages → "Indexed" count. Target by end of week 1: 50+ pages crawled. | You |

**Expected outcome by end of week 1:** 50+ pages "Crawled" or "Indexed" in GSC. Impressions still near 0 — too early.

### Week 2 — Plug content gaps (lowest-difficulty wins)

| Action | Detail |
|---|---|
| Write 2 NL strain pages: Gelato + White Widow | ~400–600 words each, links to matching product, H2s targeting "kopen / effect / smaak" | Me |
| Add product → article internal links | Each product page links to 1–2 relevant articles by category (Cali → "Wat is Cali Weed?", Hash → "Verschil hasj en wiet", etc.) | Me |
| Replace inlined logo base64 with `/favicon.svg` reference | Lighter page weight on every page | Me |
| Fix any PageSpeed "poor" CWV findings from week 1 | Likely: defer Google Fonts, preload key image | Me |

**Expected outcome:** site weight drops, page count grows to ~185. First long-tail impressions appearing in GSC Performance for the new strain/article keywords.

### Week 3 — More cluster + first city pages

| Action | Detail |
|---|---|
| Write 3 NL strain pages: Northern Lights, Sour Diesel, Lemon Haze | Same template |
| Write 1 DE city page: `/weed-kaufen-hamburg` | ~400 words, "wir liefern nach Hamburg in 2–4 Werktagen" + link to shop |
| Write 1 DE city page: `/weed-kaufen-muenchen` | Same template |

**Expected outcome:** 6 new pages live. First impressions on `gelato kopen`, `white widow kopen`, city-specific DE terms. Likely positions 30–80 — that's normal early.

### Week 4 — First backlink push begins

| Action | Detail |
|---|---|
| Implement outreach for first 5 directory submissions (see backlinks.md) | You — uses templates |
| Submit to NL/DE/BE cannabis directories (5–10) | You |
| Reach out to 2–3 cannabis blogs with a content collaboration pitch | You |
| Track: log every outreach + reply in a spreadsheet | You |

**Expected outcome by end of month 1:**
- **Indexation:** 90–100% of sitemap (170+ pages) appearing in GSC Indexed.
- **Impressions:** 100–500/day on long-tail terms (article + strain pages).
- **Clicks:** 5–30/day — small but real.
- **Backlinks:** 2–5 new (directories, maybe 1 editorial).
- **Rankings on head terms:** still nowhere (positions 50+). Expected.

---

## Month 2 — Expand + iterate on what's working (weeks 5–8)

### Week 5 — City + payment expansion

| Action | Detail |
|---|---|
| 2 more DE city pages: Köln, Frankfurt | Same template |
| 1 NL article: `wietolie effecten en gebruik` | Builds on existing wietolie page |
| 1 FR article: `cannabis premium belgique` | Fills the French cluster gap |

### Week 6 — Use GSC data to retitle

By now you'll have ~4 weeks of GSC Performance data. **This is the most valuable optimisation moment of the whole 90 days.**

| Action | Detail |
|---|---|
| Export top 20 queries from GSC | Filter by impressions > 50 |
| For each query getting impressions but low CTR (<2%), rewrite the title tag | Me — I rewrite, you confirm |
| For each query ranking 11–20 (page 2), expand the matching page (more content + better internal links) | Me + you |

**Why this matters:** ranking on page 2 with low CTR means you're close but the snippet isn't compelling. A retitle can move position 12 → 6 within weeks.

### Week 7 — Reviews infrastructure

| Action | Detail |
|---|---|
| Set up post-checkout review request flow (Tidio automation or email) | You — uses Tidio |
| Collect first 10–20 honest reviews | Customers — happens organically |
| Once a product has ≥5 reviews, wire `AggregateRating` schema | Me, programmatically across PRODUCTS array |

**SEO impact:** stars appearing in search results boost CTR 10–25% on product queries.

### Week 8 — Mid-quarter audit + backlink push 2

| Action | Detail |
|---|---|
| Mid-quarter audit: rerun PageSpeed, check GSC Coverage for any unexpected exclusions, verify Tidio still loading | Me + you |
| Second backlink push: 5–10 new outreach emails | You |
| If any specific article is getting >100 impressions, write a sister article on the same topic | Me |

**Expected outcome by end of month 2:**
- **Pages indexed:** 195+ (covers month 2 additions)
- **Impressions:** 500–2000/day
- **Clicks:** 50–200/day
- **First-page rankings (positions 1–10):** 5–15 long-tail terms (strain + city + payment).
- **Backlinks:** 5–15 total. (Cannabis is hard for editorial links; directory volume matters.)

---

## Month 3 — Compound the gains (weeks 9–12)

By month 3, you should see clear data on what's working. The plan from here adapts to your GSC numbers — no point setting a fixed plan that ignores reality.

### Week 9 — Double down on the top 5 winning topics

Look at GSC: which 5 articles/pages are getting the most clicks? For each:
- Expand the content by 300–500 words.
- Add an FAQ block to the page (FAQ schema → potential rich result).
- Add 3 more internal links *to* that page from sibling articles.

### Week 10 — Product page enhancement (top 20 sellers)

For your 20 best-selling products:
- Expand description from 1 line to 3–4 sentences (genetics, effects, flavour profile, recommended use).
- Add 3–5 FAQ items per page.
- Wire FAQ schema.

This is high-effort but high-yield: 20 product pages × better content + FAQ schema = serious commercial-intent improvement.

### Week 11 — Backlink push 3 + guest content

| Action | Detail |
|---|---|
| Third backlink push (10+ outreaches) | You |
| Pitch 2 guest posts to NL/DE cannabis blogs | You |
| Identify any unlinked brand mentions (Google search `"bestwiets" -site:bestwiets.com`) — reach out for a link | You |

### Week 12 — Quarter wrap + plan Q2

| Action | Detail |
|---|---|
| Run the audit again (`seo-audit.md`) — note what changed | Me |
| Pull the GSC report for the full 90 days | You |
| Identify the 5 pages that drove the most clicks → that's your content template for Q2 | You + me |

**Expected outcome by end of month 3 / end of 90 days:**
- **Pages indexed:** 200+
- **Impressions:** 1500–6000/day
- **Clicks:** 200–800/day
- **First-page rankings:** 15–40 long-tail terms
- **Backlinks:** 15–30 total
- **Head terms** ("wiet kopen" / "cannabis online kaufen"): likely positions 25–60. **Still not page 1.** That's the 6–12 month horizon and requires sustained backlink building.

---

## Honest expectations for revenue/sales impact

I'm not going to fabricate a revenue projection — anyone who tells you "you'll do €X in month 3" without knowing your conversion rate, AOV, and current baseline is making numbers up.

What I can tell you confidently:
- **Months 1–2:** organic traffic is small but real. Most clicks come from long-tail articles, not commercial pages.
- **Month 3 onwards:** traffic compounds month over month *if* you keep publishing 1–2 articles per week and adding backlinks. Stopping content = stagnation within ~2 months.
- **Month 6+:** head terms become possible. Long-tail conversions should be paying for the operational cost of running the SEO program by this point.

## What kills this plan

In rough order of how often I've seen each kill projects:

1. **You stop publishing content.** Two articles a week is the minimum cadence for an actively-growing site in a competitive niche.
2. **You stop building backlinks.** SEO without off-site work caps out fast.
3. **You buy spammy backlinks** trying to shortcut. Cannabis is heavily scrutinised; one bad link blast can poison the domain.
4. **You don't act on GSC data.** Real signals showing up in week 6+ that go ignored leave wins on the table.

## Reporting cadence (what to look at, when)

- **Daily (5 min):** GSC → Performance → Total clicks. Just watch the trend.
- **Weekly (20 min):** GSC top queries (sort by impressions). Note any surprises. New keywords appearing = new content opportunities.
- **Monthly (1 hr):** Full GSC review: impressions/clicks/CTR/avg position trend. Backlink count from Ahrefs/SEMrush free reports. Tidio chat trends.

I can produce the monthly review template — it's basically: top 20 queries, top 10 pages by clicks, pages with CTR <1% needing a retitle, new keywords entering top 50, and a 2-sentence "what worked, what didn't" summary.
