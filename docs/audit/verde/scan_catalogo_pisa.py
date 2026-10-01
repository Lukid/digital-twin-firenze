#!/usr/bin/env python3
# Scansiona il catalogo opendata.comune.pisa.it (/catalogo-opendata?page=N) ed estrae i titoli.
import re,sys,urllib.request,concurrent.futures as cf,json,html
B="https://opendata.comune.pisa.it/catalogo-opendata"
def get(n):
    for _ in range(3):
        try:
            return n,urllib.request.urlopen(urllib.request.Request(f"{B}?page={n}",headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read().decode('utf8','ignore')
        except Exception as e: err=str(e)
    return n,None
out={}
with cf.ThreadPoolExecutor(6) as ex:
    for n,h in ex.map(get,range(0,133)):
        if h is None: out[n]=None; continue
        items=[]
        for u,t in re.findall(r'<a[^>]+href="(https://opendata\.comune\.pisa\.it/(?:content|opendata)/[^"?]+)"[^>]*>(.*?)</a>',h,flags=re.S):
            t=html.unescape(re.sub(r'<[^>]+>','',t)).strip()
            if t and t not in('Tabella','Grafico','Mappa'): items.append((u,t))
        out[n]=items
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False,indent=0)
print(sum(len(v) for v in out.values() if v),'titoli;','pagine fallite:',[k for k,v in out.items() if v is None])
