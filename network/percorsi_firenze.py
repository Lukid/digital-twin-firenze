#!/usr/bin/env python3
"""F04 passo 5 (Firenze): percorsi campione (consentiti e vietati) sul grafo non verificato, dai civici e dalle fermate T2 al Polo (ingresso più vicino fra i 7 edifici), a Vamba e ai rifugi climatici (RC1-RC5, D32).
Uso: python network/percorsi_firenze.py. Output: network/firenze_novoli/percorsi_campione.{json,geojson}.
Script a parte rispetto a percorsi.py: i casi sono scritti nel codice, come a Pisa; qui cambiano ID, destinazioni e civici."""
import json, os, sys
import geopandas as gpd, shapely, shapely.ops
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
POLO = dest["dst_university_w83537185"]; E_POLO, E_POLI = POLO["ingresso_predefinito"], POLO["ingressi_predefiniti"]   # D1 e i 7 ingressi degli edifici (D19)
E_RIF = sorted(e["entrance_id"] for d in dest.values() if d["categoria"] == "cooling_refuge" for e in d["ingressi"]); E_MEDAGLIE = [e["entrance_id"] for e in dest["dst_refuge_rif_fi_02399"]["ingressi"]]
E_VAMBA = dest["dst_school_fiee86002g"]["ingresso_predefinito"]; T_AGLI, T_REG, T_SD = "ent_gtfs_fm9057", "ent_gtfs_fm9056", "ent_gtfs_fm9055"
pb = shapely.MultiPoint([ent[e]["xy"] for e in E_POLI])   # distanza dal Polo = dall'ingresso più vicino in linea d'aria
ok = civ[(civ.stato == "reachable_candidate") & (civ.componente == "cmp_01") & (civ.TIPO == "N")].copy(); ok["d"] = ok.geometry.distance(pb)   # solo civici neri (abitazioni)
CIV = {t: ok.assign(s=(ok.d - t).abs()).sort_values(["s", "CODICECIVI"]).index[0] for t in (150, 400, 700, 1000)}   # a parità di distanza decide CODICECIVI, non l'id del Comune
def cc(codice): return civ.index[civ.CODICECIVI == codice][0]   # chiave stabile del civico (D30): il Comune rinumera gli ID, non CODICECIVI
punti = {"ent": lambda eid: (Point(ent[eid]["xy"]), snap_of(ent[eid]), f"{eid} ({ent[eid]['classe']})"),
         "civ": lambda cid: (civ.loc[cid].geometry, SN.snap(civ.loc[cid].geometry, SO["max_m"], SO["candidati"], SO["tipi_arco_esclusi"]), f"{cid} ({civ.loc[cid].indirizzo})")}
casi = [("R01", "ent", T_SD, "polo", None, "Fermata T2 San Donato - Università (indicata dall'Ateneo) verso l'ingresso del Polo più vicino per rete"),
        ("R02", "ent", T_REG, "polo", None, "Fermata T2 Novoli - Regione Toscana verso l'ingresso del Polo più vicino per rete"),
        ("R03", "ent", T_REG, "ent", E_POLO, "Fermata Regione Toscana verso l'edificio D1 (sensibilità alla scelta dell'ingresso)"),
        ("R04", "civ", CIV[150], "polo", None, "Civico a circa 150 m in linea d'aria dal Polo, verso l'ingresso più vicino per rete"),
        ("R05", "civ", CIV[400], "polo", None, "Civico a circa 400 m"),
        ("R06", "civ", CIV[700], "polo", None, "Civico a circa 700 m"),
        ("R07", "civ", CIV[1000], "polo", None, "Civico a circa 1000 m"),
        ("R08", "civ", CIV[400], "ent", E_VAMBA, "Civico di R05 verso l'accesso della scuola Vamba"),
        ("R09", "ent", T_AGLI, "ent", E_VAMBA, "Fermata Torre degli Agli verso Vamba"),
        ("R10", "civ", CIV[400], "ent", T_REG, "Civico di R05 verso la fermata Regione Toscana"),
        ("V01", "civ", cc("D61200018415000300000000000N"), "polo", None, "VIETATO: via della Verna 3, collegata al resto della rete solo da tratti access=private"),
        ("V02", "civ", cc("D61200013220002701800000000N"), "polo", None, "VIETATO (restrizione diversa): via del Ponte di Mezzo 27/18, collegata solo da un tunnel stradale senza marciapiede"),
        # verso i rifugi climatici (D32), proposti nel report F1; stato da verificare come gli altri
        ("RC1", "ent", T_REG, "vicino", E_MEDAGLIE, "Fermata T2 Novoli - Regione Toscana verso il Giardino di Piazza delle Medaglie d'Oro, ingresso più vicino per rete fra i due dichiarati"),
        ("RC2", "ent", T_AGLI, "ent", "ent_rib_6_0", "Fermata T2 Torre degli Agli verso la Biblioteca Filippo Buonarroti (Viale Guidoni 188)"),
        ("RC3", "ent", "ent_civ_d15", "ent", "ent_rif_01523_0", "Ingresso D15 del Polo verso il Giardino di piazza dei Cavalieri di Vittorio Veneto (Via Luigi Morandi 2)"),
        ("RC4", "civ", CIV[400], "vicino", E_RIF, "Civico di R05 verso il rifugio climatico più vicino per rete"),
        ("RC5", "ent", E_VAMBA, "vicino", E_RIF, "Accesso della scuola primaria Vamba verso il rifugio climatico più vicino per rete")]
res, feats = [], []
def piu_vicino(sa, entrate=E_POLI, ripiego=E_POLO):
    """Ingresso fra `entrate` (default: i 7 del Polo) con il percorso più corto (grafo verificato, poi permissivo); a parità di stato vince il primo dell'elenco."""
    def lung(e, H):
        out = percorso(H, sa, snap_of(ent[e])); return riassunto(*out, sa["dist_m"] + ent[e]["aggancio"]["dist_m"])["lunghezza_totale_m"] if out else None
    for H in (G, P):
        l = {e: lung(e, H) for e in entrate if sa["stato"] == "agganciato"}; l = {e: v for e, v in l.items() if v is not None}
        if l: return min(l, key=l.get)
    return ripiego
for cid, ta, a, tb, b, desc in casi:
    pa, sa, na = punti[ta](a)
    if tb == "polo": tb, b = "ent", piu_vicino(sa); desc += f" ({b})"
    elif tb == "vicino": tb, b = "ent", piu_vicino(sa, b, b[0]); desc += f" ({b})"
    pbb, sb, nb = punti[tb](b)
    r = {"id": cid, "descrizione": desc, "origine": na, "destinazione": nb, "snap_origine": {k: sa.get(k) for k in ("edge_id", "dist_m", "stato")}, "snap_destinazione": {k: sb.get(k) for k in ("edge_id", "dist_m", "stato")},
         "diretta_m": round(pa.distance(pbb), 1), "stato_verifica": "da_verificare", "grafo": json.load(open(RES / "rete_manifest.json"))["graph_id"]}
    if ta == "civ": r["civico"] = civ.loc[a].CODICECIVI   # per ritrovare il civico se il Comune cambia gli id
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
