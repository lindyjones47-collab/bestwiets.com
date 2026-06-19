# Technical SEO Audit — bestwiets.com

**Audit date:** 2026-06-19
**Method:** live HTTP checks against `bestwiets.com`, source review of `index.html` and `generate.py`.

## Executive summary

The site is **technically healthy** for a single-file SPA hosted on GitHub Pages. The biggest historic problem (every deep URL returning 404 with one shared title) has been fixed via pre-rendering. **180 URLs** are indexable with unique meta, structured data, and correct `hreflang`. The remaining wins are off-site (backlinks, GSC submission follow-through) and content (more clusters, more original guides).

---

## 1. Indexability

| Check | Status |
|---|---|
| Sitemap submitted to GSC | ✅ (you confirmed) |
| `robots.txt` present and pointing at sitemap | ✅ |
| All routes return 200 (not 404) | ✅ verified live for `/`, `/shop`, `/product/*`, `/en/`, `/de/`, `/be`, `/fr`, articles |
| `404.html` fallback for unknown URLs | ✅ — lightweight redirector, preserves the permalink via `?p=` |
| Canonical on every page | ✅ |
| Trailing-slash consistency | ✅ language homes use `/nl/`-style trailing slash; everything else extensionless |

**Verdict:** clean. Indexation will be limited by crawl rate and authority, not by site issues.

## 2. Meta tags (titles, descriptions, OG, Twitter)

- Every one of the 180 routes has a **unique `<title>`** and **`<meta name=description>`** in the static HTML (driven by `generate.py`, regenerated from `index.html`).
- OpenGraph + Twitter Card metadata is present on every page.
- `og:locale` is set per language; `og:locale:alternate` lists the other two.
- **Found gap:** product titles follow `{Name} kopen – €{price} | WietStore`. That's good for Dutch; on the `/en/` and `/de/` versions, the product pages still use the Dutch-style title (because products themselves haven't been localized — by design). Acceptable for now since products live at unprefixed URLs (`/product/{slug}`).

## 3. Headings (H1/H2/H3)

- Home: H1 = "Wiet kopen & online bestellen" — matches primary keyword.
- Shop: H1 = "De Shop" — generic; ideally would target a keyword. **(Optimisation idea:** change to "Wiet, hasj en cali weed kopen" — but that may sacrifice UX clarity. Lean toward leaving as-is and letting the title tag carry the keyword.)
- Products: H1 = product name — correct.
- Country pages: H1 includes location keyword (e.g. "Cannabis kaufen in Deutschland", "Wiet kopen in België") — correct.
- Articles: H1 = article title — correct.
- **No H1-stacking issues** found.

## 4. Structured data (JSON-LD)

| Schema | Where | Status |
|---|---|---|
| `Organization` | sitewide | ✅ |
| `WebSite` (with SearchAction) | sitewide | ✅ |
| `Product` + `Offer` | every product page (130) | ✅ |
| `Article` | every blog post (28) | ✅ |
| `FAQPage` | home | ✅ |
| `BreadcrumbList` | product, article, /be, /fr, /de country landing | ✅ |
| `Review` / `AggregateRating` | — | ❌ intentionally absent (no genuine reviews) |
| `LocalBusiness` | — | ❌ not applicable (no physical storefront) |

**Action when ready:** collect real reviews (via Tidio post-sale, email follow-up). Once you have ≥5 honest reviews on a product, I'll wire `AggregateRating` into that product's schema. Don't fabricate — Google penalises this.

## 5. Hreflang

- Default pages: `nl` / `en` / `de` + `x-default → /` ✅
- Belgium pages: `nl-BE → /be` and `fr-BE → /fr` ✅ (regional)
- Germany country landing: `de → /de/cannabis-kaufen-deutschland` ✅
- Articles do not emit hreflang alternates because translations don't exist 1-to-1 — correct behaviour (avoids false alternates).

## 6. URLs

- Clean, extensionless, keyword-rich slugs (`/verschil-hasj-en-wiet`, `/cannabis-online-kaufen-deutschland`).
- Lowercase, hyphenated. ✅
- No tracking params in canonical URLs.

## 7. Internal linking

- **Topical clusters:** articles tagged with `lang` + `topic`; related-articles block picks same-language + same-topic first.
- **Country pages → cluster articles:** `/be` links to `wiet-online-bestellen-belgie` and `online-wiet-kopen-in-belgie`; `/fr` links to `acheter-weed-en-ligne-belgique`; `/de/cannabis-kaufen-deutschland` links to 3 German articles.
- **Product → product:** "More from this category" block on each product page (4 related).
- **Footer:** links to all country pages, info pages, and blog.
- **Gap:** product pages do **not** link to relevant blog articles. E.g. a Cali product could link to "Wat is Cali Weed?". This is a meaningful enhancement — see roadmap Week 6.

## 8. Mobile / responsiveness

- Viewport meta correct.
- Tested at 375px, 768px, 1280px — no horizontal overflow, hamburger nav, 2-column shop grid on phones.
- Touch targets ≥ 44px on mobile (filter selects, qty buttons, payment cards).
- **No PageSpeed Insights run yet** — I can't load that tool from here. Recommend running once and acting on Core Web Vitals findings. Likely culprits: Google Fonts (4 weights × 3 families is heavy), 9.4 MB of product images.

## 9. Page weight / performance hypothesis

- HTML file: ~600KB (large because of inlined logo PNG base64 + 130 products + 28 articles + L10N inline). One file is actually faster than many small ones over HTTPS.
- Images: lazy-loaded (`loading="lazy"`).
- Fonts: Google Fonts with `display=swap` — good.
- **Quick win:** convert the inlined logo base64 to a real SVG file (the SVG favicon already exists). Would shave ~30–40KB off every page.
- **No render-blocking JS** — script is at the end of `<body>` and Tidio loads `async`.

## 10. Accessibility & UX signals

- ARIA labels on nav, cart, drawer close.
- `alt` text on all product images.
- Focus outlines on form inputs.
- Age-gate text in footer + checkout checkbox.

## 11. Top concrete fixes (in priority order)

1. **Submit refreshed sitemap in GSC** (only takes 30 seconds; pushes the 12 new pages from the last batches into the crawl queue).
2. **Run PageSpeed Insights** for `/`, `/shop`, `/product/gelato-41`, fix any "poor" Core Web Vitals.
3. **Add product → article internal links** for the 5 categories (1–2 link mappings per category, programmatic in `pageProduct`).
4. **Replace inlined logo base64 with `/favicon.svg`** referenced normally — speeds up every page.
5. **Start collecting reviews** via Tidio after checkout, so we can add `AggregateRating` honestly later.

## 12. Things that are NOT site issues (so stop worrying about them)

- Rankings being slow to appear → normal for a new site; takes weeks–months.
- Cannabis ads being restricted on Google Ads → policy, not technical. Doesn't affect organic.
- The site occasionally showing `In stock` in raw HTML (e.g. in the product data array) → that's a string in JS, never rendered as text on Dutch pages. Verified.
