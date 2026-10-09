#!/usr/bin/env python3
"""F04 passo 5 (Firenze): percorsi campione (consentiti e vietati) sul grafo non verificato, dai civici e dalle fermate T2 al Polo e a Vamba.
Uso: python network/percorsi_firenze.py. Output: network/firenze_novoli/percorsi_campione.{json,geojson}.
Script a parte rispetto a percorsi.py: i casi sono scritti nel codice, come a Pisa; qui cambiano ID, destinazioni e civici."""
import json, os, sys
import geopandas as gpd, shapely.ops
from pyproj import Transformer
from shapely.geometry import Point, mapping
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare lib e rete_lib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "pipeline"))
from rete_lib import *
G, D = carica(); P = permissivo(G, D["esclusi"])
SN = Snapper(G, D["esclusi"], D["bloccati"], gpd.read_file(OSM_GPKG, layer="buildings")); SO = REGOLE["snapping"]["origini"]
dest = {d["destination_id"]: d for d in json.load(open(RES / "destinazioni.json"))["destinazioni"]}
ent = {e["entrance_id"]: e for d in dest.values() for e in d["ingressi"]}
civ = gpd.read_file(OUT / "origini_snap.gpkg", layer="origini").set_index("id")
to_ll = Transformer.from_crs(7791, 4326, always_xy=True)
def ll(g): return mapping(shapely.ops.transform(lambda x, y, z=None: to_ll.transform(x, y), g))
EDG = {k: d for _, _, k, d in G.edges(keys=True, data=True)}
def n_way_attraversamento(archi): return len({EDG[a]["way_id"] for a in archi if a in EDG and EDG[a]["tipo_arco"] == "attraversamento"})   # un attraversamento OSM è spesso spezzato in più tratti
def snap_of(e): a = dict(e["aggancio"]); a["proj"] = tuple(a["proj"]); return a
POLO = dest["dst_university_w83537185"]; E_POLO, E_POLO2 = [e["entrance_id"] for e in POLO["ingressi"][:2]]
E_VAMBA = dest["dst_school_fiee86002g"]["ingresso_predefinito"]; T_AGLI, T_REG = "ent_gtfs_fm9057", "ent_gtfs_fm9056"
pb = Point(ent[E_POLO]["xy"])
ok = civ[(civ.stato == "reachable_candidate") & (civ.componente == "cmp_01") & (civ.TIPO == "N")].copy(); ok["d"] = ok.geometry.distance(pb)   # solo civici neri (abitazioni)
CIV = {t: ok.iloc[(ok.d - t).abs().argsort()[:1]].index[0] for t in (150, 400, 700, 1000)}
punti = {"ent": lambda eid: (Point(ent[eid]["xy"]), snap_of(ent[eid]), f"{eid} ({ent[eid]['classe']})"),
         "civ": lambda cid: (civ.loc[cid].geometry, SN.snap(civ.loc[cid].geometry, SO["max_m"], SO["candidati"], SO["tipi_arco_esclusi"]), f"{cid} ({civ.loc[cid].indirizzo})")}
casi = [("R01", "ent", T_AGLI, "ent", E_POLO, "Fermata T2 Novoli - Torre degli Agli verso l'ingresso del Polo (con indirizzo)"),
        ("R02", "ent", T_REG, "ent", E_POLO, "Fermata T2 Novoli - Regione Toscana verso l'ingresso del Polo"),
        ("R03", "ent", T_REG, "ent", E_POLO2, "Fermata Regione Toscana verso l'altro ingresso del Polo (sensibilità alla scelta dell'ingresso)"),
        ("R04", "civ", CIV[150], "ent", E_POLO, "Civico a circa 150 m in linea d'aria dal Polo"),
        ("R05", "civ", CIV[400], "ent", E_POLO, "Civico a circa 400 m"),
        ("R06", "civ", CIV[700], "ent", E_POLO, "Civico a circa 700 m"),
        ("R07", "civ", CIV[1000], "ent", E_POLO, "Civico a circa 1000 m"),
        ("R08", "civ", CIV[400], "ent", E_VAMBA, "Civico di R05 verso l'accesso della scuola Vamba"),
        ("R09", "ent", T_AGLI, "ent", E_VAMBA, "Fermata Torre degli Agli verso Vamba"),
        ("R10", "civ", CIV[400], "ent", T_REG, "Civico di R05 verso la fermata Regione Toscana"),
        ("V01", "civ", "adr_fi_31825", "ent", E_POLO, "VIETATO: via della Verna 3, collegata al resto della rete solo da tratti access=private"),
        ("V02", "civ", "adr_fi_90008", "ent", E_POLO, "VIETATO (restrizione diversa): via del Ponte di Mezzo 27/18, collegata solo da un tunnel stradale senza marciapiede")]
res, feats = [], []
for cid, ta, a, tb, b, desc in casi:
    pa, sa, na = punti[ta](a); pbb, sb, nb = punti[tb](b)
    r = {"id": cid, "descrizione": desc, "origine": na, "destinazione": nb, "snap_origine": {k: sa.get(k) for k in ("edge_id", "dist_m", "stato")}, "snap_destinazione": {k: sb.get(k) for k in ("edge_id", "dist_m", "stato")},
         "diretta_m": round(pa.distance(pbb), 1), "stato_verifica": "da_verificare", "grafo": json.load(open(RES / "rete_manifest.json"))["graph_id"]}
    if sa["stato"] != "agganciato" or sb["stato"] != "agganciato": r["stato"] = "insufficient_data"
    elif out := percorso(G, sa, sb):
        H, nodi, archi = out; r.update(stato="reachable", **riassunto(H, nodi, archi, sa["dist_m"] + sb["dist_m"]))
        r["attraversamenti_way"] = n_way_attraversamento(r["archi"]); r["deviazione"] = round(r["lunghezza_totale_m"] / max(r["diretta_m"], 1), 2); r["_geom"] = geom_percorso(H, nodi, archi, pa, sa, pbb, sb)
    elif outp := percorso(P, sa, sb):
        H, nodi, archi = outp; rr = riassunto(H, nodi, archi, sa["dist_m"] + sb["dist_m"])
        r.update(stato="forbidden", motivo="nessun percorso sul grafo verificato; collegato solo attraverso tratti con restrizione documentata", restrizioni=rr["restrizioni_attraversate"],
                 permissivo_lunghezza_m=rr["lunghezza_totale_m"], archi_permissivi=rr["archi"], origine_componente=civ.loc[a].componente if ta == "civ" else None)
        r["_geom"] = geom_percorso(H, nodi, archi, pa, sa, pbb, sb)
    else: r.update(stato="isolated", motivo="nessun percorso nemmeno ignorando le restrizioni")
    res.append(r)
    if "_geom" in r:
        g = r.pop("_geom"); pr = {k: v for k, v in r.items() if k in ("id", "descrizione", "origine", "destinazione", "stato", "lunghezza_totale_m", "diretta_m", "deviazione", "attraversamenti", "attraversamenti_way", "tratti_marciapiede_ignoto", "m_marciapiede_ignoto", "scale", "sottopassi", "stato_verifica", "restrizioni")}
        pr["permissivo_lunghezza_m"] = r.get("permissivo_lunghezza_m"); pr["marciapiede_dichiarato"] = False
        feats.append({"type": "Feature", "geometry": ll(g), "properties": {k: v for k, v in pr.items() if v is not None}})
for r in res:   # i tratti vietati, per l'anteprima
    for e in r.get("archi_permissivi", []):
        ex = next((x for x in D["esclusi"] if x["edge_id"] == e), None)
        if ex: feats.append({"type": "Feature", "geometry": ll(ex["geometry"]), "properties": {"id": r["id"], "tipo": "tratto_vietato", "motivo": ex["motivo"], "edge_id": ex["edge_id"]}})
json.dump({"type": "FeatureCollection", "name": "percorsi_campione_firenze", "nota": "EPSG:4326 solo per la visualizzazione; calcolo in EPSG:7791. Percorsi su grafo OSM non verificato, nessuna certificazione di accessibilità.", "features": feats}, open(RES / "percorsi_campione.geojson", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(res, open(RES / "percorsi_campione.json", "w"), ensure_ascii=False, indent=1, default=str)
for r in res: print({k: v for k, v in r.items() if k not in ("archi", "archi_permissivi", "snap_origine", "snap_destinazione", "grafo", "attraversamenti_tipi")})
