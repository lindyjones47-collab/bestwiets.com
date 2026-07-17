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
PRICE_VALID_UNTIL = "%d-12-31" % (datetime.date.today().year + 1)  # keeps Product offers "fresh" for Google

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

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

def write_route(out_path, title, desc, path, og_image, jsonld, alts=None, lang="nl", body=""):
    block = "<!--SEO:START-->\n" + seo_block(title, desc, path, og_image, jsonld, alts) + "\n<!--SEO:END-->"
    html = MARKER.sub(lambda m: block, TEMPLATE)
    # Pre-render the route's real content into <main id="app"> so crawlers see it
    # without executing JS. The SPA overwrites #app.innerHTML on load, so users
    # still get the interactive version — this block is purely for first paint + SEO.
    app = "<!--APP:START-->\n" + (body or "") + "\n<!--APP:END-->"
    html = APP_MARKER.sub(lambda m: app, html)
    if lang != "nl":
        html = html.replace('<html lang="nl">', '<html lang="%s">' % lang, 1)
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
        "home": ("Cannabis online kaufen & bestellen | Gras & Haschisch geliefert – WietStore", "Cannabis online kaufen bei WietStore: Premium Gras, Haschisch und Öl. Diskret geliefert in NL, Belgien & Deutschland. Zahlung per Bank, Bitcoin oder USDT."),
        "shop": ("Gras, Haschisch & Cali Weed kaufen – Online Cannabis Shop | WietStore", "Entdecke das gesamte Sortiment: Gras, Haschisch, Cali Weed, Gruis und Öl. Online bestellen und diskret geliefert in NL, Belgien und Deutschland."),
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

def _product_links(items=None, limit=None):
    items = items if items is not None else PRODUCTS
    if limit:
        items = items[:limit]
    return '<ul class="pr-list">%s</ul>' % "".join(
        '<li><a href="/product/%s">%s kopen</a> &mdash; &euro;%.2f</li>' % (esc(p["slug"]), esc(p["name"]), p["price"])
        for p in items)

def _article_links():
    return '<ul class="pr-list">%s</ul>' % "".join(
        '<li><a href="/%s">%s</a></li>' % (esc(b["slug"]), esc(b["title"])) for b in BLOG)

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
        lis = "".join("<li>%s &mdash; &euro;%.2f</li>" % (esc(v["label"]), v["price"]) for v in p["variants"])
        variants_html = '<p><strong>%s:</strong></p><ul class="pr-specs">%s</ul>' % (
            "Beschikbare aantallen" if _is_qty else "Beschikbare varianten", lis)
    return (
        '<article class="pr">'
        + _crumb_html([("Home", "/"), ("Shop", "/shop"), (p["name"], path)])
        + "<h1>%s kopen</h1>" % esc(p["name"])
        + '<img src="%s" alt="%s kopen" width="480" height="480" loading="eager">' % (esc(p["img"]), esc(p["name"]))
        + '<p class="pr-price"><strong>%s&euro;%.2f</strong> &middot; %s &middot; %s</p>' % (price_prefix, p["price"], esc(p.get("cat", "")), avail)
        + "<p>%s</p>" % esc(p["desc"])
        + specs_html
        + variants_html
        + "<p>Vanaf 10 gram krijg je automatisch 3% korting. Discreet en geurloos bezorgd in Nederland, Belgi&euml; en Duitsland.</p>"
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
            "Bekijk het volledige assortiment van WietStore: <strong>wiet, hasj, cali weed, gruis en wietolie</strong>. Alle producten worden discreet en geurloos bezorgd in Nederland, Belgi&euml; en Duitsland. Vanaf 10 gram ontvang je automatisch 3% korting.",
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
            "Browse WietStore's full range: <strong>weed, hash, cali weed, grit and cannabis oil</strong>. Everything is delivered discreetly and odourlessly across the Netherlands, Belgium and Germany. From 10 grams you automatically get a 3% discount.",
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
            "Entdecke das gesamte Sortiment von WietStore: <strong>Gras, Haschisch, Cali Weed, Gruis und &Ouml;l</strong>. Alles wird diskret und geruchsneutral in die Niederlande, nach Belgien und Deutschland geliefert. Ab 10 Gramm erh&auml;ltst du automatisch 3% Rabatt.",
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

def page_body(key, lang="nl"):
    h1, paras = PAGE_CONTENT[lang][key]
    html = '<section class="pr"><h1>%s</h1>' % h1
    html += "".join("<p>%s</p>" % para for para in paras)
    if key == "shop":
        html += _product_links()
    elif key == "blog":
        html += _article_links()
    elif key == "home":
        html += _product_links(limit=12)
        html += '<p><a href="/shop">Alle producten &rarr;</a></p>' if lang == "nl" else (
            '<p><a href="/en/shop">All products &rarr;</a></p>' if lang == "en" else '<p><a href="/de/shop">Alle Produkte &rarr;</a></p>')
    html += "</section>"
    return html

def country_body(h1, lead, cta_href, cta_label):
    return ('<section class="pr"><h1>%s</h1><p>%s</p>%s'
            '<p><a href="%s">%s</a></p></section>') % (h1, lead, _product_links(limit=16), cta_href, cta_label)

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
BE_ALTS = [("nl-BE", "/be"), ("fr-BE", "/fr"), ("nl", "/"), ("x-default", "/")]
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
DE_LANDING_ALTS = [("de", "/de/cannabis-kaufen-deutschland"), ("nl", "/"), ("x-default", "/")]
de_path = "/de/cannabis-kaufen-deutschland"
de_bc = crumb([("Startseite", "/de/"), ("Cannabis kaufen Deutschland", de_path)])
de_body = country_body(
    "Cannabis kaufen in Deutschland",
    "Cannabis online kaufen und diskret nach Deutschland liefern lassen. WietStore bietet Premium-Weed, Haschisch und Cali Weed in Amsterdamer Coffeeshop-Qualit&auml;t, geruchsneutral verpackt und in der Regel innerhalb von 2&ndash;4 Werktagen geliefert. Bezahlung per Bank&uuml;berweisung, Bitcoin oder USDT.",
    "/de/shop", "Zum gesamten Sortiment &rarr;")
write_route("de/cannabis-kaufen-deutschland.html",
            "Cannabis kaufen in Deutschland | Diskreter Versand – WietStore",
            "Cannabis online kaufen und nach Deutschland liefern lassen. Premium Weed, Haschisch und Cali Weed in Coffeeshop-Qualität, diskret in 2–4 Werktagen geliefert.",
            de_path, OG_DEFAULT, [de_bc], DE_LANDING_ALTS, lang="de", body=de_body)
urls.append((de_path, TODAY, "0.9"))

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
                 "België en Duitsland. Vanaf 10 gram krijg je automatisch 3% korting.")
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
    title = "%s kopen – €%.2f | WietStore" % (p["name"], p["price"])
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
    write_route("product/%s.html" % p["slug"], title, desc, path, img, [product, bc], body=render_product(p))
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
