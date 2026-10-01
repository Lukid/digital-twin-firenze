#!/usr/bin/env python3
"""Destinazioni per zona e quante hanno almeno un nodo entrance=* entro 80 m dal centro (proxy grezzo: i centroidi di edifici grandi sono lontani dagli ingressi)."""
import json, math
from analizza_osm import ZONE, d
P = json.load(open("campioni/osm_poi.json"))["elements"]; res = {}
for z, b in ZONE.items():
    ent = [(e["lat"], e["lon"]) for e in json.load(open(f"campioni/osm_{z}.json"))["elements"] if e["type"] == "node" and "entrance" in e.get("tags", {})]
    c = {}; withent = 0; dest = 0
    for e in P:
        la = e.get("lat") or e["center"]["lat"]; lo = e.get("lon") or e["center"]["lon"]
        if not (b[0] <= la <= b[2] and b[1] <= lo <= b[3]): continue
        t = e["tags"]; k = t.get("amenity") or t.get("highway") or t.get("railway"); c[k] = c.get(k, 0) + 1
        if t.get("amenity") in ("school", "university", "college", "hospital", "kindergarten"):
            dest += 1; withent += any(d((la, lo), x) < 80 for x in ent)
    res[z] = dict(conteggi=c, destinazioni=dest, con_ingresso_entro_80m=withent)
print(json.dumps(res, ensure_ascii=False))
