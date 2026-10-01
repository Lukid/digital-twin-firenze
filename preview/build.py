#!/usr/bin/env python3
"""Edifici, alberi, rete, percorsi e ingressi da T04/T05; scuola, fermate e attraversamenti dall'audit. Esegue con pipeline/.venv/bin/python. Converte i campioni dell'audit (solo Z2) in GeoJSON EPSG:4326 per index.html."""
import csv, json, os
A = os.path.join(os.path.dirname(__file__), "..", "docs", "audit")
OUT = os.path.join(os.path.dirname(__file__), "data")
S, W, N, E = json.load(open(f"{A}/ZONE.json"))["zone"]["Z2"]["bbox"]
r = lambda v: round(v, 6)
inb = lambda lat, lon: S <= lat <= N and W <= lon <= E

def dump(name, feats):
    p = f"{OUT}/{name}.geojson"
    json.dump({"type": "FeatureCollection", "features": feats}, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
    print(name, len(feats), os.path.getsize(p) // 1024, "KB")

F = lambda g, p: {"type": "Feature", "geometry": g, "properties": p}
P = lambda lat, lon: {"type": "Point", "coordinates": [r(lon), r(lat)]}

# T05: edifici e alberi gia in 4326 (arrotondati), T04: percorsi e ingressi
G = os.path.join(os.path.dirname(__file__), "..")
def rnd(c): return [rnd(x) for x in c] if isinstance(c[0], list) else [r(c[0]), r(c[1])]
def copia(src, name, keep=None, flt=lambda f: True):
    fs = []
    for f in json.load(open(f"{G}/{src}"))["features"]:
        if not flt(f): continue
        p = {k: v for k, v in f["properties"].items() if k != "cls" and (keep is None or k in keep)}
        fs.append(F({"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}, p))
    dump(name, fs)
copia("geometry/edifici_z2.geojson", "edifici")
copia("geometry/alberi_z2.geojson", "alberi")
copia("network/percorsi_campione.geojson", "percorsi")
copia("network/destinazioni_ingressi.geojson", "ingressi", flt=lambda f: f["geometry"]["type"] == "Point" and f["properties"]["classe"] != "ingresso_fermata")

# grafo T04, solo archi che toccano Z2, EPSG:4326
import geopandas as gpd
from shapely.geometry import box
a = gpd.read_file(f"{G}/data/norm/network/rete_z2.gpkg", layer="archi").to_crs(4326)
a = a[a.intersects(box(W, S, E, N))]
dump("rete", [F({"type": "LineString", "coordinates": [[r(x), r(y)] for x, y in g.coords]},
                {"id": x.edge_id, "tipo": x.tipo_arco, "highway": x.highway, "nome": x["name"] if isinstance(x["name"], str) else "",
                 "marciapiede": x.marciapiede_stato, "m": round(x.length_m, 1)})
              for _, x in a.iterrows() for g in [x.geometry] if g.geom_type == "LineString"])

# scuola e ingressi
c = json.load(open(f"{A}/destinazioni/campioni/candidati_caso_A.json"))["Z2"]
dump("scuola", [F(P(*c["centro_osm"]), {"id": c["osm"], "nome": c["nome_osm"], "indirizzo": "via Filippo Corridoni 42"})])

# fermate GTFS Z2
fer = [F(P(float(x["lat"]), float(x["lon"])), {"id": x["stop_code"], "nome": x["nome"], "corse": int(x["corse_oggi"]), "linee": x["linee_oggi"]})
       for x in csv.DictReader(open(f"{A}/destinazioni/campioni/gtfs_fermate_zone.csv", encoding="utf-8")) if x["zona"] == "Z2"]
dump("fermate", fer)

json.dump([r(S), r(W), r(N), r(E)], open(f"{OUT}/bbox.json", "w"))
