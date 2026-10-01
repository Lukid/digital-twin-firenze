#!/usr/bin/env python3
"""Passo 3: destinazioni (Battisti, fermate GTFS di Z2), ingressi e origini (civici SIT di Z2) agganciati alla rete.
Output: network/{destinazioni.json, destinazioni_ingressi.geojson, snapping_report.json}, data/norm/network/origini_snap.gpkg"""
import collections, json, pickle, sys
import shapely.ops
import geopandas as gpd, numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, mapping
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "pipeline"))
from lib import AOI
from rete_lib import *

Z = AOI["z2_en"]; NORM = ROOT / "data/norm"
G, D = carica()
osm = pickle.load(open(OUT / "osm_estratto.pkl", "rb"))
pts = gpd.read_file(NORM / "osm_pisa.gpkg", layer="points"); bld = gpd.read_file(NORM / "osm_pisa.gpkg", layer="buildings")
SN = Snapper(G, D["esclusi"], D["bloccati"], bld)
SR = REGOLE["snapping"]; MAXI, NC_I = SR["ingressi"]["max_m"], SR["ingressi"]["candidati"]; MAXO, NC_O = SR["origini"]["max_m"], SR["origini"]["candidati"]
to_ll = Transformer.from_crs(7791, 4326, always_xy=True)   # solo per i file di visualizzazione (7791 ~ 6706 ~ 4326 entro 1 m)
def ll(g): return mapping(shapely.ops.transform(lambda x, y, z=None: to_ll.transform(x, y), g))

def snap_ent(p, ent_id):
    s = SN.snap(p, MAXI, NC_I)
    if s["stato"] == "agganciato":
        s["raccordo_m"] = s["dist_m"]; s["componente"] = G.nodes[s["u"]]["componente"]
    return s

# ---------------------------------------------------------------- Battisti
BATT = [a for a in osm["aree"] if a["id"] == 695634299][0]
S = Polygon([(x, y) for _, x, y in BATT["nodes"]])
AUDIT_IDS = [5101368983, 5101368984, 5101368985, 6532183886, 13804118745, 13804118746, 13804118752, 13804368962]   # 8 ingressi dell'audit T01
ent = pts[pts.kind == "entrance"].copy(); ent["osm"] = ent.id.str.replace("nod_osm_", "").astype("int64")
cand = ent[(ent.distance(S) <= 25) | ent.osm.isin(AUDIT_IDS)]
def classe_ingresso(r):
    t = json.loads(r.tags); g = r.geometry; dpoly = S.distance(g)
    on = bld[bld.distance(g) <= 1.0]
    bdesc = []
    frac = None
    for _, b in on.iterrows():
        f = b.geometry.intersection(S).area / b.geometry.area; frac = f if frac is None else max(frac, f)
        bdesc.append(f"{b.id} ({json.loads(b.tags).get('building')}, {b.area_m2:.0f} m2, {f*100:.0f}% nel perimetro della scuola)")
    addr = (t.get("addr:street", "") + " " + t.get("addr:housenumber", "")).strip()
    base = f"ingresso OSM entrance={t.get('entrance')}, indirizzo {addr or 'assente'}, a {dpoly:.1f} m dal perimetro OSM della scuola (way 695634299, via Filippo Corridoni 42)"
    if dpoly <= 3 and (frac is None or frac > 0.5):
        c = "probabile_ingresso_scuola"; why = base + "; dentro il perimetro, su " + ("; ".join(bdesc) if bdesc else "nessun edificio mappato") + "; indirizzo assente o coerente: nessun segnale di un altro edificio"
    elif dpoly > 3 and (frac is None or frac < 0.1):
        c = "probabile_edificio_contiguo"; why = base + "; fuori dal perimetro, su " + ("; ".join(bdesc) if bdesc else "nessun edificio mappato") + ("; numero civico diverso da 42" if addr else "")
    else:
        c = "incerto"; why = base + "; segnali contrastanti: " + "; ".join(bdesc)
    return c, why, dpoly
rows = []
for _, r in cand.iterrows():
    c, why, dp = classe_ingresso(r)
    s = snap_ent(r.geometry, r.id)
    rows.append({"entrance_id": f"ent_osm_n{r.osm}", "osm_node": r.osm, "classe": c, "motivazione": why, "dist_perimetro_m": round(dp, 1), "nell_audit_t01": int(r.osm) in AUDIT_IDS,
                 "stato_verifica": "da_verificare", "tags": json.loads(r.tags), "xy": (r.geometry.x, r.geometry.y), "aggancio": s})
battisti_ent = sorted(rows, key=lambda r: r["dist_perimetro_m"])

# ---------------------------------------------------------------- Fermate GTFS di Z2
st = gpd.read_file(NORM / "gtfs_at_toscana.gpkg", layer="stops").cx[Z[0]:Z[2], Z[1]:Z[3]]
plat = pts[pts.tags.str.contains('"public_transport": "platform"') & ~pts.tags.str.contains('"railway"')].copy()
fermate = []
def norm_nome(s): return "".join(ch for ch in str(s).lower() if ch.isalnum())
for _, r in st.iterrows():
    near = plat.assign(d=plat.distance(r.geometry)); near = near[near.d <= 25].sort_values("d")
    nomi = {norm_nome(json.loads(t).get("name")): i for i, t in zip(near.index, near.tags)}
    if len(near):
        o = near.iloc[0]; punto = o.geometry; eid = "ent_osm_n" + o.id.replace("nod_osm_", ""); fonte = f"piattaforma OSM a {o.d:.1f} m dal punto GTFS"; ref = json.loads(o.tags).get("name")
    else:
        punto = r.geometry; eid = "ent_gtfs_" + r.stop_code.lower(); fonte = "punto GTFS (nessuna piattaforma OSM entro 25 m)"; ref = None
    s = snap_ent(punto, eid)
    fermate.append({"destination_id": r.id, "stop_code": r.stop_code, "nome": r.stop_name, "corse": int(r.trips_on_ref_date), "entrance_id": eid, "ingresso_fonte": fonte, "nome_osm": ref,
                    "stato_verifica": "da_verificare", "xy": (punto.x, punto.y), "gtfs_xy": (r.geometry.x, r.geometry.y), "aggancio": s})

# ---------------------------------------------------------------- scrittura destinazioni
dest = {"graph_id": json.load(open(NET / "rete_manifest.json"))["graph_id"], "classificazione": "ingressi OSM = measured; classe ingresso e aggancio = derived (regole in regole.json e nel codice); tutto da_verificare",
        "destinazioni": [{"destination_id": "dst_school_piee82101p", "categoria": "school", "nome": "Scuola Primaria C. Battisti", "indirizzo": "via Filippo Corridoni 42", "codice_mim": "PIEE82101P (dall'audit T01, non nel SIT)",
                          "fonte": "OSM way 695634299", "stato_verifica": "da_verificare", "condizioni_accesso": "non note (orari, cancello, ingresso alunni vs pubblico)",
                          "ingresso_predefinito": next((r["entrance_id"] for r in battisti_ent if r["classe"] == "probabile_ingresso_scuola"), None), "ingressi": battisti_ent}] +
                        [{"destination_id": f["destination_id"], "categoria": "stop", "nome": f["nome"], "stop_code": f["stop_code"], "corse_giorno_rif": f["corse"], "fonte": "GTFS Autolinee Toscane",
                          "stato_verifica": "da_verificare", "condizioni_accesso": "non note (pensilina, marciapiede, accessibilità non dichiarata nel feed)", "ingresso_predefinito": f["entrance_id"], "ingressi": [f]} for f in fermate]}
json.dump(dest, open(NET / "destinazioni.json", "w"), ensure_ascii=False, indent=1, default=str)
feats = []
for d in dest["destinazioni"]:
    for e in d["ingressi"]:
        p = Point(e["xy"]); a = e["aggancio"]
        feats.append({"type": "Feature", "geometry": ll(p), "properties": {"id": e["entrance_id"], "destinazione": d["destination_id"], "nome": d["nome"], "classe": e.get("classe", "ingresso_fermata"), "stato": a["stato"], "raccordo_m": a.get("dist_m"), "verifica": "da_verificare"}})
        if a["stato"] == "agganciato":
            feats.append({"type": "Feature", "geometry": ll(LineString([p, Point(a["proj"])])), "properties": {"id": e["entrance_id"], "tipo": "raccordo", "m": a["dist_m"]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(NET / "destinazioni_ingressi.geojson", "w"), ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- origini: civici SIT di Z2
civ = gpd.read_file(NORM / "sit_civici.gpkg").cx[Z[0]:Z[2], Z[1]:Z[3]].copy()
raw = np.array([distanza_vicino(SN, g) for g in civ.geometry]); res = [SN.snap(g, MAXO, NC_O, SR["origini"]["tipi_arco_esclusi"]) for g in civ.geometry]
civ["stato"] = [("reachable_candidate" if r["stato"] == "agganciato" else "insufficient_data") for r in res]
civ["edge_id"] = [r.get("edge_id") for r in res]; civ["raccordo_m"] = [r.get("dist_m") for r in res]
civ["motivo"] = [r.get("motivo") for r in res]; civ["scartati_prima"] = [len(r["scartati"]) for r in res]
civ["componente"] = [G.nodes[r["u"]]["componente"] if r["stato"] == "agganciato" else None for r in res]
civ["dist_diretta_arco_m"] = raw.round(2)
rac = [LineString([g, Point(r["proj"])]) if r["stato"] == "agganciato" and r["dist_m"] > 0 else None for g, r in zip(civ.geometry, res)]
civ["snap_u"] = [r.get("u") for r in res]; civ["snap_v"] = [r.get("v") for r in res]; civ["snap_offset_m"] = [r.get("offset_m") for r in res]
f = OUT / "origini_snap.gpkg"; f.unlink(missing_ok=True)
civ.drop(columns=["cls"], errors="ignore").to_file(f, layer="origini", driver="GPKG")
gpd.GeoDataFrame({"id": [i for i, r in zip(civ.id, rac) if r is not None]}, geometry=[r for r in rac if r is not None], crs=7791).to_file(f, layer="raccordi", driver="GPKG")
ag = civ[civ.stato != "insufficient_data"]; pc = lambda a, q: float(np.percentile(a, q)) if len(a) else None
rep = {"parametri": {"origini_max_m": MAXO, "ingressi_max_m": MAXI, "candidati": NC_O}, "origini_totali_z2": len(civ), "agganciate": len(ag), "non_agganciate_insufficient_data": int((civ.stato == "insufficient_data").sum()),
       "non_agganciate_motivi": dict(collections.Counter(civ[civ.stato == "insufficient_data"].motivo.str.replace(r"\d+ m", "N m", regex=True))),
       "distanza_arco_piu_vicino_senza_vincoli_m": {f"p{q}": round(pc(raw, q), 1) for q in (50, 75, 90, 95, 99)} | {"max": round(float(raw.max()), 1)},
       "raccordo_registrato_m": {f"p{q}": round(pc(ag.raccordo_m.astype(float), q), 1) for q in (50, 75, 90, 95, 99)} | {"max": round(float(ag.raccordo_m.max()), 1)},
       "civici_oltre_20_m": int((ag.raccordo_m.astype(float) > 20).sum()), "civici_primo_candidato_scartato": int((civ.scartati_prima > 0).sum()),
       "per_componente": dict(collections.Counter(ag.componente)), "agganciati_a_componenti_isolate": int((ag.componente != "cmp_01").sum()),
       "per_tipo_arco_agganciato": dict(collections.Counter(G.edges[(r["u"], r["v"], r["edge_id"])]["tipo_arco"] for r in res if r["stato"] == "agganciato")),
       "per_marciapiede_arco_agganciato": dict(collections.Counter(G.edges[(r["u"], r["v"], r["edge_id"])]["marciapiede_stato"] for r in res if r["stato"] == "agganciato")),
       "ingressi_battisti": [{"id": e["entrance_id"], "classe": e["classe"], "stato": e["aggancio"]["stato"], "raccordo_m": e["aggancio"].get("dist_m"), "componente": e["aggancio"].get("componente")} for e in battisti_ent],
       "fermate_z2": len(fermate), "fermate_agganciate": sum(1 for x in fermate if x["aggancio"]["stato"] == "agganciato"),
       "fermate_raccordo_m": {f"p{q}": round(pc([x["aggancio"]["dist_m"] for x in fermate if x["aggancio"]["stato"] == "agganciato"], q), 1) for q in (50, 90)} | {"max": max([x["aggancio"]["dist_m"] for x in fermate if x["aggancio"]["stato"] == "agganciato"])},
       "fermate_non_agganciate": [(x["stop_code"], x["aggancio"].get("motivo")) for x in fermate if x["aggancio"]["stato"] != "agganciato"],
       "fermate_su_componenti": dict(collections.Counter(x["aggancio"].get("componente") for x in fermate))}
json.dump(rep, open(NET / "snapping_report.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False, indent=1)); print(len(cand), [(r["entrance_id"], r["classe"]) for r in battisti_ent])
