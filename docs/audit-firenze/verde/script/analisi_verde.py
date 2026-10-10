"""F01 verde: censimento alberi, siti alberi (rilievo celerimetrico) nei riquadri FA e FB. Scrive campioni/verde_stats.json e campioni/*.csv."""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, geopandas as gpd, pandas as pd
from zone import ZONE, poly4326
RAW=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../data/raw/fi_audit_20261001")
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../campioni")
CRS=7791
al=gpd.read_file(f"{RAW}/alberi.geojson").set_crs(4326,allow_override=True)
si=gpd.read_file(f"{RAW}/sAlbero/sAlbero_p.shp")
si=gpd.GeoDataFrame(si.drop(columns="geometry"),geometry=gpd.GeoSeries(si.geometry.explode(index_parts=False).values,crs=si.crs).force_2d().values if False else si.geometry.apply(lambda g:g.geoms[0]),crs=si.crs)
al,es,si=[x.to_crs(CRS) for x in (al,es,si)]
S={"n_alberi_città":len(al),"n_siti_città":len(si),"colonne_alberi":list(al.columns[:-1]),"colonne_siti":["salberoid","salbero_p","Z"]}
zp={z:gpd.GeoSeries([poly4326(b)],crs=4326).to_crs(CRS).iloc[0] for z,b in ZONE.items()}
zp["FA&FB"]=zp["FA"].intersection(zp["FB"]); zp["FA|FB"]=zp["FA"].union(zp["FB"])
S["area_km2"]={z:round(p.area/1e6,3) for z,p in zp.items()}
for z,p in zp.items():
    a=al[al.within(p)]; s=si[si.within(p)]
    d={"alberi":len(a),"siti":len(s)}
    if len(a):
        d["alberi_specie_vuote"]=int(a.SPECIE.isna().sum()+(a.SPECIE.astype(str).str.strip()=="").sum())
        c=a.CIRCONF_CM.dropna(); d["circonf_cm"]={"n":len(c),"zero_o_nulla":int((a.CIRCONF_CM.fillna(0)<=0).sum()),"p10_med_p90":[round(float(np.percentile(c[c>0],q)),1) for q in (10,50,90)]}
        d["alberi_per_ettaro"]=round(len(a)/(p.area/1e4),2)
        d["top_specie"]=a.SPECIE.value_counts().head(8).to_dict()
        d["quartiere"]=a.QUARTIERE.value_counts().to_dict()
        d["id_unici"]=int(a.ID.is_unique); d["codsito_unici"]=int(a.CODSITO_ALBERO.nunique())
    S[z]=d
# siti alberi: attributi e confronto con censimento (distanza al sito più vicino)
S["siti_Z_ok"]=float(si.geometry.apply(lambda g:g.has_z).mean())
n=si.salberoid.str.extract(r"_(\d+)$")[0].astype(int); S["siti_id_range"]=[int(n.min()),int(n.max())]
S["censimento_CODSITO_range"]=[int(al.CODSITO_ALBERO.min()),int(al.CODSITO_ALBERO.max())]
j=gpd.sjoin_nearest(al[["ID","CODSITO_ALBERO","geometry"]],si[["salberoid","geometry"]].assign(sid=n.values),how="left",distance_col="dist")
j=j.drop_duplicates("ID"); S["censimento_vs_siti"]={"dist_m_p50_p90_p99":[round(float(np.percentile(j.dist,q)),2) for q in (50,90,99)],
  "quota_entro_1m":round(float((j.dist<=1).mean()),3),"quota_entro_3m":round(float((j.dist<=3).mean()),3),
  "stesso_id_numerico":round(float((j.sid==j.CODSITO_ALBERO).mean()),3)}
# stesso confronto nei due riquadri
for z in ("FA","FB"):
    k=j[j.geometry.within(zp[z])]; S["censimento_vs_siti"][z]={"n":len(k),"p50_p90":[round(float(np.percentile(k.dist,q)),2) for q in (50,90)],"quota_entro_3m":round(float((k.dist<=3).mean()),3)}
for z in ("FA","FB"): al[al.within(zp[z])].to_crs(4326).iloc[:200].to_file(f"{OUT}/alberi_{z}_primi200.geojson",driver="GeoJSON")
json.dump(S,open(f"{OUT}/verde_stats.json","w"),indent=1,ensure_ascii=False,default=str)
print(json.dumps(S,indent=1,ensure_ascii=False,default=str))
