#!/usr/bin/env python3
# Overpass: alberi OSM per zona + completezza attributi. Scrive campioni/osm_<zona>.json e osm_stats.json
import json,urllib.request,urllib.parse,time,datetime
Z=json.load(open('zone.json')); out={}
EP="https://overpass-api.de/api/interpreter"
def q(bb,body):
    s,w,n,e=bb; b=f"({s},{w},{n},{e})"
    return f'[out:json][timeout:90];({body.replace("BB",b)});out meta center;'
def run(query):
    for _ in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(EP,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'dt-pisa-audit/0.1'}),timeout=120)
            return json.load(r)
        except Exception as ex: err=str(ex); time.sleep(10)
    return {'error':err}
KEYS=['species','species:it','genus','taxon','height','est_height','diameter_crown','crown_diameter','circumference','diameter','leaf_type','leaf_cycle','start_date','ref','source','denotation','natural']
for z,bb in Z.items():
    if z=='nota': continue
    d=run(q(bb,'node["natural"="tree"]BB;way["natural"="tree_row"]BB;way["natural"="wood"]BB;way["landuse"="forest"]BB;way["leisure"~"park|garden"]BB;way["landuse"="grass"]BB;relation["leisure"="park"]BB;'))
    json.dump(d,open(f'campioni/osm_{z}.json','w'),ensure_ascii=False)
    if 'elements' not in d: out[z]={'errore':d}; print(z,'ERRORE',d); continue
    el=d.get('elements',[])
    t=[e for e in el if e['type']=='node' and e.get('tags',{}).get('natural')=='tree']
    st={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'alberi_nodi':len(t),'tree_row':sum(1 for e in el if e.get('tags',{}).get('natural')=='tree_row'),
        'aree_verdi_way_rel':sum(1 for e in el if e['type']!='node' and e.get('tags',{}).get('natural')!='tree_row'),
        'attributi':{k:sum(1 for e in t if k in e['tags']) for k in KEYS if k!='natural'},
        'timestamp_osm_nodi_min_max':[min([e['timestamp'] for e in t],default=None),max([e['timestamp'] for e in t],default=None)]}
    out[z]=st; print(z,json.dumps(st,ensure_ascii=False))
json.dump(out,open('campioni/osm_stats.json','w'),ensure_ascii=False,indent=1)
