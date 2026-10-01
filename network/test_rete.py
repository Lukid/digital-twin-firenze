#!/usr/bin/env python3
"""Test della rete T04 (assert). Esegue su data/norm/network dopo build.sh: python network/test_rete.py"""
import json, sys, pickle, collections
import geopandas as gpd, networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
sys.path.insert(0, __import__("os").path.dirname(__file__))
from rete_lib import *

G, D = carica(); P = permissivo(G, D["esclusi"])
bld = gpd.read_file(ROOT / "data/norm/osm_pisa.gpkg", layer="buildings")
SN = Snapper(G, D["esclusi"], D["bloccati"], bld)
dest = json.load(open(NET / "destinazioni.json"))["destinazioni"]
ent = {e["entrance_id"]: e for d in dest for e in d["ingressi"]}
snap = lambda e: {**e["aggancio"], "proj": tuple(e["aggancio"]["proj"])}
civ = gpd.read_file(OUT / "origini_snap.gpkg", layer="origini").set_index("id")
MAXO = REGOLE["snapping"]["origini"]["max_m"]

# 1. percorso consentito: fermata Pellico -> ingresso probabile Battisti
batt = next(d for d in dest if d["destination_id"] == "dst_school_piee82101p")
pell = next(d for d in dest if d["destination_id"] == "dst_stop_pi4390")
sa, sb = snap(pell["ingressi"][0]), snap(ent[batt["ingresso_predefinito"]])
out = percorso(G, sa, sb)
assert out, "percorso Pellico -> Battisti non trovato"
H, nodi, archi = out
diretta = Point(pell["ingressi"][0]["xy"]).distance(Point(ent[batt["ingresso_predefinito"]]["xy"]))
tot = sum(e["length_m"] for e in archi)
assert diretta <= tot <= 2 * diretta, (diretta, tot)
assert all(e["tipo_arco"] != "escluso" and not e.get("restrizione") for e in archi)
print(f"1 ok: Pellico -> Battisti {tot:.0f} m (diretta {diretta:.0f} m)")

# 2. percorso vietato rifiutato: via Poerio 3 si collega solo con un tratto access=private
o = civ.loc["adr_sit_11884"].geometry; so = SN.snap(o, MAXO, 6, REGOLE["snapping"]["origini"]["tipi_arco_esclusi"])
assert so["stato"] == "agganciato"
assert percorso(G, so, sb) is None, "il grafo ha trovato un percorso attraverso un tratto vietato"
perm = percorso(P, so, sb)
assert perm, "il grafo permissivo di controllo dovrebbe collegare i due punti (altrimenti il caso non prova nulla)"
rest = [e["restrizione"] for e in perm[2] if e.get("restrizione")]
assert rest and all(r.startswith("access=") for r in rest), rest
usati = {e["edge_id"] for e in perm[2] if e.get("restrizione")}
assert not usati & {k for _, _, k in G.edges(keys=True)}, "un arco vietato è nel grafo"
for b in D["bloccati"]: assert b["node_id"] not in G, f"nodo bloccante nel grafo: {b['node_id']}"
print(f"2 ok: via Poerio 3 -> Battisti rifiutato ({len(usati)} archi {sorted(set(rest))}; permissivo {sum(e['length_m'] for e in perm[2]):.0f} m)")

# 3. nessun arco su banchine e binari
rail = {w["id"] for w in D["binari"]} | {w["id"] for w in D["banchine"] if "railway" in w["tags"]}
for u, v, k, d in G.edges(keys=True, data=True):
    assert int(d["way_id"].split("_")[-1]) not in rail, f"arco su way ferroviaria: {k}"
    assert d["highway"] not in ("proposed", "construction", "motorway", "motorway_link"), k
LIN = [LineString([(x, y) for _, x, y in w["nodes"]]).buffer(1.5) for w in D["binari"] if w["tags"]["railway"] in ("rail", "light_rail", "tram", "subway", "funicular", "platform", "platform_edge") and len(w["nodes"]) > 1]
# sovrapposizione per singolo binario: un attraversamento in diagonale supera di poco 3 m, un arco che corre sul binario molto di più
sovrapposti = [(k, round(m, 1)) for u, v, k, d in G.edges(keys=True, data=True) if (m := max((d["geom"].intersection(l).length for l in LIN), default=0)) > 5]
assert not sovrapposti, f"archi sovrapposti ai binari per più di 5 m: {sovrapposti[:5]}"
sotto = [d for _, _, d in G.edges(data=True) if d["tipo_arco"] == "sottopasso" or d["tunnel"]]
print(f"3 ok: nessun arco su binari/banchine; {len(sotto)} archi in sottopasso/tunnel conservati")

# 4. regole di esclusione e di conservazione
for u, v, k, d in G.edges(keys=True, data=True):
    assert d["foot"] not in ("no", "use_sidepath", "customers"), k
    assert not (d["access"] in REGOLE["access"]["esclusi"] and d["foot"] not in REGOLE["foot"]["ammessi_sempre"]), k
assert len({k for _, _, k in G.edges(keys=True)}) == G.number_of_edges()
assert all(n.startswith("nod_osm_") for n in G) and all(k.startswith("edg_osm_") for _, _, k in G.edges(keys=True))
assert sum(1 for _, _, d in G.edges(data=True) if d["marciapiede_stato"] == "ignoto") > 0 and not any(d["marciapiede_dichiarato"] for _, _, d in G.edges(data=True) if d["marciapiede_stato"] in ("ignoto", "assente"))
assert any(d["tipo_arco"] == "attraversamento" for _, _, d in G.edges(data=True)) and any(d["scala"] for _, _, d in G.edges(data=True))
print("4 ok: foot/access rispettati, ID stabili e univoci, marciapiede ignoto mai dichiarato, attraversamenti e scale presenti")

# 5. ogni destinazione agganciata a un ingresso
for d in dest:
    assert d["ingressi"] and d["ingresso_predefinito"], d["destination_id"]
    e = ent[d["ingresso_predefinito"]]; a = e["aggancio"]
    assert a["stato"] == "agganciato" and a["dist_m"] <= REGOLE["snapping"]["ingressi"]["max_m"], (d["destination_id"], a)
    assert (a["u"], a["v"], a["edge_id"]) in G.edges(keys=True) or G.has_edge(a["u"], a["v"], a["edge_id"]), d["destination_id"]
    assert e["stato_verifica"] == "da_verificare"
    if d["categoria"] == "school": assert e["tags"].get("entrance") and e["classe"] == "probabile_ingresso_scuola"
classi = collections.Counter(e["classe"] for e in batt["ingressi"])
assert classi["probabile_ingresso_scuola"] >= 1 and classi["probabile_edificio_contiguo"] >= 1
print(f"5 ok: {len(dest)} destinazioni agganciate a un ingresso; Battisti {dict(classi)}")

# 6. origini: non agganciati = insufficient_data, mai forzati
na = civ[civ.stato == "insufficient_data"]
assert na.edge_id.isna().all() and na.raccordo_m.isna().all()
assert (civ[civ.stato != "insufficient_data"].raccordo_m.astype(float) <= MAXO).all()
print(f"6 ok: origini {len(civ)}, agganciate {len(civ) - len(na)}, insufficient_data {len(na)}")

# 7. archi memorizzati in verso opposto alla geometria: l'offset dello snap è sulla geometria (regressione)
W = lambda x, y, dd: min(e["length_m"] for e in dd.values())
inv = [(u, v, k, d) for u, v, k, d in G.edges(keys=True, data=True) if d["nod_da"] != u and d["length_m"] > 30]
assert inv, "nessun arco invertito per il test"
u, v, k, d = inv[0]; off = round(d["length_m"] * 0.1, 2); pt = d["geom"].interpolate(off)
s_a = {"u": u, "v": v, "edge_id": k, "offset_m": off, "proj": (pt.x, pt.y), "dist_m": 0.0}
H7 = con_agganci(G, {"A": s_a})
da, a_ = d["nod_da"], d["nod_a"]
for X in list(G.nodes)[::400]:
    atteso = min(off + nx.shortest_path_length(G, da, X, weight=W), d["length_m"] - off + nx.shortest_path_length(G, a_, X, weight=W))   # calcolo indipendente
    got = nx.shortest_path_length(H7, "snp_A", X, weight=W)
    assert abs(got - atteso) < 0.1, (X, got, atteso)
    assert got >= pt.distance(Point(G.nodes[X]["x"], G.nodes[X]["y"])) - 0.01, "distanza di rete minore della linea d'aria"
print(f"7 ok: arco invertito {k}, distanze di rete = calcolo indipendente e >= linea d'aria")
print("TUTTI I TEST OK")
