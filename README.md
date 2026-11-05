# Florida's On The Fly Charters — website

Static HTML/CSS/JS site built from the Figma design (B2 system). No framework.

- `site-src/pages/*.html` — page bodies, each with a small header block (title, description, URL path).
- `site-src/build.py` — wraps every page with the shared head, top bar, nav, mega menu, mobile menu, footer, sticky mobile bar and booking popup, then writes `site/<path>/index.html`. Run `python3 florida-on-the-fly/site-src/build.py`.
- `site/` — the deployable site (Vercel Root Directory = `florida-on-the-fly/site`, preset "Other").
- `site/css/styles.css` — one stylesheet; colors and fonts are variables at the top.
- `site/js/site.js` — one script. **Paste the real booking link and form endpoint into `SITE_CONFIG` at the top.**
- `site/vercel.json` — clean URLs, redirects from old URLs, cache headers.

## Before launch
1. `site-src/build.py`: set `BLOCK_INDEXING = False` (it currently adds noindex tags, a disallow-all robots.txt and an X-Robots-Tag header), fill in the `SOCIAL` links, and rebuild.
2. `site/js/site.js`: set `BOOKING_URL` and `FORM_ENDPOINT`.
3. Replace the Figma-captured photos in `site/img/` with the originals (same file names).

Preview locally: `cd florida-on-the-fly/site && python3 -m http.server 8080`.
