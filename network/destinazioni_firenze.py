#!/usr/bin/env python3
"""F04 passo 3 (Firenze): destinazioni con ingressi, origini (civici del Comune) agganciate alla rete, barriere del Comune come attributo degli edifici.
Uso: python network/destinazioni_firenze.py
Output in network/firenze_novoli/: destinazioni.json, destinazioni_ingressi.geojson, snapping_report.json, barriere_edifici.json; origini_snap.gpkg in data/norm/firenze_novoli/network/.
Perché uno script a parte: le destinazioni di Pisa (Battisti, GTFS bus) sono scritte nel codice di destinazioni.py; qui si riusano Snapper e le funzioni di rete_lib."""
import collections, json, os, pickle, sys
import geopandas as gpd, networkx as nx, numpy as np, pandas as pd, shapely.ops
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, mapping
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare lib e rete_lib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "pipeline"))
from lib import AOI, NORM
from rete_lib import *
from coordinate import arrotonda

Z = AOI["z2_en"]
G, D = carica(); P = permissivo(G, D["esclusi"])
osm = pickle.load(open(OUT / "osm_estratto.pkl", "rb"))
pts = gpd.read_file(OSM_GPKG, layer="points"); bld = gpd.read_file(OSM_GPKG, layer="buildings")
SN = Snapper(G, D["esclusi"], D["bloccati"], bld)
SR = REGOLE["snapping"]; MAXI, NC_I = SR["ingressi"]["max_m"], SR["ingressi"]["candidati"]; MAXO, NC_O = SR["origini"]["max_m"], SR["origini"]["candidati"]
to_ll = Transformer.from_crs(7791, 4326, always_xy=True)   # solo per i file di visualizzazione
def ll(g): return arrotonda(mapping(shapely.ops.transform(lambda x, y, z=None: to_ll.transform(x, y), g)))   # D39
def area(osm_id): return Polygon([(x, y) for _, x, y in next(a for a in osm["aree"] if a["id"] == osm_id)["nodes"]])
def snap_ent(p):
    s = SN.snap(p, MAXI, NC_I)
    if s["stato"] == "agganciato": s["raccordo_m"] = s["dist_m"]; s["componente"] = G.nodes[s["u"]]["componente"]
    return s
def ingresso(eid, classe, fonte, p, **kw):
    return {"entrance_id": eid, "classe": classe, "fonte_ingresso": fonte, "stato_verifica": "da_verificare", **kw, "xy": (p.x, p.y), "aggancio": snap_ent(p)}

# ---------------------------------------------------------------- perimetri e barriere del Comune (attributo dell'edificio o della destinazione, non dell'arco)
POLO, VAMBA = area(83537185), area(781536026)      # amenity=university "Polo delle Scienze Sociali"; amenity=school "Vamba"
bar = gpd.read_file(NORM / "fi_barriere.gpkg").cx[Z[0]:Z[2], Z[1]:Z[3]]
def schede(perimetro, tol=5):
    """Schede del Comune dentro il perimetro (tolleranza 5 m): il punto della scheda è sul lotto, non sull'ingresso."""
    return [{"scheda": r.scheda, "bar_id": r.id, "destinazione_uso": r.destinaz_u, "indirizzo": r.indirizzo, "grado_accessibilita": r.grado_acce, "url_scheda": r.url.split('"')[1] if '"' in r.url else r.url}
            for r in bar.itertuples() if r.geometry.distance(perimetro) <= tol]
NOTA_BAR = "schede di edifici del rilievo 2013 (grado Accessibile / Parzialmente / Non accessibile): attributo dell'edificio, non dell'ostacolo sul percorso"

# ---------------------------------------------------------------- Polo delle Scienze Sociali: un ingresso per edificio dell'Ateneo (D19, 10 ottobre 2026)
# Indirizzi dall'elenco edifici del report di accessibilità dell'Ateneo (unifisostenibile.unifi.it, "REPORT accessibilità, Riepilogo per CAMPUS");
# il punto è il civico del Comune (fi_civici). Prima erano due ingressi OSM: biblioteca e una corte interna (network/firenze_novoli/verifica_ingressi_polo.md).
EDIFICI_POLO = [("D1", "VIA DELLE PANDETTE", "32", "scuole e segreterie"), ("D4", "VIA DELLE PANDETTE", "35", "aule, Dipartimento di Scienze Giuridiche"),
                ("D5", "VIA DELLE PANDETTE", "21", "aule, DSPS"), ("D6", "VIA DELLE PANDETTE", "9", "aule, DISEI"), ("D10", "VIA DELLE PANDETTE", "2", "biblioteca"),
                ("D14", "VIA DELLE PANDETTE", "3", "bar, sale lettura, aula studio"), ("D15", "PIAZZA UGO DI TOSCANA", "5", "aule tesi, laboratori")]
civ_fi = gpd.read_file(NORM / "fi_civici.gpkg").cx[Z[0]:Z[2], Z[1]:Z[3]]
polo_ing = []
for ed, via, num, uso in EDIFICI_POLO:
    r = civ_fi[(civ_fi.STRADA.str.strip() == via) & (civ_fi.NUMEROCIVI.str.strip() == num)]
    assert len(r) == 1, (via, num, len(r))
    r = r.iloc[0]
    polo_ing.append(ingresso(f"ent_civ_{ed.lower()}", "civico_edificio_ateneo", f"civico del Comune {r.id} ({via.title()} {num}); edificio {ed} ({uso}) dall'elenco edifici dell'Ateneo",
                             r.geometry, edificio=ed, civico_id=r.id, dentro_perimetro=bool(POLO.covers(r.geometry))))
def ingresso_o_perimetro(ings, perimetro, did):
    """Se non c'è alcun ingresso mappato: punto del perimetro più vicino alla rete (dichiarato come tale, mai un ingresso reale)."""
    return ings or [ingresso(f"ent_perim_{did}", "punto_sul_perimetro", "derivato: punto del perimetro OSM più vicino alla rete, NON è un ingresso mappato", punto_perimetro(perimetro, G))]
dest = [{"destination_id": "dst_university_w83537185", "categoria": "university", "nome": "Polo delle Scienze Sociali (Università degli Studi di Firenze)", "indirizzo": "via delle Pandette",
         "id_note": "Il Polo non ha un codice ufficiale: id da OSM way 83537185 (perimetro d'insieme). Ingressi: un civico del Comune per edificio dell'Ateneo (D1, D4, D5, D6, D10, D14, D15); il più vicino per ogni origine.",
         "fonte": "OSM way 83537185", "stato_verifica": "da_verificare", "condizioni_accesso": "edifici aperti dal lunedì al venerdì 7:30-20:00 (pagine del DISEI); porte, cancelli e ingresso per disabili non verificati",
         "barriere_comune": {"nota": NOTA_BAR, "schede": schede(POLO)}, "ingressi": ingresso_o_perimetro(polo_ing, POLO, "w83537185")}]

# ---------------------------------------------------------------- Scuola Vamba: ingressi OSM (nessuno), poi accessi della Città metropolitana (uno per codice MIM)
sc = gpd.read_file(NORM / "fi_scuole_statali.gpkg").set_index("codicescuo"); acc = gpd.read_file(NORM / "cm_edscol_firenze.gpkg", layer="accessi").set_index("CODICE")
ent_v = pts[(pts.kind == "entrance") & (pts.distance(VAMBA) <= 25)]
for cod, tipo in (("FIEE86002G", "primaria"), ("FIAA86002A", "infanzia")):
    did = "dst_school_" + cod.lower()
    ings = [ingresso("ent_osm_n" + r.id.removeprefix("nod_osm_"), "ingresso_osm", "OSM entrance", r.geometry) for _, r in ent_v.iterrows()]
    if not ings and cod in acc.index:
        a = acc.loc[cod]; ings = [ingresso(f"ent_cm_{cod}_0", "accesso_citta_metropolitana", f"accesso della Città metropolitana {a.id} ({a.INDIRIZZO}), a {Point(a.geometry).distance(sc.loc[cod].geometry):.0f} m dal punto MIM", a.geometry)]
    dest.append({"destination_id": did, "categoria": "school", "nome": f"Scuola {tipo} Vamba", "indirizzo": "via del Giardino della Bizzarria 1", "codice_mim": cod, "fonte": "MIM scuole statali 2026/27 (punto) e OSM way 781536026 (perimetro)",
                 "stato_verifica": "da_verificare", "condizioni_accesso": "non note (orari, ingresso alunni o pubblico). Un solo accesso nei dati, condiviso dai due codici",
                 "barriere_comune": {"nota": NOTA_BAR, "schede": schede(VAMBA)}, "ingressi": ingresso_o_perimetro(ings, VAMBA, cod.lower())})

# ---------------------------------------------------------------- Fermate T2 nel riquadro (GTFS GEST), più San Donato - Università (FM9055): è la fermata che l'Ateneo indica per il Polo
# e sta circa 100 m a sud del riquadro, dentro il margine di rete (D20). Le stop_position OSM stanno sul binario: l'ingresso è il punto GTFS agganciato alla rete pedonale
FERMATE_EXTRA = ["FM9055"]
gt = gpd.read_file(NORM / "gtfs_gest_firenze.gpkg"); st = gt.cx[Z[0]:Z[2], Z[1]:Z[3]]
st = pd.concat([gt[gt.stop_code.isin(FERMATE_EXTRA)], st]).drop_duplicates("id")
for _, r in st.iterrows():
    dest.append({"destination_id": r.id, "categoria": "tram", "nome": r.stop_name, "stop_code": r.stop_code, "linee": r.lines, "corse_giorno_rif": int(r.trips_on_ref_date), "fonte": "GTFS GEST (tram)",
                 "stato_verifica": "da_verificare", "condizioni_accesso": "non note (marciapiede e banchina: nessun dato nel feed)",
                 "ingressi": [ingresso("ent_gtfs_" + r.stop_code.lower(), "ingresso_fermata", "punto GTFS (le stop_position OSM sono sul binario)", r.geometry)]})

# ---------------------------------------------------------------- Rifugi climatici del Comune entro i 700 m del margine di rete (D32, 17 ottobre 2026)
# Ingresso = civico del Comune all'indirizzo dichiarato dalla fonte (campo ingresso delle aree, indirizzo e civico della biblioteca), cercato in tutta l'area allargata.
# Parco delle Cascine (rif_fi_02556) escluso: i suoi indirizzi d'ingresso (Piazzale dell'Indiano 3, Viale delle Cornacchie 2) non sono fra i civici dell'area allargata.
RIFUGI = [("rif_fi_02399", [("VIA ARCANGELO CORELLI", "19"), ("VIA FRANCESCO BARACCA", "135/D")]), ("rib_fi_6", [("VIALE ALESSANDRO GUIDONI", "188")]),
          ("rif_fi_01523", [("VIA LUIGI MORANDI", "2")]), ("rif_fi_01631", [("VIA GUGLIELMO JERVIS", "13")]), ("rif_fi_05409", [("VIA ARTURO TOSCANINI", "20")]),
          ("rif_fi_02394", [("VIA ARTURO TOSCANINI", "5")]), ("rif_fi_01545", [("PIAZZA GIACOMO PUCCINI", "24/A")])]
civ_all = gpd.read_file(NORM / "fi_civici.gpkg")
rif = pd.concat([gpd.read_file(NORM / "fi_rifugi_aree.gpkg").rename(columns={"nome_area": "nome"}), gpd.read_file(NORM / "fi_rifugi_biblioteche.gpkg")]).set_index("id")
for rid, indirizzi in RIFUGI:
    r = rif.loc[rid]; bib = rid.startswith("rib_"); ings = []
    for i, (via, num) in enumerate(indirizzi):
        c = civ_all[(civ_all.STRADA.str.strip() == via) & (civ_all.NUMEROCIVI.str.strip() == num)]
        assert len(c) == 1, (rid, via, num, len(c))
        c = c.iloc[0]
        ings.append(ingresso(f"ent_{rid.replace('_fi_', '_')}_{i}", "civico_ingresso_rifugio", f"civico del Comune {c.id} ({via.title()} {num}); indirizzo d'ingresso dichiarato dalla fonte: "
                             + (f"{r.indirizzo} {r.civico}" if bib else r.ingresso), c.geometry, civico_id=c.id, civico=c.CODICECIVI))
    dest.append({"destination_id": f"dst_refuge_{rid}", "categoria": "cooling_refuge", "nome": r.nome, "fonte": f"{r.source_id} ({rid})", "stato_verifica": "da_verificare",
                 "tipo_rifugio": "biblioteca" if bib else "area_fresca", **({} if bib else {"ombreggiatura_dichiarata_pct": int(r.percentuale_ombreggi)}),
                 "condizioni_accesso": f"orari della biblioteca: {r.orario} (non sempre aperta)" if bib else "giardino pubblico: orari e cancelli non noti",
                 "ingressi": ings, **({"ingressi_predefiniti": [e["entrance_id"] for e in ings]} if len(ings) > 1 else {})})   # più ingressi: vince il più vicino
for d in dest: d["ingresso_predefinito"] = d["ingressi"][0]["entrance_id"]
dest[0]["ingresso_predefinito"] = "ent_civ_d1"   # D1, scuole e segreterie: ingresso singolo per i percorsi campione e la compatibilità
dest[0]["ingressi_predefiniti"] = [e["entrance_id"] for e in dest[0]["ingressi"]]   # accessibilità: vince l'ingresso più vicino per ogni origine
man = json.load(open(RES / "rete_manifest.json"))
json.dump({"graph_id": man["graph_id"], "classificazione": "civici del Comune, accessi CM e punti GTFS = measured; classe dell'ingresso e aggancio = derived; tutto da_verificare", "destinazioni": dest},
          open(RES / "destinazioni.json", "w"), ensure_ascii=False, indent=1, default=str)
feats = []
for d in dest:
    for e in d["ingressi"]:
        p = Point(e["xy"]); a = e["aggancio"]
        feats.append({"type": "Feature", "geometry": ll(p), "properties": {"id": e["entrance_id"], "destinazione": d["destination_id"], "nome": d["nome"], "classe": e["classe"], "stato": a["stato"], "raccordo_m": a.get("dist_m"), "verifica": "da_verificare"}})
        if a["stato"] == "agganciato": feats.append({"type": "Feature", "geometry": ll(LineString([p, Point(a["proj"])])), "properties": {"id": e["entrance_id"], "tipo": "raccordo", "m": a["dist_m"]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(RES / "destinazioni_ingressi.geojson", "w"), ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- tutte le schede del riquadro: edificio OSM più vicino entro 25 m (o nessuno)
righe = []
for r in bar.itertuples():
    d = bld.distance(r.geometry); j = d.idxmin()
    righe.append({"bar_id": r.id, "scheda": r.scheda, "grado_accessibilita": r.grado_acce, "destinazione_uso": r.destinaz_u, "indirizzo": r.indirizzo,
                  "edificio_osm": bld.id[j] if d[j] <= 25 else None, "dist_edificio_m": round(float(d[j]), 1),
                  "destinazioni": [x["destination_id"] for x in dest if any(s["bar_id"] == r.id for s in x.get("barriere_comune", {}).get("schede", []))]})
json.dump({"nota": NOTA_BAR + ". Aggancio: edificio OSM più vicino entro 25 m, solo informativo", "schede_nel_riquadro": len(righe), "per_grado": dict(collections.Counter(x["grado_accessibilita"] for x in righe)),
           "agganciate_a_edificio": sum(1 for x in righe if x["edificio_osm"]), "schede": righe}, open(RES / "barriere_edifici.json", "w"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- origini: civici del Comune nel riquadro
civ = gpd.read_file(NORM / "fi_civici.gpkg").cx[Z[0]:Z[2], Z[1]:Z[3]].copy()
civ["indirizzo"] = (civ.STRADA.str.strip() + " " + civ.NUMEROCIVI.str.strip()).str.strip()
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

# stato rispetto alla destinazione principale: stessa componente = reachable; altrimenti forbidden se il grafo di controllo (con i tratti vietati) li collega, isolated se no
lab = {n: i for i, c in enumerate(nx.connected_components(P)) for n in c}
ing0 = dest[0]["ingressi"][0]["aggancio"]; ag = civ[civ.stato != "insufficient_data"]
def stato_polo(r): return "reachable" if r.componente == ing0["componente"] else ("forbidden" if lab[r.snap_u] == lab[ing0["u"]] else "isolated")
ag_stato = [stato_polo(r) for r in ag.itertuples()]
pc = lambda a, q: float(np.percentile(a, q)) if len(a) else None
rep = {"parametri": {"origini_max_m": MAXO, "ingressi_max_m": MAXI, "candidati": NC_O, "destinazione_di_riferimento": dest[0]["destination_id"], "ingresso_di_riferimento": dest[0]["ingresso_predefinito"]},
       "origini_totali_riquadro": len(civ), "per_tipo_civico": dict(collections.Counter(civ.TIPO)), "agganciate": len(ag), "non_agganciate_insufficient_data": int((civ.stato == "insufficient_data").sum()),
       "stato_rispetto_al_polo": {"reachable": ag_stato.count("reachable"), "forbidden": ag_stato.count("forbidden"), "isolated": ag_stato.count("isolated"), "insufficient_data": int((civ.stato == "insufficient_data").sum())},
       "non_agganciate_motivi": dict(collections.Counter(civ[civ.stato == "insufficient_data"].motivo.str.replace(r"\d+ m", "N m", regex=True))),
       "distanza_arco_piu_vicino_senza_vincoli_m": {f"p{q}": round(pc(raw, q), 1) for q in (50, 75, 90, 95, 99)} | {"max": round(float(raw.max()), 1)},
       "raccordo_registrato_m": {f"p{q}": round(pc(ag.raccordo_m.astype(float), q), 1) for q in (50, 75, 90, 95, 99)} | {"max": round(float(ag.raccordo_m.max()), 1)},
       "civici_oltre_20_m": int((ag.raccordo_m.astype(float) > 20).sum()), "civici_primo_candidato_scartato": int((civ.scartati_prima > 0).sum()),
       "per_componente": dict(collections.Counter(ag.componente)), "agganciati_a_componenti_isolate": int((ag.componente != "cmp_01").sum()),
       "per_tipo_arco_agganciato": dict(collections.Counter(G.edges[(r["u"], r["v"], r["edge_id"])]["tipo_arco"] for r in res if r["stato"] == "agganciato")),
       "per_marciapiede_arco_agganciato": dict(collections.Counter(G.edges[(r["u"], r["v"], r["edge_id"])]["marciapiede_stato"] for r in res if r["stato"] == "agganciato")),
       "destinazioni": [{"id": d["destination_id"], "ingressi": [{"id": e["entrance_id"], "classe": e["classe"], "stato": e["aggancio"]["stato"], "raccordo_m": e["aggancio"].get("dist_m"), "componente": e["aggancio"].get("componente")} for e in d["ingressi"]],
                         "schede_barriere": len(d.get("barriere_comune", {}).get("schede", []))} for d in dest]}
json.dump(rep, open(RES / "snapping_report.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False, indent=1))
