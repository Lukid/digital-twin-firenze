#!/usr/bin/env python3
"""Metriche rete pedonale per riquadro dai JSON Overpass in campioni/. Solo stdlib + networkx. Stampa JSON e scrive campioni/metriche_osm.json."""
import json, math, collections, sys
import networkx as nx
import os
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
ZONE = {k: tuple(v["bbox"]) for k, v in json.load(open("../RIQUADRO.json"))["zone"].items()}
DED = {"footway", "path", "pedestrian", "steps", "cycleway", "bridleway"}
ROAD = {"primary","secondary","tertiary","residential","unclassified","living_street","service","trunk","primary_link","secondary_link","tertiary_link","trunk_link","road"}
WALK = DED | ROAD | {"track"}
def d(a, b):
    k = 111320.0; return math.hypot((a[0]-b[0])*k, (a[1]-b[1])*k*math.cos(math.radians(43.80)))
def inside(p, bb): return bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3]
def sw(t):
    v = [t.get(k) for k in ("sidewalk","sidewalk:left","sidewalk:right","sidewalk:both")]
    v = [x for x in v if x]
    if not v: return "assente"
    if all(x in ("no","none","separate") and x != "separate" for x in v): return "no"
    if any(x == "separate" for x in v) and all(x in ("separate","no","none") for x in v): return "separate"
    return "si"
out = {}
for z, bb in ZONE.items():
    els = json.load(open(f"campioni/osm_{z}.json"))["elements"]
    km = collections.Counter(); n = collections.Counter(); G = nx.Graph(); tags = collections.Counter()
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and "highway" in t:
            h = t["highway"]; g = e["geometry"]
            L = sum(d((g[i]["lat"],g[i]["lon"]),(g[i+1]["lat"],g[i+1]["lon"])) for i in range(len(g)-1)
                    if inside(((g[i]["lat"]+g[i+1]["lat"])/2,(g[i]["lon"]+g[i+1]["lon"])/2), bb))
            if L == 0: continue
            if t.get("footway") == "crossing": km["footway_crossing_km"] += L; n["way_footway_crossing"] += 1
            elif t.get("footway") == "sidewalk": km["footway_sidewalk_km"] += L; n["way_footway_sidewalk"] += 1
            if h in DED: km["dedicata_km"] += L; km["dedicata_"+h+"_km"] += L
            if h in ROAD:
                km["strade_km"] += L; 
                if h != "service": km["strade_nonservice_km"] += L; km["sw_"+sw(t)+"_km"] += L
            if h in WALK and t.get("foot") not in ("no","private") and t.get("access") not in ("no","private"):
                km["percorribile_km"] += L
                nd = e["nodes"]
                for i in range(len(nd)-1):
                    G.add_edge(nd[i], nd[i+1], w=d((g[i]["lat"],g[i]["lon"]),(g[i+1]["lat"],g[i+1]["lon"])))
            if h in WALK and t.get("foot") in ("no",) : n["way_foot_no"] += 1
            for k in ("lit","wheelchair","surface","tactile_paving","incline"): 
                if k in t and h in DED|{"pedestrian"}: tags[k] += 1
            n["way_"+("ded" if h in DED else "road" if h in ROAD else "altro")] += 1
        elif e["type"] == "node" and inside((e["lat"], e["lon"]), bb):
            if t.get("highway") == "crossing": 
                n["crossing_nodes"] += 1; n["crossing_"+t.get("crossing", "senza_tag")] += 1
                if "tactile_paving" in t: n["crossing_tactile_tag"] += 1
                if "kerb" in t: n["crossing_kerb_tag"] += 1
            if "kerb" in t: n["kerb_nodes"] += 1
            if "barrier" in t: n["barrier_"+t["barrier"]] += 1; n["barrier_tot"] += 1
            if "entrance" in t:
                n["entrance_tot"] += 1; n["entrance_"+t["entrance"]] += 1
                if "wheelchair" in t: n["entrance_wheelchair_tag"] += 1
            if t.get("railway") == "crossing": n["railway_crossing"] += 1
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    cl = [sum(G[u][v]["w"] for u, v in G.subgraph(c).edges) for c in comps]
    out[z] = dict(km={k: round(v/1000, 2) for k, v in km.items()}, n=dict(n), tag_dedicate=dict(tags),
        componenti=len(comps), km_componente_max=round(cl[0]/1000, 2) if cl else 0,
        km_fuori_max=round((sum(cl)-cl[0])/1000, 2) if cl else 0,
        componenti_sotto_100m=sum(1 for x in cl if x < 100),
        top5_componenti_km=[round(x/1000, 2) for x in cl[:5]])
if __name__ == "__main__":
  json.dump(out, open("campioni/metriche_osm.json", "w"), indent=1, ensure_ascii=False)
  print(json.dumps(out, indent=1, ensure_ascii=False))
