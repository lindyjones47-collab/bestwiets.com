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
import json, math, os, re, datetime, hashlib, html

SITE = "https://bestwiets.com"
OG_DEFAULT = SITE + "/images/2026/06/Tropicana-Cookies.png"
TODAY = datetime.date.today().isoformat()
PRICE_VALID_UNTIL = "%d-12-31" % (datetime.date.today().year + 1)  # keeps Product offers "fresh" for Google

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

# Content-stable <lastmod>: a page's sitemap date only advances when ITS content
# actually changes (not on every rebuild). Prevents "everything changed today"
# from diluting the freshness signal Google uses for crawl scheduling.
_LM_PATH = os.path.join(ROOT, ".sitemap-lastmod.json")
try:
    _LM_STORE = json.load(open(_LM_PATH, encoding="utf-8"))
except Exception:
    _LM_STORE = {}
PAGE_LASTMOD = {}
def _lastmod(path, *parts):
    sig = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
    prev = _LM_STORE.get(path)
    date = prev["d"] if (prev and prev.get("h") == sig) else TODAY
    _LM_STORE[path] = {"h": sig, "d": date}
    PAGE_LASTMOD[path] = date
    return date

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

DESC_DE = json.loads(re.search(r"const DESC_DE = (\{.*?\});\n", TEMPLATE, re.S).group(1))
ATTR_DE = json.loads(re.search(r"const ATTR_DE = (\{.*?\});\n", TEMPLATE, re.S).group(1))
CAT_DE = json.loads(re.search(r"const CAT_DE = (\{.*?\});\n", TEMPLATE, re.S).group(1))
CHROME_DE = json.loads(re.search(r"const _CHROME_DE = (\{.*?\});\n", TEMPLATE, re.S).group(1))

def product_meta_desc_de(p):  # mirrors _metaDescDe() in index.html
    first = DESC_DE.get(p["slug"], p["desc"]).split(". ")[0].strip().rstrip(".")
    md = "%s kaufen bei WietStore. %s. Diskret geliefert nach Deutschland, Österreich & in die Schweiz." % (p["name"], first)
    if len(md) > 158:
        md = md[:155].rsplit(" ", 1)[0] + "…"
    return md

def _de_chrome(html):
    """German labels + German URLs in the static header of German pages (mirrors _localizeChrome)."""
    h0 = html.index('<header class="site">'); h1 = html.index("</header>", h0)
    hd = html[h0:h1]
    for nl, de in CHROME_DE.items():
        hd = re.sub(r">(\s*)%s(\s*)<" % re.escape(esc(nl).replace("&quot;", '"')), lambda m: ">%s%s%s<" % (m.group(1), esc(de), m.group(2)), hd)
    hd = hd.replace('href="/shop"', 'href="/de/shop"').replace('href="/" data-nav="home"', 'href="/de/" data-nav="home"')
    for k in ("about", "delivery", "contact"):
        hd = hd.replace('href="/%s" data-nav="%s"' % (k, k), 'href="/de/%s" data-nav="%s"' % (k, k))
    return html[:h0] + hd + html[h1:]

def product_meta_desc(p):
    """Concise, SERP-friendly meta description (~150 chars) — first sentence only."""
    first = p["desc"].split(". ")[0].strip().rstrip(".")
    md = "%s kopen bij WietStore. %s. Discreet bezorgd in NL, België & Duitsland." % (p["name"], first)
    if len(md) > 158:
        md = md[:155].rsplit(" ", 1)[0] + "…"
    return md

def extract_array(html, name):
    marker = "const %s = " % name
    i = html.index(marker) + len(marker)
    arr, _ = json.JSONDecoder().raw_decode(html, i)
    return arr

PRODUCTS = extract_array(TEMPLATE, "PRODUCTS")
BLOG = extract_array(TEMPLATE, "BLOG")
CITY = extract_array(TEMPLATE, "CITY")
WEIGHT_LADDER = extract_array(TEMPLATE, "WEIGHT_LADDER")
def _jsround(x):  # same result as JS Math.round(x*100)/100 in index.html
    return math.floor(x * 100 + 0.5) / 100
for _p in PRODUCTS:  # mirrors the hydration in index.html
    if _p.get("ppg"):
        _p["variants"] = []
        for _w in WEIGHT_LADDER:
            _pg = _jsround(_p["ppg"] * (1 - _w["off"]))
            _p["variants"].append({"label": "%d g" % _w["g"], "g": _w["g"], "pg": _pg,
                                   "price": _jsround(_pg * _w["g"]), "sku": "-%dG" % _w["g"]})
        _p["price"] = _p["variants"][0]["price"]

# ---- City local-SEO landing pages (DE/AT/CH/FR) ----
CITY_COUNTRY = {
 "de": {"name": "Deutschland", "gpath": "/de/cannabis-kaufen-deutschland", "hl": "de-DE", "verb": "Weed", "home": "Startseite", "lang": "de"},
 "at": {"name": "Österreich", "gpath": "/cannabis-kaufen-oesterreich", "hl": "de-AT", "verb": "Cannabis", "home": "Startseite", "lang": "de"},
 "ch": {"name": "Schweiz", "gpath": "/cannabis-kaufen-schweiz", "hl": "de-CH", "verb": "Cannabis", "home": "Startseite", "lang": "de"},
 "fr": {"name": "France", "gpath": "/acheter-cannabis-france", "hl": "fr-FR", "verb": "cannabis", "home": "Accueil", "lang": "fr"},
}
def _city_links(country_key):
    items = [c for c in CITY if c["c"] == country_key]
    if not items:
        return ""
    lis = "".join('<li><a href="/%s">%s</a></li>' % (esc(c["s"]), esc(c["n"])) for c in items)
    return '<h2>%s</h2><ul class="pr-list">%s</ul>' % ("Villes de livraison" if country_key == "fr" else "Lieferstädte", lis)
def _city_nearby(c):
    same = [x for x in CITY if x["c"] == c["c"]]
    if len(same) < 2:
        return []
    pos = next(i for i, x in enumerate(same) if x["s"] == c["s"])
    out, k = [], 1
    while len(out) < min(4, len(same) - 1) and k <= len(same):
        x = same[(pos + k) % len(same)]
        if x["s"] != c["s"] and x not in out:
            out.append(x)
        k += 1
    return out
def city_meta(c):
    CC = CITY_COUNTRY[c["c"]]
    if c["c"] == "fr":
        return ("Acheter du cannabis à %s | WietStore" % c["n"],
                "Acheter du cannabis en ligne et se faire livrer à %s (%s). Weed, haschich & pré-roulés premium, livraison discrète." % (c["n"], c["r"]))
    return ("%s kaufen in %s | WietStore" % (CC["verb"], c["n"]),
            "%s online kaufen und nach %s (%s) liefern lassen. Premium Cannabis, Haschisch & Pre-Rolls, diskret in wenigen Werktagen." % (CC["verb"], c["n"], c["r"]))
def _city_featured(c):
    pre = [p for p in PRODUCTS if p.get("cat") == "Prerolls"]
    idx = CITY.index(c)
    return [pre[(idx + k) % len(pre)] for k in range(3)] if pre else []
def city_body(c):
    CC = CITY_COUNTRY[c["c"]]
    city, region = esc(c["n"]), esc(c["r"])
    featlinks = ", ".join('<a href="%s/product/%s">%s</a>' % ("" if c["c"] == "fr" else "/de", esc(p["slug"]), esc(p["name"])) for p in _city_featured(c))
    nb = " &middot; ".join('<a href="/%s">%s</a>' % (esc(x["s"]), esc(x["n"])) for x in _city_nearby(c))
    if c["c"] == "fr":
        return (
            '<section class="pr"><h1>Acheter du cannabis à %s</h1>'
            '<p>Acheter du cannabis à %s et se faire livrer discrètement ? Chez WietStore, commandez en ligne du weed, du haschich et des joints pré-roulés de qualité coffeeshop d\'Amsterdam — livrés à %s et dans toute la région %s.</p>'
            '<h2>Commander à %s</h2><p>Choisissez vos variétés dans la boutique, ajoutez-les au panier et indiquez votre adresse à %s. Payez par virement, Bitcoin ou USDT ; dès réception du paiement, la commande est expédiée.</p>'
            '<h2>Livraison à %s et en %s</h2><p>Les envois depuis les Pays-Bas atteignent %s généralement en quelques jours ouvrés. Chaque colis est emballé hermétiquement et sans odeur.</p>'
            '<h2>Populaire à %s</h2><p>Parmi les favoris : %s. Découvrez aussi tous nos <a href="/prerolls">joints pré-roulés</a> ou <a href="%s">notre offre en France</a>.</p>'
            '<h2>Questions fréquentes</h2>'
            '<h3>Livrez-vous à %s ?</h3><p>Oui, nous livrons discrètement et sans odeur à %s et dans toute la région %s, généralement en quelques jours ouvrés.</p>'
            '<h3>Comment payer ma commande à %s ?</h3><p>Vous payez en toute sécurité par virement, Bitcoin ou USDT. La commande est expédiée dès réception du paiement.</p>'
            '<p><strong>À proximité :</strong> %s</p>'
            '<p><a href="/shop">Voir tout l\'assortiment &rarr;</a></p>'
            '<p style="color:#6f6f68;font-size:.85rem;">Réservé aux adultes de 18 ans et plus. Respectez la législation en vigueur et consommez de manière responsable.</p></section>'
        ) % (city, city, city, region, city, city, city, region, city, city, featlinks, CC["gpath"], city, city, region, city, nb)
    verb = CC["verb"]
    return (
        '<section class="pr"><h1>%s kaufen in %s</h1>'
        '<p>%s nach %s bestellen und diskret liefern lassen? Bei WietStore bestellst du online Cannabis, Haschisch und vorgerollte Joints in Amsterdamer Coffeeshop-Qualität — zuverlässig geliefert nach %s und in ganz %s.</p>'
        '<h2>So bestellst du nach %s</h2><p>Wähle deine Sorten im Shop, lege sie in den Warenkorb und gib an der Kasse deine Lieferadresse in %s ein. Bezahle per Banküberweisung, Bitcoin oder USDT; nach Zahlungseingang wird deine Bestellung versandt.</p>'
        '<h2>Lieferung nach %s und %s</h2><p>Sendungen aus den Niederlanden erreichen %s in der Regel innerhalb weniger Werktage. Jede Lieferung wird luftdicht und geruchsneutral verpackt — von außen ist nicht erkennbar, was im Paket ist.</p>'
        '<h2>Beliebt in %s</h2><p>Besonders gefragt: %s. Entdecke auch alle <a href="/prerolls">vorgerollten Joints</a> oder das gesamte <a href="%s">%s-Sortiment</a>.</p>'
        '<h2>Häufige Fragen</h2>'
        '<h3>Liefert WietStore nach %s?</h3><p>Ja, wir liefern diskret und geruchsneutral nach %s und in die gesamte Region %s, in der Regel innerhalb weniger Werktage.</p>'
        '<h3>Wie bezahle ich meine Bestellung nach %s?</h3><p>Du bezahlst sicher per Banküberweisung, Bitcoin oder USDT. Nach Zahlungseingang wird deine Bestellung versandt.</p>'
        '<p><strong>Auch in der Nähe:</strong> %s</p>'
        '<p><a href="/shop">Komplettes Sortiment ansehen &rarr;</a></p>'
        '<p style="color:#6f6f68;font-size:.85rem;">Nur für Erwachsene ab 18 Jahren. Bitte beachte die geltenden Gesetze und konsumiere verantwortungsbewusst.</p></section>'
    ) % (verb, city, verb, city, city, region, city, city, city, region, city, city, featlinks, CC["gpath"], CC["name"], city, city, region, city, nb)
def city_jsonld(c, path):
    CC = CITY_COUNTRY[c["c"]]
    if c["c"] == "fr":
        faq = [("Livrez-vous à %s ?" % c["n"], "Oui, nous livrons discrètement et sans odeur à %s et dans toute la région %s, généralement en quelques jours ouvrés." % (c["n"], c["r"])),
               ("Comment payer ma commande à %s ?" % c["n"], "Vous payez en toute sécurité par virement, Bitcoin ou USDT. La commande est expédiée dès réception du paiement.")]
    else:
        faq = [("Liefert WietStore nach %s?" % c["n"], "Ja, wir liefern diskret und geruchsneutral nach %s und in die gesamte Region %s, in der Regel innerhalb weniger Werktage." % (c["n"], c["r"])),
               ("Wie bezahle ich meine Bestellung nach %s?" % c["n"], "Du bezahlst sicher per Banküberweisung, Bitcoin oder USDT. Nach Zahlungseingang wird deine Bestellung versandt.")]
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": "Cannabis delivery",
               "provider": {"@type": "Organization", "name": "WietStore", "url": SITE},
               "areaServed": {"@type": "City", "name": c["n"]}, "url": SITE + path}
    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    bc = crumb([(CC["home"], "/"), (CC["name"], CC["gpath"]), (c["n"], path)])
    return [service, faq_schema, bc]

# Page meta (kept in sync with _PAGE_SEO in index.html)
PAGES = {
    "home":            ("/",                 "Wiet Kopen & Online Bestellen | Cannabis & Hasj Bezorgd – WietStore",
                        "Wiet online kopen bij WietStore: premium cannabis, hasj en wietolie. Discreet bezorgd in NL, België & Duitsland. Betaal met bank, Bitcoin of USDT."),
    "shop":            ("/shop",             "Wiet, Hasj & Cali Weed Kopen – Online Cannabis Shop | WietStore",
                        "Bekijk het volledige assortiment: wiet, hasj, cali weed, gruis en wietolie. Online bestellen en discreet bezorgd in Nederland, België en Duitsland."),
    "blog":            ("/blog",             "Blog – Wiet & Cannabis Gidsen | WietStore",
                        "Lees onze gidsen en nieuws over wiet kopen, hasj, bezorging en betalen met crypto."),
    "delivery":        ("/delivery",         "Bezorging & Verzending | WietStore",
                        "Discreet en geurloos bezorgd in Nederland, België, Duitsland en Frankrijk — vaak binnen 24 uur."),
    "about":           ("/about",            "Over WietStore | Online Cannabis Shop",
                        "Premium cannabis van Amsterdam-coffeeshopkwaliteit, veilig en discreet bezorgd in NL, BE en DE."),
    "returns":         ("/returns",          "Retouren & Terugbetalingen | WietStore",
                        "Lees het retour- en terugbetalingsbeleid van WietStore: hoe je een beschadigde of onjuiste bestelling meldt en wat je kunt verwachten."),
    "contact":         ("/contact",          "Contact | WietStore",
                        "Vragen over je bestelling of bezorging? Neem contact op via e-mail of WhatsApp."),
    "bestelhandleiding":("/bestelhandleiding","Bestelhandleiding – Wiet Bestellen met Crypto | WietStore",
                        "Stap-voor-stap uitleg om wiet online te bestellen en veilig te betalen met crypto."),
    "voorwaarden":     ("/voorwaarden",      "Algemene Voorwaarden | WietStore",
                        "De algemene voorwaarden van WietStore: bestellen, betalen, leeftijdsvereisten en je verantwoordelijkheden als klant. Lees ze voor je bestelt."),
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
APP_MARKER = re.compile(r"<!--APP:START-->.*?<!--APP:END-->", re.S)

ROUTE_META = {}  # path -> (title, desc, lang); feeds sitemap.md / llms.txt
ROUTE_BODY = {}  # path -> pre-rendered body HTML; feeds the .md copies

def write_route(out_path, title, desc, path, og_image, jsonld, alts=None, lang="nl", body=""):
    ROUTE_META[path] = (title, desc, lang)
    ROUTE_BODY[path] = body or ""
    # record a content-stable lastmod (title+desc+body drive the freshness signal)
    _lastmod(path, title, desc, body or "")
    block = "<!--SEO:START-->\n" + seo_block(title, desc, path, og_image, jsonld, alts) + "\n<!--SEO:END-->"
    html = MARKER.sub(lambda m: block, TEMPLATE)
    # Pre-render the route's real content into <main id="app"> so crawlers see it
    # without executing JS. The SPA overwrites #app.innerHTML on load, so users
    # still get the interactive version — this block is purely for first paint + SEO.
    app = "<!--APP:START-->\n" + (body or "") + "\n<!--APP:END-->"
    html = APP_MARKER.sub(lambda m: app, html)
    if lang != "nl":
        html = html.replace('<html lang="nl">', '<html lang="%s">' % lang, 1)
    if lang == "de":
        html = _de_chrome(html)
        html = html.replace('<meta property="og:locale" content="nl_NL">', '<meta property="og:locale" content="de_DE">', 1)
        html = html.replace('<meta property="og:locale:alternate" content="de_DE">', '<meta property="og:locale:alternate" content="nl_NL">', 1)
    full = os.path.join(ROOT, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True) if os.path.dirname(out_path) else None
    open(full, "w", encoding="utf-8").write(html)

# ---- Localization (key pages get /nl/ + /de/ versions with hreflang) ----
LOC_PAGES = ["home", "shop", "delivery", "about", "contact"]
def loc_url(lang, key):
    base = {"home": "", "shop": "/shop", "delivery": "/delivery", "about": "/about", "contact": "/contact"}[key]
    pre = ("/" + lang) if lang != "nl" else ""   # Dutch is the default (bare); en/de are prefixed
    if key == "home":
        return (pre + "/") if pre else "/"   # /en/ , /de/ , / (folder index resolves with trailing slash)
    return pre + base                         # /shop , /en/shop , ...
def alts_for(key):
    return [("nl", loc_url("nl", key)), ("en", loc_url("en", key)),
            ("de", loc_url("de", key)), ("x-default", loc_url("nl", key))]
LOC_META = {
    "en": {
        "home": ("Buy Weed Online | Cannabis & Hash Delivered – WietStore", "Buy weed and hash online at WietStore: premium cannabis, hash and oil, discreetly delivered across NL, Belgium & Germany. Pay by bank, Bitcoin or USDT."),
        "shop": ("Buy Weed, Hash & Cali Weed – Online Cannabis Shop | WietStore", "Browse the full range: weed, hash, cali weed, grit and cannabis oil. Order online and get it discreetly delivered in NL, BE and DE."),
        "delivery": ("Delivery & Shipping | WietStore", "Discreet, odourless delivery across the Netherlands, Belgium, Germany and France — often within 24 hours."),
        "about": ("About WietStore | Online Cannabis Shop", "Premium cannabis of Amsterdam coffeeshop quality, delivered safely and discreetly in NL, BE and DE."),
        "contact": ("Contact | WietStore", "Questions about your order or delivery? Get in touch by email or WhatsApp."),
    },
    "de": {
        "home": ("Cannabis online kaufen | Gras & Haschisch bestellen – WietStore", "Cannabis online kaufen bei WietStore: Premium Gras, Haschisch und Öl. Diskret geliefert in NL, Belgien & Deutschland. Zahlung per Bank, Bitcoin oder USDT."),
        "shop": ("Gras, Haschisch & Cali Weed kaufen | Cannabis Shop – WietStore", "Entdecke das gesamte Sortiment: Gras, Haschisch, Cali Weed, Gruis und Öl. Online bestellen und diskret geliefert in NL, Belgien und Deutschland."),
        "delivery": ("Lieferung & Versand | WietStore", "Diskret und geruchsneutral geliefert in die Niederlande, Belgien, Deutschland und Frankreich — oft innerhalb von 24 Stunden."),
        "about": ("Über WietStore | Online Cannabis Shop", "Premium Cannabis in Amsterdamer Coffeeshop-Qualität, sicher und diskret geliefert in NL, BE und DE."),
        "contact": ("Kontakt | WietStore", "Fragen zu deiner Bestellung oder Lieferung? Kontaktiere uns per E-Mail oder WhatsApp."),
    },
}

# ============================================================================
#  Pre-rendered <main> body per route
#  Real, unique, crawlable HTML so Googlebot never sees an empty SPA shell.
# ============================================================================
def _crumb_html(items):
    parts = []
    for i, (n, u) in enumerate(items):
        if i:
            parts.append('<span aria-hidden="true"> › </span>')
        parts.append('<a href="%s">%s</a>' % (u, esc(n)) if u else '<span>%s</span>' % esc(n))
    return '<nav class="pr-crumb" aria-label="Kruimelpad">%s</nav>' % "".join(parts)

def _product_links(items=None, limit=None, lang="nl"):
    items = items if items is not None else PRODUCTS
    if limit:
        items = items[:limit]
    de = lang == "de"
    return '<ul class="pr-list">%s</ul>' % "".join(
        '<li><a href="%s/product/%s">%s %s</a> &mdash; %s&euro;%.2f</li>' % ("/de" if de else "", esc(p["slug"]), esc(p["name"]), "kaufen" if de else "kopen",
                                                                       ("ab " if de else "vanaf ") if p.get("variants") else "", p["price"])
        for p in items)

def _article_links():
    return '<ul class="pr-list">%s</ul>' % "".join(
        '<li><a href="/%s">%s</a></li>' % (esc(b["slug"]), esc(b["title"])) for b in BLOG)

MIN_ORDER = int(re.search(r'const MIN_ORDER\s*=\s*(\d+)', TEMPLATE).group(1))

def _related_html(p):  # same selection as the SPA's pageProduct (same category, first 4)
    rel = [x for x in PRODUCTS if x.get('cat') == p.get('cat') and x['slug'] != p['slug']][:4]
    if not rel:
        return ''
    return '<h2>Ook interessant</h2>' + _product_links(rel)

def render_product_de(p):
    path = "/de/product/" + p["slug"]
    specs = []
    if p.get("thc"):
        specs.append("<li><strong>THC:</strong> %s</li>" % esc(p["thc"]))
    for label, key in (("Geschmack", "flavors"), ("Wirkung", "effects"), ("Medizinisch", "medicinal")):
        if p.get(key):
            specs.append("<li><strong>%s:</strong> %s</li>" % (label, esc(", ".join(ATTR_DE.get(v, v) for v in p[key]))))
    specs_html = ('<ul class="pr-specs">%s</ul>' % "".join(specs)) if specs else ""
    avail = "Auf Lager" if p.get("stock") == "In stock" else "Vorübergehend ausverkauft"
    variants_html = ""
    if p.get("variants"):
        _is_qty = "stuks" in p["variants"][0]["label"].lower()
        lis = "".join("<li>%s &mdash; &euro;%.2f%s</li>" % (esc(re.sub(r"(?i)\bstuks?\b", "Stück", v["label"])), v["price"], " (&euro;%.2f/g)" % v["pg"] if v.get("pg") else "") for v in p["variants"])
        variants_html = '<p><strong>%s:</strong></p><ul class="pr-specs">%s</ul>' % (
            "Verfügbare Gewichte" if p.get("ppg") else ("Verfügbare Mengen" if _is_qty else "Verfügbare Varianten"), lis)
    rel = [x for x in PRODUCTS if x.get("cat") == p.get("cat") and x["slug"] != p["slug"]][:4]
    return (
        '<article class="pr">'
        + _crumb_html([("Startseite", "/de/"), ("Shop", "/de/shop"), (p["name"], path)])
        + "<h1>%s kaufen</h1>" % esc(p["name"])
        + '<img src="%s" alt="%s kaufen" width="480" height="480" loading="eager">' % (esc(p["img"]), esc(p["name"]))
        + '<p class="pr-price"><strong>%s&euro;%.2f</strong> &middot; %s &middot; %s</p>' % ("ab " if p.get("variants") else "", p["price"], esc(CAT_DE.get(p.get("cat"), p.get("cat", ""))), avail)
        + "<p>%s</p>" % esc(DESC_DE.get(p["slug"], p["desc"]))
        + specs_html + variants_html
        + ("<p>Erhältlich von 3 bis 100 Gramm. " if p.get("ppg") else "<p>") + "Diskret und geruchsneutral geliefert nach Deutschland, Österreich, in die Schweiz, nach Frankreich, Belgien und in die Niederlande.</p>"
        + "<p>Versandkosten: Deutschland, Österreich, Schweiz und andere europäische Länder &euro;20, Niederlande &euro;15 (Amsterdam &euro;10). Mindestbestellwert &euro;%d. Bezahlung per Banküberweisung, Bitcoin, USDT oder Litecoin.</p>" % MIN_ORDER
        + (("<h2>Das könnte dir auch gefallen</h2>" + _product_links(rel, lang="de")) if rel else "")
        + '<p><a href="/de/shop">Zum gesamten Sortiment</a> &middot; <a href="/de/delivery">Lieferung &amp; Versand</a> &middot; <a href="/de/cannabis-kaufen-deutschland">Cannabis kaufen in Deutschland</a></p>'
        + "</article>"
    )

def render_product(p):
    path = "/product/" + p["slug"]
    specs = []
    for label, key in (("THC", "thc"), ("Smaak", "flavors"), ("Effect", "effects"), ("Medicinaal", "medicinal")):
        v = p.get(key)
        if v:
            specs.append("<li><strong>%s:</strong> %s</li>" % (label, esc(", ".join(v) if isinstance(v, list) else v)))
    specs_html = ('<ul class="pr-specs">%s</ul>' % "".join(specs)) if specs else ""
    avail = "Op voorraad" if p.get("stock") == "In stock" else "Tijdelijk uitverkocht"
    variants_html = ""
    price_prefix = ""
    if p.get("variants"):
        price_prefix = "vanaf "
        _is_qty = "stuks" in p["variants"][0]["label"].lower()
        lis = "".join("<li>%s &mdash; &euro;%.2f%s</li>" % (esc(v["label"]), v["price"], " (&euro;%.2f/g)" % v["pg"] if v.get("pg") else "") for v in p["variants"])
        variants_html = '<p><strong>%s:</strong></p><ul class="pr-specs">%s</ul>' % (
            "Beschikbare gewichten" if p.get("ppg") else ("Beschikbare aantallen" if _is_qty else "Beschikbare varianten"), lis)
    return (
        '<article class="pr">'
        + _crumb_html([("Home", "/"), ("Shop", "/shop"), (p["name"], path)])
        + "<h1>%s kopen</h1>" % esc(p["name"])
        + '<img src="%s" alt="%s kopen" width="480" height="480" loading="eager">' % (esc(p["img"]), esc(p["name"]))
        + '<p class="pr-price"><strong>%s&euro;%.2f</strong> &middot; %s &middot; %s</p>' % (price_prefix, p["price"], esc(p.get("cat", "")), avail)
        + "<p>%s</p>" % esc(p["desc"])
        + specs_html
        + variants_html
        + ("<p>Verkrijgbaar van 3 tot 100 gram. " if p.get("ppg") else "<p>") + "Discreet en geurloos bezorgd in Nederland, Belgi&euml;, Duitsland, Oostenrijk, Zwitserland en Frankrijk.</p>"
        + "<p>Bezorgkosten: Amsterdam &euro;10, rest van Nederland &euro;15, overige Europese landen &euro;20. Minimale bestelwaarde &euro;%d. Betalen via bankoverschrijving, Bitcoin, USDT of Litecoin.</p>" % MIN_ORDER
        + _related_html(p)
        + '<p><a href="/shop">Bekijk het volledige assortiment</a> &middot; <a href="/bestelhandleiding">Bestelhandleiding</a> &middot; <a href="/delivery">Bezorging &amp; verzending</a></p>'
        + "</article>"
    )

def render_article(b):
    path = "/" + b["slug"]
    back = {"nl": ("&larr; Terug naar de blog", "Bekijk de shop"),
            "fr": ("&larr; Retour au blog", "Voir la boutique"),
            "de": ("&larr; Zurück zum Blog", "Zum Shop"),
            "en": ("&larr; Back to the blog", "Visit the shop")}.get(b.get("lang", "nl"))
    return (
        '<article class="pr">'
        + _crumb_html([("Home", "/"), ("Blog", "/blog"), (b["title"], path)])
        + "<h1>%s</h1>" % esc(b["title"])
        + '<img src="%s" alt="%s" width="480" height="270" loading="eager">' % (esc(b["img"]), esc(b["title"]))
        + '<div class="pr-body">%s</div>' % b["html"]
        + '<p><a href="/blog">%s</a> &middot; <a href="/shop">%s</a></p>' % back
        + "</article>"
    )

# Authored intro content for the static / country pages (H1 + paragraphs).
# Paragraphs may contain trusted inline HTML links, so they are NOT escaped.
PAGE_CONTENT = {
    "nl": {
        "home": ("Wiet kopen en online bestellen bij WietStore", [
            "Welkom bij WietStore, jouw betrouwbare adres om <strong>wiet online te kopen en te bestellen</strong>. Wij bieden premium cannabis, hasj, cali weed en wietolie van Amsterdamse coffeeshopkwaliteit, discreet en geurloos bezorgd in Nederland, Belgi&euml; en Duitsland.",
            "Betaal eenvoudig via bankoverschrijving, Bitcoin of USDT. Bekijk het volledige aanbod in de <a href=\"/shop\">shop</a>, lees meer over onze <a href=\"/delivery\">discrete bezorging</a> of raadpleeg de <a href=\"/bestelhandleiding\">bestelhandleiding</a>.",
            "Populaire producten:"]),
        "shop": ("Wiet, hasj &amp; cali weed kopen", [
            "Bekijk het volledige assortiment van WietStore: <strong>wiet, hasj, cali weed, gruis en wietolie</strong>. Alle producten worden discreet en geurloos bezorgd in Nederland, Belgi&euml; en Duitsland. Kies je gewicht van 3 tot 100 gram.",
            "Klik op een product voor de volledige beschrijving, THC-gehalte, smaak en effect:"]),
        "blog": ("Blog &ndash; wiet &amp; cannabis gidsen", [
            "Lees onze gidsen en nieuws over <strong>wiet kopen, hasj, bezorging en betalen met crypto</strong>. Praktische informatie voor iedereen die veilig en discreet cannabis online wil bestellen.",
            "Alle artikelen:"]),
        "delivery": ("Bezorging &amp; verzending", [
            "WietStore bezorgt <strong>discreet en geurloos</strong> in Nederland, Belgi&euml;, Duitsland en Frankrijk. Bestellingen binnen Nederland worden vaak al binnen 24 uur geleverd; naar Belgi&euml; en Duitsland duurt het doorgaans 2&ndash;4 werkdagen.",
            "Alle pakketten worden neutraal en reukdicht verpakt, zonder verwijzing naar de inhoud. De bezorgkosten bedragen &euro;10 in Amsterdam, &euro;15 naar andere Nederlandse steden en &euro;20 naar overige Europese landen. De minimale bestelwaarde is &euro;100.",
            "Vragen over je bezorging? Neem <a href=\"/contact\">contact</a> met ons op of bekijk de <a href=\"/shop\">shop</a>."]),
        "about": ("Over WietStore", [
            "WietStore is een in Nederland gevestigde cannabisshop die premium wiet, hasj en wietolie van <strong>Amsterdamse coffeeshopkwaliteit</strong> levert aan klanten in Nederland, Belgi&euml;, Duitsland en Frankrijk.",
            "Wij richten ons op productkwaliteit, discrete bezorging en goede klantvoorlichting. Elk product wordt zorgvuldig geselecteerd en voorzien van een eerlijke beschrijving met THC-gehalte, smaak en effect.",
            "Bekijk ons <a href=\"/shop\">assortiment</a> of lees onze <a href=\"/blog\">gidsen</a>."]),
        "returns": ("Retouren &amp; terugbetalingen", [
            "Door de aard van onze producten kunnen geopende of gebruikte artikelen om hygi&euml;ne- en veiligheidsredenen niet worden geretourneerd.",
            "Is er iets mis met je bestelling &mdash; bijvoorbeeld een beschadigd of onjuist geleverd product &mdash; neem dan binnen 48 uur na ontvangst <a href=\"/contact\">contact</a> met ons op met je bestelnummer. We zoeken samen naar een passende oplossing."]),
        "contact": ("Contact", [
            "Vragen over je bestelling, bezorging of betaling? Ons team helpt je graag.",
            "E-mail: <a href=\"mailto:bestwiets@outlook.com\">bestwiets@outlook.com</a><br>WhatsApp: <a href=\"https://wa.me/31635237086\">+31 6 35237086</a>",
            "We reageren doorgaans binnen enkele uren. Vermeld bij vragen over een bestaande bestelling altijd je bestelnummer."]),
        "bestelhandleiding": ("Bestelhandleiding &ndash; wiet bestellen met crypto", [
            "Wiet bestellen bij WietStore is eenvoudig. Volg deze stappen:",
            "<strong>1.</strong> Kies je producten in de <a href=\"/shop\">shop</a> en voeg ze toe aan je winkelwagen (minimale bestelwaarde &euro;100).<br><strong>2.</strong> Ga naar afrekenen en vul je bezorggegevens en gewenste bezorgregio in.<br><strong>3.</strong> Kies je betaalmethode: bankoverschrijving, Bitcoin of USDT.<br><strong>4.</strong> Plaats je bestelling &mdash; je ontvangt een bevestiging per e-mail en wij nemen contact op met de betaalgegevens.<br><strong>5.</strong> Na ontvangst van je betaling wordt je bestelling discreet verzonden.",
            "Meer weten over de bezorging? Bekijk de <a href=\"/delivery\">bezorgpagina</a>."]),
        "voorwaarden": ("Algemene voorwaarden", [
            "Door een bestelling te plaatsen bij WietStore ga je akkoord met onze algemene voorwaarden. Je verklaart meerderjarig te zijn volgens de wetgeving in jouw land.",
            "WietStore levert uitsluitend aan volwassen klanten. Je bent zelf verantwoordelijk voor het naleven van de lokale wet- en regelgeving die op jou van toepassing is. Prijzen en beschikbaarheid kunnen zonder voorafgaande kennisgeving wijzigen.",
            "Vragen over deze voorwaarden? Neem <a href=\"/contact\">contact</a> met ons op."]),
    },
    "en": {
        "home": ("Buy weed and order cannabis online at WietStore", [
            "Welcome to WietStore, your trusted place to <strong>buy weed online</strong>. We offer premium cannabis, hash, cali weed and cannabis oil of Amsterdam coffeeshop quality, delivered discreetly and odourlessly across the Netherlands, Belgium and Germany.",
            "Pay easily by bank transfer, Bitcoin or USDT. Browse the full range in the <a href=\"/en/shop\">shop</a> or read about our <a href=\"/en/delivery\">discreet delivery</a>.",
            "Popular products:"]),
        "shop": ("Buy weed, hash &amp; cali weed", [
            "Browse WietStore's full range: <strong>weed, hash, cali weed, grit and cannabis oil</strong>. Everything is delivered discreetly and odourlessly across the Netherlands, Belgium and Germany. Choose your weight from 3 to 100 grams.",
            "Click a product for the full description, THC level, flavour and effect:"]),
        "delivery": ("Delivery &amp; shipping", [
            "WietStore delivers <strong>discreetly and odourlessly</strong> across the Netherlands, Belgium, Germany and France. Orders within the Netherlands often arrive within 24 hours; delivery to Belgium and Germany usually takes 2&ndash;4 working days.",
            "Every parcel is packed neutrally and odour-proof, with no reference to the contents. Have a question? <a href=\"/en/contact\">Contact us</a> or visit the <a href=\"/en/shop\">shop</a>."]),
        "about": ("About WietStore", [
            "WietStore is a Netherlands-based cannabis shop delivering premium weed, hash and cannabis oil of <strong>Amsterdam coffeeshop quality</strong> to customers in the Netherlands, Belgium, Germany and France.",
            "We focus on product quality, discreet delivery and clear customer information. Browse our <a href=\"/en/shop\">range</a> to learn more."]),
        "contact": ("Contact", [
            "Questions about your order, delivery or payment? Our team is happy to help.",
            "Email: <a href=\"mailto:bestwiets@outlook.com\">bestwiets@outlook.com</a><br>WhatsApp: <a href=\"https://wa.me/31635237086\">+31 6 35237086</a>",
            "We usually reply within a few hours. For questions about an existing order, please include your order number."]),
    },
    "de": {
        "home": ("Cannabis online kaufen und bestellen bei WietStore", [
            "Willkommen bei WietStore, deiner vertrauensw&uuml;rdigen Adresse, um <strong>Cannabis online zu kaufen</strong>. Wir bieten Premium-Gras, Haschisch, Cali Weed und Cannabis&ouml;l in Amsterdamer Coffeeshop-Qualit&auml;t, diskret und geruchsneutral geliefert in die Niederlande, nach Belgien und Deutschland.",
            "Bezahle bequem per Bank&uuml;berweisung, Bitcoin oder USDT. Entdecke das gesamte Sortiment im <a href=\"/de/shop\">Shop</a> oder lies mehr &uuml;ber unsere <a href=\"/de/delivery\">diskrete Lieferung</a>.",
            "Beliebte Produkte:"]),
        "shop": ("Gras, Haschisch &amp; Cali Weed kaufen", [
            "Entdecke das gesamte Sortiment von WietStore: <strong>Gras, Haschisch, Cali Weed, Gruis und &Ouml;l</strong>. Alles wird diskret und geruchsneutral in die Niederlande, nach Belgien und Deutschland geliefert. W&auml;hle dein Gewicht von 3 bis 100 Gramm.",
            "Klicke auf ein Produkt f&uuml;r die vollst&auml;ndige Beschreibung, THC-Gehalt, Geschmack und Wirkung:"]),
        "delivery": ("Lieferung &amp; Versand", [
            "WietStore liefert <strong>diskret und geruchsneutral</strong> in die Niederlande, nach Belgien, Deutschland und Frankreich. Lieferungen nach Deutschland dauern in der Regel 2&ndash;4 Werktage.",
            "Jedes Paket wird neutral und geruchsdicht verpackt, ohne Hinweis auf den Inhalt. Fragen? <a href=\"/de/contact\">Kontaktiere uns</a> oder besuche den <a href=\"/de/shop\">Shop</a>."]),
        "about": ("&Uuml;ber WietStore", [
            "WietStore ist ein in den Niederlanden ans&auml;ssiger Cannabis-Shop, der Premium-Gras, Haschisch und Cannabis&ouml;l in <strong>Amsterdamer Coffeeshop-Qualit&auml;t</strong> an Kunden in den Niederlanden, Belgien, Deutschland und Frankreich liefert.",
            "Wir legen Wert auf Produktqualit&auml;t, diskrete Lieferung und gute Kundeninformation. Entdecke unser <a href=\"/de/shop\">Sortiment</a>."]),
        "contact": ("Kontakt", [
            "Fragen zu deiner Bestellung, Lieferung oder Zahlung? Unser Team hilft dir gerne.",
            "E-Mail: <a href=\"mailto:bestwiets@outlook.com\">bestwiets@outlook.com</a><br>WhatsApp: <a href=\"https://wa.me/31635237086\">+31 6 35237086</a>",
            "Wir antworten in der Regel innerhalb weniger Stunden. Bitte gib bei Fragen zu einer bestehenden Bestellung deine Bestellnummer an."]),
    },
}

# Crawlable country links (homepage + landing pages link to every market — DACH + FR focus)
COUNTRY_LINKS = [
    ("/de/cannabis-kaufen-deutschland", "Deutschland"),
    ("/cannabis-kaufen-oesterreich", "Österreich"),
    ("/cannabis-kaufen-schweiz", "Schweiz"),
    ("/acheter-cannabis-france", "France"),
    ("/be", "België"),
]
def _country_links(lang="nl"):
    lbl = {"nl": "Wij bezorgen in", "de": "Wir liefern nach", "en": "We deliver to",
           "fr": "Nous livrons en"}.get(lang, "Wij bezorgen in")
    lis = " &middot; ".join('<a href="%s">%s</a>' % (u, esc(n)) for u, n in COUNTRY_LINKS)
    return '<p class="pr-countries"><strong>%s:</strong> %s</p>' % (lbl, lis)

def page_body(key, lang="nl"):
    h1, paras = PAGE_CONTENT[lang][key]
    html = '<section class="pr"><h1>%s</h1>' % h1
    html += "".join("<p>%s</p>" % para for para in paras)
    if key == "shop":
        html += _product_links(lang=lang)
    elif key == "blog":
        html += _article_links()
    elif key == "home":
        html += _product_links(limit=12, lang=lang)
        if lang == "de":
            html += _city_links("de") + "<h2>Ratgeber</h2>" + '<ul class="pr-list">%s</ul>' % "".join(
                '<li><a href="/%s">%s</a></li>' % (esc(b["slug"]), esc(b["title"])) for b in BLOG if b.get("lang") == "de")
        html += '<p><a href="/shop">Alle producten &rarr;</a></p>' if lang == "nl" else (
            '<p><a href="/en/shop">All products &rarr;</a></p>' if lang == "en" else '<p><a href="/de/shop">Alle Produkte &rarr;</a></p>')
        html += _country_links(lang)
    html += "</section>"
    return html

def country_body(h1, lead, cta_href, cta_label, lang="nl"):
    return ('<section class="pr"><h1>%s</h1><p>%s</p>%s'
            '<p><a href="%s">%s</a></p></section>') % (h1, lead, _product_links(limit=16, lang=lang), cta_href, cta_label)

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
    write_route(out, title, desc, path, OG_DEFAULT, jsonld, alts, body=page_body(key, "nl"))
    urls.append((path, TODAY, "1.0" if key == "home" else ("0.9" if key == "shop" else "0.6")))

# Localized pages (/en/*, /de/*) — Dutch is the default and is generated by the loop above
for lang in ("en", "de"):
    for key in LOC_PAGES:
        title, desc = LOC_META[lang][key]
        path = loc_url(lang, key)
        out = "%s/index.html" % lang if key == "home" else "%s/%s.html" % (lang, key)
        write_route(out, title, desc, path, OG_DEFAULT, [], alts_for(key), lang=lang, body=page_body(key, lang))
        urls.append((path, TODAY, "0.8" if key in ("home", "shop") else "0.5"))

# Belgium country landing pages (regional hreflang nl-BE / fr-BE)
COUNTRY_ALTS = [("nl-BE", "/be"), ("fr-BE", "/fr"), ("de-DE", "/de/cannabis-kaufen-deutschland"),
                ("de-AT", "/cannabis-kaufen-oesterreich"), ("de-CH", "/cannabis-kaufen-schweiz"),
                ("fr-FR", "/acheter-cannabis-france")]  # one reciprocal hreflang cluster
BE_ALTS = COUNTRY_ALTS
BELGIUM = {
    "be": ("nl", "Wiet Kopen België | Veilige & Discrete Levering – WietStore",
           "Wiet kopen in België? Bestel premium wiet, hasj en cali weed online bij WietStore. Discreet en betrouwbaar bezorgd in heel België, vaak binnen 2–4 werkdagen.",
           "Wiet kopen in België"),
    "fr": ("fr", "Acheter du Cannabis en Belgique | Livraison Discrète – WietStore",
           "Acheter du cannabis en ligne en Belgique : weed, haschich et cali weed premium, livrés discrètement partout en Belgique. Paiement par virement, Bitcoin ou USDT.",
           "Acheter du cannabis en Belgique"),
}
BE_CTA = {"be": ("/shop", "Bekijk het volledige assortiment &rarr;"),
          "fr": ("/shop", "Voir tout l'assortiment &rarr;")}
for key, (lang, title, desc, crumb_name) in BELGIUM.items():
    path = "/" + key
    bc = crumb([("Home", "/"), (crumb_name, path)])
    cta_href, cta_label = BE_CTA[key]
    body = country_body(esc(crumb_name), esc(desc), cta_href, cta_label)
    write_route("%s.html" % key, title, desc, path, OG_DEFAULT, [bc], BE_ALTS, lang=lang, body=body)
    urls.append((path, TODAY, "0.9"))

# Germany country landing page (German URL targeting "cannabis kaufen Deutschland")
DE_LANDING_ALTS = COUNTRY_ALTS
de_path = "/de/cannabis-kaufen-deutschland"
de_bc = crumb([("Startseite", "/de/"), ("Cannabis kaufen Deutschland", de_path)])
de_body = country_body(
    "Cannabis kaufen in Deutschland",
    "Cannabis online kaufen und diskret nach Deutschland liefern lassen. WietStore bietet Premium-Weed, Haschisch und Cali Weed in Amsterdamer Coffeeshop-Qualit&auml;t, geruchsneutral verpackt und in der Regel innerhalb von 2&ndash;4 Werktagen geliefert. Bezahlung per Bank&uuml;berweisung, Bitcoin oder USDT.",
    "/de/shop", "Zum gesamten Sortiment &rarr;", lang="de") + '<section class="pr">' + _city_links("de") + '</section>'
write_route("de/cannabis-kaufen-deutschland.html",
            "Cannabis kaufen in Deutschland | Diskreter Versand – WietStore",
            "Cannabis online kaufen und nach Deutschland liefern lassen. Premium Weed, Haschisch und Cali Weed in Coffeeshop-Qualität, diskret in 2–4 Werktagen geliefert.",
            de_path, OG_DEFAULT, [de_bc], DE_LANDING_ALTS, lang="de", body=de_body)
urls.append((de_path, TODAY, "0.9"))

# Austria / Switzerland / France country landing pages (DACH + FR ranking focus)
EXTRA_LANDINGS = [
    {"slug": "cannabis-kaufen-oesterreich", "lang": "de", "hl": "de-AT", "home": "Startseite",
     "crumb": "Cannabis kaufen Österreich",
     "title": "Cannabis kaufen in Österreich | Diskrete Lieferung – WietStore",
     "desc": "Cannabis online kaufen und nach Österreich liefern lassen: Premium Weed, Haschisch und Pre-Rolls in Coffeeshop-Qualität, diskret verpackt.",
     "h1": "Cannabis kaufen in Österreich",
     "lead": "Cannabis online kaufen und diskret nach Österreich liefern lassen. WietStore bietet Premium-Weed, Haschisch, Cali Weed und vorgerollte Joints in Amsterdamer Coffeeshop-Qualit&auml;t, geruchsneutral verpackt. Bezahlung per Bank&uuml;berweisung, Bitcoin oder USDT.",
     "cta": ("/shop", "Zum gesamten Sortiment &rarr;")},
    {"slug": "cannabis-kaufen-schweiz", "lang": "de", "hl": "de-CH", "home": "Startseite",
     "crumb": "Cannabis kaufen Schweiz",
     "title": "Cannabis kaufen in der Schweiz | Diskrete Lieferung – WietStore",
     "desc": "Cannabis online kaufen und in die Schweiz liefern lassen: Premium Weed, Haschisch und Pre-Rolls in Coffeeshop-Qualität, diskret verpackt.",
     "h1": "Cannabis kaufen in der Schweiz",
     "lead": "Cannabis online kaufen und diskret in die Schweiz liefern lassen. WietStore bietet Premium-Weed, Haschisch, Cali Weed und vorgerollte Joints in Amsterdamer Coffeeshop-Qualit&auml;t, geruchsneutral verpackt. Bezahlung per Bank&uuml;berweisung, Bitcoin oder USDT.",
     "cta": ("/shop", "Zum gesamten Sortiment &rarr;")},
    {"slug": "acheter-cannabis-france", "lang": "fr", "hl": "fr-FR", "home": "Accueil",
     "crumb": "Acheter du cannabis en France",
     "title": "Acheter du Cannabis en France | Livraison Discrète – WietStore",
     "desc": "Acheter du cannabis en ligne et se faire livrer en France : weed, haschich et pré-roulés premium de qualité coffeeshop d'Amsterdam, livrés discrètement.",
     "h1": "Acheter du cannabis en France",
     "lead": "Acheter du cannabis en ligne et se faire livrer discr&egrave;tement en France. WietStore propose du weed, du haschich, du cali weed et des joints pr&eacute;-roul&eacute;s de qualit&eacute; coffeeshop d'Amsterdam, emball&eacute;s sans odeur. Paiement par virement, Bitcoin ou USDT.",
     "cta": ("/shop", "Voir tout l'assortiment &rarr;")},
]
_LAND_CK = {"de-AT": "at", "de-CH": "ch", "fr-FR": "fr"}
for L in EXTRA_LANDINGS:
    path = "/" + L["slug"]
    bc = crumb([(L["home"], "/"), (L["crumb"], path)])
    alts = COUNTRY_ALTS
    _ck = _LAND_CK[L["hl"]]
    body = ('<section class="pr"><h1>%s</h1><p>%s</p>%s%s<p><a href="%s">%s</a></p></section>') % (
        esc(L["h1"]), L["lead"], _product_links(limit=16, lang=L["lang"]), _country_links(L["lang"]),
        L["cta"][0], L["cta"][1])
    body += '<section class="pr">' + _city_links(_ck) + '</section>'
    write_route("%s.html" % L["slug"], L["title"], L["desc"], path, OG_DEFAULT, [bc], alts,
                lang=L["lang"], body=body)
    urls.append((path, TODAY, "0.9"))

# City local-SEO landing pages (Home -> Country -> City crawl path; fixes discoverability)
for c in CITY:
    cc = CITY_COUNTRY[c["c"]]
    cpath = "/" + c["s"]
    ctitle, cdesc = city_meta(c)
    write_route("%s.html" % c["s"], ctitle, cdesc, cpath, OG_DEFAULT, city_jsonld(c, cpath),
                [(cc["hl"], cpath), ("x-default", cpath)], lang=cc["lang"], body=city_body(c))
    urls.append((cpath, TODAY, "0.7"))

# Prerolls / voorgedraaide joints category landing page (/prerolls)
_pre_items = [p for p in PRODUCTS if p.get("cat") == "Prerolls"]
if _pre_items:
    pre_title = "Voorgedraaide Joints & Pre-Rolls Kopen | WietStore"
    pre_desc = ("Voorgedraaide joints en pre-rolls kopen bij WietStore: handgerold van premium wiet — "
                "Amnesia, Lemon Haze, Gelato en meer. Discreet bezorgd in NL, BE & DE.")
    pre_og = SITE + "/images/2026/07/preroll-power-pack-18-gram.jpg"
    pre_bc = crumb([("Home", "/"), ("Pre-Rolls", "/prerolls")])
    pre_collection = {"@context": "https://schema.org", "@type": "CollectionPage",
                      "name": "Voorgedraaide Joints & Pre-Rolls", "url": SITE + "/prerolls",
                      "description": pre_desc}
    pre_itemlist = {"@context": "https://schema.org", "@type": "ItemList",
                    "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                         "url": SITE + "/product/" + p["slug"], "name": p["name"]}
                                        for i, p in enumerate(_pre_items)]}
    # FAQ (visible content below + FAQPage schema, mirrors PREROLL_FAQ in index.html pagePrerolls)
    PREROLL_FAQ = [
        ("Wat zijn voorgedraaide joints?",
         "Voorgedraaide joints, ook wel pre-rolls genoemd, zijn kant-en-klare joints die met de hand "
         "zijn gerold van premium wiet. Je hoeft zelf niet te draaien — gewoon aansteken en genieten."),
        ("Hoeveel joints zitten er in een pakket?",
         "Onze pre-rolls zijn verkrijgbaar per 3, 12 of 30 stuks, waarbij grotere pakketten voordeliger "
         "zijn per stuk. Daarnaast bieden we voordeelpakketten zoals het Preroll Power Pack van 18 gram."),
        ("Welke soorten pre-rolls kan ik kiezen?",
         "Kies uit energieke sativa's zoals Amnesia en Lemon Haze, gebalanceerde hybrides zoals Gelato, "
         "of ontspannende indica's zoals Purple Kinky Kush. Elke soort heeft een aangegeven THC-bereik."),
        ("Hoe worden de pre-rolls bezorgd?",
         "Alle bestellingen worden discreet en geurloos verpakt en betrouwbaar bezorgd in Nederland, "
         "België en Duitsland — vaak binnen enkele werkdagen."),
    ]
    pre_faq_schema = {"@context": "https://schema.org", "@type": "FAQPage",
                      "mainEntity": [{"@type": "Question", "name": q,
                                      "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in PREROLL_FAQ]}
    pre_faq_html = '<h2>Veelgestelde vragen</h2>' + "".join(
        "<h3>%s</h3><p>%s</p>" % (esc(q), esc(a)) for q, a in PREROLL_FAQ)
    pre_intro = ("Voorgedraaide joints kopen zonder zelf te rollen? Bij WietStore vind je handgerolde "
                 "pre-rolls van premium toppen — van frisse Amnesia en Lemon Haze tot romige Gelato en "
                 "krachtige indica's. Direct klaar voor gebruik en discreet, geurloos bezorgd in Nederland, "
                 "België en Duitsland.")
    pre_body = ('<section class="pr"><h1>Voorgedraaide Joints &amp; Pre-Rolls kopen</h1>'
                '<p>%s</p>%s%s'
                '<p><a href="/shop">Bekijk het volledige assortiment &rarr;</a></p></section>') % (
                    pre_intro, _product_links(_pre_items), pre_faq_html)
    write_route("prerolls.html", pre_title, pre_desc, "/prerolls", pre_og,
                [pre_collection, pre_itemlist, pre_faq_schema, pre_bc],
                alts=[("nl", "/prerolls"), ("x-default", "/prerolls")], body=pre_body)
    urls.append(("/prerolls", TODAY, "0.9"))

# Blog articles
for b in BLOG:
    path = "/" + b["slug"]
    title = "%s | WietStore" % b["title"]
    img = SITE + b["img"]
    article = {"@context": "https://schema.org", "@type": "Article", "headline": b["title"],
               "image": img, "description": b["excerpt"],
               "author": {"@type": "Organization", "name": "WietStore"},
               "publisher": {"@type": "Organization", "name": "WietStore",
                             "logo": {"@type": "ImageObject", "url": SITE + "/favicon.svg"}},
               "mainEntityOfPage": SITE + path}
    bc = crumb([("Home", "/"), ("Blog", "/blog"), (b["title"], path)])
    write_route("%s.html" % b["slug"], title, b["excerpt"], path, img, [article, bc], lang=b.get("lang", "nl"), body=render_article(b))
    urls.append((path, TODAY, "0.7"))

# Products
for p in PRODUCTS:
    path = "/product/" + p["slug"]
    title = "%s kopen – %s€%.2f | WietStore" % (p["name"], "vanaf " if p.get("variants") else "", p["price"])
    desc = product_meta_desc(p)
    img = SITE + p["img"]
    # additionalProperty entries (THC, Smaak, Effect, Medicinaal) — surfaces structured attributes to Google.
    extras = []
    if p.get("thc"):
        extras.append({"@type": "PropertyValue", "name": "THC", "value": p["thc"]})
    if p.get("flavors"):
        extras.append({"@type": "PropertyValue", "name": "Smaak", "value": ", ".join(p["flavors"])})
    if p.get("effects"):
        extras.append({"@type": "PropertyValue", "name": "Effect", "value": ", ".join(p["effects"])})
    if p.get("medicinal"):
        extras.append({"@type": "PropertyValue", "name": "Medicinaal", "value": ", ".join(p["medicinal"])})
    _avail = "https://schema.org/InStock" if p["stock"] == "In stock" else "https://schema.org/OutOfStock"
    if p.get("variants"):
        _prices = [v["price"] for v in p["variants"]]
        offers = {"@type": "AggregateOffer", "url": SITE + path, "priceCurrency": "EUR",
                  "lowPrice": "%.2f" % min(_prices), "highPrice": "%.2f" % max(_prices),
                  "offerCount": len(_prices), "availability": _avail,
                  "priceValidUntil": PRICE_VALID_UNTIL, "itemCondition": "https://schema.org/NewCondition"}
    else:
        offers = {"@type": "Offer", "url": SITE + path, "price": "%.2f" % p["price"],
                  "priceCurrency": "EUR", "availability": _avail,
                  "priceValidUntil": PRICE_VALID_UNTIL, "itemCondition": "https://schema.org/NewCondition"}
    product = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "image": img,
               "description": p["desc"], "category": p["cat"], "sku": p["slug"],
               "brand": {"@type": "Brand", "name": "WietStore"}, "offers": offers}
    if extras:
        product["additionalProperty"] = extras
    bc = crumb([("Home", "/"), ("Shop", "/shop"), (p["name"], path)])
    _palts = [("nl", path), ("de", "/de" + path), ("x-default", path)]
    write_route("product/%s.html" % p["slug"], title, desc, path, img, [product, bc], _palts, body=render_product(p))
    urls.append((path, TODAY, "0.8"))
    # German product page (/de/product/<slug>) — Germany-first SEO
    dpath = "/de" + path
    dtitle = "%s kaufen – %s€%.2f | WietStore" % (p["name"], "ab " if p.get("variants") else "", p["price"])
    dextras = []
    if p.get("thc"):
        dextras.append({"@type": "PropertyValue", "name": "THC", "value": p["thc"]})
    for _lbl, _k in (("Geschmack", "flavors"), ("Wirkung", "effects"), ("Medizinisch", "medicinal")):
        if p.get(_k):
            dextras.append({"@type": "PropertyValue", "name": _lbl, "value": ", ".join(ATTR_DE.get(v, v) for v in p[_k])})
    doffers = dict(offers, url=SITE + dpath)
    dproduct = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "image": img,
                "description": DESC_DE.get(p["slug"], p["desc"]), "category": CAT_DE.get(p["cat"], p["cat"]), "sku": p["slug"],
                "brand": {"@type": "Brand", "name": "WietStore"}, "offers": doffers}
    if dextras:
        dproduct["additionalProperty"] = dextras
    dbc = crumb([("Startseite", "/de/"), ("Shop", "/de/shop"), (p["name"], dpath)])
    write_route("de/product/%s.html" % p["slug"], dtitle, product_meta_desc_de(p), dpath, img, [dproduct, dbc], _palts,
                lang="de", body=render_product_de(p))
    urls.append((dpath, TODAY, "0.8"))

# Sitemap — use content-stable lastmod per URL (only changes when the page changes)
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      '  <!-- Readable site map with page purposes: https://bestwiets.com/sitemap.md ; guide for LLMs: https://bestwiets.com/llms.txt -->']
for path, lastmod, prio in urls:
    lastmod = PAGE_LASTMOD.get(path, lastmod)
    sm.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (SITE, path, lastmod, prio))
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
# persist the lastmod manifest so unchanged pages keep their date on the next build
json.dump(_LM_STORE, open(_LM_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)

# ---------- Public reading maps: /sitemap.md and /llms.txt (same source data as the HTML) ----------
_LANG_NAME = {"nl": "Nederlands", "de": "Deutsch", "en": "English", "fr": "Français"}
def _md(t):
    return re.sub(r"\s+", " ", html.unescape(t)).replace("[", "(").replace("]", ")").strip()
def _mdpath(path):
    return path + "index.md" if path.endswith("/") else path + ".md"
def _line(path):
    t, d, l = ROUTE_META[path]
    return "- [%s](%s%s) · [Markdown](%s%s) — %s _(%s)_" % (_md(t), SITE, path, SITE, _mdpath(path), _md(d), _LANG_NAME.get(l, l))
_seen = set()
def _sec(title, intro, paths):
    paths = [p for p in paths if p in ROUTE_META and p not in _seen]
    _seen.update(paths)
    if not paths:
        return []
    return ["", "## " + title, "", intro, ""] + [_line(p) for p in paths]
_prod_paths = {}
for _p in PRODUCTS:
    _prod_paths.setdefault(_p.get("cat", "Overig"), []).append("/product/" + _p["slug"])
_city_by_cc = {}
for _c in CITY:
    _city_by_cc.setdefault(_c["c"], []).append("/" + _c["s"])
_blog_by_lang = {}
for _b in BLOG:
    _blog_by_lang.setdefault(_b.get("lang", "nl"), []).append("/" + _b["slug"])
smd = ["# WietStore (bestwiets.com) — site map", "",
       "Every public page of bestwiets.com, grouped by topic, with its purpose and language. "
       "Each entry links the canonical HTML page and its Markdown copy (same content, generated from the same data); prices, stock and delivery terms on the HTML pages are authoritative. "
       "Generated from the same source data as the website (%d pages)." % len(urls)]
smd += _sec("Main pages", "Home, shop, ordering, delivery, returns, terms and contact.",
            ["/", "/shop", "/prerolls", "/delivery", "/bestelhandleiding", "/returns", "/voorwaarden", "/about", "/contact", "/blog",
             "/en/", "/en/shop", "/en/delivery", "/en/about", "/en/contact", "/de/", "/de/shop", "/de/delivery", "/de/about", "/de/contact"])
smd += _sec("Country pages", "Ordering and delivery per country (Belgium, Germany, Austria, Switzerland, France).",
            ["/be", "/fr", "/de/cannabis-kaufen-deutschland", "/cannabis-kaufen-oesterreich", "/cannabis-kaufen-schweiz", "/acheter-cannabis-france"])
for _cc, _name in (("de", "Germany"), ("at", "Austria"), ("ch", "Switzerland"), ("fr", "France")):
    smd += _sec("City pages — " + _name, "Local delivery information per city in %s." % _name, _city_by_cc.get(_cc, []))
for _cat, _ps in _prod_paths.items():
    smd += _sec("Produkte (Deutsch) — " + CAT_DE.get(_cat, _cat), "Deutsche Produktseiten mit Preis pro Gewicht oder Stück, THC, Geschmack und Wirkung.", ["/de" + x for x in _ps])
for _cat, _ps in _prod_paths.items():
    smd += _sec("Products (Dutch) — " + _cat, "Dutch product pages with price per weight or per item, THC, taste and effect.", _ps)
for _l, _ps in _blog_by_lang.items():
    smd += _sec("Guides (%s)" % _LANG_NAME.get(_l, _l), "Articles about strains, buying, payment and delivery.", _ps)
smd += _sec("Other pages", "Remaining public pages.", sorted(ROUTE_META))
open(os.path.join(ROOT, "sitemap.md"), "w", encoding="utf-8", newline="\n").write("\n".join(smd) + "\n")

# Markdown copies of every page (for LLM readers; search engines are pointed at the HTML via robots.txt)
def _html_to_md(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", h)
    h = re.sub(r'(?is)<img\b[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"[^>]*>', lambda m: "![%s](%s)" % (m.group(2), m.group(1) if m.group(1).startswith("http") else SITE + m.group(1)), h)
    h = re.sub(r"(?is)<img\b[^>]*>", "", h)
    h = re.sub(r'(?is)<a\b[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', lambda m: "[%s](%s)" % (re.sub(r"<[^>]+>", "", m.group(2)).strip(), m.group(1) if re.match(r"(?i)https?:|mailto:|tel:", m.group(1)) else SITE + m.group(1)), h)
    for n in range(1, 5):
        h = re.sub(r"(?is)<h%d\b[^>]*>(.*?)</h%d>" % (n, n), lambda m, n=n: "\n\n" + "#" * n + " " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n\n", h)
    h = re.sub(r"(?is)<li\b[^>]*>", "\n- ", h)
    h = re.sub(r"(?is)<(strong|b)\b[^>]*>(.*?)</\1>", r"**\2**", h)
    h = re.sub(r"(?is)<(em|i)\b[^>]*>(.*?)</\1>", r"*\2*", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</?(p|div|section|article|ul|ol|nav|aside|table|tr)\b[^>]*>", "\n\n", h)
    h = re.sub(r"(?s)<[^>]+>", "", h)
    h = html.unescape(h)
    h = "\n".join(l.rstrip() for l in h.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", h).strip()
_MD_MANIFEST = os.path.join(ROOT, ".md-mirrors.json")
_old_md = set(json.load(open(_MD_MANIFEST, encoding="utf-8"))) if os.path.exists(_MD_MANIFEST) else set()
_new_md = set()
for _path, (_t, _d, _l) in ROUTE_META.items():
    _rel = _mdpath(_path).lstrip("/")
    _body = _html_to_md(ROUTE_BODY.get(_path, ""))
    _hdr = ("# %s\n\n> Canonical page: %s%s · Language: %s · Updated: %s · Source: generated from the same data as the HTML page · Maintainer: WietStore (bestwiets@outlook.com)\n\n%s\n\n"
            % (_md(_t), SITE, _path, _LANG_NAME.get(_l, _l), PAGE_LASTMOD.get(_path, TODAY), _md(_d)))
    _full = os.path.join(ROOT, _rel)
    os.makedirs(os.path.dirname(_full) or ROOT, exist_ok=True)
    open(_full, "w", encoding="utf-8", newline="\n").write(_hdr + _body + "\n")
    _new_md.add(_rel)
for _rel in _old_md - _new_md:  # pages that no longer exist lose their copy too
    try:
        os.remove(os.path.join(ROOT, _rel))
    except OSError:
        pass
json.dump(sorted(_new_md), open(_MD_MANIFEST, "w", encoding="utf-8"), indent=0)

_FEE_EN = {"Amsterdam": "Amsterdam", "Andere stad in Nederland": "rest of the Netherlands", "Ander land in Europa": "other European countries"}
_fees = ", ".join("%s €%s" % (_FEE_EN.get(k, k), v) for k, v in re.findall(r'"([^"]+)"\s*:\s*(\d+)', re.search(r"const DELIVERY_FEES\s*=\s*\{([^}]*)\}", TEMPLATE).group(1)))
llms = """# WietStore (bestwiets.com)

> WietStore is a Dutch online cannabis shop (Amsterdam, Netherlands) selling weed per gram, hash, cali weed, grit, pre-rolled joints and THC oil, delivered discreetly to Germany, Austria, Switzerland, France, Belgium and the Netherlands. Adults 18+ only.

If you are an LLM looking for information about this site, use the content map at https://bestwiets.com/sitemap.md to find the relevant topic and its page, and rely on that canonical page for prices, stock and terms. If the information you need is not on the site, report that gap instead of guessing.

Every page has a Markdown copy at the same address with ".md" appended (folder pages use "index.md", e.g. https://bestwiets.com/de/index.md); the site map links each one. German-language pages: https://bestwiets.com/de/ (shop: /de/shop, products: /de/product/<name>).

Key facts (from the live shop configuration):
- Minimum order: €%d
- Delivery fees: %s
- Payment: bank transfer, Bitcoin, USDT or Litecoin (payment details are sent after ordering)
- Weed is sold per gram in weights from 3 g to 100 g at the listed price per gram
- Contact: bestwiets@outlook.com, WhatsApp +31 6 35237086
- Buyers are responsible for checking the cannabis laws of their own country

## Maps
- [Site map with every page](https://bestwiets.com/sitemap.md): all pages grouped by topic, with purpose and language
- [XML sitemap](https://bestwiets.com/sitemap.xml): machine-readable URL list

## Shop and ordering
- [Shop](https://bestwiets.com/shop): full assortment with prices
- [Pre-rolls](https://bestwiets.com/prerolls): pre-rolled joints
- [How to order](https://bestwiets.com/bestelhandleiding): step-by-step ordering guide (Dutch)
- [Delivery & shipping](https://bestwiets.com/en/delivery): delivery areas, times and packaging
- [Returns](https://bestwiets.com/returns) and [terms](https://bestwiets.com/voorwaarden)
- [Contact](https://bestwiets.com/en/contact)

## Countries
- [Germany](https://bestwiets.com/de/cannabis-kaufen-deutschland), [Austria](https://bestwiets.com/cannabis-kaufen-oesterreich), [Switzerland](https://bestwiets.com/cannabis-kaufen-schweiz), [France](https://bestwiets.com/acheter-cannabis-france), [Belgium (NL)](https://bestwiets.com/be), [Belgium (FR)](https://bestwiets.com/fr)

## Optional
- [Blog](https://bestwiets.com/blog): guides on strains, payment and delivery
""" % (MIN_ORDER, _fees)
open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8", newline="\n").write(llms)
print("Wrote sitemap.md (%d linked pages) and llms.txt" % len(_seen))

print("Generated %d pages + %d articles + %d products = %d routes" % (
    len(PAGES), len(BLOG), len(PRODUCTS), len(urls)))
print("Wrote sitemap.xml with %d URLs" % len(urls))
