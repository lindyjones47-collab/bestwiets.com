#!/usr/bin/env python3
"""
Static SEO pre-renderer for bestwiets.com (a single-file SPA).

Why: GitHub Pages can't render the SPA server-side, so without this every deep
URL (products, articles, pages) would return a 404 status to crawlers with one
shared <title>/description. This script copies index.html once per route and
swaps in a per-page SEO block (title, description, canonical, OG/Twitter,
JSON-LD) between the <!--SEO:START--> / <!--SEO:END--> markers, writing a real
static file per URL so each returns 200 with its own meta. It also writes
sitemap.xml.

WORKFLOW: edit index.html (the template), then run `python generate.py`, then
commit. index.html stays the single source of truth.
"""
import json, os, re, datetime

SITE = "https://bestwiets.com"
OG_DEFAULT = SITE + "/images/2026/06/Tropicana-Cookies.png"
TODAY = datetime.date.today().isoformat()

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

def extract_array(html, name):
    marker = "const %s = " % name
    i = html.index(marker) + len(marker)
    arr, _ = json.JSONDecoder().raw_decode(html, i)
    return arr

PRODUCTS = extract_array(TEMPLATE, "PRODUCTS")
BLOG = extract_array(TEMPLATE, "BLOG")

# Page meta (kept in sync with _PAGE_SEO in index.html)
PAGES = {
    "home":            ("/",                 "Wiet Kopen & Online Bestellen | Cannabis & Hasj Bezorgd – WietStore",
                        "Wiet kopen en online bestellen bij WietStore. Premium cannabis, hasj en wietolie, discreet bezorgd in Nederland, België en Duitsland. Betaal met bank, Bitcoin of USDT."),
    "shop":            ("/shop",             "Wiet, Hasj & Cali Weed Kopen – Online Cannabis Shop | WietStore",
                        "Bekijk het volledige assortiment: wiet, hasj, cali weed, gruis en wietolie. Online bestellen en discreet bezorgd in Nederland, België en Duitsland."),
    "blog":            ("/blog",             "Blog – Wiet & Cannabis Gidsen | WietStore",
                        "Lees onze gidsen en nieuws over wiet kopen, hasj, bezorging en betalen met crypto."),
    "delivery":        ("/delivery",         "Bezorging & Verzending | WietStore",
                        "Discreet en geurloos bezorgd in Nederland, België, Duitsland en Frankrijk — vaak binnen 24 uur."),
    "about":           ("/about",            "Over WietStore | Online Cannabis Shop",
                        "Premium cannabis van Amsterdam-coffeeshopkwaliteit, veilig en discreet bezorgd in NL, BE en DE."),
    "returns":         ("/returns",          "Retouren & Terugbetalingen | WietStore",
                        "Lees ons retour- en terugbetalingsbeleid bij WietStore."),
    "contact":         ("/contact",          "Contact | WietStore",
                        "Vragen over je bestelling of bezorging? Neem contact op via e-mail of WhatsApp."),
    "bestelhandleiding":("/bestelhandleiding","Bestelhandleiding – Wiet Bestellen met Crypto | WietStore",
                        "Stap-voor-stap uitleg om wiet online te bestellen en veilig te betalen met crypto."),
    "voorwaarden":     ("/voorwaarden",      "Algemene Voorwaarden | WietStore",
                        "De algemene voorwaarden van WietStore."),
}

FAQ = [
    ("Hoe bestel ik wiet of hasj?", "Voeg de gewenste producten toe aan je winkelwagen en reken af. Zodra je betaling binnen is, wordt je bestelling verwerkt en discreet verzonden."),
    ("Is online wiet bestellen veilig?", "Ja. Alle producten worden geurloos en discreet verpakt en betrouwbaar bezorgd in Nederland, België en Duitsland."),
    ("Welke betaalmethoden accepteren jullie?", "Je kunt betalen via bankoverschrijving, Bitcoin (BTC) of USDT. Na het afrekenen nemen we contact met je op met de betaalgegevens."),
]

def crumb(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
                                for i, (n, u) in enumerate(items)]}

def seo_block(title, desc, path, og_image, jsonld, alts=None):
    url = SITE + path
    lines = [
        "<title>%s</title>" % esc(title),
        '<meta name="description" content="%s">' % esc(desc),
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<link rel="canonical" href="%s">' % url,
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="WietStore">',
        '<meta property="og:title" content="%s">' % esc(title),
        '<meta property="og:description" content="%s">' % esc(desc),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s">' % og_image,
        '<meta property="og:locale" content="nl_NL">',
        '<meta property="og:locale:alternate" content="de_DE">',
        '<meta property="og:locale:alternate" content="en_GB">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % esc(title),
        '<meta name="twitter:description" content="%s">' % esc(desc),
        '<meta name="twitter:image" content="%s">' % og_image,
    ]
    for hl, href in (alts or []):
        lines.append('<link rel="alternate" hreflang="%s" href="%s%s">' % (hl, SITE, href))
    for j in jsonld:
        lines.append('<script type="application/ld+json">%s</script>' % json.dumps(j, ensure_ascii=False))
    return "\n".join(lines)

MARKER = re.compile(r"<!--SEO:START-->.*?<!--SEO:END-->", re.S)

def write_route(out_path, title, desc, path, og_image, jsonld, alts=None):
    block = "<!--SEO:START-->\n" + seo_block(title, desc, path, og_image, jsonld, alts) + "\n<!--SEO:END-->"
    html = MARKER.sub(lambda m: block, TEMPLATE)
    full = os.path.join(ROOT, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True) if os.path.dirname(out_path) else None
    open(full, "w", encoding="utf-8").write(html)

# ---- Localization (key pages get /nl/ + /de/ versions with hreflang) ----
LOC_PAGES = ["home", "shop", "delivery", "about", "contact"]
def loc_url(lang, key):
    base = {"home": "", "shop": "/shop", "delivery": "/delivery", "about": "/about", "contact": "/contact"}[key]
    pre = ("/" + lang) if lang != "en" else ""
    if key == "home":
        return (pre + "/") if pre else "/"   # /nl/ , /de/ , / (folder index resolves with trailing slash)
    return pre + base                         # /shop , /nl/shop , ...
def alts_for(key):
    return [("en", loc_url("en", key)), ("nl", loc_url("nl", key)),
            ("de", loc_url("de", key)), ("x-default", loc_url("en", key))]
LOC_META = {
    "nl": {
        "home": ("Wiet Kopen & Online Bestellen | Cannabis & Hasj Bezorgd – WietStore", "Wiet kopen en online bestellen bij WietStore. Premium cannabis, hasj en wietolie, discreet bezorgd in Nederland, België en Duitsland. Betaal met bank, Bitcoin of USDT."),
        "shop": ("Wiet, Hasj & Cali Weed Kopen – Online Cannabis Shop | WietStore", "Bekijk het volledige assortiment: wiet, hasj, cali weed, gruis en wietolie. Online bestellen en discreet bezorgd in Nederland, België en Duitsland."),
        "delivery": ("Bezorging & Verzending | WietStore", "Discreet en geurloos bezorgd in Nederland, België, Duitsland en Frankrijk — vaak binnen 24 uur."),
        "about": ("Over WietStore | Online Cannabis Shop", "Premium cannabis van Amsterdam-coffeeshopkwaliteit, veilig en discreet bezorgd in NL, BE en DE."),
        "contact": ("Contact | WietStore", "Vragen over je bestelling of bezorging? Neem contact op via e-mail of WhatsApp."),
    },
    "de": {
        "home": ("Cannabis online kaufen & bestellen | Gras & Haschisch geliefert – WietStore", "Cannabis online kaufen bei WietStore. Premium Gras, Haschisch und Öl, diskret geliefert in die Niederlande, Belgien und Deutschland. Zahlung per Bank, Bitcoin oder USDT."),
        "shop": ("Gras, Haschisch & Cali Weed kaufen – Online Cannabis Shop | WietStore", "Entdecke das gesamte Sortiment: Gras, Haschisch, Cali Weed, Gruis und Öl. Online bestellen und diskret geliefert in NL, Belgien und Deutschland."),
        "delivery": ("Lieferung & Versand | WietStore", "Diskret und geruchsneutral geliefert in die Niederlande, Belgien, Deutschland und Frankreich — oft innerhalb von 24 Stunden."),
        "about": ("Über WietStore | Online Cannabis Shop", "Premium Cannabis in Amsterdamer Coffeeshop-Qualität, sicher und diskret geliefert in NL, BE und DE."),
        "contact": ("Kontakt | WietStore", "Fragen zu deiner Bestellung oder Lieferung? Kontaktiere uns per E-Mail oder WhatsApp."),
    },
}

urls = []  # (path, lastmod, priority)

# Pages (English)
for key, (path, title, desc) in PAGES.items():
    jsonld = []
    if key == "home":
        jsonld.append({"@context": "https://schema.org", "@type": "FAQPage",
                       "mainEntity": [{"@type": "Question", "name": q,
                                       "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]})
    out = "index.html" if key == "home" else "%s.html" % key
    alts = alts_for(key) if key in LOC_PAGES else None
    write_route(out, title, desc, path, OG_DEFAULT, jsonld, alts)
    urls.append((path, TODAY, "1.0" if key == "home" else ("0.9" if key == "shop" else "0.6")))

# Localized pages (/nl/*, /de/*)
for lang in ("nl", "de"):
    for key in LOC_PAGES:
        title, desc = LOC_META[lang][key]
        path = loc_url(lang, key)
        out = "%s/index.html" % lang if key == "home" else "%s/%s.html" % (lang, key)
        write_route(out, title, desc, path, OG_DEFAULT, [], alts_for(key))
        urls.append((path, TODAY, "0.8" if key in ("home", "shop") else "0.5"))

# Blog articles
for b in BLOG:
    path = "/" + b["slug"]
    title = "%s | WietStore Blog" % b["title"]
    img = SITE + b["img"]
    article = {"@context": "https://schema.org", "@type": "Article", "headline": b["title"],
               "image": img, "description": b["excerpt"],
               "author": {"@type": "Organization", "name": "WietStore"},
               "publisher": {"@type": "Organization", "name": "WietStore",
                             "logo": {"@type": "ImageObject", "url": SITE + "/favicon.svg"}},
               "mainEntityOfPage": SITE + path}
    bc = crumb([("Home", "/"), ("Blog", "/blog"), (b["title"], path)])
    write_route("%s.html" % b["slug"], title, b["excerpt"], path, img, [article, bc])
    urls.append((path, TODAY, "0.7"))

# Products
for p in PRODUCTS:
    path = "/product/" + p["slug"]
    title = "%s kopen – €%.2f | WietStore" % (p["name"], p["price"])
    desc = "%s online kopen bij WietStore. %s Discreet bezorgd in Nederland, België en Duitsland." % (p["name"], p["desc"])
    img = SITE + p["img"]
    product = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "image": img,
               "description": p["desc"], "category": p["cat"], "brand": {"@type": "Brand", "name": "WietStore"},
               "offers": {"@type": "Offer", "url": SITE + path, "price": "%.2f" % p["price"],
                          "priceCurrency": "EUR",
                          "availability": "https://schema.org/InStock" if p["stock"] == "In stock" else "https://schema.org/OutOfStock"}}
    bc = crumb([("Home", "/"), ("Shop", "/shop"), (p["name"], path)])
    write_route("product/%s.html" % p["slug"], title, desc, path, img, [product, bc])
    urls.append((path, TODAY, "0.8"))

# Sitemap
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, lastmod, prio in urls:
    sm.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (SITE, path, lastmod, prio))
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))

print("Generated %d pages + %d articles + %d products = %d routes" % (
    len(PAGES), len(BLOG), len(PRODUCTS), len(urls)))
print("Wrote sitemap.xml with %d URLs" % len(urls))
