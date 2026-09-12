# reynaldi-website

Single-page static portfolio for **Reynaldi Wong** — DevOps Engineer.

Porcelain-inspired blue-and-white design, zero build step. Plain HTML + CSS + JS.

## Structure

```
index.html              single page (6 sections + footer)
assets/
  css/  tokens.css      design tokens (colors, type, radius, motion)
        base.css        reset, fonts, primitives
        home.css        layout & components
  js/   reveal.js       scroll reveal (IntersectionObserver)
        nav.js          sticky nav, scroll progress, mobile drawer
        hero.js         JSON hero typewriter + live "playtime" counter
  fonts/                self-hosted woff2 (Cormorant Garamond 600, Inter 400/600)
  img/                  me.webp/me.jpg, off-duty.webm, tool icons
favicon.png · apple-touch-icon.png · og-image.webp
robots.txt · sitemap.xml · 404.html
```

## Run locally

Any static file server works. E.g.:

```bash
python -m http.server 8000
# then open http://localhost:8000
```

Or just open `index.html` directly in a browser.

## Deploy

Deploy the folder as-is to any static host (Cloudflare Pages, Netlify, Vercel,
GitHub Pages, S3, nginx…). No build, no dependencies. Point the domain at it.

## Notes

- Fonts are latin-subset woff2, self-hosted, `font-display: swap`.
- `skyrim.gif` was re-encoded to a muted looping `off-duty.webm` (~69 KB) with a
  WebP poster frame.
- Reduced-motion users get static content (no reveal/typewriter).

