"""F01 edifici e quote: conteggi per riquadro (UV Regione, OSM, cassone edilizio Comune), copertura e altezze; nDSM 2023 (e 2017) contro altezza UV.
Scrive campioni/edifici_stats.json e campioni/ndsm_confronto.csv."""
import os, sys, json, glob, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.merge import merge
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from shapely.geometry import Polygon, MultiPolygon, shape
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE, bbox_m
from shapely.geometry import box
HERE=os.path.dirname(os.path.abspath(__file__)); C=f"{HERE}/../campioni"; RAW=f"{HERE}/../../../../data/raw/fi_audit_20261001"
CRS=7791
zp={z:box(*bbox_m(b)) for z,b in ZONE.items()}   # riquadro in metri (rettangolo in 7791: approssima di pochi cm il rettangolo geografico)
zp["FA|FB"]=zp["FA"].union(zp["FB"])
S={}
# --- UV Regione
uv=[]
for z in ("FA","FB"):
    for u in json.load(open(f"{C}/rt_uv_{z}.json")):
        g=gpd.GeoSeries([MultiPolygon([Polygon(p[0],p[1:]) for p in u["polys"]])],crs=4326).to_crs(CRS).iloc[0]
        uv.append({**{k:v for k,v in u.items() if k!="polys"},"geometry":g})
uv=gpd.GeoDataFrame(uv,crs=CRS).drop_duplicates("featureid"); uv["av"]=pd.to_numeric(uv.uv_av,errors="coerce"); uv["qs"]=pd.to_numeric(uv.uv_qs,errors="coerce"); uv["qe"]=pd.to_numeric(uv.uv_qe,errors="coerce")
uv["area"]=uv.area
# --- OSM
def osm(z):
    out=[]
    for e in json.load(open(f"{C}/osm_buildings_{z}.json"))["elements"]:
        if e["type"]=="way" and "geometry" in e and len(e["geometry"])>=4:
            out.append({"osm_id":e["id"],**e["tags"],"geometry":Polygon([(p["lon"],p["lat"]) for p in e["geometry"]])})
        elif e["type"]=="relation":
            outer=[Polygon([(p["lon"],p["lat"]) for p in m["geometry"]]) for m in e.get("members",[]) if m.get("role")=="outer" and len(m.get("geometry",[]))>=4]
            if outer: out.append({"osm_id":e["id"],**e.get("tags",{}),"geometry":MultiPolygon(outer) if len(outer)>1 else outer[0]})
    return gpd.GeoDataFrame(out,crs=4326).to_crs(CRS)
om=pd.concat([osm("FA"),osm("FB")]).drop_duplicates("osm_id"); om=gpd.GeoDataFrame(om,crs=CRS)
# --- Cassone edilizio (Comune, rilievo celerimetrico, PolygonZ, Monte Mario)
cs=gpd.read_file(f"{RAW}/csEdi/csEdi_s.shp").to_crs(CRS)
def inzone(g,z): return g[g.geometry.centroid.within(zp[z])]
def cnt(g,z): return len(inzone(g,z))
S["conteggi"]={z:{"uv_regione":cnt(uv,z),"osm":cnt(om,z),"cassone_comune":cnt(cs,z)} for z in zp}
S["area_m2_totale"]={z:{"uv":round(float(inzone(uv,z).area.sum())),"osm":round(float(inzone(om,z).area.sum())),"cassone":round(float(inzone(cs,z).area.sum()))} for z in zp}
S["cassone_totale_città"]=len(cs); S["cassone_colonne"]=[c for c in cs.columns if c!="geometry"]; S["cassone_ha_Z"]=bool(cs.geometry.has_z.mean()>0.5)
# --- attributi UV
def distr(s,n=8): return {str(k):int(v) for k,v in s.value_counts(dropna=False).head(n).items()}
for z in ("FA","FB"):
    u=inzone(uv,z); d={}
    d["n"]=len(u); d["uv_av_valorizzata"]=int((u.av>0).sum()); d["uv_av_p10_p50_p90"]=[round(float(np.percentile(u.av[u.av>0],q)),1) for q in (10,50,90)]
    d["portico_uv_dpor"]=distr(u.uv_dpor); d["anno"]=distr(u.anno); d["dtvolo"]=distr(u.dtvolo.str[:4]); d["scala"]=distr(u.scala); d["uso"]=distr(u.edifc_duso)
    d["stato"]=distr(u.edifc_dstat); d["sotterraneo"]=distr(u.edifc_dsot); d["classe_uv_cl"]=distr(u.uv_cl)
    S.setdefault("uv_attributi",{})[z]=d
# --- attributi OSM
for z in ("FA","FB"):
    o=inzone(om,z); d={"n":len(o)}
    for k in ("height","building:levels","min_height","building:min_level","roof:height","building:part"):
        d[k]=int(o[k].notna().sum()) if k in o else 0
    d["tag_building"]=distr(o.building); d["con_altezza_o_piani"]=int((o.get("height",pd.Series(dtype=object)).notna()|o.get("building:levels",pd.Series(dtype=object)).notna()).sum()) if len(o) else 0
    S.setdefault("osm_attributi",{})[z]=d
# --- copertura OSM vs UV vs cassone: quota area OSM coperta da UV
uvu=uv.geometry.union_all(); csu=cs.geometry.union_all(); omu=om.geometry.union_all()
for z in ("FA","FB"):
    o=inzone(om,z); u=inzone(uv,z)
    S.setdefault("sovrapposizione",{})[z]={"osm_con_centroide_in_uv":round(float(o.geometry.centroid.within(uvu).mean()),3),
       "uv_con_centroide_in_osm":round(float(u.geometry.centroid.within(omu).mean()),3),
       "osm_area_coperta_da_uv":round(float(o.geometry.intersection(uvu).area.sum()/o.area.sum()),3),
       "uv_area_coperta_da_osm":round(float(u.geometry.intersection(omu).area.sum()/u.area.sum()),3),
       "uv_area_coperta_da_cassone":round(float(u.geometry.intersection(csu).area.sum()/u.area.sum()),3),
       "osm_area_coperta_da_cassone":round(float(o.geometry.intersection(csu).area.sum()/o.area.sum()),3)}
# --- raster
def mosaic(d):
    fs=sorted(glob.glob(f"{RAW}/lidar/{d}/*.ASC")+glob.glob(f"{RAW}/lidar/{d}/*.asc")); src=[rasterio.open(f) for f in fs]
    a,t=merge(src,nodata=-9999); a=a[0].astype("float32"); a[a==-9999]=np.nan; return a,t
def sample_geom(a,t,g):
    m=~geometry_mask([g],out_shape=a.shape,transform=t); return a[m]
res={}
for anno in ("2023","2017"):
    dsm,t=mosaic(f"dsm{anno}"); dtm,t2=mosaic(f"dtm{anno}"); assert t==t2
    # allineamento: stessa griglia; nDSM
    nd=dsm-dtm; res[anno]=(nd,t,dsm,dtm)
    S.setdefault("raster",{})[anno]={"cella_m":abs(t.a),"shape":list(dsm.shape),"nodata_dsm":round(float(np.isnan(dsm).mean()),4),"nodata_dtm":round(float(np.isnan(dtm).mean()),4),
        "estensione_E_N":[round(t.c),round(t.f+t.e*dsm.shape[0]),round(t.c+t.a*dsm.shape[1]),round(t.f)]}
for anno in ("2023","2017"):
    nd_,t_,_,_=res[anno]
    for z in ("FA","FB"):
        mk=~geometry_mask([zp[z]],out_shape=nd_.shape,transform=t_)
        S["raster"][anno][f"nodata_nDSM_{z}"]=round(float(np.isnan(nd_[mk]).mean()),4)
# nDSM 2023: UV con area >=40 m2, buffer interno -1 m, bordo non fuori dal mosaico
nd,t,dsm,dtm=res["2023"]; nd17,t17,dsm17,dtm17=res["2017"]
rows=[]
for _,r in uv.iterrows():
    g=r.geometry
    if g.area<40 or not (g.centroid.within(zp["FA|FB"])): continue
    gi=g.buffer(-1.0)
    if gi.is_empty or gi.area<15: continue
    v=sample_geom(nd,t,gi); v=v[~np.isnan(v)]
    if len(v)<20: continue
    v17=sample_geom(nd17,t17,gi); v17=v17[~np.isnan(v17)]
    zz="FA" if g.centroid.within(zp["FA"]) else "FB"
    vt=sample_geom(dtm,t,gi); vt=vt[~np.isnan(vt)]
    rows.append(dict(zona=zz,uv_id=r.uv_id,uv_qs=r.qs,uv_qe=r.qe,dtm23_med=round(float(np.median(vt)),2) if len(vt) else np.nan,area_m2=round(g.area),uv_av=r.av,uv_por=r.uv_dpor,anno_uv=r.anno,ndsm23_med=round(float(np.median(v)),2),ndsm23_p90=round(float(np.percentile(v,90)),2),
                     ndsm17_med=round(float(np.median(v17)),2) if len(v17)>=20 else np.nan))
D=pd.DataFrame(rows); D.to_csv(f"{C}/ndsm_confronto.csv",index=False)
def st(x): x=np.asarray(x,float); x=x[~np.isnan(x)]; return {"n":int(len(x)),"mediana":round(float(np.median(x)),2),"p10":round(float(np.percentile(x,10)),2),"p90":round(float(np.percentile(x,90)),2),"MAE":round(float(np.mean(np.abs(x))),2)}
K=D[D.uv_av>0]
S["ndsm_vs_uv"]={"n_uv_testati":len(D)}
for z in ("ALL","FA","FB"):
    k=K if z=="ALL" else K[K.zona==z]
    S["ndsm_vs_uv"][z]={"ndsm23_med - uv_av":st(k.ndsm23_med-k.uv_av),"ndsm23_p90 - uv_av":st(k.ndsm23_p90-k.uv_av),"ndsm17_med - uv_av":st(k.ndsm17_med-k.uv_av),"ndsm23_med - ndsm17_med":st(k.ndsm23_med-k.ndsm17_med)}
# quota di UV entro +-1 m e +-2 m
d=(K.ndsm23_med-K.uv_av).abs(); S["ndsm_vs_uv"]["quota_entro_1m"]=round(float((d<=1).mean()),3); S["ndsm_vs_uv"]["quota_entro_2m"]=round(float((d<=2).mean()),3)
S["ndsm_vs_uv"]["quota_entro_1m_ndsm17"]=round(float(((K.ndsm17_med-K.uv_av).abs()<=1).mean()),3)
# per classe di altezza UV
K=K.assign(cl=pd.cut(K.uv_av,[0,4,8,15,100],labels=["<4","4-8","8-15",">15"]))
S["ndsm_vs_uv"]["per_classe_altezza_uv"]={str(c):st(g.ndsm23_med-g.uv_av) for c,g in K.groupby("cl",observed=True)}
# portici
P=D[D.uv_por.fillna("").ne("Al Suolo")]; S["portici_uv"]={"n_uv_non_al_suolo_testati":len(P),"valori":distr(uv.uv_dpor,12)}
# quota di spiccato UV (uv_qs) contro DTM 2023 sotto l'impronta: scarto sistematico (datum) e volumi sospesi (scarto molto sopra la mediana)
dq=(D.uv_qs-D.dtm23_med).dropna(); med=float(dq.median())
S["quota_spiccato_uv_vs_dtm23"]={**st(dq),"mediana_scarto_usata_come_datum":round(med,2),"uv_con_spiccato_oltre_2_5m_sopra_il_suolo":int(((dq-med)>2.5).sum()),"uv_con_spiccato_oltre_2_5m_sotto_il_suolo":int(((dq-med)<-2.5).sum()),
   "uv_con_spiccato_oltre_2_5m_sopra_il_suolo_per_portico":distr(D.loc[dq[(dq-med)>2.5].index,"uv_por"])}
# OSM con altezza: confronto con nDSM
rows=[]
for _,r in om.iterrows():
    h=None
    try: h=float(str(r.get("height","")).replace("m","").strip()) if pd.notna(r.get("height")) else None
    except: pass
    if h is None and pd.notna(r.get("building:levels")):
        try: h=float(r["building:levels"])*3.0
        except: pass
    if h is None: continue
    gi=r.geometry.buffer(-1.0)
    if gi.is_empty or gi.area<15: continue
    v=sample_geom(nd,t,gi); v=v[~np.isnan(v)]
    if len(v)>=20: rows.append(dict(osm_id=r.osm_id,h_osm=h,ndsm23_med=float(np.median(v))))
S["osm_vs_ndsm"]={"n":len(rows),**(st([x["ndsm23_med"]-x["h_osm"] for x in rows]) and {"ndsm - h_osm":st([x["ndsm23_med"]-x["h_osm"] for x in rows])} if rows else {})}
# edifici nuovi o spariti rispetto a UV 2011: OSM con nDSM mediana <1.5 m (non ci sono edifici nel 2023) e celle alte fuori da tutte le impronte
rows=[]
for z in ("FA","FB"):
    for _,r in inzone(om,z).iterrows():
        gi=r.geometry.buffer(-1.0)
        if gi.is_empty or gi.area<15: continue
        v=sample_geom(nd,t,gi); v=v[~np.isnan(v)]
        if len(v)>=20: rows.append(float(np.median(v)))
S["osm_ndsm_mediana_sotto_1_5m"]={"n_testati":len(rows),"n_sotto":int((np.array(rows)<1.5).sum())}
# area con nDSM>3 m non coperta da nessuna impronta (UV, OSM, cassone) nei riquadri, esclusa vegetazione non distinguibile: solo conteggio grezzo
allf=gpd.GeoSeries([uvu,omu,csu]).union_all().buffer(2)
for z in ("FA","FB"):
    mk=~geometry_mask([zp[z]],out_shape=nd.shape,transform=t); hi=(nd>3)&mk
    cov=geometry_mask([allf],out_shape=nd.shape,transform=t,invert=True)
    S.setdefault("celle_alte_senza_impronta",{})[z]={"area_nDSM_gt3m_m2":round(float(hi.sum()*abs(t.a*t.e))),"di_cui_fuori_da_tutte_le_impronte_m2":round(float((hi&~cov).sum()*abs(t.a*t.e)))}
json.dump(S,open(f"{C}/edifici_stats.json","w"),indent=1,ensure_ascii=False)
print(json.dumps(S,indent=1,ensure_ascii=False))
