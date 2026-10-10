#!/usr/bin/env python3
"""Test della rete F04 di Firenze Novoli (assert). Esegue su data/norm/firenze_novoli/network dopo build_firenze.sh: python network/test_rete_firenze.py"""
import collections, json, os, pickle, re, subprocess, sys
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare rete_lib
import geopandas as gpd, networkx as nx
from shapely.geometry import LineString, Point, Polygon
sys.path.insert(0, os.path.dirname(__file__))
from rete_lib import *

G, D = carica(); P = permissivo(G, D["esclusi"])
bld = gpd.read_file(OSM_GPKG, layer="buildings")
SN = Snapper(G, D["esclusi"], D["bloccati"], bld)
dest = json.load(open(RES / "destinazioni.json"))["destinazioni"]
ent = {e["entrance_id"]: e for d in dest for e in d["ingressi"]}
snap = lambda e: {**e["aggancio"], "proj": tuple(e["aggancio"]["proj"])}
civ = gpd.read_file(OUT / "origini_snap.gpkg", layer="origini").set_index("id")
SO = REGOLE["snapping"]["origini"]; MAXO = SO["max_m"]
man = json.load(open(RES / "rete_manifest.json"))
D_ = {d["destination_id"]: d for d in dest}
polo, vamba = D_["dst_university_w83537185"], D_["dst_school_fiee86002g"]

# 1. percorso consentito: fermata T2 Regione Toscana -> ingresso del Polo
sa, sb = snap(ent["ent_gtfs_fm9056"]), snap(ent[polo["ingresso_predefinito"]])
out = percorso(G, sa, sb); assert out, "percorso fermata -> Polo non trovato"
H, nodi, archi = out
diretta = Point(ent["ent_gtfs_fm9056"]["xy"]).distance(Point(ent[polo["ingresso_predefinito"]]["xy"])); tot = sum(e["length_m"] for e in archi)
assert diretta <= tot <= 2 * diretta, (diretta, tot)
assert all(e["tipo_arco"] != "escluso" and not e.get("restrizione") for e in archi)
print(f"1 ok: Regione Toscana -> Polo {tot:.0f} m (diretta {diretta:.0f} m)")

# 2. percorsi vietati rifiutati: via della Verna 3 (access=private) e via del Ponte di Mezzo 27/18 (tunnel stradale senza marciapiede)
for cid, motivo in (("adr_fi_31825", "access=private"), ("adr_fi_90008", "tunnel_stradale_senza_marciapiede")):
    so = SN.snap(civ.loc[cid].geometry, MAXO, 6, SO["tipi_arco_esclusi"]); assert so["stato"] == "agganciato"
    assert percorso(G, so, sb) is None, f"il grafo ha trovato un percorso vietato da {cid}"
    perm = percorso(P, so, sb); assert perm, "il grafo di controllo dovrebbe collegare i due punti (altrimenti il caso non prova nulla)"
    rest = [e["restrizione"] for e in perm[2] if e.get("restrizione")]
    assert motivo in rest, (cid, rest)
    assert not {e["edge_id"] for e in perm[2] if e.get("restrizione")} & {k for _, _, k in G.edges(keys=True)}, "un arco vietato è nel grafo"
    print(f"2 ok: {cid} -> Polo rifiutato (restrizioni {sorted(set(rest))}; permissivo {sum(e['length_m'] for e in perm[2]):.0f} m)")
for b in D["bloccati"]: assert b["node_id"] not in G, f"nodo bloccante nel grafo: {b['node_id']}"

# 3. nessun arco su banchine e binari
rail = {w["id"] for w in D["binari"]} | {w["id"] for w in D["banchine"] if "railway" in w["tags"]}
for u, v, k, d in G.edges(keys=True, data=True):
    assert int(d["way_id"].split("_")[-1]) not in rail, f"arco su way ferroviaria: {k}"
    assert d["highway"] not in ("proposed", "construction", "motorway", "motorway_link"), k
LIN = [LineString([(x, y) for _, x, y in w["nodes"]]).buffer(1.5) for w in D["binari"] if w["tags"]["railway"] in ("rail", "light_rail", "tram", "subway", "funicular", "platform", "platform_edge") and len(w["nodes"]) > 1]
# a Firenze il tram corre anche in strada e le strade lo attraversano in diagonale: fino a 6,3 m per singolo binario (Pisa 5 m); un arco che corre sul binario supera 7 m
ovl = {k: max((d["geom"].intersection(l).length for l in LIN), default=0) for u, v, k, d in G.edges(keys=True, data=True)}
sovrapposti = [(k, round(m, 1)) for k, m in ovl.items() if m > 7]
assert not sovrapposti, f"archi sovrapposti ai binari per più di 7 m: {sovrapposti[:5]}"
print(f"3 ok: nessun arco su binari/banchine (sovrapposizione massima {max(ovl.values()):.1f} m); {sum(1 for _, _, d in G.edges(data=True) if d['tipo_arco'] == 'sottopasso' or d['tunnel'])} archi in sottopasso/tunnel conservati")

# 4. regole di esclusione e di conservazione
for u, v, k, d in G.edges(keys=True, data=True):
    assert d["foot"] not in ("no", "use_sidepath", "customers"), k
    assert not (d["access"] in REGOLE["access"]["esclusi"] and d["foot"] not in REGOLE["foot"]["ammessi_sempre"]), k
assert len({k for _, _, k in G.edges(keys=True)}) == G.number_of_edges()
assert all(n.startswith("nod_osm_") for n in G) and all(k.startswith("edg_osm_") for _, _, k in G.edges(keys=True))
assert sum(1 for _, _, d in G.edges(data=True) if d["marciapiede_stato"] == "ignoto") > 0 and not any(d["marciapiede_dichiarato"] for _, _, d in G.edges(data=True) if d["marciapiede_stato"] in ("ignoto", "assente"))
assert any(d["tipo_arco"] == "attraversamento" for _, _, d in G.edges(data=True)) and any(d["scala"] for _, _, d in G.edges(data=True))
assert not any(k.startswith(("grado", "scheda", "barriere")) for _, _, d in G.edges(data=True) for k in d), "le barriere del Comune sono schede di edifici, non attributi dell'arco"
print("4 ok: foot/access rispettati, ID stabili e univoci, marciapiede ignoto mai dichiarato, attraversamenti e scale presenti, nessuna scheda sugli archi")

# 5. destinazioni: ogni destinazione agganciata a un ingresso con classe dichiarata e verifica da_verificare; barriere come attributo della destinazione
CLASSI = {"ingresso_osm", "accesso_citta_metropolitana", "ingresso_fermata", "punto_sul_perimetro"}
for d in dest:
    assert re.fullmatch(r"dst_[a-z]{2,12}_[a-z0-9_]{2,60}", d["destination_id"]) and d["ingressi"] and d["ingresso_predefinito"] in ent, d["destination_id"]
    for e in d["ingressi"]:
        assert re.fullmatch(r"ent_[a-z]{2,8}_[A-Za-z0-9_.-]{1,60}", e["entrance_id"]) and e["classe"] in CLASSI and e["stato_verifica"] == "da_verificare", e["entrance_id"]
        a = e["aggancio"]; assert a["stato"] == "agganciato" and a["dist_m"] <= REGOLE["snapping"]["ingressi"]["max_m"], (e["entrance_id"], a)
        assert G.has_edge(a["u"], a["v"], a["edge_id"]), e["entrance_id"]
assert [e["classe"] for e in polo["ingressi"]] == ["ingresso_osm"] * len(polo["ingressi"]) and len(polo["ingressi"]) >= 2
assert vamba["ingressi"][0]["classe"] == "accesso_citta_metropolitana" and vamba["codice_mim"] == "FIEE86002G" and D_["dst_school_fiaa86002a"]["codice_mim"] == "FIAA86002A"
assert sum(1 for d in dest if d["categoria"] == "tram") == 2 and all(d["ingressi"][0]["classe"] == "ingresso_fermata" for d in dest if d["categoria"] == "tram")
for d in (polo, vamba):
    s = d["barriere_comune"]["schede"]; assert s and all(x["grado_accessibilita"] in ("Accessibile", "Parzialmente Accessibile", "Non Accessibile") for x in s), d["destination_id"]
bar = json.load(open(RES / "barriere_edifici.json")); assert bar["schede_nel_riquadro"] == len(bar["schede"]) == sum(bar["per_grado"].values())
# ingresso senza fonte: punto sul perimetro, dichiarato come tale
poly = Polygon([(x, y) for _, x, y in next(a for a in pickle.load(open(OUT / "osm_estratto.pkl", "rb"))["aree"] if a["id"] == 83537185)["nodes"]])
pp = punto_perimetro(poly, G); assert poly.exterior.distance(pp) < 1e-6 and SN.snap(pp, 40, 6)["stato"] == "agganciato"
print(f"5 ok: {len(dest)} destinazioni agganciate; Polo {len(polo['ingressi'])} ingressi OSM, Vamba accesso CM, 2 fermate T2; schede Polo {len(polo['barriere_comune']['schede'])}, Vamba {len(vamba['barriere_comune']['schede'])}; punto sul perimetro ok")

# 6. origini: non agganciati = insufficient_data, mai forzati; stati che sommano
na = civ[civ.stato == "insufficient_data"]
assert na.edge_id.isna().all() and na.raccordo_m.isna().all()
assert (civ[civ.stato != "insufficient_data"].raccordo_m.astype(float) <= MAXO).all()
rep = json.load(open(RES / "snapping_report.json")); assert sum(rep["stato_rispetto_al_polo"].values()) == len(civ) == rep["origini_totali_riquadro"]
assert rep["stato_rispetto_al_polo"]["forbidden"] > 0 and rep["stato_rispetto_al_polo"]["insufficient_data"] == len(na)
print(f"6 ok: origini {len(civ)}, agganciate {len(civ) - len(na)}, insufficient_data {len(na)}, stati {rep['stato_rispetto_al_polo']}")

# 7. archi memorizzati in verso opposto alla geometria: l'offset dello snap è sulla geometria (regressione)
W = lambda x, y, dd: min(e["length_m"] for e in dd.values())
inv = [(u, v, k, d) for u, v, k, d in G.edges(keys=True, data=True) if d["nod_da"] != u and d["length_m"] > 30]
assert inv, "nessun arco invertito per il test"
u, v, k, d = inv[0]; off = round(d["length_m"] * 0.1, 2); pt = d["geom"].interpolate(off)
H7 = con_agganci(G, {"A": {"u": u, "v": v, "edge_id": k, "offset_m": off, "proj": (pt.x, pt.y), "dist_m": 0.0}})
da, a_ = d["nod_da"], d["nod_a"]
for X in list(G.nodes)[::800]:
    if not nx.has_path(G, da, X): continue
    atteso = min(off + nx.shortest_path_length(G, da, X, weight=W), d["length_m"] - off + nx.shortest_path_length(G, a_, X, weight=W))
    got = nx.shortest_path_length(H7, "snp_A", X, weight=W)
    assert abs(got - atteso) < 0.1, (X, got, atteso)
    assert got >= pt.distance(Point(G.nodes[X]["x"], G.nodes[X]["y"])) - 0.01, "distanza di rete minore della linea d'aria"
print(f"7 ok: arco invertito {k}, distanze di rete = calcolo indipendente e >= linea d'aria")

# 8. manifest: id, area, snapshot e sha256 coerenti con snapshot e baseline congelata
snp = json.load(open(ROOT / "pipeline/snapshots" / f"{man['snapshot_id']}.json")); bas = json.load(open(ROOT / "pipeline/baselines/bas_firenze_novoli_20261009.json"))
assert re.fullmatch(r"grf_firenze_novoli_osm_\d{8}", man["graph_id"]) and man["aoi_id"] == "aoi_firenze_novoli" and man["crs"] == "EPSG:7791"
assert man["sha256_osm"] == snp["sha256"] == next(s["sha256"] for s in bas["snapshot"] if s["snapshot_id"] == man["snapshot_id"])
assert man["nodi"] == G.number_of_nodes() and man["archi"] == G.number_of_edges()
assert man["regole_sha256"] == __import__("hashlib").sha256((NET / "regole.json").read_bytes()).hexdigest()
print(f"8 ok: {man['graph_id']} coerente con snapshot e baseline")

# 9. Senza DT_AOI rete_lib punta a Firenze (D15); Pisa resta raggiungibile con DT_AOI=aoi_z2
r = subprocess.run([sys.executable, "-c", "import os; os.environ.pop('DT_AOI', None); import rete_lib as R; print(R.STEM, R.OUT.relative_to(R.ROOT), R.RES.relative_to(R.ROOT), R.OSM_SNAP['snapshot_id'])"],
                   cwd=os.path.dirname(__file__) or ".", capture_output=True, text=True, check=True)
assert r.stdout.split() == ["rete_firenze_novoli", "data/norm/firenze_novoli/network", "network/firenze_novoli", "snp_osm_firenze_20261009"], r.stdout
print("9 ok: area predefinita Firenze")
print("TUTTI I TEST OK")
