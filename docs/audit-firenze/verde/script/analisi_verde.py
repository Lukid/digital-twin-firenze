"""F01 verde: censimento alberi, siti alberi (rilievo celerimetrico) e Life Escapos nei riquadri FA e FB. Scrive campioni/verde_stats.json e campioni/*.csv."""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, geopandas as gpd, pandas as pd
from zone import ZONE, poly4326
RAW=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../data/raw/fi_audit_20261001")
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../campioni")
CRS=7791
al=gpd.read_file(f"{RAW}/alberi.geojson").set_crs(4326,allow_override=True)
es=gpd.read_file(f"{RAW}/escapos.geojson").set_crs(7791,allow_override=True)
si=gpd.read_file(f"{RAW}/sAlbero/sAlbero_p.shp")
si=gpd.GeoDataFrame(si.drop(columns="geometry"),geometry=gpd.GeoSeries(si.geometry.explode(index_parts=False).values,crs=si.crs).force_2d().values if False else si.geometry.apply(lambda g:g.geoms[0]),crs=si.crs)
al,es,si=[x.to_crs(CRS) for x in (al,es,si)]
S={"n_alberi_città":len(al),"n_escapos":len(es),"n_siti_città":len(si),"colonne_alberi":list(al.columns[:-1]),"colonne_escapos":list(es.columns[:-1]),"colonne_siti":["salberoid","salbero_p","Z"]}
zp={z:gpd.GeoSeries([poly4326(b)],crs=4326).to_crs(CRS).iloc[0] for z,b in ZONE.items()}
zp["FA&FB"]=zp["FA"].intersection(zp["FB"]); zp["FA|FB"]=zp["FA"].union(zp["FB"])
S["area_km2"]={z:round(p.area/1e6,3) for z,p in zp.items()}
for z,p in zp.items():
    a=al[al.within(p)]; e=es[es.within(p)]; s=si[si.within(p)]
    d={"alberi":len(a),"escapos":len(e),"siti":len(s)}
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
# Life Escapos
S["escapos"]={"colonne":list(es.columns[:-1]),"nota":"cens_id = ID del censimento"}
ids_ID=set(al.ID); ids_C=set(al.CODSITO_ALBERO)
S["escapos"]["cens_id_in_ID"]=int(es.cens_id.isin(ids_ID).sum()); S["escapos"]["cens_id_in_CODSITO"]=int(es.cens_id.isin(ids_C).sum())
m=es.merge(al.drop(columns="geometry").rename(columns={"ID":"cens_id"}),on="cens_id",how="left",suffixes=("","_cens"))
# distanza escapos -> albero censimento con stesso id (via ID e via CODSITO) e al più vicino
alid=al.set_index("ID").geometry
rows=[]
nn=gpd.sjoin_nearest(es[["id","cens_id","species","geometry"]],al[["ID","CODSITO_ALBERO","SPECIE","CIRCONF_CM","geometry"]],how="left",distance_col="dist").drop_duplicates("id")
nn["stesso_id"]=nn.cens_id==nn.ID; nn["stesso_codsito"]=nn.cens_id==nn.CODSITO_ALBERO
nn["stessa_specie"]=nn.species.str.lower().str.split().str[:2].str.join(" ")==nn.SPECIE.str.lower().str.split().str[:2].str.join(" ")
S["escapos"]["nearest"]={"dist_m_p50_p90_max":[round(float(np.percentile(nn.dist,q)),2) for q in (50,90,100)],"nearest_ha_stesso_ID":int(nn.stesso_id.sum()),"nearest_ha_stesso_CODSITO":int(nn.stesso_codsito.sum()),"stessa_specie":int(nn.stessa_specie.sum())}
rows=[]
for _,r in es.iterrows():
    for col,idc in (("ID","ID"),("CODSITO_ALBERO","CODSITO_ALBERO")):
        t=al[al[idc]==r.cens_id]
        if len(t): rows.append((r.id,col,float(t.geometry.iloc[0].distance(r.geometry)),t.SPECIE.iloc[0],r.species))
d=pd.DataFrame(rows,columns=["id","chiave","dist","specie_cens","specie_escapos"])
for col in ("ID","CODSITO_ALBERO"):
    k=d[d.chiave==col]
    S["escapos"][f"join_{col}"]={"n":len(k),"dist_p50_p90_max":[round(float(np.percentile(k.dist,q)),2) for q in (50,90,100)] if len(k) else None,"specie_uguale":int((k.specie_cens.str.lower().str.split().str[:2].str.join(" ")==k.specie_escapos.str.lower().str.split().str[:2].str.join(" ")).sum()) if len(k) else 0}
# DBH escapos vs circonferenza censimento (via nearest)
nn["dbh_cens"]=nn.CIRCONF_CM/np.pi; x=es.set_index("id").dbh_cm.reindex(nn.id).values
ok=nn.dist<=3; S["escapos"]["dbh_vs_circonf_censimento"]={"n":int(ok.sum()),"rapporto_med_dbh_escapos/dbh_cens":round(float(np.median(x[ok.values]/nn.dbh_cens[ok].values)),3),"scarto_mediano_cm":round(float(np.median(x[ok.values]-nn.dbh_cens[ok].values)),2)}
desc={}
for c in ["dbh_cm","h_m","crn_w_m","can_h_m","canopy_area_m2","lai"]:
    v=es[c]; desc[c]={"min":round(float(v.min()),2),"p50":round(float(v.median()),2),"max":round(float(v.max()),2),"nulli":int(v.isna().sum())}
S["escapos"]["parametri"]=desc
S["escapos"]["top_specie"]=es.species.value_counts().head(8).to_dict()
S["escapos"]["rapporto_h_chioma_base"]=round(float((es.can_h_m/es.h_m).median()),3)
nn.drop(columns="geometry").to_csv(f"{OUT}/escapos_vs_censimento.csv",index=False)
for z in ("FA","FB"): al[al.within(zp[z])].to_crs(4326).iloc[:200].to_file(f"{OUT}/alberi_{z}_primi200.geojson",driver="GeoJSON")
json.dump(S,open(f"{OUT}/verde_stats.json","w"),indent=1,ensure_ascii=False,default=str)
print(json.dumps(S,indent=1,ensure_ascii=False,default=str))
