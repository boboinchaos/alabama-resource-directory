#!/usr/bin/env python3
"""AI knowledge-base pages (/kb/) for the GoHighLevel assistants (Riley).

Plain, noindex pages built from _src/data.json, written so a retrieval-based agent
can find answers in small chunks:

  /kb/totals/            every count in plain sentences (statewide, each county, each need)
  /kb/county/{county}/   one page per county: its totals, then every program by need
  /kb/{need}/            one page per need: statewide programs, then county-specific ones by county
  /kb/                   index of all pages
  /kb/sitemap.xml        every /kb/ URL, for a sitemap crawl in GoHighLevel

After changing data:  python3 _src/kbgen.py, push, then re-sync the knowledge base in GoHighLevel.
"""
import os, json, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("BUILD_OUT", ROOT)
DOMAIN = "https://www.alabamaresourcedirectory.com"
D = json.load(open(os.path.join(ROOT, "_src", "data.json"), encoding="utf-8"))
NEEDS, CO, PROGS = D["needs"], D["counties"], D["programs"]
E = lambda s: html.escape(str(s), quote=True)
TODAY = datetime.date.today()
ASOF = TODAY.strftime("%B %-d, %Y")
HEAD = '<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>%s</title></head><body>'
URLS = []

def serves(p, c): return p["counties"] == "all" or c in p["counties"]
def county_programs(c):
    """Same definition as the county hub pages: need programs plus general-help programs."""
    return [p for p in PROGS if serves(p, c) and (p["needs"] or p.get("general"))]
def plural(n, w): return "%d %s%s" % (n, w, "" if n == 1 else "s")

def line(p, county=None):
    parts = ["<b>%s</b>" % E(p["name"])]
    phone = p.get("phone") or p.get("phone_note") or ("See website" if p.get("phone_web") else "")
    if phone: parts.append("Phone: " + E(phone))
    if p.get("desc"): parts.append(E(p["desc"]))
    if p.get("who"): parts.append("Who qualifies: " + E(p["who"]))
    parts.append("Serves: " + ("every Alabama county" if p["counties"] == "all" else E(p["badge"].replace("Local · ", ""))))
    if p.get("where"): parts.append("Address: " + E(p["where"]))
    if p.get("email"): parts.append("Email: " + E(p["email"]))
    web = p.get("web") or p.get("apply") or p.get("phone_web")
    if web: parts.append("Website: " + E(web))
    return "<li>%s</li>" % " — ".join(parts)

def write(rel, title, body):
    p = os.path.join(OUT, rel, "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(HEAD % E(title) + body + "</body></html>")
    URLS.append(DOMAIN + "/" + rel + "/")

def totals_sentence(c):
    cn = CO[c]; allp = county_programs(c)
    nloc = sum(1 for p in allp if p["local"])
    per = ["%s: %d" % (n["title"], sum(1 for p in allp if n["key"] in p["needs"])) for n in NEEDS]
    return ("%s County, Alabama has %s in total that serve its residents, including %d local programs "
            "(the rest are statewide or national). By type of help: %s. A program that helps with several needs is counted once under each. "
            "Full list: %s/alabama/%s/" % (cn, plural(len(allp), "program"), nloc, "; ".join(per), DOMAIN, c))

# ---- totals page
state_n = len([p for p in PROGS if p["needs"] or p.get("general")])
sw = [p for p in PROGS if p["counties"] == "all"]
body = ["<h1>Alabama Resource Directory: how many programs, by county and by need</h1>",
        "<p>As of %s, the Alabama Resource Directory lists %d assistance programs across all 67 Alabama counties and 17 types of help. "
        "%d of them are statewide or national programs that serve every county.</p>" % (ASOF, state_n, len(sw)),
        "<h2>Statewide totals by type of help</h2><p>%s.</p>" % "; ".join(
            "%s: %d programs" % (n["title"], sum(1 for p in PROGS if n["key"] in p["needs"])) for n in NEEDS),
        "<h2>Totals for each county</h2>"]
for c, cn in CO.items():
    body.append("<h3>%s County</h3><p>%s</p>" % (E(cn), E(totals_sentence(c))))
write("kb/totals", "Alabama Resource Directory: program counts by county and need", "".join(body))

# ---- one page per county
for c, cn in CO.items():
    allp = county_programs(c)
    out = ["<h1>Help in %s County, Alabama</h1>" % E(cn), "<p>%s</p>" % E(totals_sentence(c))]
    for n in NEEDS:
        items = [p for p in allp if n["key"] in p["needs"]]
        loc = [p for p in items if p["local"]]; st = [p for p in items if not p["local"]]
        out.append("<h2>%s in %s County (%s)</h2>" % (E(n["title"]), E(cn), plural(len(items), "program")))
        if loc: out.append("<h3>Local and regional programs for %s in %s County</h3><ul>%s</ul>" % (E(n["title"].lower()), E(cn), "".join(line(p) for p in loc)))
        if st: out.append("<h3>Statewide programs for %s that also serve %s County</h3><ul>%s</ul>" % (E(n["title"].lower()), E(cn), "".join(line(p) for p in st)))
    gen = [p for p in allp if p.get("general")]
    if gen:
        out.append("<h2>General help for anyone in %s County</h2><ul>%s</ul>" % (E(cn), "".join(line(p) for p in gen)))
    write("kb/county/%s" % c, "Help in %s County, Alabama" % cn, "".join(out))

# ---- one page per need
for n in NEEDS:
    k = n["key"]; progs = [p for p in PROGS if k in p["needs"]]
    out = ["<h1>Alabama resources for: %s</h1>" % E(n["kb_label"]),
           "<p>Help with %s in Alabama. %d programs in total. Statewide programs first, then county-specific programs by county.</p>" % (E(n["kb_label"].lower()), len(progs)),
           "<h2>Statewide programs for %s (any Alabama county)</h2><ul>%s</ul>" % (E(n["title"].lower()), "".join(line(p) for p in progs if p["counties"] == "all"))]
    for c, cn in CO.items():
        loc = [p for p in progs if p["counties"] != "all" and c in p["counties"]]
        if loc:
            out.append("<h2>%s County, Alabama — %s (%s)</h2><ul>%s</ul>" % (E(cn), E(n["short"]), plural(len(loc), "county-specific program"), "".join(line(p) for p in loc)))
    write("kb/%s" % k, "Alabama resources for: %s" % n["kb_label"], "".join(out))

# ---- index + sitemap
idx = ['<h1>Alabama Resource Directory knowledge base</h1><p>Updated %s.</p><ul>' % ASOF,
       '<li><a href="/kb/totals/">Program counts by county and need</a></li>']
idx += ['<li><a href="/kb/county/%s/">%s County</a></li>' % (c, E(cn)) for c, cn in CO.items()]
idx += ['<li><a href="/kb/%s/">%s</a></li>' % (n["key"], E(n["kb_label"])) for n in NEEDS]
idx.append("</ul>")
write("kb", "Alabama Resource Directory knowledge base", "".join(idx))
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sm += ["<url><loc>%s</loc><lastmod>%s</lastmod></url>" % (u, TODAY.isoformat()) for u in sorted(URLS)]
sm.append("</urlset>")
open(os.path.join(OUT, "kb", "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(OUT, "kb", "urls.txt"), "w").write("\n".join(sorted(URLS)) + "\n")
print("kb pages:", len(URLS))
