#!/usr/bin/env python3
"""Passo 1: estrae dal file OSM congelato (stesso di T03) le way 'highway' e 'railway' del buffer (riquadro + margine dell'area, DT_AOI),
con riferimenti ai nodi (serve per la topologia vera: due way sono collegate solo se condividono un nodo)
e i nodi con tag. Output: osm_estratto.pkl in rete_lib.OUT (Pisa: data/norm/network/)"""
import glob, pickle, sys, pathlib
import osmium
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from lib import AOI, to_en
sys.path.insert(0, str(ROOT / "network"))
from rete_lib import OUT, AREA
pbf = sorted(glob.glob(str(ROOT / "data/raw" / AREA["osm"] / "*/*.osm.pbf")) + glob.glob(str(ROOT / "data/raw" / AREA["osm"] / "*.osm.pbf")))[0]
x0, y0, x1, y1 = AOI["buf_en"]
M = 60  # margine in più: tiene le way che sconfinano di poco, il grafo viene poi tagliato dal buffer
def inb(e, n): return x0 - M <= e <= x1 + M and y0 - M <= n <= y1 + M
ways, nodes_tag, aree = [], {}, []
fp = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations()
for o in fp:
    if o.is_node():
        if len(o.tags) and o.location.valid():
            e, n = to_en(o.location.lon, o.location.lat)
            if inb(e, n): nodes_tag[o.id] = (e, n, dict(o.tags))
    else:
        t = o.tags
        if t.get("amenity") in ("school", "kindergarten", "university", "college"):   # perimetri di servizio (per gli ingressi)
            try:
                pts = [(n.ref, *to_en(n.lon, n.lat)) for n in o.nodes]
                if any(inb(e, n) for _, e, n in pts): aree.append({"id": o.id, "tags": dict(t), "nodes": pts})
            except osmium.InvalidLocationError: pass
        if "highway" not in t and "railway" not in t: continue
        try: pts = [(n.ref, *to_en(n.lon, n.lat)) for n in o.nodes]
        except osmium.InvalidLocationError: continue
        if not any(inb(e, n) for _, e, n in pts): continue
        ways.append({"id": o.id, "tags": dict(t), "nodes": pts})
OUT.mkdir(parents=True, exist_ok=True); out = OUT / "osm_estratto.pkl"
pickle.dump({"pbf": pbf, "ways": ways, "nodes_tag": nodes_tag, "aree": aree}, open(out, "wb"))
print(pbf, len(ways), "way", len(nodes_tag), "nodi con tag", len(aree), "aree servizio")
