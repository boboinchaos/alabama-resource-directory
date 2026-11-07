#!/usr/bin/env python3
"""Page generator for alabamaresourcedirectory.com.

Builds every data-driven page from _src/data.json:
  /alabama/{county}/{need}/   county + need listing pages (about 1,100)
  /alabama/{county}/          county hubs
  /help/{need}/               statewide need pages
  assets/agent-data.json      data the AI assistant and seo.py read
  assets/search-index.json    data for /search/

Hand-written pages (home, /alabama/, /help/, about, advertise, for-organizations,
suggest, privacy, search, 404, demo) are edited directly and never touched here.

Run from the repo root, then run the SEO pass and the knowledge-base pages:

    python3 _src/build.py && python3 _src/seo.py && python3 _src/kbgen.py

To add or change a program, edit _src/data.json (see _src/README.md).
"""
import os, re, json, html, datetime, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
OUT = os.environ.get("BUILD_OUT", ROOT)          # write somewhere else for testing

# ---- CONFIG ---------------------------------------------------------------------
DOMAIN = "https://www.alabamaresourcedirectory.com"
SITE = "Alabama Resource Directory"
LOCAL_FIRST_AD_AFTER = 10      # sponsor slot goes after this many local listings
# -------------------------------------------------------------------------------

D = json.load(open(os.path.join(SRC, "data.json"), encoding="utf-8"))
NEEDS = D["needs"]                                   # list of {key, slug, title, phrase, bring, icon}
NK = {n["key"]: n for n in NEEDS}
COUNTIES = D["counties"]                             # slug -> name, in display order
PROGS = D["programs"]                                # global display order
CHECKED = datetime.date.today().strftime("%B %Y")
YEAR = datetime.date.today().year

E = lambda s: html.escape(str(s), quote=True)
def q(s, safe=""): return urllib.parse.quote(s, safe=safe)
def wr(path, s):
    p = os.path.join(OUT, path.strip("/"), "index.html") if not path.endswith((".json",)) else os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

def serves(p, c): return p["counties"] == "all" or c in p["counties"]
def on_page(c, k): return [p for p in PROGS if k in p["needs"] and serves(p, c)]

# ---------------------------------------------------------------- one listing
EXT = ' rel="nofollow noopener" target="_blank"'
LBL = {"who": "Who", "where": "Where", "email": "Email", "notes": "Good to know", "bring": "Bring", "amount": "Amount"}

def tel_digits(phone):
    """Click-to-call target: the first phone number in the text, plus its extension."""
    m = re.search(r"(?:1[\s.-]?)?\(?(\d{3})\)?[\s.-]*(\d{3})[\s.-]*(\d{4})(?:\s*(?:ext\.?|x)\s*(\d+))?", phone, re.I)
    if m: return "".join(m.groups()[:3]) + ("," + m.group(4) if m.group(4) else "")
    m = re.search(r"\d[\d-]*", phone)                 # short codes: 2-1-1, 988, 711
    return re.sub(r"\D", "", m.group(0)) if m else ""

def listing(p, county=None):
    o = ["<h3>%s</h3>" % E(p["name"])]
    if p.get("alias"): o.append('<p class="alias">%s</p>' % E(p["alias"]))
    o.append('\n<div><span class="badge%s">%s</span>%s</div>' % (
        " local" if p["local"] else "", E(p["badge"]), ('<span class="badge">%s</span>' % E(p["tag"])) if p.get("tag") else ""))
    if "desc" in p: o.append("<p>%s</p>" % E(p["desc"]))
    if p.get("phone"):
        o.append('<a class="phone" href="tel:%s">%s</a>' % (tel_digits(p["phone"]), E(p["phone"])))
    elif p.get("phone_web"):
        o.append('<a class="phone" href="%s"%s>No phone listed · Website ↗</a>' % (E(p["phone_web"]), EXT))
    else:
        o.append('<span class="muted">%s</span>' % E(p.get("phone_note") or "No phone listed: visit, or ask 2-1-1 for hours"))
    o.append("\n<dl>")
    for k in p.get("field_order") or LBL:
        if k not in p: continue
        v = p[k]
        if k == "where":
            v = E(v) if p.get("where_nolink") else '<a href="https://www.google.com/maps/search/?api=1&query=%s"%s>%s</a>' % (q(v), EXT, E(v))
        elif k == "email": v = '<a href="mailto:%s">%s</a>' % (E(v), E(v))
        elif k == "bring": v = "<ul>" + "".join("<li>%s</li>" % E(x) for x in v) + "</ul>"
        else: v = E(v)
        o.append("<dt>%s</dt><dd>%s</dd>" % (LBL[k], v))
    o.append('</dl>\n<div class="acts">')
    if p.get("apply"): o.append('<a class="btn btn-sm" href="%s"%s>Apply</a>' % (E(p["apply"]), EXT))
    if p.get("web"): o.append('<a class="btn btn-sm btn-ghost" href="%s"%s>Website</a>' % (E(p["web"]), EXT))
    fix = "/suggest/?listing=%s" % q(p["name"], "/") + ("&amp;county=%s" % q(county) if county else "")
    o.append('<a class="fix" href="%s">Wrong info? Tell us</a></div>' % fix)
    return '<article class="res" id="r-%s">%s</article>' % (p["id"], "".join(o))

def org_ld(p):
    it = {"@type": "Organization", "name": p["name"]}
    if p.get("phone"): it["telephone"] = p["phone"]
    if p.get("where") and not p.get("where_nolink"): it["address"] = p["where"]
    url = p.get("web")
    if url: it["url"] = url
    if p.get("desc"): it["description"] = p["desc"]
    return it

# ---------------------------------------------------------------- page chrome
def ld(obj): return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False)

def head(title, desc, path, lds, robots=True):
    url = DOMAIN + path
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%s</title><meta name="description" content="%s">\n%s<link rel="canonical" href="%s">\n'
            '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:type" content="website"><meta property="og:site_name" content="%s">\n'
            '<meta name="theme-color" content="#0b1626"><link rel="stylesheet" href="/assets/site.css">%s\n</head>'
            % (E(title), E(desc), '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">' if robots else "",
               url, E(title), E(desc), url, SITE, "".join(ld(x) for x in lds)))

TOP = ('<body><a class="skip" href="#main">Skip to main content</a>\n<header class="top"><div class="wrap"><a class="logo" href="/"><i aria-hidden="true">✚</i>%s</a>\n'
       '<nav class="main" aria-label="Main"><a href="/alabama/">Counties</a><a href="/help/">Types of help</a><a href="/search/">Search</a><a href="/blog/">Guides</a>'
       '<a href="/advertise/">Advertise</a><a class="pro" href="/for-organizations/">For organizations</a></nav></div></header>\n' % SITE)

def foot():
    return ('</main><footer><div class="wrap">\n<p><b>%s</b> lists free and low-cost help in all 67 Alabama counties. Programs checked %s. '
            'Funding opens and closes, so call to confirm before you go. We don\'t run these programs and can\'t promise eligibility.</p>\n'
            '<p>In a crisis, call or text <a href="tel:988">988</a>. For any local help, dial <a href="tel:211">2-1-1</a>. Emergencies: <a href="tel:911">911</a>.</p>\n'
            '<p><a href="/about/">About</a> · <a href="/blog/">Guides</a> · <a href="/get-repair-quotes/">Repair quotes</a> · <a href="/suggest/">Suggest or fix a listing</a> · '
            '<a href="/advertise/">Advertise</a> · <a href="/for-organizations/">For organizations</a> · <a href="/privacy/">Privacy</a> · <a href="/sitemap.xml">Sitemap</a></p>\n'
            '<p>© %d %s</p></div></footer><script src="/assets/site.js" defer></script><script src="/assets/agent.js" defer></script></body></html>'
            % (SITE, CHECKED, YEAR, SITE))

def crumbs(items):
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(items)]}
    html_ = " › ".join('<a href="%s">%s</a>' % (u, E(n)) for n, u in items[:-1]) + " › " + E(items[-1][0])
    return bc, '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>' % html_

def itemlist(name, progs):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "numberOfItems": len(progs),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": org_ld(p)} for i, p in enumerate(progs[:100])]}

def finder(c="", n=""):
    co = "".join('<option value="%s"%s>%s County</option>' % (s, " selected" if s == c else "", E(nm)) for s, nm in COUNTIES.items())
    ne = "".join('<option value="%s"%s>%s</option>' % (x["slug"], " selected" if x["slug"] == n else "", E(x["title"])) for x in NEEDS)
    return ('<form class="finder" role="search" aria-label="Find help"><div><label for="fc">County</label><select id="fc" name="c"><option value="">Choose a county</option>%s</select></div>\n'
            '<div><label for="fn">What do you need?</label><select id="fn" name="n"><option value="">Any kind of help</option>%s</select></div><button class="btn" type="submit">Find help</button></form>' % (co, ne))

def sponsor(text):
    return ('<aside class="ad house" aria-label="Sponsor spot"><span class="ad-lbl">Sponsor spot</span><p><b>Your business here.</b> %s</p>'
            '<a class="btn btn-sm" href="/advertise/#contact">Advertise here</a></aside>' % E(text))

def side(bring_key, spon):
    items = "".join("<li>%s</li>" % E(x) for x in D["bring"][bring_key])
    return ('<aside class="side"><div class="box"><h3>📋 What to bring</h3><p class="muted" style="margin:0">Most programs ask for:</p><ul>%s</ul></div>%s'
            '<div class="box"><h3>Help people for a living?</h3><p style="margin:0 0 10px">Case managers and advocates: build a one-page Help Action Plan, email it as a PDF and keep client records with the Pro version.</p>'
            '<a class="btn btn-sm" href="/for-organizations/">See Pro features</a></div></aside>' % (items, spon))

# ---------------------------------------------------------------- county + need pages
def county_need(c, n):
    cn = COUNTIES[c]; k = n["key"]; path = "/alabama/%s/%s/" % (c, n["slug"])
    items = on_page(c, k)
    loc = [p for p in items if p["local"]]; sw = [p for p in items if not p["local"]]
    bc, cr = crumbs([("Home", "/"), ("Alabama counties", "/alabama/"), ("%s County" % cn, "/alabama/%s/" % c), (n["title"], path)])
    title = "%s in %s County, AL | %d Programs" % (n["title"], cn, len(items))
    desc = "%d programs for %s in %s County, Alabama. Phone numbers, who qualifies and what to bring." % (len(items), n["phrase"], cn)
    spon = sponsor("Reach families in %s County looking for %s." % (cn, n["title"].lower()))
    body = []
    if loc:
        body.append("<h2>Local in %s County (%d)</h2>" % (E(cn), len(loc)))
        for i, p in enumerate(loc):
            body.append(listing(p, cn))
            if i + 1 == min(len(loc), LOCAL_FIRST_AD_AFTER): body.append(spon)
    if sw:
        body.append("<h2>Statewide programs that serve %s County (%d)</h2>" % (E(cn), len(sw)))
        body += [listing(p, cn) for p in sw]
    other = "".join('<a href="/alabama/%s/%s/">%s</a>' % (c, x["slug"], E(x["title"])) for x in NEEDS if x["key"] != k)
    main = ('<main id="main" class="wrap">%s<h1>%s in <em>%s County</em>, AL</h1><p class="lede">%d programs for %s in %s County, Alabama%s. '
            'Phone numbers, who qualifies and what to bring. Call first: funding opens and closes.</p>%s<div class="layout"><div>%s'
            '<h2>Other help in %s County</h2><div class="jump">%s</div></div>%s</div>' % (
                cr, E(n["title"]), E(cn), len(items), E(n["phrase"]), E(cn),
                (", including %d local options" % len(loc)) if loc else "", finder(c, n["slug"]), "".join(body), E(cn), other, side(n["bring"], spon)))
    wr(path, head(title, desc, path, [bc, itemlist("%s in %s County, Alabama" % (n["title"], cn), items)]) + TOP + main + foot())
    return items

# ---------------------------------------------------------------- county hubs
def county_hub(c, per_need):
    cn = COUNTIES[c]; path = "/alabama/%s/" % c
    seen = {}
    for n in NEEDS:
        for p in per_need[n["key"]]: seen.setdefault(p["id"], p)
    general = [p for p in PROGS if p.get("general") and serves(p, c)]
    for p in general: seen.setdefault(p["id"], p)
    allp = [p for p in PROGS if p["id"] in seen]
    nloc = sum(1 for p in allp if p["local"])
    bc, cr = crumbs([("Home", "/"), ("Alabama counties", "/alabama/"), ("%s County" % cn, path)])
    title = "Free Help in %s County, AL: Bills, Food, Rent | %d Programs" % (cn, len(allp))
    desc = "%d programs serving %s County, Alabama (%d local): utility bill help, food pantries, rent and eviction help, shelters, repairs and more." % (len(allp), cn, nloc)
    spon = sponsor("Reach families in %s County." % cn)
    tiles = "".join('<a class="tile" href="/alabama/%s/%s/">%s<span>%s<small>%d programs</small></span></a>' % (
        c, n["slug"], n["icon"], E(n["title"]), len(per_need[n["key"]])) for n in NEEDS)
    main = ('<main id="main" class="wrap">%s<h1>Free help in <em>%s County</em>, Alabama</h1><p class="lede">%d programs serve %s County, including %d local ones. Pick what you need.</p>'
            '%s%s<div class="grid">%s</div><div class="layout"><div><h2>General help for anyone in %s County</h2>%s</div>%s</div>' % (
                cr, E(cn), len(allp), E(cn), nloc, finder(c), spon, tiles, E(cn), "".join(listing(p, cn) for p in general), side("any", spon)))
    wr(path, head(title, desc, path, [bc, itemlist("Assistance programs in %s County, Alabama" % cn, allp)]) + TOP + main + foot())
    return allp

# ---------------------------------------------------------------- statewide need pages
def help_page(n, local_counts):
    path = "/help/%s/" % n["slug"]
    sw = [p for p in PROGS if p["counties"] == "all" and not p["local"] and n["key"] in p["needs"]]
    bc, cr = crumbs([("Home", "/"), ("Types of help", "/help/"), (n["title"], path)])
    title = "%s in Alabama | %s" % (n["title"], SITE)
    desc = "%s in Alabama: statewide programs plus local options in all 67 counties. Phone numbers, who qualifies and what to bring." % n["title"]
    spon = sponsor("Reach families in Alabama looking for %s." % n["title"].lower())
    cols = "".join('<li><a href="/alabama/%s/%s/">%s County</a>%s</li>' % (
        c, n["slug"], E(cn), ' <span class="muted">(%d local)</span>' % local_counts[c]) for c, cn in COUNTIES.items())
    main = ('<main id="main" class="wrap">%s<h1>%s <em>in Alabama</em></h1><p class="lede">Statewide programs for %s, plus local help in every county. Pick your county for the full local list.</p>'
            '%s<div class="layout"><div><h2>Pick your county</h2><ul class="cols">%s</ul>%s<h2>Statewide programs</h2>%s</div>%s</div>' % (
                cr, E(n["title"]), E(n["phrase"]), finder("", n["slug"]), cols, spon, "".join(listing(p) for p in sw), side(n["bring"], spon)))
    wr(path, head(title, desc, path, [bc, itemlist("%s in Alabama" % n["title"], sw)], robots=False) + TOP + main + foot())

# ---------------------------------------------------------------- data files
def strip_local(b): return b[len("Local · "):] if b.startswith("Local · ") else b

def search_index():
    rows = []
    for p in sorted(PROGS, key=lambda p: p["counties"] != "all"):       # statewide first, then display order
        c = next(iter(COUNTIES)) if p["counties"] == "all" else p["counties"][0]
        u = "/alabama/%s/%s#r-%s" % (c, (NK[p["needs"][0]]["slug"] + "/") if p["needs"] else "", p["id"])
        t = " ".join([p["name"], p.get("alias", ""), p.get("desc", ""), strip_local(p["badge"]), " ".join(NK[k]["title"] for k in p["needs"])]).lower()
        ph = p.get("phone") or ("See website" if p.get("phone_web") else p.get("phone_note") or "No phone listed: visit, or ask 2-1-1 for hours")
        rows.append({"n": p["name"], "s": strip_local(p["badge"]), "p": ph, "u": u, "t": t})
    with open(os.path.join(OUT, "assets", "search-index.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

def agent_data(per):
    top = {c: {k: [[p["name"], p.get("phone") or "See website", tel_digits(p["phone"]) if p.get("phone") else "", 1 if p["local"] else 0,
                    p.get("where", ""), "" if p.get("phone") else (p.get("web") or p.get("phone_web") or "")] for p in items[:4]]
               for k, items in per[c].items()} for c in COUNTIES}
    out = {"needs": {n["key"]: {"s": n["slug"], "t": n["title"]} for n in NEEDS}, "counties": COUNTIES, "cities": D["cities"], "zips": D["zips"],
           "bring": D["bring"], "top": top, "counts": {c: {k: len(v) for k, v in per[c].items()} for c in COUNTIES}}
    with open(os.path.join(OUT, "assets", "agent-data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- run
def main():
    per = {}
    for c in COUNTIES:
        per[c] = {n["key"]: county_need(c, n) for n in NEEDS}
    for c in COUNTIES:
        county_hub(c, per[c])
    for n in NEEDS:
        help_page(n, {c: sum(1 for p in per[c][n["key"]] if p["local"]) for c in COUNTIES})
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    search_index(); agent_data(per)
    print("built", len(COUNTIES) * len(NEEDS), "county pages,", len(COUNTIES), "county hubs,", len(NEEDS), "help pages")

if __name__ == "__main__":
    main()
