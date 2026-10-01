#!/usr/bin/env python3
"""Passo 5: 10 percorsi campione (9 consentiti, 1 vietato) su grafo non verificato.
Output: network/percorsi_campione.json (ID, metriche, esito), network/percorsi_campione.geojson (EPSG:4326 per l'anteprima)."""
import json, sys
import geopandas as gpd, networkx as nx, numpy as np
import shapely.ops
from pyproj import Transformer
from shapely.geometry import Point, mapping
from rete_lib import *
sys.path.insert(0, str(ROOT / "pipeline"))
from lib import AOI
G, D = carica(); P = permissivo(G, D["esclusi"])
bld = gpd.read_file(ROOT / "data/norm/osm_pisa.gpkg", layer="buildings")
SN = Snapper(G, D["esclusi"], D["bloccati"], bld); MAXO = REGOLE["snapping"]["origini"]["max_m"]; NC = REGOLE["snapping"]["origini"]["candidati"]
dest = {d["destination_id"]: d for d in json.load(open(NET / "destinazioni.json"))["destinazioni"]}
ent = {e["entrance_id"]: e for d in dest.values() for e in d["ingressi"]}
civ = gpd.read_file(OUT / "origini_snap.gpkg", layer="origini").set_index("id")
to_ll = Transformer.from_crs(7791, 4326, always_xy=True)
def ll(g): return mapping(shapely.ops.transform(lambda x, y, z=None: to_ll.transform(x, y), g))
def snap_of(e): a = dict(e["aggancio"]); a["proj"] = tuple(a["proj"]); return a

batt = dest["dst_school_piee82101p"]; E_MAIN = batt["ingresso_predefinito"]
E_CONT = next(e["entrance_id"] for e in sorted(batt["ingressi"], key=lambda e: e["dist_perimetro_m"]) if e["classe"] == "probabile_edificio_contiguo" and e["tags"].get("addr:street", "").endswith("Corridoni"))
pb = Point(ent[E_MAIN]["xy"])
ok = civ[(civ.stato == "reachable_candidate") & (civ.componente == "cmp_01")].copy(); ok["d"] = ok.geometry.distance(pb)
def civico_a(target): r = ok.iloc[(ok.d - target).abs().argsort()[:1]]; return r.index[0]
CIV = {t: civico_a(t) for t in (150, 400, 700, 1000)}
ST = {d["stop_code"]: {**d["ingressi"][0], "nome": d["nome"], "did": d["destination_id"]} for d in dest.values() if d["categoria"] == "stop"}
punti = {"stop": lambda code: (Point(ST[code]["xy"]), snap_of(ST[code]), f"{ST[code]['did']} ({ST[code]['nome']})"),
         "ent": lambda eid: (Point(ent[eid]["xy"]), snap_of(ent[eid]), f"{eid} ({ent[eid].get('classe','')})"),
         "civ": lambda cid: (civ.loc[cid].geometry, SN.snap(civ.loc[cid].geometry, MAXO, NC, REGOLE["snapping"]["origini"]["tipi_arco_esclusi"]), f"{cid} ({civ.loc[cid].indirizzo})")}
casi = [("R01", "stop", "PI4390", "ent", E_MAIN, "Fermata Pellico verso l'ingresso probabile della scuola"),
        ("R02", "stop", "PI4390", "ent", E_CONT, "Fermata Pellico verso un ingresso 'edificio contiguo' (sensibilità alla scelta dell'ingresso)"),
        ("R03", "stop", "PI4074", "ent", E_MAIN, "Fermata Corridoni 1 (la più vicina) verso l'ingresso"),
        ("R04", "civ", CIV[150], "ent", E_MAIN, "Civico a circa 150 m in linea d'aria"),
        ("R05", "civ", CIV[400], "ent", E_MAIN, "Civico a circa 400 m"),
        ("R06", "civ", CIV[700], "ent", E_MAIN, "Civico a circa 700 m"),
        ("R07", "civ", CIV[1000], "ent", E_MAIN, "Civico a circa 1000 m"),
        ("R08", "stop", "PI0001", "ent", E_MAIN, "Stazione (fermata bus PI0001) verso l'ingresso"),
        ("R09", "civ", CIV[400], "stop", "PI4390", "Civico R05 verso la fermata Pellico (verso opposto)"),
        ("V01", "civ", "adr_sit_11884", "ent", E_MAIN, "VIETATO: via Poerio 3, collegata al resto della rete solo da un tratto access=private")]
res, feats = [], []
for cid, ta, a, tb, b, desc in casi:
    pa, sa, na = punti[ta](a); pbb, sb, nb = punti[tb](b)
    r = {"id": cid, "descrizione": desc, "origine": na, "destinazione": nb, "snap_origine": {k: sa.get(k) for k in ("edge_id", "dist_m", "stato")}, "snap_destinazione": {k: sb.get(k) for k in ("edge_id", "dist_m", "stato")},
         "diretta_m": round(pa.distance(pbb), 1), "stato_verifica": "da_verificare", "grafo": json.load(open(NET / "rete_manifest.json"))["graph_id"]}
    if sa["stato"] != "agganciato" or sb["stato"] != "agganciato": r["stato"] = "insufficient_data"
    else:
        out = percorso(G, sa, sb)
        if out:
            H, nodi, archi = out; r.update(stato="reachable", **riassunto(H, nodi, archi, sa["dist_m"] + sb["dist_m"]))
            r["deviazione"] = round(r["lunghezza_totale_m"] / max(r["diretta_m"], 1), 2)
            g = geom_percorso(H, nodi, archi, pa, sa, pbb, sb); r["_geom"] = g
        else:
            outp = percorso(P, sa, sb)
            if outp:
                H, nodi, archi = outp; rr = riassunto(H, nodi, archi, sa["dist_m"] + sb["dist_m"])
                r.update(stato="forbidden", motivo="nessun percorso sul grafo verificato; collegato solo attraverso tratti con restrizione documentata", restrizioni=rr["restrizioni_attraversate"],
                         permissivo_lunghezza_m=rr["lunghezza_totale_m"], archi_permissivi=rr["archi"], origine_componente=civ.loc[a].componente if ta == "civ" else None)
                r["_geom"] = geom_percorso(H, nodi, archi, pa, sa, pbb, sb)
            else: r.update(stato="isolated", motivo="nessun percorso nemmeno ignorando le restrizioni")
    res.append(r)
    if "_geom" in r:
        g = r.pop("_geom"); pr = {k: v for k, v in r.items() if k in ("id", "descrizione", "origine", "destinazione", "stato", "lunghezza_totale_m", "diretta_m", "deviazione", "attraversamenti", "tratti_marciapiede_ignoto", "m_marciapiede_ignoto", "scale", "sottopassi", "stato_verifica", "restrizioni")}
        pr["permissivo_lunghezza_m"] = r.get("permissivo_lunghezza_m"); pr["marciapiede_dichiarato"] = False
        feats.append({"type": "Feature", "geometry": ll(g), "properties": {k: v for k, v in pr.items() if v is not None}})
# i punti dei tratti vietati, per l'anteprima
for r in res:
    if r["stato"] == "forbidden":
        for e in r["archi_permissivi"]:
            ex = next((x for x in D["esclusi"] if x["edge_id"] == e), None)
            if ex: feats.append({"type": "Feature", "geometry": ll(ex["geometry"]), "properties": {"id": r["id"], "tipo": "tratto_vietato", "motivo": ex["motivo"], "edge_id": ex["edge_id"]}})
json.dump({"type": "FeatureCollection", "name": "percorsi_campione", "nota": "EPSG:4326 solo per la visualizzazione; calcolo in EPSG:7791. Percorsi su grafo OSM non verificato, nessuna certificazione di accessibilità.", "features": feats}, open(NET / "percorsi_campione.geojson", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(res, open(NET / "percorsi_campione.json", "w"), ensure_ascii=False, indent=1, default=str)
for r in res: print({k: v for k, v in r.items() if k not in ("archi", "archi_permissivi", "snap_origine", "snap_destinazione", "grafo", "attraversamenti_tipi")})
