# bestwiet.com — Site Backup

A self-contained backup of the bestwiet.com storefront, built as a single-page
site. All pages, products, content, and styling are bundled into `index.html`.

## Contents
- `index.html` — the complete site (home, shop, product pages, delivery,
  bestelhandleiding, terms, about, returns, contact, blog) with cart and checkout.

## Pages / routes
Navigation uses client-side hash routing:
- `#home`, `#shop`, `#product/<slug>`, `#delivery`, `#bestelhandleiding`,
  `#voorwaarden`, `#about`, `#returns`, `#contact`, `#checkout`

## Running locally
Open `index.html` in a browser, or serve the folder:

    python3 -m http.server 8000
    # then open http://localhost:8000

## Deploying
- **GitHub Pages:** push to the repo, then enable Pages (Settings → Pages →
  deploy from branch, root). The site is served from `index.html`.
- **WordPress / other host:** upload `index.html` as a full-page template or
  point a page/subdomain at it.

## Notes
- Product photos, the hero/banner image, and the footer/header logo load from
  `bestwiet.com` image URLs; they resolve as long as that domain serves them.
  The leaf badge is embedded directly. For a fully offline backup, download
  those images locally and update the URLs.
- The "WIETSTORE" wordmark is rendered as live HTML text (crawlable for SEO),
  not baked into an image.
