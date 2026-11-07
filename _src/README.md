# Site tools (not part of the public pages)

Everything data-driven on the site is generated from `data.json`. Run from the repo root:

    pip install markdown zipcodes        # first time only
    python3 _src/build.py                # county pages, county hubs, /help/ pages, search + agent data
    python3 _src/seo.py                  # SEO layer, city pages, blog, /near/, sitemap (always run after build.py)
    python3 _src/kbgen.py                # optional: /kb/ pages for the GoHighLevel AI assistant

Then commit and push; GitHub Pages deploys in a few minutes.

## What is generated vs. hand-written

| Generated (don't hand-edit, your change will be overwritten) | Hand-written (edit the page directly) |
| --- | --- |
| `alabama/{county}/{need}/`, `alabama/{county}/`, `help/{need}/` (build.py) | home `index.html`, `alabama/index.html`, `help/index.html` |
| city pages, `blog/`, `near/`, `get-repair-quotes/`, `sitemap.xml`, `robots.txt` (seo.py) | `about/`, `advertise/`, `for-organizations/`, `suggest/`, `privacy/`, `search/`, `404.html` |
| `assets/search-index.json`, `assets/agent-data.json` (build.py), `assets/near.json` (seo.py) | `assets/site.css`, `site.js`, `near.js`, `agent.js`, `demo/` |
| `kb/` (kbgen.py) | `_src/blog/*.md` (blog posts) |

seo.py wraps everything it adds to a page in `<!--x:NAME-->` markers; edit seo.py, not the marked text.

## data.json

- `needs`: the 17 needs, in display order. `key`, `slug` (URL), `title`, `phrase` (used in ledes and tiles),
  `bring` (which "What to bring" list), `icon` (tile SVG), `kb_label` and `short` (knowledge-base pages).
- `counties`: slug -> name, in display order. `cities`, `zips`, `bring`: lookup tables.
- `programs`: every listing, **in display order** (pages show them in this order; local programs are grouped first).

A program:

```json
{
  "id": "lc999",                       // unique, used in #r-id links; never reuse
  "name": "Example Food Pantry",
  "alias": "Example Church",           // optional second line
  "local": true,                       // true = "Local" section; false = statewide section
  "badge": "Local · Shelby County, AL",
  "tag": "Book now: funds run out",    // optional second badge
  "desc": "Food pantry Tuesdays 9-11am.",
  "phone": "(205) 555-0100 ext. 2",    // or "phone_web": "https://..." or "phone_note": "Apply online"
  "who": "Shelby County residents",
  "where": "123 Main St, Alabaster 35007",
  "email": "info@example.org",
  "notes": "Call first.",              // shown as "Good to know"
  "bring": ["Photo ID", "Proof of income"],
  "apply": "https://...",
  "web": "https://...",
  "needs": ["food"],                   // need keys; [] for general-only programs
  "counties": ["shelby"],              // county slugs, or "all"
  "general": true                      // optional: also list under "General help for anyone" on county hubs
}
```

Only `id`, `name`, `local`, `badge`, `needs` and `counties` are required. The click-to-call link is worked out
from `phone` (first number, plus its extension). A program appears on every county + need page where both its
`counties` and `needs` match. Statewide programs (`"counties": "all"`, `"local": false`) also appear on `/help/{need}/`.

## Other files

- `seo.py`: SEO layer. CONFIG at the top: `REPAIR_FORM_URL` (GoHighLevel repair-quote form link) and
  `ADSENSE_ID` (turns on Google Auto ads site-wide and writes `ads.txt`).
- `blog/*.md`: one file per guide. Front matter: title, seo_title, summary, date, needs (need keys: power, water,
  gas, plumbing, roof, food, rent, shelter, clothing, furniture, transport, equipment, respite, foster, health,
  benefits, job). New posts appear on the blog, on matching county pages and in the sitemap automatically.
- `adj.json`: which Alabama counties border each other (from Census county shapes).
- `parse.py`: pulls listing data back out of built pages (recovery tool).

## Closest-first address search (/near/)
- `assets/near.js` geocodes the visitor's address in the browser (OpenStreetMap Nominatim, ZIP fallback) and sorts programs by distance.
- Program locations: `_src/geo.json` (street-level, from the Census batch geocoder); anything not matched falls back to its ZIP center (`_src/al_zips.json`) or town center and shows "approx.".
- To re-geocode after adding programs: rebuild `_src/geocode_in.csv` (id,street,city,AL,zip), upload it at geocoding.geo.census.gov (Batch, Public_AR_Current), and merge the matched id,lat,lon into `geo.json`. Then run build.py and seo.py.
