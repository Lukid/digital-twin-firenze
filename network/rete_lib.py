"""Funzioni comuni T04: caricamento grafo, snapping documentato, percorso minimo da punti agganciati."""
import json, os, pathlib, pickle
import geopandas as gpd, networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import substring
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parents[1]
NET = ROOT / "network"   # codice e regole (uguali per ogni area)
REGOLE = json.load(open(NET / "regole.json"))

# Nomi per area (variabile DT_AOI come in pipeline/lib.py, default Pisa: percorsi e nomi storici invariati).
# osm = fonte OSM (cartella raw, snapshot, GeoPackage); gid = parte dell'id del grafo; stem = nome dei file della rete;
# out = dati pesanti (non versionati); res = manifest, report e file piccoli (versionati).
AOI_ID = os.environ.get("DT_AOI", "aoi_z2")
AREE = {"aoi_z2": dict(osm="osm_pisa", gid="z2", stem="rete_z2", out="data/norm/network", res="network", osm_gpkg="data/norm/osm_pisa.gpkg"),
        "aoi_firenze_novoli": dict(osm="osm_firenze", gid="firenze_novoli", stem="rete_firenze_novoli", out="data/norm/firenze_novoli/network", res="network/firenze_novoli",
                                   osm_gpkg="data/norm/firenze_novoli/osm_firenze.gpkg")}
AREA = AREE[AOI_ID]
OUT = ROOT / AREA["out"]; RES = ROOT / AREA["res"]; STEM = AREA["stem"]; OSM_GPKG = ROOT / AREA["osm_gpkg"]
OSM_SNAP = json.load(open(sorted((ROOT / "pipeline/snapshots").glob(f"snp_{AREA['osm']}_*.json"))[-1]))

def carica():
    d = pickle.load(open(OUT / f"{STEM}.pkl", "rb"))
    return d["G"], d

class Snapper:
    """Aggancio di un punto all'arco percorribile più vicino con raccordo valido (vedi regole.json, snapping)."""
    def __init__(self, G, esclusi, bloccati, edifici):
        self.G = G
        self.keys = [(u, v, k) for u, v, k in G.edges(keys=True)]
        self.geoms = [G.edges[e]["geom"] for e in self.keys]
        self.tree = STRtree(self.geoms)
        self.ex = [r["geometry"] for r in esclusi]; self.ex_tree = STRtree(self.ex)
        self.bl = [b["geometry"] for b in bloccati]
        self.bld = list(edifici.geometry); self.bld_tree = STRtree(self.bld)

    def _raccordo_ok(self, p, proj, rac):
        for j in self.bld_tree.query(rac):
            b = self.bld[int(j)]
            if b.distance(p) <= 1.5: continue            # edificio dell'origine/ingresso
            if rac.intersection(b).length > 0.5: return False, "edificio"
        for j in self.ex_tree.query(rac):
            i = rac.intersection(self.ex[int(j)])
            if not i.is_empty and i.distance(p) > 1.0 and i.distance(proj) > 1.0: return False, "tratto_escluso"
        for b in self.bl:
            if rac.distance(b) < 1.0: return False, "nodo_bloccante"
        return True, None

    def snap(self, p, max_m, ncand=6, tipi_esclusi=()):
        idx = self.tree.query(p.buffer(max_m))
        cand = sorted(c for c in ((self.geoms[int(i)].distance(p), int(i)) for i in idx) if c[0] <= max_m and self.G.edges[self.keys[c[1]]]["tipo_arco"] not in tipi_esclusi)[:ncand]
        scartati = []
        for d, i in cand:
            g = self.geoms[i]; off = g.project(p); proj = g.interpolate(off)
            ok, why = (True, None) if d < 1e-6 else self._raccordo_ok(p, proj, LineString([p, proj]))
            if ok:
                u, v, k = self.keys[i]
                return {"stato": "agganciato", "edge_id": k, "u": u, "v": v, "offset_m": round(off, 2), "dist_m": round(d, 2), "proj": (proj.x, proj.y), "scartati": scartati}
            scartati.append({"edge_id": self.keys[i][2], "dist_m": round(d, 2), "motivo": why})
        return {"stato": "insufficient_data", "motivo": "nessun arco percorribile entro %s m" % max_m if not cand else "tutti i candidati scartati: " + ", ".join(sorted({s['motivo'] for s in scartati})), "scartati": scartati}

def punto_perimetro(poly, G):
    """Punto del perimetro di un poligono più vicino a un arco della rete (per le destinazioni senza ingresso mappato: va dichiarato come tale)."""
    from shapely.ops import nearest_points, unary_union
    return nearest_points(poly.exterior, unary_union([d["geom"] for _, _, d in G.edges(data=True) if d["geom"].distance(poly) < 100]))[0]

def distanza_vicino(snapper, p):
    """Distanza dal punto all'arco più vicino senza controlli (per le statistiche)."""
    i = snapper.tree.nearest(p)
    return snapper.geoms[int(i)].distance(p)

def con_agganci(G, agganci):
    """Copia del grafo con i punti agganciati come nodi 'snp_<nome>' che spezzano l'arco. agganci: {nome: snap}."""
    H = G.copy(); per_arco = {}
    for nome, s in agganci.items(): per_arco.setdefault((s["u"], s["v"], s["edge_id"]), []).append((s["offset_m"], nome))
    for (u0, v0, k), lst in sorted(per_arco.items(), key=lambda kv: kv[0][2]):
        # la geometria corre da nod_da a nod_a, ma in networkx (u, v) può essere l'inverso: l'offset dello snap è sulla geometria
        d = dict(H.edges[u0, v0, k]); u, v = d.get("nod_da", u0), d.get("nod_a", v0); g = d["geom"]; L = g.length; H.remove_edge(u0, v0, k)
        punti = [(0.0, u)] + sorted((o, "snp_" + n) for o, n in lst) + [(L, v)]
        for n, (o, nn) in enumerate(punti):
            if n == 0: continue
            o0, n0 = punti[n - 1]
            sg = substring(g, o0, o) if o - o0 > 1e-6 else LineString([g.interpolate(o0), g.interpolate(o)])
            if nn not in H: H.add_node(nn, x=sg.coords[-1][0], y=sg.coords[-1][1], bordo_buffer=False, in_z2=True, componente=H.nodes[u]["componente"])
            H.add_edge(n0, nn, key=f"{k}#{n}", **{**d, "geom": sg, "length_m": round(o - o0, 2), "parte_di": k})
    return H

def percorso(G, a, b, extra=None):
    """Cammino minimo per lunghezza fra due punti agganciati a e b (dict snap). None se non connessi."""
    H = con_agganci(G, {"A": a, "B": b})
    try: nodi = nx.shortest_path(H, "snp_A", "snp_B", weight=lambda u, v, dd: min(e["length_m"] for e in dd.values()))
    except nx.NetworkXNoPath: return None
    archi = []
    for u, v in zip(nodi, nodi[1:]):
        e = min(H[u][v].values(), key=lambda e: e["length_m"]); archi.append(e)
    return H, nodi, archi

def riassunto(H, nodi, archi, raccordi_m=0.0):
    tot = sum(e["length_m"] for e in archi)
    crossing = [e for e in archi if e["tipo_arco"] == "attraversamento"]
    ign = [e for e in archi if e["marciapiede_stato"] in ("ignoto", "assente")]
    barr = [H.nodes[n].get("barriera") for n in nodi if H.nodes[n].get("barriera")]
    return {"lunghezza_rete_m": round(tot, 1), "raccordi_m": round(raccordi_m, 1), "lunghezza_totale_m": round(tot + raccordi_m, 1),
            "attraversamenti": len(crossing), "attraversamenti_tipi": [e.get("crossing") or "non_specificato" for e in crossing],
            "tratti_marciapiede_ignoto": len({e.get("parte_di", e["edge_id"]) for e in ign if e["marciapiede_stato"] == "ignoto"}),
            "m_marciapiede_ignoto": round(sum(e["length_m"] for e in archi if e["marciapiede_stato"] == "ignoto"), 1),
            "m_marciapiede_assente": round(sum(e["length_m"] for e in archi if e["marciapiede_stato"] == "assente"), 1),
            "scale": sum(1 for e in archi if e["scala"]), "sottopassi": len({e.get("parte_di", e["edge_id"]) for e in archi if e["tipo_arco"] == "sottopasso" or e["tunnel"]}),
            "ponti": len({e.get("parte_di", e["edge_id"]) for e in archi if e["bridge"]}), "barriere_passate": barr,
            "restrizioni_attraversate": [e["restrizione"] for e in archi if e.get("restrizione")],
            "archi": [e.get("parte_di", e["edge_id"]) for e in archi], "marciapiede_dichiarato": all(e["marciapiede_dichiarato"] for e in archi)}

def permissivo(G, esclusi):
    """Grafo di controllo: G più i tratti esclusi per restrizione documentata (foot, access, tunnel stradale). Mai per i calcoli:
    serve a distinguere 'forbidden' (collegato solo attraverso una restrizione) da 'isolated'. Ferrovie, banchine e aree non entrano."""
    import re
    P = G.copy()
    for r in esclusi:
        m = re.match(r"edg_osm_(\d+)_(\d+)_(\d+)", r["edge_id"])
        if not m or r["motivo"] in ("ferrovia_railway", "banchina_ferroviaria", "area_poligono") or r["motivo"].startswith("highway="): continue
        a, b = f"nod_osm_{m[2]}", f"nod_osm_{m[3]}"; g = r["geometry"]
        for n, c in ((a, g.coords[0]), (b, g.coords[-1])):
            if n not in P: P.add_node(n, x=c[0], y=c[1], bordo_buffer=False, in_z2=True, componente=None)
        P.add_edge(a, b, key=r["edge_id"], geom=g, length_m=r["length_m"], tipo_arco="escluso", marciapiede_stato="n/a", marciapiede_dichiarato=False, scala=False,
                   bridge=r["bridge"], tunnel=r["tunnel"], restrizione=r["motivo"], edge_id=r["edge_id"])
    return P

def geom_percorso(H, nodi, archi, p_a, s_a, p_b, s_b):
    """LineString del percorso: raccordo origine, archi in ordine di marcia, raccordo destinazione."""
    coords = [(p_a.x, p_a.y), s_a["proj"]]
    for n, e in zip(nodi, archi):
        c = list(e["geom"].coords)
        if Point(c[0]).distance(Point(coords[-1])) > Point(c[-1]).distance(Point(coords[-1])): c.reverse()
        coords += c
    coords += [s_b["proj"], (p_b.x, p_b.y)]
    out = [coords[0]]
    for c in coords[1:]:
        if Point(c).distance(Point(out[-1])) > 1e-6: out.append(c)
    return LineString(out)
