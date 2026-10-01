"""Confronta altezza UV (uv_av) con DSM 2021 meno quota suolo, sui tile 500 m. Output: campioni/ndsm_confronto.csv e riepilogo stdout."""
import json, glob, csv, sys, os, numpy as np, rasterio
from rasterio.features import geometry_mask
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform
from pyproj import Transformer
T=Transformer.from_crs(4326,32632,always_xy=True).transform
rows=[]
for z in ("Z1","Z2","Z3","Z4"):
    dsm=rasterio.open(glob.glob(f"campioni/dsm_{z}_*.tif")[0]); a=dsm.read(1)
    d10=rasterio.open(glob.glob(f"campioni/dtm10_{z}_*.tif")[0]).read(1)
    for u in json.load(open(f"campioni/rt_uv_{z}.json")):
        g=MultiPolygon([Polygon(p[0],p[1:]) for p in u["polys"]]); g=transform(T,g)
        if not g.is_valid or g.area<40: continue
        b=g.bounds; L,Bt,R,Tp=dsm.bounds
        if b[0]<L or b[2]>R or b[1]<Bt or b[3]>Tp: continue
        gi=g.buffer(-1.0)
        if gi.is_empty or gi.area<15: continue
        m=~geometry_mask([gi],out_shape=a.shape,transform=dsm.transform)
        v=a[m]; 
        # anello esterno 2-4 m per il suolo locale
        ring=g.buffer(4).difference(g.buffer(2)); mr=~geometry_mask([ring],out_shape=a.shape,transform=dsm.transform)
        c=g.centroid; r,cc=dsm.index(c.x,c.y)
        rows.append(dict(zona=z,uv_id=u["uv_id"],area=round(g.area),uv_av=float(u["uv_av"]),uv_qe=float(u["uv_qe"]),uv_qs=float(u["uv_qs"]),
          dsm_med=float(np.median(v)),dsm_p90=float(np.percentile(v,90)),dsm_ring_p10=float(np.percentile(a[mr],10)),dtm10=float(d10[r,cc])))
with open("campioni/ndsm_confronto.csv","w",newline="") as f:
    w=csv.DictWriter(f,rows[0].keys()); w.writeheader(); w.writerows(rows)
R={k:np.array([r[k] for r in rows]) for k in rows[0] if k not in("zona","uv_id")}; Z=np.array([r["zona"] for r in rows])
def st(x): return f"n={len(x)} med={np.median(x):.2f} p10={np.percentile(x,10):.2f} p90={np.percentile(x,90):.2f} MAE={np.mean(np.abs(x)):.2f}"
for z in ("ALL","Z1","Z2","Z3","Z4"):
    k=np.ones(len(Z),bool) if z=="ALL" else Z==z
    if not k.any(): continue
    print(z,"datum  DSMringP10 - uv_qs :",st((R["dsm_ring_p10"]-R["uv_qs"])[k]))
    print(z,"datum  dtm10 - uv_qs     :",st((R["dtm10"]-R["uv_qs"])[k]))
    print(z,"altezza (DSMp90-ringP10) - uv_av:",st((R["dsm_p90"]-R["dsm_ring_p10"]-R["uv_av"])[k]))
    print(z,"altezza (DSMp90-uv_qs) - uv_av  :",st((R["dsm_p90"]-R["uv_qs"]-R["uv_av"])[k]))
    print(z,"quota tetto DSMp90 - uv_qe      :",st((R["dsm_p90"]-R["uv_qe"])[k]))
