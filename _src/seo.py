#!/usr/bin/env python3
"""SEO layer for alabamaresourcedirectory.com.

Runs on the built site in the repo root. Safe to re-run: every block it adds is
wrapped in <!--x:NAME--> ... <!--/x:NAME--> markers and replaced on each run.

  python3 _src/seo.py            # from the repo root

What it does
  * county+need pages: city-aware titles/descriptions, "serving" line, FAQ (+FAQPage
    schema), nearby-county links, related guides, contractor quote box on repair pages,
    noindex for pages with no local or regional listing
  * county hubs: cities list, nearby counties, guides
  * city pages: /alabama/{county}/{city}/ for cities with 8+ programs located there
  * blog: /blog/ and /blog/{slug}/ from _src/blog/*.md
  * /get-repair-quotes/ lead page (contractor leads)
  * Blog link in nav, OG image + Twitter tags, Organization schema, sitemap, robots
"""
import os, re, json, html, glob, datetime, collections
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
DOMAIN = "https://www.alabamaresourcedirectory.com"
SITE = "Alabama Resource Directory"
TODAY = datetime.date.today().isoformat()
CHECKED = datetime.date.today().strftime("%B %Y")

# ---- CONFIG: paste a GoHighLevel form link here when it exists ----------------
REPAIR_FORM_URL = ""          # e.g. https://api.leadconnectorhq.com/widget/form/XXXX
CONTACT_EMAIL = "hello@alabamaresourcedirectory.com"
# -----------------------------------------------------------------------------

E = lambda s: html.escape(str(s), quote=True)
def T(s): return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)

def put(s, name, block, anchor, before=True):
    """Remove old block NAME, then insert new block before/after first `anchor`."""
    s = re.sub(r"<!--x:%s-->.*?<!--/x:%s-->" % (name, name), "", s, flags=re.S)
    if not block:
        return s
    b = "<!--x:%s-->%s<!--/x:%s-->" % (name, block, name)
    i = s.find(anchor)
    if i < 0:
        return s
    return s[:i] + b + s[i:] if before else s[:i + len(anchor)] + b + s[i + len(anchor):]

AG = json.load(open(os.path.join(ROOT, "assets/agent-data.json")))
NEEDS = AG["needs"]                       # key -> {s: slug, t: title}
SLUG2KEY = {v["s"]: k for k, v in NEEDS.items()}
COUNTIES = AG["counties"]                 # slug -> display
CITYMAP = AG["cities"]                    # city lower -> county slug
ADJ = json.load(open(os.path.join(SRC, "adj.json")))["adj"]
NAME2SLUG = {v.lower(): k for k, v in COUNTIES.items()}
def adj(slug):
    return [NAME2SLUG[n.lower()] for n in ADJ.get(COUNTIES[slug], []) if n.lower() in NAME2SLUG]

PHRASE = {
 "power": "help paying a power bill", "water": "help with a water bill or shutoff",
 "gas": "help paying a gas or heating bill", "plumbing": "help with plumbing repairs",
 "roof": "help with roof and home repairs", "food": "free food and food pantries",
 "rent": "help with rent or an eviction", "shelter": "emergency shelter",
 "clothing": "free clothing", "furniture": "free furniture or a bed",
 "transport": "a ride or transportation help",
 "equipment": "a wheelchair, ramp, prosthetic or medical equipment",
 "respite": "respite and caregiver help", "foster": "foster care, kinship or adoption support",
 "health": "free or low-cost medical and dental care",
 "benefits": "help with Social Security, SSI or Medicaid", "job": "job and income help"}
SHORT = {
 "power": "Power Bill Help", "water": "Water Bill Help", "gas": "Gas & Heating Bill Help",
 "plumbing": "Plumbing Repair Help", "roof": "Roof & Home Repair Help", "food": "Food Pantries",
 "rent": "Rent & Eviction Help", "shelter": "Homeless Shelters", "clothing": "Free Clothing",
 "furniture": "Free Furniture & Beds", "transport": "Rides & Transportation",
 "equipment": "Wheelchairs & Medical Equipment", "respite": "Respite & Caregiver Help",
 "foster": "Foster & Kinship Support", "health": "Free Medical & Dental Care",
 "benefits": "SSI, Social Security & Medicaid Help", "job": "Job & Income Help"}
LEADS = {"roof", "plumbing", "equipment"}     # needs that get the contractor quote box

def city_title(c):
    return " ".join(w if w in ("of",) else w[:1].upper() + w[1:] for w in c.split())
def cslug(c): return re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")

# ---------------------------------------------------------------- data from pages
def parse_page(s):
    items = []
    for rid, a in re.findall(r'<article class="res" id="r-([^"]+)">(.*?)</article>', s, re.S):
        g = lambda p: (re.search(p, a, re.S) or [None, ""])[1] if re.search(p, a, re.S) else ""
        ph = re.search(r'<a class="phone" href="tel:(\d+)">(.*?)</a>', a)
        items.append(dict(id=rid, html=a, name=T(g(r"<h3>(.*?)</h3>")),
            badge=T(g(r'<span class="badge[^"]*">(.*?)</span>')), local='class="badge local"' in a,
            phone=T(ph.group(2)) if ph else "", addr=T(g(r"<dt>Where</dt><dd>(.*?)</dd>")),
            desc=T(g(r"</div><p>(.*?)</p>")), who=T(g(r"<dt>Who</dt><dd>(.*?)</dd>"))))
    return items

PAGES = {}
for c in COUNTIES:
    for k, n in NEEDS.items():
        p = os.path.join(ROOT, "alabama", c, n["s"], "index.html")
        if os.path.exists(p):
            PAGES[(c, k)] = parse_page(rd(p))

def regional(i): return i["local"] and "67 Alabama" not in i["badge"]
def county_only(i, c): return i["local"] and i["badge"].endswith(COUNTIES[c] + " County, AL")

# programs physically located in each city
CITY = collections.defaultdict(dict)       # (city, county) -> id -> (item, set(needkeys))
for (c, k), items in PAGES.items():
    for i in items:
        if not (i["addr"] and i["local"]):
            continue
        a = i["addr"].lower()
        for city, cty in CITYMAP.items():
            if cty == c and re.search(r"\b" + re.escape(city) + r"\b", a):
                CITY[(city, c)].setdefault(i["id"], [i, set()])[1].add(k)
TOPCITY = collections.defaultdict(list)
for (city, c), d in sorted(CITY.items(), key=lambda x: -len(x[1])):
    TOPCITY[c].append((city, len(d)))
CITYPAGES = {(city, c) for (city, c), d in CITY.items() if len(d) >= 8}
def cities_of(c, n=3): return [city_title(x) for x, _ in TOPCITY[c][:n]]

# ---------------------------------------------------------------- blog
POSTS = []
for f in sorted(glob.glob(os.path.join(SRC, "blog", "*.md"))):
    raw = rd(f)
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    meta = dict(l.split(": ", 1) for l in m.group(1).splitlines() if ": " in l)
    meta["body"] = m.group(2)
    meta["slug"] = os.path.basename(f)[:-3]
    meta["needs"] = [x.strip() for x in meta.get("needs", "").split(",") if x.strip()]
    POSTS.append(meta)
POSTS.sort(key=lambda p: p["date"], reverse=True)
def guides_for(k): return [p for p in POSTS if k in p["needs"]]

# ---------------------------------------------------------------- shared chrome
SAMPLE = rd(os.path.join(ROOT, "about", "index.html"))
NAV_OLD = '<a href="/advertise/">Advertise</a><a class="pro" href="/for-organizations/">For organizations</a>'
NAV_NEW = '<a href="/blog/">Guides</a><a href="/advertise/">Advertise</a><a class="pro" href="/for-organizations/">For organizations</a>'
OGIMG = DOMAIN + "/assets/og.png"

def fix_chrome(s):
    if '<a href="/blog/">' not in s.split("</nav>", 1)[0]:
        s = s.replace(NAV_OLD, NAV_NEW, 1)
    # footer links
    s = s.replace('<a href="/about/">About</a> · <a href="/suggest/">',
                  '<a href="/about/">About</a> · <a href="/blog/">Guides</a> · <a href="/get-repair-quotes/">Repair quotes</a> · <a href="/suggest/">', 1) \
        if '/get-repair-quotes/">Repair quotes' not in s else s
    tags = ('<meta property="og:image" content="%s"><meta property="og:image:width" content="1200">'
            '<meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">'
            '<meta property="og:locale" content="en_US">' % OGIMG)
    s = put(s, "og", tags, "</head>")
    return s

def set_title(s, title, desc=None):
    s = re.sub(r"<title>.*?</title>", "<title>%s</title>" % E(title), s, count=1, flags=re.S)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(title), s, count=1)
    if desc:
        s = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + E(desc), s, count=1)
        s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + E(desc), s, count=1)
    return s

def set_robots(s, noindex):
    s = re.sub(r'<meta name="robots"[^>]*>', "", s)
    tag = '<meta name="robots" content="%s">' % ("noindex,follow" if noindex else "index,follow,max-image-preview:large,max-snippet:-1")
    return s.replace("<link rel=\"canonical\"", tag + "<link rel=\"canonical\"", 1)

def ld(obj): return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False)

def head(title, desc, path, extra="", noindex=False):
    url = DOMAIN + path
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>%s</title><meta name="description" content="%s">\n<meta name="robots" content="%s"><link rel="canonical" href="%s">\n'
        '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:type" content="website"><meta property="og:site_name" content="%s">\n'
        '<meta name="theme-color" content="#0b1626"><link rel="stylesheet" href="/assets/site.css">%s</head>'
        % (E(title), E(desc), "noindex,follow" if noindex else "index,follow,max-image-preview:large,max-snippet:-1",
           url, E(title), E(desc), url, SITE, extra))

BODY_TOP = SAMPLE[SAMPLE.index("<body>"):SAMPLE.index('<main id="main"')]
FOOT = SAMPLE[SAMPLE.index("</main>"):]
def page(title, desc, path, main, crumbs, extra_ld=(), noindex=False):
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(crumbs)]}
    cr = " › ".join('<a href="%s">%s</a>' % (u, E(n)) for n, u in crumbs[:-1]) + " › " + E(crumbs[-1][0])
    extra = ld(bc) + "".join(ld(x) for x in extra_ld)
    s = head(title, desc, path, extra, noindex) + BODY_TOP + '<main id="main" class="wrap"><nav class="crumbs" aria-label="Breadcrumb">%s</nav>%s' % (cr, main) + FOOT
    return fix_chrome(s)

# ---------------------------------------------------------------- reusable blocks
def jump(links): return '<div class="jump">' + "".join('<a href="%s">%s</a>' % (u, E(t)) for t, u in links) + "</div>"

def guides_block(k, county=None):
    gs = guides_for(k)
    if not gs:
        return ""
    return ('<section class="guides"><h2>Guides that can help</h2><ul class="glist">' +
            "".join('<li><a href="/blog/%s/">%s</a><span>%s</span></li>' % (p["slug"], E(p["title"]), E(p["summary"])) for p in gs[:3]) +
            "</ul></section>")

def quote_box(k, place):
    what = {"roof": "a roof repair or replacement", "plumbing": "a plumbing repair",
            "equipment": "a wheelchair ramp, grab bars or a walk-in shower"}[k]
    return ('<div class="box quote"><h3>🛠️ Don\'t qualify, or can\'t wait?</h3>'
            '<p style="margin:0 0 10px">Free programs have waiting lists. Get a no-cost quote for %s from a licensed contractor serving %s.</p>'
            '<a class="btn btn-sm" href="/get-repair-quotes/?need=%s&amp;area=%s">Get a free quote</a></div>' % (what, E(place), k, E(place)))

def faq_block(qas):
    h = '<section class="faq"><h2>Common questions</h2>' + "".join(
        '<details><summary>%s</summary><div>%s</div></details>' % (E(q), a) for q, a in qas) + "</section>"
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": T(a)}} for q, a in qas]}
    return h, ld(schema)

def listing_names(items, n=3):
    out = []
    for i in items[:n]:
        out.append("<b>%s</b>%s" % (E(i["name"]), " (%s)" % E(i["phone"]) if i["phone"] else ""))
    if len(out) > 1:
        return ", ".join(out[:-1]) + " and " + out[-1]
    return out[0] if out else ""

# ---------------------------------------------------------------- county + need pages
noindexed, indexed = set(), set()
for (c, k), items in PAGES.items():
    n = NEEDS[k]; cn = COUNTIES[c]; path = "/alabama/%s/%s/" % (c, n["s"])
    fp = os.path.join(ROOT, path.strip("/"), "index.html")
    s = rd(fp)
    loc = [i for i in items if regional(i)]
    only = [i for i in items if county_only(i, c)]
    cities = cities_of(c)
    total = len(items)
    noindex = not loc
    (noindexed if noindex else indexed).add(path)

    city_part = " (%s)" % cities[0] if cities else ""
    title = "%s in %s County, AL%s | %d Programs" % (SHORT[k], cn, city_part, total)
    if len(title) > 70:
        title = "%s in %s County, AL | %d Programs" % (SHORT[k], cn, total)
    near = (", ".join(cities[:2]) + " and nearby") if cities else "every town in the county"
    desc = ("%d programs for %s in %s County, Alabama, serving %s. %d are local. Phone numbers, who qualifies, what to bring." %
            (total, PHRASE[k], cn, near, len(loc)))
    s = set_title(s, title, desc)
    s = set_robots(s, noindex)

    serving = ('<p class="serving">Serving %s. %s Last checked %s.</p>' % (
        (", ".join(cities[:-1]) + " and " + cities[-1] + " and the rest of %s County" % cn) if len(cities) > 1 else
        ((cities[0] + " and the rest of %s County" % cn) if cities else "all of %s County" % cn),
        ("%d programs here are run in or for %s County alone." % (len(only), cn)) if only else
        "Most help here comes through regional and statewide programs that cover %s County." % cn,
        CHECKED))
    s = put(s, "serving", serving, '<form class="finder"')

    # FAQ
    first = only or loc or items
    bring = re.search(r'<h3>📋 What to bring</h3>.*?<ul>(.*?)</ul>', s, re.S)
    bring_t = ", ".join(T(x) for x in re.findall(r"<li>(.*?)</li>", bring.group(1))) if bring else "a photo ID, proof of address and proof of income"
    nb = adj(c)
    qas = [("Where can I get %s in %s County, Alabama?" % (PHRASE[k], cn),
            "Start with %s. This page lists %d programs that serve %s County: %d local or regional and %d statewide or national." %
            (listing_names([i for i in first if i["phone"]] or first), total, cn, len(loc), total - len(loc)))]
    ex = next((i for i in first if i["who"]), None)
    if ex:
        qas.append(("Who qualifies for %s in %s County?" % (PHRASE[k], cn),
                    "Every program sets its own rules, so read the <i>Who</i> line on each listing. For example, %s serves: %s." % (E(ex["name"]), E(ex["who"].rstrip(".")))))
    qas.append(("What should I bring when I apply?", "Most programs ask for: %s. Call first and ask what that office needs, since it changes." % E(bring_t)))
    qas.append(("What if every program says it is out of money?",
                "Funding opens and closes, often at the start of the month. Dial 2-1-1 (free, 24/7) and ask for %s near your address, and check programs in neighboring counties%s that may serve you." %
                (PHRASE[k], (" like " + ", ".join(COUNTIES[x] for x in nb[:3])) if nb else "")))
    fh, fs = faq_block(qas)
    s = put(s, "faqld", fs, "</head>")

    blocks = fh
    if nb:
        blocks += "<h2>%s in nearby counties</h2>" % E(n["t"]) + jump(
            [("%s County" % COUNTIES[x], "/alabama/%s/%s/" % (x, n["s"])) for x in nb])
    cps = [(city, cc) for (city, cc) in CITYPAGES if cc == c]
    if cps:
        blocks += "<h2>Help by city in %s County</h2>" % E(cn) + jump(
            [(city_title(city) + ", AL", "/alabama/%s/%s/" % (c, cslug(city))) for city, _ in sorted(cps)])
    blocks += guides_block(k)
    s = put(s, "more", blocks, "<h2>Other help in ")
    s = put(s, "quote", quote_box(k, "%s County" % cn) if k in LEADS else "", '<aside class="side">', before=False)
    s = fix_chrome(s)
    wr(fp, s)

# ---------------------------------------------------------------- city pages
for (city, c) in sorted(CITYPAGES):
    d = CITY[(city, c)]; ct = city_title(city); cn = COUNTIES[c]
    path = "/alabama/%s/%s/" % (c, cslug(city))
    by = collections.defaultdict(list)
    for iid, (item, ks) in d.items():
        k0 = sorted(ks, key=lambda x: list(NEEDS).index(x))[0]
        by[k0].append((item, ks))
    needs_here = [k for k in NEEDS if k in by]
    main = ('<h1>Free help in <em>%s</em>, Alabama</h1><p class="lede">%d programs with an office in %s, %s County: %s and more. '
            'Each listing has the phone number, who qualifies and what to bring. Last checked %s.</p>' %
            (E(ct), len(d), E(ct), E(cn), ", ".join(SHORT[k].lower() for k in needs_here[:4]), CHECKED))
    main += jump([(SHORT[k], "#" + NEEDS[k]["s"]) for k in needs_here])
    main += '<div class="layout"><div>'
    items_ld = []
    for k in needs_here:
        main += '<h2 id="%s">%s in %s</h2>' % (NEEDS[k]["s"], E(NEEDS[k]["t"]), E(ct))
        for item, ks in sorted(by[k], key=lambda x: x[0]["name"]):
            a = item["html"]
            a = re.sub(r'<a class="fix" href="[^"]*">', '<a class="fix" href="/suggest/?listing=%s&amp;county=%s">' % (E(item["name"]), E(cn)), a)
            also = [x for x in NEEDS if x in ks and x != k]
            if also:
                a = a.replace('<div class="acts">', '<p class="muted" style="font-size:15px;margin:8px 0 0">Also helps with: %s</p><div class="acts">' %
                              ", ".join('<a href="/alabama/%s/%s/">%s</a>' % (c, NEEDS[x]["s"], E(SHORT[x])) for x in also), 1)
            main += '<article class="res">%s</article>' % a
            o = {"@type": "Organization", "name": item["name"]}
            if item["phone"]: o["telephone"] = item["phone"]
            if item["addr"]: o["address"] = item["addr"]
            items_ld.append(o)
        main += '<p><a href="/alabama/%s/%s/">See all %d programs for %s in %s County →</a></p>' % (
            c, NEEDS[k]["s"], len(PAGES.get((c, k), [])), E(SHORT[k].lower()), E(cn))
    others = [(city_title(x) + ", AL", "/alabama/%s/%s/" % (cc, cslug(x))) for (x, cc) in sorted(CITYPAGES) if cc in [c] + adj(c) and x != city]
    main += "<h2>Countywide help</h2><p>Programs that cover all of %s County, including statewide ones, are on the county pages:</p>" % E(cn)
    main += jump([(SHORT[k], "/alabama/%s/%s/" % (c, NEEDS[k]["s"])) for k in NEEDS])
    if others:
        main += "<h2>Nearby cities</h2>" + jump(others)
    main += ('</div><aside class="side"><div class="box"><h3>Need help now?</h3><p style="margin:0">Dial <a href="tel:211">2-1-1</a> any time for local help. '
             'In a crisis, call or text <a href="tel:988">988</a>.</p></div>'
             '<aside class="ad house" aria-label="Sponsor spot"><span class="ad-lbl">Sponsor spot</span><p><b>Your business here.</b> Reach %s families looking for help.</p>'
             '<a class="btn btn-sm" href="/advertise/#contact">Advertise here</a></aside>%s</aside></div>' % (E(ct), quote_box("roof", ct)))
    title = "Free Help in %s, AL: Bills, Food, Rent & Repairs | %d Programs" % (ct, len(d))
    desc = "%d assistance programs with offices in %s, Alabama (%s County): %s. Phone numbers, who qualifies and what to bring." % (
        len(d), ct, cn, ", ".join(SHORT[k].lower() for k in needs_here[:5]))
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": "Assistance programs in %s, Alabama" % ct,
          "numberOfItems": len(items_ld), "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": o} for i, o in enumerate(items_ld[:100])]}
    wr(os.path.join(ROOT, path.strip("/"), "index.html"),
       page(title, desc, path, main, [("Home", "/"), ("Alabama counties", "/alabama/"), ("%s County" % cn, "/alabama/%s/" % c), (ct, path)], [il]))
    indexed.add(path)

# ---------------------------------------------------------------- county hubs
for c, cn in COUNTIES.items():
    fp = os.path.join(ROOT, "alabama", c, "index.html")
    s = rd(fp)
    cities = cities_of(c)
    cnt = re.search(r"(\d+) programs serve", s)
    total = cnt.group(1) if cnt else ""
    title = "Free Help in %s County, AL%s: Bills, Food, Rent | %s Programs" % (cn, (" (" + cities[0] + ")") if cities else "", total)
    if len(title) > 72:
        title = "Free Help in %s County, AL: Bills, Food, Rent | %s Programs" % (cn, total)
    s = set_title(s, title, None)
    s = set_robots(s, False)
    blk = ""
    cps = sorted(x for (x, cc) in CITYPAGES if cc == c)
    if cps:
        blk += "<h2>Help by city</h2>" + jump([(city_title(x) + ", AL", "/alabama/%s/%s/" % (c, cslug(x))) for x in cps])
    if cities:
        blk += '<p class="muted">Programs on these pages serve %s and every other town in %s County.</p>' % (", ".join(cities), E(cn))
    nb = adj(c)
    if nb:
        blk += "<h2>Nearby counties</h2>" + jump([("%s County" % COUNTIES[x], "/alabama/%s/" % x) for x in nb])
    if POSTS:
        blk += "<h2>Guides</h2>" + jump([(p["title"], "/blog/%s/" % p["slug"]) for p in POSTS[:4]])
    s = put(s, "hub", blk, "</main>")
    wr(fp, fix_chrome(s))
    indexed.add("/alabama/%s/" % c)

# ---------------------------------------------------------------- statewide need pages
for k, n in NEEDS.items():
    fp = os.path.join(ROOT, "help", n["s"], "index.html")
    if not os.path.exists(fp):
        continue
    s = rd(fp)
    s = put(s, "guides", guides_block(k), "</main>")
    if k in LEADS:
        s = put(s, "quote", '<div class="wrap" style="padding:0">%s</div>' % quote_box(k, "your county"), "</main>")
    wr(fp, fix_chrome(s))
    indexed.add("/help/%s/" % n["s"])

# ---------------------------------------------------------------- blog pages
BLOG_CSS = ""
def post_html(p):
    body = markdown.markdown(p["body"], extensions=["tables"])
    body = re.sub(r"<thead>\s*<tr>\s*(<th></th>\s*)+</tr>\s*</thead>", "", body)
    path = "/blog/%s/" % p["slug"]
    rel = [x for x in POSTS if x is not p and set(x["needs"]) & set(p["needs"])][:3] or [x for x in POSTS if x is not p][:3]
    side = '<aside class="side"><div class="box"><h3>Find help by county</h3><form class="finder" style="grid-template-columns:1fr;padding:0;border:0;margin:0;background:none" role="search"><div><label for="fc">County</label><select id="fc" name="c"><option value="">Choose a county</option>%s</select></div><input type="hidden" name="n" value="%s"><button class="btn" type="submit">Find help</button></form></div>' % (
        "".join('<option value="%s">%s County</option>' % (x, E(y)) for x, y in COUNTIES.items()),
        NEEDS[p["needs"][0]]["s"] if p["needs"] else "")
    if set(p["needs"]) & LEADS:
        side += quote_box(sorted(set(p["needs"]) & LEADS)[0], "your county")
    side += '<aside class="ad house" aria-label="Sponsor spot"><span class="ad-lbl">Sponsor spot</span><p><b>Your business here.</b> Reach Alabama families looking for help.</p><a class="btn btn-sm" href="/advertise/#contact">Advertise here</a></aside></aside>'
    main = ('<div class="layout"><article class="post"><h1>%s</h1><p class="meta">By the %s team · Updated <time datetime="%s">%s</time></p>%s'
            '<div class="box" style="margin-top:28px"><b>Every program changes.</b> Call before you go, and dial 2-1-1 for anything not listed. '
            'See something wrong? <a href="/suggest/">Tell us</a>.</div>' % (
            E(p["title"]), SITE, p["date"], datetime.date.fromisoformat(p["date"]).strftime("%B %-d, %Y"), body))
    if rel:
        main += "<h2>Related guides</h2><ul class=\"glist\">" + "".join('<li><a href="/blog/%s/">%s</a><span>%s</span></li>' % (x["slug"], E(x["title"]), E(x["summary"])) for x in rel) + "</ul>"
    main += "</article>" + side + "</div>"
    art = {"@context": "https://schema.org", "@type": "Article", "headline": p["title"], "description": p["summary"],
           "datePublished": p["date"], "dateModified": p.get("updated", p["date"]), "mainEntityOfPage": DOMAIN + path,
           "image": OGIMG, "author": {"@type": "Organization", "name": SITE, "url": DOMAIN + "/about/"},
           "publisher": {"@type": "Organization", "name": SITE, "logo": {"@type": "ImageObject", "url": DOMAIN + "/assets/logo.png"}}}
    return page(p.get("seo_title", p["title"]) + " | " + SITE if len(p.get("seo_title", p["title"])) < 45 else p.get("seo_title", p["title"]),
                p["summary"], path, main, [("Home", "/"), ("Guides", "/blog/"), (p["title"], path)], [art])

for p in POSTS:
    wr(os.path.join(ROOT, "blog", p["slug"], "index.html"), post_html(p))
    indexed.add("/blog/%s/" % p["slug"])
if POSTS:
    main = ('<h1>Guides to <em>getting help</em> in Alabama</h1><p class="lede">Plain-English, step-by-step guides to bill help, home repairs, benefits and more, '
            'written from the programs in this directory.</p><ul class="glist big">' +
            "".join('<li><a href="/blog/%s/">%s</a><span>%s</span></li>' % (p["slug"], E(p["title"]), E(p["summary"])) for p in POSTS) + "</ul>")
    bl = {"@context": "https://schema.org", "@type": "Blog", "name": SITE + " Guides", "url": DOMAIN + "/blog/",
          "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": DOMAIN + "/blog/%s/" % p["slug"], "datePublished": p["date"]} for p in POSTS]}
    wr(os.path.join(ROOT, "blog", "index.html"),
       page("Guides: How to Get Help With Bills, Repairs & Benefits in Alabama", "Step-by-step guides to LIHEAP, Alabama Power bill help, free roof and home repair programs, ramps and more in Alabama.",
            "/blog/", main, [("Home", "/"), ("Guides", "/blog/")], [bl]))
    indexed.add("/blog/")

# ---------------------------------------------------------------- repair quote lead page
form = ('<iframe src="%s" style="width:100%%;min-height:720px;border:0;border-radius:14px;background:#fff" title="Request a repair quote" loading="lazy"></iframe>' % E(REPAIR_FORM_URL)) if REPAIR_FORM_URL else (
    '<form class="box lead" id="leadform" action="mailto:%s" method="post" enctype="text/plain">'
    '<label>What do you need?<select name="need"><option value="roof">Roof repair or replacement</option><option value="plumbing">Plumbing repair</option>'
    '<option value="equipment">Wheelchair ramp, grab bars or accessible bathroom</option><option value="other">Other home repair</option></select></label>'
    '<label>County or city<input name="area" required></label><label>Your name<input name="name" required autocomplete="name"></label>'
    '<label>Phone<input name="phone" type="tel" required autocomplete="tel"></label><label>Email (optional)<input name="email" type="email" autocomplete="email"></label>'
    '<label>Tell us about the job<textarea name="details" rows="4"></textarea></label>'
    '<label class="chk"><input type="checkbox" required name="consent" value="yes"> I agree to be contacted by phone, text or email about my request by up to 3 local contractors. Consent is not required to buy anything.</label>'
    '<button class="btn" type="submit">Request my free quotes</button></form>' % CONTACT_EMAIL)
main = ('<div class="layout"><div><h1>Free repair quotes from <em>local contractors</em></h1>'
        '<p class="lede">Free repair programs often have long waiting lists or strict income rules. If you don\'t qualify or can\'t wait, '
        'tell us about the job and licensed Alabama contractors will call you with a quote. It costs nothing to ask.</p>%s'
        '<p class="muted" style="font-size:15px">Contractors pay to receive requests, which keeps this directory free. We never sell your information to lenders. '
        'Still want a free program? See <a href="/help/roof-home-repair-help/">roof and home repair help</a>, <a href="/help/plumbing-repair-help/">plumbing repair help</a> '
        'and <a href="/blog/free-roof-replacement-programs-alabama/">free roof programs in Alabama</a>.</p></div>'
        '<aside class="side"><div class="box"><h3>Are you a contractor?</h3><p style="margin:0 0 10px">Get exclusive repair requests from homeowners in your counties. Roofing, plumbing, HVAC, ramps and accessibility.</p>'
        '<a class="btn btn-sm" href="/advertise/#contractors">Get repair leads</a></div></aside></div>'
        '<script>(function(){var p=new URLSearchParams(location.search),f=document.getElementById("leadform");if(!f)return;'
        'if(p.get("need"))f.need.value=p.get("need");if(p.get("area"))f.area.value=p.get("area");})()</script>') % form
wr(os.path.join(ROOT, "get-repair-quotes", "index.html"),
   page("Free Roof, Plumbing & Ramp Repair Quotes in Alabama | " + SITE, "Don't qualify for a free repair program? Get free quotes from licensed local Alabama contractors for roofs, plumbing, ramps and accessibility.",
        "/get-repair-quotes/", main, [("Home", "/"), ("Repair quotes", "/get-repair-quotes/")]))
indexed.add("/get-repair-quotes/")

# ---------------------------------------------------------------- advertise: contractor leads section
fp = os.path.join(ROOT, "advertise", "index.html")
s = rd(fp)
s = put(s, "contractors", '<section id="contractors" class="cta"><h2 style="margin-top:0">Repair leads for contractors</h2>'
    '<p>Homeowners on our roof, plumbing and accessibility pages who don\'t qualify for free programs can ask for quotes. '
    'We send each request to no more than 3 contractors in that county, or to one contractor exclusively.</p>'
    '<ul><li><b>Exclusive county territory</b>: every repair request in your counties, flat monthly fee</li>'
    '<li><b>Pay per lead</b>: only pay for requests you accept</li><li><b>Featured contractor</b>: your name, phone and badge at the top of repair pages in your county</li></ul>'
    '<a class="btn" href="mailto:%s?subject=Contractor%%20leads">Ask about your counties</a></section>' % CONTACT_EMAIL, "</main>")
wr(fp, fix_chrome(s))

# ---------------------------------------------------------------- home + every other page
fp = os.path.join(ROOT, "index.html")
s = rd(fp)
org = {"@context": "https://schema.org", "@type": "Organization", "name": SITE, "url": DOMAIN + "/", "logo": DOMAIN + "/assets/logo.png",
       "email": CONTACT_EMAIL, "areaServed": {"@type": "State", "name": "Alabama"},
       "description": "Free directory of assistance programs in all 67 Alabama counties."}
s = put(s, "org", ld(org), "</head>")
top = sorted(CITYPAGES, key=lambda x: (-len(CITY[x]), x))[:24]
blk = "<h2>Popular cities</h2>" + jump([(city_title(x) + ", AL", "/alabama/%s/%s/" % (c, cslug(x))) for x, c in top])
if POSTS:
    blk += '<h2>Guides</h2><ul class="glist">' + "".join('<li><a href="/blog/%s/">%s</a><span>%s</span></li>' % (p["slug"], E(p["title"]), E(p["summary"])) for p in POSTS[:6]) + "</ul>"
s = put(s, "homeblk", blk, "</main>")
wr(fp, fix_chrome(s))

for fp in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
    rel = "/" + os.path.relpath(os.path.dirname(fp), ROOT).replace(os.sep, "/") + "/"
    rel = "/" if rel == "/./" else rel
    if rel.startswith(("/_src", "/kb", "/demo", "/.git")):
        continue
    s = rd(fp); s2 = fix_chrome(s)
    if s2 != s:
        wr(fp, s2)
    if rel in ("/", "/alabama/", "/help/", "/about/", "/advertise/", "/for-organizations/", "/search/", "/suggest/", "/privacy/"):
        indexed.add(rel)

# 404 must not carry a canonical
fp = os.path.join(ROOT, "404.html"); s = rd(fp)
s = re.sub(r'<link rel="canonical"[^>]*>', "", s)
if '<meta name="robots"' not in s:
    s = s.replace("<title>", '<meta name="robots" content="noindex"><title>', 1)
wr(fp, fix_chrome(s))

# ---------------------------------------------------------------- css
CSS = """
.serving{color:var(--mute);margin:-4px 0 0;max-width:760px}
.faq details{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:0 0 8px}
.faq summary{cursor:pointer;font-weight:800}.faq details div{margin-top:8px}
.glist{list-style:none;padding:0;display:grid;gap:10px}.glist li{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.glist a{font:800 18px var(--display);text-decoration:none}.glist span{display:block;color:var(--mute);font-size:15px;margin-top:4px}
.box.quote{border-color:var(--volt)}
.post{max-width:760px}.post .meta{color:var(--mute);font-size:15px}.post h2{font-size:24px}.post li{margin:4px 0}
.post table{border-collapse:collapse;width:100%;margin:12px 0}.post td,.post th{border:1px solid var(--line);padding:8px;text-align:left}
.lead label{display:block;font-weight:700;margin:0 0 12px}.lead input,.lead select,.lead textarea{display:block;width:100%;margin-top:6px;font:inherit;padding:12px;border-radius:10px;border:2px solid var(--line);background:var(--bg);color:var(--ink)}
.lead .chk{font-weight:500;font-size:15px;display:flex;gap:10px;align-items:flex-start}.lead .chk input{width:auto;margin-top:4px}
"""
fp = os.path.join(ROOT, "assets", "site.css"); s = rd(fp)
s = re.sub(r"/\*x:seo\*/.*?/\*/x:seo\*/", "", s, flags=re.S) + "/*x:seo*/" + CSS + "/*/x:seo*/"
wr(fp, s)

# ---------------------------------------------------------------- sitemap + robots
def pri(u):
    if u == "/": return "1.0"
    if u.count("/") <= 3: return "0.8"
    return "0.6"
urls = sorted(u for u in indexed if u not in noindexed)
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sm.append("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (DOMAIN, u, TODAY, pri(u)))
sm.append("</urlset>")
wr(os.path.join(ROOT, "sitemap.xml"), "\n".join(sm) + "\n")
wr(os.path.join(ROOT, "robots.txt"), "User-agent: *\nAllow: /\nDisallow: /demo/\nDisallow: /_src/\n\nSitemap: %s/sitemap.xml\n" % DOMAIN)

print("county+need pages:", len(PAGES), "| noindexed (no local listing):", len(noindexed),
      "| city pages:", len(CITYPAGES), "| posts:", len(POSTS), "| sitemap urls:", len(urls))
