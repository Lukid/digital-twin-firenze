#!/usr/bin/env python3
"""Converte i campioni dell'audit (solo Z2) in GeoJSON EPSG:4326 per index.html."""
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

# edifici: unita volumetriche, altezza uv_av (volo 2010)
b = []
for u in json.load(open(f"{A}/edifici/campioni/rt_uv_Z2.json")):
    try: h = float(u["uv_av"])
    except ValueError: h = None
    for poly in u["polys"]:
        c = poly[0]
        if not any(inb(y, x) for x, y in c): continue
        b.append(F({"type": "Polygon", "coordinates": [[[r(x), r(y)] for x, y in ring] for ring in poly]},
                   {"id": u["uv_id"], "h": h if h is not None else 6.0, "h_nota": "misurato" if h is not None else "stimato",
                    "uso": u["edifc_duso"], "anno": u["anno"], "volo": u["dtvolo"]}))
dump("edifici", b)

# rete OSM
osm = json.load(open(f"{A}/rete/campioni/osm_Z2.json"))["elements"]
PED = {"footway", "pedestrian", "steps", "path", "platform"}
rete, attr = [], []
for e in osm:
    t = e.get("tags", {})
    if e["type"] == "way" and t.get("highway") in PED:
        rete.append(F({"type": "LineString", "coordinates": [[r(g["lon"]), r(g["lat"])] for g in e["geometry"]]},
                      {"id": f"way/{e['id']}", "tipo": t["highway"], "nome": t.get("name", ""), "superficie": t.get("surface", "")}))
    elif e["type"] == "node" and t.get("highway") == "crossing" and inb(e["lat"], e["lon"]):
        attr.append(F(P(e["lat"], e["lon"]), {"id": f"node/{e['id']}", "tipo": t.get("crossing", ""), "segnaletica": t.get("crossing:markings", ""),
                                               "semaforo": t.get("crossing") == "traffic_signals"}))
dump("rete_pedonale", rete); dump("attraversamenti", attr)

# scuola e ingressi
c = json.load(open(f"{A}/destinazioni/campioni/candidati_caso_A.json"))["Z2"]
dump("scuola", [F(P(*c["centro_osm"]), {"id": c["osm"], "nome": c["nome_osm"], "indirizzo": "via Filippo Corridoni 42"})])
dump("ingressi", [F(P(i["lat"], i["lon"]), {"id": f"node/{i['id']}", "tipo": i["tag"]["entrance"],
                    "indirizzo": " ".join(filter(None, [i["tag"].get("addr:street"), i["tag"].get("addr:housenumber")]))})
                  for i in c["ingressi_osm_nel_bbox"]])

# fermate GTFS Z2
fer = [F(P(float(x["lat"]), float(x["lon"])), {"id": x["stop_code"], "nome": x["nome"], "corse": int(x["corse_oggi"]), "linee": x["linee_oggi"]})
       for x in csv.DictReader(open(f"{A}/destinazioni/campioni/gtfs_fermate_zone.csv", encoding="utf-8")) if x["zona"] == "Z2"]
dump("fermate", fer)

# alberi OSM
dump("alberi", [F(P(e["lat"], e["lon"]), {"id": f"node/{e['id']}", "data": e.get("timestamp", "")[:10]})
                for e in json.load(open(f"{A}/verde/campioni/osm_Z2.json"))["elements"]
                if e["type"] == "node" and e.get("tags", {}).get("natural") == "tree" and inb(e["lat"], e["lon"])])
json.dump([r(S), r(W), r(N), r(E)], open(f"{OUT}/bbox.json", "w"))
