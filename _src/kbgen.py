#!/usr/bin/env python3
"""AI knowledge-base pages (/kb/) for the GoHighLevel assistants (Riley).

One plain, noindex page per need, listing every program from _src/data.json:
statewide programs first, then local programs county by county. GoHighLevel
crawls them in Exact URL mode (one URL per page). After changing data, run this,
push, then re-sync the knowledge base in GoHighLevel.

    python3 _src/kbgen.py          # from the repo root
"""
import os, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("BUILD_OUT", ROOT)
D = json.load(open(os.path.join(ROOT, "_src", "data.json"), encoding="utf-8"))
E = lambda s: html.escape(str(s), quote=True)
HEAD = '<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>%s</title></head><body>'

def line(p):
    parts = ["<b>%s</b>" % E(p["name"])]
    phone = p.get("phone") or p.get("phone_note") or ("See website" if p.get("phone_web") else "")
    if phone: parts.append("Phone: " + E(phone))
    if p.get("desc"): parts.append(E(p["desc"]))
    if p.get("who"): parts.append("Who qualifies: " + E(p["who"]))
    if p.get("where"): parts.append("Address: " + E(p["where"]))
    if p.get("email"): parts.append("Email: " + E(p["email"]))
    web = p.get("web") or p.get("apply") or p.get("phone_web")
    if web: parts.append("Website: " + E(web))
    return "<li>%s</li>" % " — ".join(parts)

def write(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)

counts = []
for n in D["needs"]:
    k = n["key"]
    progs = [p for p in D["programs"] if k in p["needs"]]
    sw = [p for p in progs if p["counties"] == "all"]
    title = "Alabama resources for: %s" % n["kb_label"]
    out = [HEAD % E(title), "<h1>%s</h1>" % E(title),
           "<p>Help with %s in Alabama, from the Alabama Resource Directory (alabamaresourcedirectory.com). "
           "Statewide programs first, then local resources by county.</p>" % E(n["kb_label"].lower()),
           "<h2>Statewide programs (any Alabama county)</h2><ul>%s</ul>" % "".join(line(p) for p in sw)]
    total = len(sw)
    for c, cn in D["counties"].items():
        loc = [p for p in progs if p["counties"] != "all" and c in p["counties"]]
        if loc:
            out.append("<h2>%s County, Alabama — %s</h2><ul>%s</ul>" % (E(cn), E(n["short"]), "".join(line(p) for p in loc)))
            total += len(loc)
    out.append("</body></html>")
    write(os.path.join("kb", k, "index.html"), "".join(out))
    counts.append((n, total))

idx = [HEAD % "Alabama Resource Directory knowledge base", "<h1>Alabama Resource Directory knowledge base</h1><ul>"]
idx += ['<li><a href="/kb/%s/">%s</a> (%d)</li>' % (n["key"], E(n["kb_label"]), t) for n, t in counts]
idx.append("</ul></body></html>")
write(os.path.join("kb", "index.html"), "".join(idx))
print("kb pages:", len(counts))
