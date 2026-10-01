#!/usr/bin/env python3
"""Passo 2: grafo pedonale Z2+500 m dalle regole di network/regole.json.
Input: data/norm/network/osm_estratto.pkl (passo 1). Output: data/norm/network/{rete_z2.gpkg, rete_z2.graphml, rete_z2.pkl},
network/{rete_manifest.json, componenti.json}."""
import collections, hashlib, json, pathlib, pickle, sys
import geopandas as gpd, networkx as nx
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from lib import AOI
OUT = ROOT / "data/norm/network"; NET = ROOT / "network"
R = json.load(open(NET / "regole.json"))
X0, Y0, X1, Y1 = AOI["buf_en"]; Z = AOI["z2_en"]
SNAP = json.load(open(ROOT / "pipeline/snapshots/snp_osm_pisa_20261001.json"))
D = pickle.load(open(OUT / "osm_estratto.pkl", "rb"))
NT = D["nodes_tag"]

HW, FOOT_OK = R["highway"], set(R["foot"]["ammessi_sempre"])
SIDEWALK_POS = {"yes", "both", "left", "right"}

def sidewalk_state(t):
    v = [t.get(k) for k in ("sidewalk", "sidewalk:both", "sidewalk:left", "sidewalk:right") if t.get(k)]
    if any(x in SIDEWALK_POS for x in v): return "presente"
    if any(x == "separate" for x in v): return "separato"
    if v and all(x in ("no", "none") for x in v): return "assente"
    return "ignoto"

def classify(t):
    """-> (percorribile, motivo_esclusione, note[])"""
    h, note = t["highway"], []
    foot, acc = t.get("foot"), t.get("access")
    if t.get("railway") == "platform" or (t.get("public_transport") == "platform" and any(t.get(k) == "yes" for k in ("train", "subway", "tram", "light_rail"))):
        return False, "banchina_ferroviaria", note
    if "railway" in t: return False, "ferrovia_railway", note
    if t.get("area") == "yes": return False, "area_poligono", note
    if h in HW["esclusi"]: return False, f"highway={h}", note
    if foot in R["foot"]["esclusi"]: return False, f"foot={foot}", note
    pos = foot in FOOT_OK
    if h in HW["solo_con_foot_esplicito"]["classi"]:
        if not pos: return False, "classe_non_pedonale_senza_foot", note
    elif h not in HW["percorribili"]: return False, f"highway={h}_non_ammesso", note
    if not pos and acc in R["access"]["esclusi"]: return False, f"access={acc}", note
    if foot in R["foot"]["ammesso_con_nota"]: note.append(f"foot={foot}")
    if not pos and acc in R["access"]["ammesso_con_nota"]: note.append(f"access={acc}")
    if t.get("tunnel") == "yes" and h not in ("footway", "pedestrian", "path", "steps") and not pos \
            and sidewalk_state(t) not in ("presente", "separato"):
        return False, "tunnel_stradale_senza_marciapiede", note
    return True, None, note

def tipo_arco(t):
    h = t["highway"]
    if t.get("footway") == "crossing" or (h == "footway" and "crossing" in t): return "attraversamento"
    if h == "steps": return "scala"
    if t.get("tunnel") in ("yes", "building_passage"): return "sottopasso"
    if t.get("bridge") == "yes": return "ponte"
    if t.get("footway") == "sidewalk": return "marciapiede_disegnato"
    if h in ("living_street", "residential", "service", "unclassified", "tertiary", "tertiary_link", "secondary", "secondary_link", "primary", "primary_link", "trunk", "trunk_link", "motorway", "motorway_link"): return "strada"
    return "sentiero"

def num(v):
    try: return float(str(v).replace(",", ".").split()[0])
    except Exception: return None

# ---- way da usare (aree e ferrovia esclusi dalla segmentazione)
ways = [w for w in D["ways"] if "highway" in w["tags"] and "railway" not in w["tags"] and w["tags"].get("area") != "yes"]
banchine = [w for w in D["ways"] if "highway" in w["tags"] and ("railway" in w["tags"] or w["tags"].get("area") == "yes")]
binari = [w for w in D["ways"] if "railway" in w["tags"] and w["tags"]["railway"] in ("rail", "light_rail", "tram", "subway", "narrow_gauge", "funicular", "platform", "platform_edge")]
for w in ways: w["ok"], w["motivo"], w["note"] = classify(w["tags"])
banchina_nodi = {n for w in D["ways"] if "highway" in w["tags"] and classify(w["tags"])[1] == "banchina_ferroviaria" for n, _, _ in w["nodes"]}

# ---- punti di spezzatura
inc = collections.Counter()
for w in ways:
    for n in set(n for n, _, _ in w["nodes"]): inc[n] += 1
BAR = set(R["barriere"]["nodi_spezzano"])
def nodo_barriera(t): return t.get("barrier") in BAR
def nodo_crossing(t): return t.get("highway") == "crossing"
def nodo_kerb(t): return t.get("barrier") == "kerb" or "kerb" in t
special = {n for n, (_, _, t) in NT.items() if nodo_barriera(t) or nodo_crossing(t)}

def barriera_stato(t):
    b = t.get("barrier")
    if b in R["barriere"]["bloccanti"]: return "bloccato", f"barrier={b}"
    if b == "gate" or b in R["barriere"]["passabili_con_nota"]:
        for k in ("access", "foot"):
            if t.get(k) in R["access"]["esclusi"] + ["no"] and not (k == "access" and t.get("foot") in FOOT_OK): return "bloccato", f"barrier={b} {k}={t[k]}"
        return "passabile", f"barrier={b}: da verificare" if b in ("gate", "sally_port", "lift_gate", "turnstile", "swing_gate") else f"barrier={b}"
    return "passabile", f"barrier={b}"

segs, esclusi = [], []
for w in ways:
    pts, t = w["nodes"], w["tags"]
    cut = [0] + [i for i in range(1, len(pts) - 1) if inc[pts[i][0]] >= 2 or pts[i][0] in special or sum(1 for p in pts if p[0] == pts[i][0]) > 1] + [len(pts) - 1]
    seen = collections.Counter()
    for a, b in zip(cut, cut[1:]):
        sub = pts[a:b + 1]
        g = LineString([(x, y) for _, x, y in sub])
        m = g.interpolate(0.5, normalized=True)
        if not (X0 <= m.x <= X1 and Y0 <= m.y <= Y1): continue
        n0, n1 = sub[0][0], sub[-1][0]
        eid = f"edg_osm_{w['id']}_{n0}_{n1}"; seen[eid] += 1
        if seen[eid] > 1: eid += f"_{seen[eid]}"
        segs.append(dict(w=w, id=eid, n0=n0, n1=n1, geom=g, verts=[n for n, _, _ in sub]))

# ---- attributi arco
def edge_attrs(s):
    w, t = s["w"], s["w"]["tags"]
    tp = tipo_arco(t)
    mk = sidewalk_state(t) if tp == "strada" else ("non_applicabile" if tp in ("sentiero", "scala", "attraversamento", "marciapiede_disegnato", "sottopasso", "ponte") and t["highway"] in ("footway", "pedestrian", "path", "steps", "platform", "cycleway") else sidewalk_state(t))
    a = {"edge_id": s["id"], "way_id": f"way_osm_{w['id']}", "nod_da": f"nod_osm_{s['n0']}", "nod_a": f"nod_osm_{s['n1']}",
         "length_m": round(s["geom"].length, 2), "highway": t["highway"], "tipo_arco": tp, "name": t.get("name"),
         "marciapiede_stato": mk, "marciapiede_dichiarato": mk in ("presente", "separato", "non_applicabile"),
         "scala": t["highway"] == "steps", "bridge": t.get("bridge"), "tunnel": t.get("tunnel"), "layer": t.get("layer"), "level": t.get("level"),
         "indoor": t.get("indoor") == "yes", "foot": t.get("foot"), "access": t.get("access"), "surface": t.get("surface"),
         "width": t.get("width"), "incline": t.get("incline"), "lit": t.get("lit"), "wheelchair": t.get("wheelchair"),
         "tactile_paving": t.get("tactile_paving"), "step_count": t.get("step_count"), "handrail": t.get("handrail"), "ramp": t.get("ramp"),
         "crossing": t.get("crossing"), "crossing_markings": t.get("crossing:markings"),
         "n_kerb": sum(1 for n in s["verts"] if n in NT and nodo_kerb(NT[n][2])),
         "termina_su_banchina": bool({s["n0"], s["n1"]} & banchina_nodi),
         "note": "; ".join(w["note"]) or None}
    return a

from shapely.ops import unary_union
PLAT = unary_union([Polygon([(x, y) for _, x, y in w["nodes"]]).buffer(0.5) for w in D["ways"] if w["tags"].get("railway") == "platform" and len(w["nodes"]) > 3 and w["nodes"][0][0] == w["nodes"][-1][0]])
edges, excl_rows = [], []
for s in segs:
    a = edge_attrs(s)
    if s["w"]["ok"] and PLAT.intersection(s["geom"]).length > 0.5 * s["geom"].length:   # scale e percorsi disegnati dentro la banchina
        excl_rows.append({**{k: a[k] for k in ("edge_id", "way_id", "highway", "name", "length_m", "foot", "access", "tunnel", "bridge")}, "motivo": "banchina_ferroviaria", "geometry": s["geom"]})
    elif s["w"]["ok"]: edges.append((s, a))
    else: excl_rows.append({**{k: a[k] for k in ("edge_id", "way_id", "highway", "name", "length_m", "foot", "access", "tunnel", "bridge")}, "motivo": s["w"]["motivo"], "geometry": s["geom"]})
for w in banchine:   # banchine e aree: registrate come escluse (solo per vista e test)
    if "highway" in w["tags"]:
        g = LineString([(x, y) for _, x, y in w["nodes"]]) if len(w["nodes"]) > 1 else None
        if g is not None and g.intersects(Polygon([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)])):
            excl_rows.append({"edge_id": f"way_osm_{w['id']}", "way_id": f"way_osm_{w['id']}", "highway": w["tags"]["highway"], "name": w["tags"].get("name"), "length_m": round(g.length, 2),
                              "foot": w["tags"].get("foot"), "access": w["tags"].get("access"), "tunnel": w["tags"].get("tunnel"), "bridge": w["tags"].get("bridge"),
                              "motivo": classify(w["tags"])[1] if "railway" in w["tags"] else "area_poligono", "geometry": g})

# ---- nodi
G = nx.MultiGraph()
bloccati = []
coords = {}
for w in ways:
    for n, x, y in w["nodes"]: coords[n] = (x, y)
for s, a in edges:
    for n in (s["n0"], s["n1"]):
        if f"nod_osm_{n}" in G: continue
        x, y = coords[n]; t = NT.get(n, (0, 0, {}))[2]
        at = {"x": x, "y": y, "bordo_buffer": min(x - X0, X1 - x, y - Y0, Y1 - y) < R["area"]["bordo_m"], "in_z2": Z[0] <= x <= Z[2] and Z[1] <= y <= Z[3]}
        if nodo_crossing(t): at.update(crossing=t.get("crossing"), tactile_paving=t.get("tactile_paving"), kerb=t.get("kerb"), crossing_markings=t.get("crossing:markings"), semaforo=t.get("crossing") == "traffic_signals" or t.get("crossing:signals") == "yes")
        if nodo_barriera(t):
            st, nota = barriera_stato(t); at.update(barriera=t["barrier"], barriera_stato=st, barriera_nota=nota)
            if st == "bloccato": bloccati.append({"node_id": f"nod_osm_{n}", "motivo": nota, "geometry": Point(x, y)})
        G.add_node(f"nod_osm_{n}", **at)
bloc_ids = {b["node_id"] for b in bloccati}
for s, a in edges:
    if a["nod_da"] in bloc_ids or a["nod_a"] in bloc_ids: continue
    G.add_edge(a["nod_da"], a["nod_a"], key=a["edge_id"], geom=s["geom"], **a)
G.remove_nodes_from([n for n in list(G.nodes) if G.degree(n) == 0])

# ---- componenti (ordine: km decrescenti)
comps = sorted(nx.connected_components(G), key=lambda c: -sum(d["length_m"] for _, _, d in G.subgraph(c).edges(data=True)))
for i, c in enumerate(comps, 1):
    for n in c: G.nodes[n]["componente"] = f"cmp_{i:02d}"
for u, v, k, d in G.edges(keys=True, data=True): d["componente"] = G.nodes[u]["componente"]

# ---- layer discordanti: nodo interno a ponte/tunnel condiviso con way di altro livello (da rivedere)
def lk(w): t = w["tags"]; return (t.get("layer", "0"), t.get("bridge"), t.get("tunnel"))
wn = collections.defaultdict(list)
for w in ways:
    if w["ok"]:
        for i, (n, _, _) in enumerate(w["nodes"]): wn[n].append((w, 0 < i < len(w["nodes"]) - 1))
sospetti = sorted({f"nod_osm_{n}" for n, l in wn.items() if f"nod_osm_{n}" in G and len({lk(w) for w, _ in l}) > 1 and any(i and (lk(w)[1] or lk(w)[2] in ("yes",)) for w, i in l)})

# ---- salvataggio
def gdf(rows, cols=None): return gpd.GeoDataFrame(rows, geometry="geometry", crs=7791)
nodi = gdf([{"node_id": n, **{k: v for k, v in d.items() if k not in ("x", "y")}, "geometry": Point(d["x"], d["y"])} for n, d in G.nodes(data=True)])
nodi["grado"] = [G.degree(n) for n in nodi.node_id]
archi = gdf([{**{k: v for k, v in d.items() if k != "geom"}, "geometry": d["geom"]} for _, _, d in G.edges(data=True)])
gp = OUT / "rete_z2.gpkg"
if gp.exists(): gp.unlink()
for name, g in (("nodi", nodi), ("archi", archi), ("archi_esclusi", gdf(excl_rows)), ("nodi_bloccati", gdf(bloccati) if bloccati else gdf([{"node_id": None, "motivo": None, "geometry": Point(0, 0)}]).iloc[0:0])):
    g.to_file(gp, layer=name, driver="GPKG")
H = nx.Graph()   # GraphML: attributi scalari, senza geometria (la geometria è nel GeoPackage)
for n, d in G.nodes(data=True): H.add_node(n, **{k: v for k, v in d.items() if v is not None})
for u, v, k, d in G.edges(keys=True, data=True): H.add_edge(u, v, **{kk: vv for kk, vv in d.items() if kk != "geom" and vv is not None}) if not H.has_edge(u, v) else None
nx.write_graphml(H, OUT / "rete_z2.graphml")
pickle.dump({"G": G, "binari": binari, "banchine": banchine, "bloccati": bloccati, "esclusi": excl_rows}, open(OUT / "rete_z2.pkl", "wb"))

# ---- report componenti
ex_geoms = [r["geometry"] for r in excl_rows]; ex_tree = STRtree(ex_geoms)
area_g = [Polygon([(x, y) for _, x, y in w["nodes"]]) for w in D["ways"] if "highway" in w["tags"] and w["tags"].get("area") == "yes" and "railway" not in w["tags"] and len(w["nodes"]) > 3]
ar_tree = STRtree(area_g) if area_g else None
main = comps[0]; main_geoms = [d["geom"] for u, v, d in G.subgraph(main).edges(data=True)]; mt = STRtree(main_geoms)
rows = []
for i, c in enumerate(comps, 1):
    sg = G.subgraph(c); es = list(sg.edges(data=True)); km = sum(d["length_m"] for _, _, d in es) / 1000
    kz = sum(d["length_m"] for u, _, d in es if G.nodes[u]["in_z2"]) / 1000
    r = {"componente": f"cmp_{i:02d}", "nodi": len(c), "archi": len(es), "km": round(km, 3), "km_in_z2": round(kz, 3), "principale": i == 1,
         "tipi": dict(collections.Counter(d["tipo_arco"] for _, _, d in es)), "highway": dict(collections.Counter(d["highway"] for _, _, d in es))}
    if i > 1:
        geom = [d["geom"] for _, _, d in es]; mg = max(geom, key=lambda g: g.length)
        gap = min(g.distance(main_geoms[int(mt.nearest(g))]) for g in geom)
        why = []
        if any(G.nodes[n]["bordo_buffer"] for n in c): why.append("taglio del buffer: la rete prosegue fuori dal riquadro")
        if gap <= 3: why.append(f"possibile connessione mancante: a {gap:.1f} m dalla componente principale senza nodo condiviso")
        near = set()
        for g in geom:
            for j in ex_tree.query(g.buffer(3)):
                if ex_geoms[int(j)].distance(g) <= 3: near.add(excl_rows[int(j)]["motivo"])
        if near: why.append("adiacente a tratti esclusi: " + ", ".join(sorted(near)))
        if ar_tree is not None and any(area_g[int(j)].distance(g) <= 5 for g in geom for j in ar_tree.query(g.buffer(5))): why.append("vicino a un'area a poligono non modellata (piazza o banchina)")
        if any(b["geometry"].distance(Point(G.nodes[n]["x"], G.nodes[n]["y"])) < 3 for b in bloccati for n in c): why.append("vicino a un nodo bloccante (cancello privato o muro)")
        if all(d["highway"] == "service" for _, _, d in es): why.append("solo viabilità di servizio (cortile, parcheggio, passo carraio) non collegata")
        if any(d["tipo_arco"] in ("scala", "sottopasso") for _, _, d in es): why.append("contiene scale o sottopasso con una sola estremità collegata")
        if not why: why.append("nessuna connessione mappata in OSM: lacuna di mappatura o vero isolamento, da verificare")
        r.update(gap_dalla_principale_m=round(gap, 1), motivi=why)
    rows.append(r)
json.dump(rows, open(NET / "componenti.json", "w"), ensure_ascii=False, indent=1)

def km(f): return round(sum(d["length_m"] for _, _, d in G.edges(data=True) if f(d)) / 1000, 3)
Zed = lambda d: G.nodes[d["nod_da"]]["in_z2"]
man = {"graph_id": f"grf_z2_osm_{SNAP['snapshot_id'][-8:]}", "aoi_id": "aoi_z2", "crs": "EPSG:7791", "snapshot_id": SNAP["snapshot_id"], "sha256_osm": SNAP["sha256"],
       "regole_sha256": hashlib.sha256((NET / "regole.json").read_bytes()).hexdigest(), "area_buffer_en": AOI["buf_en"], "z2_en": Z,
       "nodi": G.number_of_nodes(), "archi": G.number_of_edges(), "km_totali": km(lambda d: True), "km_in_z2": km(Zed),
       "archi_per_tipo": dict(collections.Counter(d["tipo_arco"] for _, _, d in G.edges(data=True))),
       "km_per_tipo": {t: km(lambda d, t=t: d["tipo_arco"] == t) for t in sorted({d["tipo_arco"] for _, _, d in G.edges(data=True)})},
       "km_per_marciapiede": {t: km(lambda d, t=t: d["marciapiede_stato"] == t) for t in ("presente", "separato", "assente", "ignoto", "non_applicabile")},
       "km_non_certificati": km(lambda d: not d["marciapiede_dichiarato"]),
       "archi_scala": sum(1 for _, _, d in G.edges(data=True) if d["scala"]), "archi_sottopasso": sum(1 for _, _, d in G.edges(data=True) if d["tipo_arco"] == "sottopasso" or d["tunnel"]), "archi_ponte": sum(1 for _, _, d in G.edges(data=True) if d["bridge"]),
       "nodi_crossing": sum(1 for _, d in G.nodes(data=True) if d.get("crossing") is not None or "crossing_markings" in d), "nodi_barriera_passabile": sum(1 for _, d in G.nodes(data=True) if d.get("barriera_stato") == "passabile"),
       "nodi_bloccanti": len(bloccati), "nodi_bordo_buffer": sum(1 for _, d in G.nodes(data=True) if d["bordo_buffer"]),
       "vicoli_ciechi_veri_in_z2": sum(1 for n, d in G.nodes(data=True) if G.degree(n) == 1 and not d["bordo_buffer"] and d["in_z2"]),
       "vicoli_ciechi_bordo": sum(1 for n, d in G.nodes(data=True) if G.degree(n) == 1 and d["bordo_buffer"]),
       "esclusi_per_motivo": dict(collections.Counter(r["motivo"] for r in excl_rows).most_common()),
       "km_esclusi_per_motivo": {m: round(sum(r["length_m"] for r in excl_rows if r["motivo"] == m) / 1000, 3) for m in sorted({r["motivo"] for r in excl_rows})},
       "way_area_poligono_escluse": sum(1 for w in D["ways"] if w["tags"].get("area") == "yes" and "highway" in w["tags"] and "railway" not in w["tags"]),
       "nodi_layer_sospetti": sospetti, "componenti": len(comps), "formati": ["rete_z2.gpkg (nodi, archi, archi_esclusi, nodi_bloccati): riferimento", "rete_z2.pkl (MultiGraph con geometrie): riferimento per gli script", "rete_z2.graphml: solo scambio, archi paralleli fusi in uno"]}
json.dump(man, open(NET / "rete_manifest.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in man.items() if k not in ("nodi_layer_sospetti",)}, ensure_ascii=False, indent=1)[:3500])
print([(r["componente"], r["km"], r["km_in_z2"], r.get("motivi")) for r in rows[:12]])
