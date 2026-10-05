"""F01 verde: altezza chioma da CHM (DSM 2023 - DTM 2023, 0,5 m) contro altezza misurata Life Escapos (h_m) e altezza di inizio chioma (h_m - can_h_m?).
Life Escapos è CC BY-NC 4.0: uso solo come verifica. Scrive campioni/chm_vs_escapos.csv e campioni/chm_stats.json."""
import os, sys, glob, json, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.merge import merge
from rasterio.features import geometry_mask
from shapely.geometry import Point
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=f"{HERE}/../../../../data/raw/fi_audit_20261001"; C=f"{HERE}/../campioni"
def mosaic(d):
    src=[rasterio.open(f) for f in sorted(glob.glob(f"{RAW}/lidar/{d}/*.ASC"))]; a,t=merge(src,nodata=-9999); a=a[0].astype("float32"); a[a==-9999]=np.nan; return a,t
dsm,t=mosaic("dsm2023"); dtm,_=mosaic("dtm2023"); chm=dsm-dtm
es=gpd.read_file(f"{RAW}/escapos.geojson").set_crs(7791,allow_override=True)
al=gpd.read_file(f"{RAW}/alberi.geojson").set_crs(4326,allow_override=True).to_crs(7791)
uv=[]  # edifici (UV Regione) per escludere alberi addossati a un edificio
import json as J
from shapely.geometry import Polygon, MultiPolygon
for z in ("FA","FB"):
    for u in J.load(open(f"{HERE}/../../edifici/campioni/rt_uv_{z}.json")): uv.append(MultiPolygon([Polygon(p[0],p[1:]) for p in u["polys"]]))
bld=gpd.GeoSeries(uv,crs=4326).to_crs(7791).union_all()
def stat(g,r):
    m=~geometry_mask([g.buffer(r)],out_shape=chm.shape,transform=t); v=chm[m]; v=v[~np.isnan(v)]
    return (float(v.max()),float(np.percentile(v,95))) if len(v) else (np.nan,np.nan)
rows=[]
for _,r in es.iterrows():
    rad=max(1.5,r.crn_w_m/2)   # raggio di ricerca = semi-chioma misurata, almeno 1,5 m (tolleranza di posizione)
    mx,p95=stat(r.geometry,rad)
    rows.append(dict(id=r.id,cens_id=r.cens_id,species=r.species,h_escapos=round(r.h_m,2),crn_w=round(r.crn_w_m,2),raggio=round(rad,2),chm_max=round(mx,2),chm_p95=round(p95,2),
                     a_meno_di_3m_da_edificio=bool(r.geometry.distance(bld)<3)))
D=pd.DataFrame(rows); D["scarto_max"]=D.chm_max-D.h_escapos; D["scarto_p95"]=D.chm_p95-D.h_escapos; D.to_csv(f"{C}/chm_vs_escapos.csv",index=False)
def st(x): x=np.asarray(x,float); x=x[~np.isnan(x)]; return {"n":int(len(x)),"mediana":round(float(np.median(x)),2),"p10":round(float(np.percentile(x,10)),2),"p90":round(float(np.percentile(x,90)),2),"MAE":round(float(np.mean(np.abs(x))),2)}
S={"tutti":{"chm_max - h":st(D.scarto_max),"chm_p95 - h":st(D.scarto_p95)}}
L=D[~D.a_meno_di_3m_da_edificio]; S["lontani_da_edifici_3m"]={"chm_max - h":st(L.scarto_max),"chm_p95 - h":st(L.scarto_p95)}
S["vicini_a_edifici"]=int(D.a_meno_di_3m_da_edificio.sum())
S["correlazione_chm_max_h"]=round(float(np.corrcoef(L.chm_max,L.h_escapos)[0,1]),3)
S["rapporto_mediano_chm_max/h_lontani"]=round(float((L.chm_max/L.h_escapos).median()),3)
for nome,k in (("h<6",L.h_escapos<6),("6<=h<10",(L.h_escapos>=6)&(L.h_escapos<10)),("h>=10",L.h_escapos>=10)): S[f"per_classe_{nome}"]=st(L.scarto_max[k])
# CHM sul censimento (3.468 alberi in FA|FB): distribuzione dell'altezza stimata (max entro 2 m), per orientamento
from shapely.geometry import box
sys.path.insert(0,HERE); from zone import ZONE, poly4326
zz=gpd.GeoSeries([poly4326(b) for b in ZONE.values()],crs=4326).to_crs(7791).union_all()
a=al[al.within(zz)].copy()
a["chm_max2m"]=[stat(g,2.0)[0] for g in a.geometry]
a["vicino_edificio"]=a.geometry.distance(bld)<3
v=a[(~a.vicino_edificio)&a.chm_max2m.notna()]
S["censimento_FA_FB"]={"n":len(a),"lontani_da_edifici":len(v),"chm_max_2m_p10_p50_p90":[round(float(np.percentile(v.chm_max2m,q)),1) for q in (10,50,90)],
   "con_chm_sotto_2m":int((v.chm_max2m<2).sum()),"correlazione_circonferenza_chm":round(float(np.corrcoef(v.CIRCONF_CM.clip(lower=1),v.chm_max2m)[0,1]),3)}
# siti alberi (rilievo celerimetrico, PointZ): quota Z contro DTM 2023 nel punto
si=gpd.read_file(f"{RAW}/sAlbero/sAlbero_p.shp"); z3=si.geometry.apply(lambda g:g.geoms[0].z); si=gpd.GeoDataFrame({"z":z3},geometry=si.geometry.apply(lambda g:Point(g.geoms[0].x,g.geoms[0].y)),crs=si.crs).to_crs(7791)
si["z"]=z3.values; si=si[si.within(zz)]
idx=[rasterio.transform.rowcol(t,g.x,g.y) for g in si.geometry]; dv=np.array([dtm[r,c] if 0<=r<dtm.shape[0] and 0<=c<dtm.shape[1] else np.nan for r,c in idx])
S["siti_alberi_Z_vs_DTM23"]={"n":int(np.isfinite(dv).sum()),**st(si.z.values-dv)}
json.dump(S,open(f"{C}/chm_stats.json","w"),indent=1,ensure_ascii=False); print(json.dumps(S,indent=1,ensure_ascii=False))
