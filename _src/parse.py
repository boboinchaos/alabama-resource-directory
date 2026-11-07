import os,re,json,html,sys
from html.parser import HTMLParser
R=sys.argv[1]
needs=[d for d in os.listdir(f'{R}/help') if os.path.isdir(f'{R}/help/{d}')]
def txt(s): return html.unescape(re.sub(r'<[^>]+>',' ',s)).split() and ' '.join(html.unescape(re.sub(r'<[^>]+>',' ',s)).split())
pages={}
for c in sorted(os.listdir(f'{R}/alabama')):
    if not os.path.isdir(f'{R}/alabama/{c}'): continue
    for n in needs:
        p=f'{R}/alabama/{c}/{n}/index.html'
        if not os.path.exists(p): continue
        s=open(p).read()
        h1=re.search(r'<h1>(.*?)</h1>',s).group(1)
        arts=re.findall(r'<article class="res" id="r-([^"]+)">(.*?)</article>',s,re.S)
        items=[]
        for rid,a in arts:
            name=txt(re.search(r'<h3>(.*?)</h3>',a).group(1))
            badge=txt(re.search(r'<span class="badge[^"]*">(.*?)</span>',a).group(1))
            local='class="badge local"' in a
            ph=re.search(r'<a class="phone" href="tel:(\d+)">(.*?)</a>',a)
            addr=re.search(r'<dt>Where</dt><dd>(.*?)</dd>',a)
            desc=re.search(r'</div><p>(.*?)</p>',a)
            who=re.search(r'<dt>Who</dt><dd>(.*?)</dd>',a)
            web=re.search(r'href="([^"]+)"[^>]*>Website</a>',a)
            items.append(dict(id=rid,name=name,badge=badge,local=local,tel=ph.group(1) if ph else '',phone=txt(ph.group(2)) if ph else '',addr=txt(addr.group(1)) if addr else '',desc=txt(desc.group(1)) if desc else '',who=txt(who.group(1)) if who else '',web=html.unescape(web.group(1)) if web else ''))
        pages[(c,n)]=dict(h1=txt(h1),items=items)
out={f'{c}|{n}':v for (c,n),v in pages.items()}
json.dump(out,open('pages.json','w'))
loc=[sum(1 for i in v['items'] if i['local']) for v in pages.values()]
print(len(pages),'pages; local counts: 0:',loc.count(0),' 1:',loc.count(1),' 2:',loc.count(2),' 3-5:',sum(1 for x in loc if 3<=x<=5),' 6+:',sum(1 for x in loc if x>5))
