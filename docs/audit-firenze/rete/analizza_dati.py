#!/usr/bin/env python3
"""Barriere (agganciate alla rete OSM), Walking City, rifugi climatici: conteggi per FA e FB. Scrive campioni/metriche_dati.json."""
import json, os, zipfile, glob, re, collections
import geopandas as gpd, numpy as np
from shapely.geometry import LineString, box
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
RAW = "../../../data/raw/fi_audit_20261001"
ZONE = {k: v["bbox"] for k, v in json.load(open("../RIQUADRO.json"))["zone"].items()}
M = "EPSG:32632"
WALK = {"footway","path","pedestrian","steps","cycleway","bridleway","track","primary","secondary","tertiary","residential","unclassified","living_street","service","trunk","primary_link","secondary_link","tertiary_link","trunk_link","road"}
def bb(z): s, w, n, e = ZONE[z]; return gpd.GeoSeries([box(w, s, e, n)], crs=4326).to_crs(M).iloc[0]
def osm_edges(z):
    r = []
    for e in json.load(open(f"campioni/osm_{z}.json"))["elements"]:
        t = e.get("tags", {})
        if e["type"] == "way" and t.get("highway") in WALK and t.get("foot") not in ("no","private") and t.get("access") not in ("no","private"):
            r.append(LineString([(p["lon"], p["lat"]) for p in e["geometry"]]))
    return gpd.GeoSeries(r, crs=4326).to_crs(M)
out = {}
# barriere
import tempfile
T = tempfile.mkdtemp(); zipfile.ZipFile(f"{RAW}/barriere.zip").extractall(T)
b = gpd.read_file(T + "/mappa_accessibilitaPoint.shp", encoding="cp850").to_crs(M)  # il dbf non dichiara la codifica: cp850 rende "università"
b["destinaz_u"] = b.destinaz_u.str.lower().str.strip()
out["barriere_totale"] = dict(schede=len(b), grado=b.grado_acce.value_counts().to_dict(), colonne=[c for c in b.columns if c != "geometry"])
rif = gpd.read_file(f"{RAW}/rifugi.geojson").to_crs(M)
wc = []
for f in sorted(glob.glob(f"{RAW}/walking/*.kmz")):
    kml = zipfile.ZipFile(f).read("doc.kml").decode("utf8")
    for ls in re.findall(r"<LineString>.*?<coordinates>(.*?)</coordinates>", kml, re.S):
        pts = [tuple(map(float, p.split(",")[:2])) for p in ls.split()]
        wc.append((os.path.basename(f), LineString(pts)))
wcg = gpd.GeoDataFrame({"file": [x[0] for x in wc]}, geometry=[x[1] for x in wc], crs=4326).to_crs(M)
out["walking_city_totale"] = dict(percorsi=wcg.file.nunique(), tratti=len(wcg), km=round(wcg.length.sum()/1000, 1))
for z in ZONE:
    B = bb(z); E = osm_edges(z); U = E.union_all()
    bz = b[b.within(B)].copy(); bz["d"] = bz.distance(U)
    sn = bz[bz.d <= 10]
    r = dict(area_km2=round(B.area/1e6, 2), barriere=len(bz), grado=bz.grado_acce.value_counts().to_dict(),
        destinazioni_top=bz.destinaz_u.value_counts().head(8).to_dict(), agganciate_10m=len(sn),
        agganciate_pct=round(100*len(sn)/len(bz), 1) if len(bz) else None,
        distanza_mediana_m=round(float(bz.d.median()), 1) if len(bz) else None,
        grado_agganciate=sn.grado_acce.value_counts().to_dict(),
        n_archi_osm=len(E))
    # rifugi
    rd = rif.distance(B); ins = rif[rif.intersects(B)]
    r["rifugi_intersecano"] = len(ins); r["rifugi_ombra_pct"] = ins.percentuale_ombreggi.astype(float).tolist()
    r["rifugi_nomi"] = ins.nome_area.tolist()
    r["rifugio_piu_vicino_dal_bordo_m"] = round(float(rd.min()), 0) if not len(ins) else 0
    r["rifugio_piu_vicino"] = rif.loc[rd.idxmin(), "nome_area"]
    # walking city
    r["walking_city_piu_vicino_m"] = round(float(wcg.distance(B).min()), 0)
    r["walking_city_km"] = round(wcg.intersection(B).length.sum()/1000, 2)
    r["walking_city_percorsi"] = sorted(set(wcg[wcg.intersects(B)].file))
    out[z] = r
json.dump(out, open("campioni/metriche_dati.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
