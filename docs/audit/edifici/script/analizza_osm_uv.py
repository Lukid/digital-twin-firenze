"""Statistiche per zona: UV Regione (altezze), OSM (height/levels), confronto OSM vs UV su edifici abbinati (centroide OSM dentro UV)."""
import json, re, csv, os, numpy as np, collections as C
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.strtree import STRtree
from shapely.ops import transform
from pyproj import Transformer
PT=Transformer.from_crs(4326,32632,always_xy=True).transform
def num(s):
    m=re.match(r'\s*([0-9]+(?:[.,][0-9]+)?)',s or ''); return float(m.group(1).replace(',','.')) if m else None
out=[];pairs=[]
for z in ("Z1","Z2","Z3","Z4"):
    uv=json.load(open(f"campioni/rt_uv_{z}.json"))
    geoms=[MultiPolygon([Polygon(p[0],p[1:]) for p in u["polys"]]).buffer(0) for u in uv]
    tree=STRtree(geoms)
    edif={u['edifc_id'] for u in uv if u.get('edifc_id')}
    if not os.path.exists(f"campioni/osm_buildings_{z}.json"): print(z,"OSM non scaricato"); osm=[]
    else: osm=json.load(open(f"campioni/osm_buildings_{z}.json"))["elements"]
    bl=[e for e in osm if 'building' in e['tags']]
    parts=[e for e in bl if 'building:part' in e['tags']]
    h=[e for e in bl if num(e['tags'].get('height')) is not None]
    lv=[e for e in bl if num(e['tags'].get('building:levels')) is not None]
    both_none=[e for e in bl if e not in h and e not in lv]
    mh=[e for e in bl if 'min_height' in e['tags'] or 'building:min_level' in e['tags']]
    porch=[e for e in bl if e['tags'].get('building')=='roof' or e['tags'].get('covered')=='yes' or e['tags'].get('building:part')=='roof']
    r=dict(zona=z,uv_unita=len(uv),uv_edifici_distinti=len(edif),uv_con_altezza=sum(1 for u in uv if float(u['uv_av'])>0),
        uv_portico=sum(1 for u in uv if u['uv_por']!='01'),osm_building=len(bl),osm_height=len(h),osm_levels=len(lv),osm_nessuno=len(both_none),
        osm_min_height=len(mh),osm_roof=len(porch),osm_building_part=len(parts))
    ct=json.load(open(f"campioni/sit_ctrpoc_{z}.geojson"))["features"]
    nuo=0;tot=0
    for f in ct:
        g=f["geometry"]
        if not g or f["properties"].get("tipo","").strip()=="mura": continue
        ring=g["coordinates"][0][0] if g["type"]=="MultiPolygon" else g["coordinates"][0]
        pg=Polygon([(p[0],p[1]) for p in ring]).buffer(0)
        if transform(PT,pg).area<40: continue
        tot+=1; c=pg.representative_point()
        if not any(geoms[i].contains(c) for i in tree.query(c)): nuo+=1
    r["ctr2022_poligoni_ge40m2"]=tot; r["ctr2022_senza_uv"]=nuo; r["ctr2022_troncato"]=False
    out.append(r)
    for e in bl:
        if 'center' in e: c=Point(e['center']['lon'],e['center']['lat'])
        elif 'geometry' in e and len(e['geometry'])>=4: c=Polygon([(p['lon'],p['lat']) for p in e['geometry']]).buffer(0).representative_point()
        else: continue
        hit=[i for i in tree.query(c) if geoms[i].contains(c)]
        if not hit: r['osm_senza_uv']=r.get('osm_senza_uv',0)+1; continue
        u=uv[max(hit,key=lambda i:float(uv[i]['uv_av']))]
        hh=num(e['tags'].get('height')); ll=num(e['tags'].get('building:levels'))
        if hh is not None or ll is not None:
            pairs.append(dict(zona=z,osm_id=e['id'],osm_height=hh,osm_levels=ll,uv_id=u['uv_id'],uv_av=float(u['uv_av']),uso=u.get('edifc_duso')))
with open("campioni/osm_vs_uv.csv","w",newline="") as f:
    w=csv.DictWriter(f,pairs[0].keys()) if pairs else None
    if w: w.writeheader(); w.writerows(pairs)
print(json.dumps(out,indent=1))
json.dump(out,open("campioni/statistiche_zone.json","w"),indent=1)
ph=[p for p in pairs if p['osm_height'] is not None]; pl=[p for p in pairs if p['osm_height'] is None and p['osm_levels'] is not None]
print("coppie con height",len(ph),"solo levels",len(pl))
if ph:
    d=np.array([p['osm_height']-p['uv_av'] for p in ph]); print("OSM height - uv_av: n=%d med=%.2f MAE=%.2f p10=%.2f p90=%.2f"%(len(d),np.median(d),np.abs(d).mean(),*np.percentile(d,[10,90])))
if pl:
    d=np.array([p['uv_av']/p['osm_levels'] for p in pl]); print("uv_av/levels (m per piano): n=%d med=%.2f p10=%.2f p90=%.2f"%(len(d),np.median(d),*np.percentile(d,[10,90])))
