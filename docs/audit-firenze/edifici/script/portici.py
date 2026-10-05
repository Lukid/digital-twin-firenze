"""Verifica del candidato portici: 'Viabilità - Area di Circolazione Pedonale (PolygonZ)' del Comune (rilievo celerimetrico). Conta gli oggetti nei riquadri e ne elenca gli attributi. Scrive campioni/portici_stats.json."""
import os, sys, json, geopandas as gpd
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE, bbox_m
from shapely.geometry import box
RAW=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../data/raw/fi_audit_20261001")
g=gpd.read_file(f"{RAW}/acPed/acPed_s.shp").to_crs(7791)
S={"n_città":len(g),"colonne":[c for c in g.columns if c!="geometry"],"ha_Z":bool(g.geometry.has_z.mean()>0.5)}
for z,b in ZONE.items():
    k=g[g.geometry.centroid.within(box(*bbox_m(b)))]; S[z]={"n":len(k),"area_m2":round(float(k.area.sum())),**{c:{str(a):int(b) for a,b in k[c].value_counts(dropna=False).head(6).items()} for c in ("acPedPos","acPedLiv","acPedSed","acPedZon")}}
json.dump(S,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../campioni/portici_stats.json"),"w"),indent=1); print(S)
