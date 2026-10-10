"""F08: congela la baseline (scenarios/firenze_novoli/baseline.json) e costruisce gli scenari dimostrativi S0, S1 (e varianti di sensibilità), S2 su Firenze Novoli.
Idempotente: la baseline e gli scenari esistenti non si riscrivono (sono immutabili); con contenuto diverso si ferma.
Uso: pipeline/.venv/bin/python scenarios/costruisci.py

Regole degli scenari (dichiarate prima di guardare i risultati dei confronti, non scelte per far 'vincere' qualcosa):
 S0  nessun intervento = baseline.
 S1  filare di alberi di dimensione tipica (classe 'medio', valori tipici di geometry/parametri_chiome.json) sul tratto di 60 m di R01 (fermata T2 San Donato - Università ->
     ingresso del Polo più vicino per rete; versione 3, D19-D20) più esposto al sole a mezzogiorno del 15 luglio 2026: massima frazione media al sole nelle fasce 12:30-13:30 (5 istanti da 15 min,
     caso con vegetazione LiDAR tipica = base di confronto principale, asse della rete, campioni a 1 m; a parità, massima esposizione media 8-18 ogni ora; poi la prima
     lungo il percorso), escluse le finestre che toccano attraversamenti, ponti, sottopassi o scale. Interasse 8 m, 7 alberi centrati nel tratto.
     Lato: il lato dal quale arriva il sole alle 13:00 del 15 luglio. Posizione (versione 2): ogni albero sul punto più vicino all'asse, fra 1,5 e 5 m, che cade
     dentro le aree di circolazione pedonale del Comune ristrette di 0,5 m e fuori dagli edifici; sono valide solo le finestre dove tutti e 7 gli alberi trovano posto.
     La versione 1 metteva gli alberi a 3 m fissi dall'asse: su Via di Novoli cadevano fra la carreggiata e i binari della T2 (correzione del 10 ottobre 2026).
     La versione 3 applica la stessa regola al nuovo R01, che parte dalla fermata indicata dall'Ateneo (prima partiva da Torre degli Agli).
     Varianti di sensibilità: chioma minima, chioma massima. La variante 'lato opposto' della versione 1 è tolta: il lato ora viene dalle aree pedonali del Comune
     (sul tratto scelto, dall'altro lato non c'è area pedonale fra 1,5 e 5 m).
     Il 15 settembre è riportato come seconda data, con lo stesso filare.
 S2  una pensilina 6 m x 2 m (intradosso 2,5 m, tetto 3,0 m) alla fermata bus "Guidoni Barsanti" (OSM nod_osm_5760828088, shelter=no). Versione 2 (10 ottobre 2026).
     Regola: fra le fermate bus del riquadro senza pensilina in OSM, la più vicina in linea d'aria a un ingresso del Polo dove, entro 8 m dal punto OSM, una fascia
     di 6 m x 3,5 m (pensilina più 1,5 m di passaggio libero) parallela alla strada più vicina sta tutta dentro le aree di circolazione pedonale del Comune,
     ad almeno 1,3 m dall'asse delle piste ciclabili e fuori dagli edifici; la pensilina occupa i 2 m della fascia dal lato della strada.
     Verifica a vista su Street View (immagini 2026): Forlanini Polo Scienze Sociali (versione 1, 55 m dal Polo) non ha spazio, la pensilina cadeva sulla ciclabile;
     Del Prete Terzolle ha già una pensilina (OSM non aggiornato); Del Prete Caciolle ha un marciapiede di circa 2,5 m; Guidoni Barsanti ha solo la palina su un
     marciapiede largo. Le due fermate T2 di Novoli hanno già la pensilina (campo pensilina=1 del dataset del Comune sulle fermate tram).
     Gli id storici (scn_fi_s2_pensilina_attesa_polo, sfc_fi_attesa_polo, area_attesa_polo) restano: la fermata non è più quella del Polo (529 m dall'ingresso più vicino).
     Con i 7 ingressi degli edifici (D19) la regola è stata rifatta su tutte le fermate senza pensilina in OSM: Guidoni Barsanti resta la più vicina con spazio.
 S3  (non creato) filare di 7 alberi su R02 con la regola di S1: R02 ha una sola finestra valida (481-541 m), sul tratto finale in comune con R01; gli alberi coincidono con quelli di S1 entro 0,3 m.
 S4  (non creato) filare con la regola di S1 sul percorso verso la scuola Vamba (R09 dalla fermata T2 Torre degli Agli, poi R08) o sulla linea dei 15 archi più usati verso la fermata T2:
     nessuna finestra dove tutti e 7 gli alberi trovano posto.
 S5, S6  pensilina 6 m x 2 m alla seconda e alla terza fermata della regola di S2 (fermate_pensilina, 10 ottobre 2026): Regione Toscana (OSM nod_osm_6027223967) e Di Novoli Sn
     (OSM nod_osm_3216618875). Scelte solo dai dati, senza controllo a vista su Street View. Ognuna ha la sua area di attesa (sfc_fi_attesa_s5, sfc_fi_attesa_s6) fra i ricevitori:
     baseline degli scenari ricongelata aggiungendo solo queste due aree."""
import json, math, pathlib, sys
from functools import lru_cache
import numpy as np, pyogrio, shapely
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S
from scenari import O, ROOT, SC, sha_file

CREATED = "2026-10-10T12:00:00Z"
DATE = ["2026-07-15", "2026-09-15"]
DATA_SCELTA = DATE[0]
FASCE = [{"id": "punta_12_30_13_30", "from": "12:30", "to": "13:30"}, {"id": "giornata_8_19", "from": "08:00", "to": "19:00"}]   # come shadow/run.py (F07)
ORARI = [f"{m // 60:02d}:{m % 60:02d}" for m in range(8 * 60, 19 * 60 + 1, 30)]   # come shadow/run.py (F07)
ROTTE = ["R01", "R02"]
POLO, FERMATA_T2 = "dst_university_w83537185", "dst_tram_fm9055"   # San Donato - Università, la fermata indicata dall'Ateneo (D20)
PIATTAFORMA_ATTESA = (679084.04, 4851684.4)   # nod_osm_5760828088 (fermata bus Guidoni Barsanti, shelter=no, check_date:shelter 2024-04-25), osm_firenze.gpkg
FERMATA_ATTESA = "Guidoni Barsanti (OSM nod_osm_5760828088, shelter=no; solo palina su Street View 2026)"
PASSAGGIO_LIBERO_M, DISTANZA_CICLABILE_M, RAGGIO_FERMATA_M = 1.5, 1.3, 8.0   # ipotesi: passaggio pedonale minimo, metà di una ciclabile da 2,6 m, distanza massima dal punto OSM
N_ARCHI = 15
FINESTRA_M, INTERASSE_M, N_ALBERI = 60.0, 8.0, 7
OFFSET_MIN_M, OFFSET_MAX_M, PASSO_OFFSET_M = 1.5, 5.0, 0.25   # ipotesi: oltre 1,5 m la linea di cammino resta libera; oltre 5 m l'albero non è più lungo il percorso
MARGINE_AREA_M = 0.5   # ipotesi: tronco ad almeno 0,5 m dal bordo dell'area pedonale (formella)
VERSIONE_S1 = 3
PENSILINA = {"lunghezza_m": 6.0, "profondita_m": 2.0, "intradosso_m": 2.5, "tetto_m": 3.0}
CLASSE = "medio"
ID = {"s0": "scn_fi_s0_baseline", "s1": "scn_fi_s1_filare_r01", "min": "scn_fi_s1v_chioma_min", "max": "scn_fi_s1v_chioma_max",
      "s2": "scn_fi_s2_pensilina_attesa_polo", "s5": "scn_fi_s5_pensilina_regione_toscana", "s6": "scn_fi_s6_pensilina_di_novoli"}
SCARTATE_A_VISTA = {"nod_osm_3273664407": "Del Prete Terzolle: ha già una pensilina su Street View 2026 (OSM non aggiornato)"}   # Forlanini Polo e Del Prete Caciolle non hanno posto già per la regola
ALTRE_PENSILINE = [("s5", "sfc_fi_attesa_s5", "seconda"), ("s6", "sfc_fi_attesa_s6", "terza")]   # S5 e S6: la seconda e la terza fermata della regola di S2 (S2 è la prima)


@lru_cache(maxsize=1)
def fermate_pensilina():
    """Regola di S2 su tutte le fermate: fermate bus OSM del riquadro con shelter=no, ordinate per distanza in linea d'aria dall'ingresso del Polo più vicino;
    restano quelle dove la fascia 6 x 3,5 m trova posto (posto_pensilina), tolte le SCARTATE_A_VISTA. Ritorna [(distanza_m, id OSM, nome, (x, y))]."""
    import geopandas as gpd
    from pyproj import Transformer
    to = Transformer.from_crs(4326, 7791, always_xy=True)
    ing = np.array([to.transform(*f["geometry"]["coordinates"]) for f in json.loads((ROOT / f"network/{O.SLUG}/destinazioni_ingressi.geojson").read_text())["features"]
                    if f["properties"].get("destinazione") == POLO])
    pt = gpd.read_file(ROOT / "data/norm" / O.SLUG / "osm_firenze.gpkg", layer="points"); x0, y0, x1, y1 = O.RIQUADRO_EN; out = []
    for _, r in pt.iterrows():
        t = json.loads(r.tags); x, y = round(r.geometry.x, 2), round(r.geometry.y, 2)
        if t.get("highway") != "bus_stop" or t.get("shelter") != "no" or r.id in SCARTATE_A_VISTA or not (x0 <= x <= x1 and y0 <= y <= y1): continue
        out.append((round(float(np.hypot(ing[:, 0] - x, ing[:, 1] - y).min()), 1), r.id, t.get("name"), (x, y)))
    return [c for c in sorted(out) if posto_pensilina(c[3], False)]


def rettangolo(centro, u, lungo, largo):
    """Rettangolo centrato in `centro` con lato lungo `lungo` lungo il versore u e `largo` lungo la normale."""
    n = np.array([-u[1], u[0]]); c = np.array(centro)
    return Polygon([c + sgn_a * lungo / 2 * u + sgn_b * largo / 2 * n for sgn_a, sgn_b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


@lru_cache(maxsize=None)
def posto_pensilina(piattaforma=PIATTAFORMA_ATTESA, obbligatorio=True):
    """Impronta della pensilina alla fermata `piattaforma` (regola di S2 nel docstring del modulo). Ritorna (poligono, versore del lato lungo, edge_id della strada di riferimento);
    None se la fascia non trova posto e obbligatorio=False."""
    G = S._grafo(); p = np.array(piattaforma); pt = Point(p); E = [e for _, _, e in G.edges(data=True)]
    st = min((e for e in E if e["tipo_arco"] == "strada"), key=lambda e: e["geom"].distance(pt)); g = st["geom"]; k = g.project(pt)
    a, b = g.interpolate(max(k - 3, 0)), g.interpolate(min(k + 3, g.length)); u = np.array([b.x - a.x, b.y - a.y]); u /= np.linalg.norm(u); n = np.array([-u[1], u[0]])
    ped = shapely.union_all(pyogrio.read_dataframe(S.AREE_PEDONALI).geometry.values); v = O.dati()["v"]; bld = shapely.union_all(v[v.tipo != "copertura_osm"].geometry.values)   # come S._contesto_geo, senza la baseline
    cyc = shapely.union_all([e["geom"] for e in E if e.get("highway") == "cycleway"]); L, D = PENSILINA["lunghezza_m"], PENSILINA["profondita_m"]
    best = None
    for aa in np.arange(-RAGGIO_FERMATA_M, RAGGIO_FERMATA_M + 1e-9, 0.25):
        for bb in np.arange(-RAGGIO_FERMATA_M, RAGGIO_FERMATA_M + 1e-9, 0.25):
            if math.hypot(aa, bb) > RAGGIO_FERMATA_M: continue
            c = p + aa * u + bb * n; fascia = rettangolo(c, u, L, D + PASSAGGIO_LIBERO_M)
            if ped.contains(fascia) and fascia.distance(cyc) >= DISTANZA_CICLABILE_M and not fascia.intersects(bld) and (best is None or math.hypot(aa, bb) < best[0]):
                best = (math.hypot(aa, bb), c)
    if not best and not obbligatorio: return None
    assert best, "nessun posto per la pensilina alla fermata scelta"
    c = best[1]; verso = 1 if g.distance(Point(c + n)) < g.distance(Point(c - n)) else -1   # verso la strada
    return rettangolo(c + verso * n * PASSAGGIO_LIBERO_M / 2, u, L, D), u, st["edge_id"]


def archi_usati():
    """Primi N_ARCHI archi 'piu_usati' di F06 verso il Polo e verso la fermata T2 (profilo base), uniti per edge_id."""
    archi, ordine = {}, []
    for dest in (POLO, FERMATA_T2):
        fc = json.loads((ROOT / f"analysis/{O.SLUG}/accessibilita_{dest}.geojson").read_text())
        top = [f["properties"] for f in fc["features"] if f["properties"].get("gruppo") == "piu_usati"][:N_ARCHI]
        for pr in top:
            if pr["id"] not in archi: archi[pr["id"]] = {"edge_id": pr["id"], "n_origini": {}}; ordine.append(pr["id"])
            archi[pr["id"]]["n_origini"][dest] = pr["n_origini"]
    return [{"receiver_id": f"edg_f06_{i + 1:02d}", **archi[e]} for i, e in enumerate(ordine)]


def congela_baseline():
    import accessibilita as A
    p = SC / "baseline.json"
    SC.mkdir(parents=True, exist_ok=True)
    bas = json.loads((ROOT / "pipeline/baselines" / f"{S.BASELINE_ID}.json").read_text())
    snapshot = []
    for sid in sorted({s["snapshot_id"] for s in bas["snapshot"]}):
        s = json.loads((ROOT / "pipeline/snapshots" / f"{sid}.json").read_text()); snapshot.append({"snapshot_id": sid, "source_id": s["source_id"], "sha256": s["sha256"], "license_state": s["license_state"]})
    man = json.loads((ROOT / "network" / O.SLUG / "rete_manifest.json").read_text())
    D = O.dati(); veg = O.vegetazione_lidar()
    import rete_lib as RL
    grafo = RL.OUT / f"{RL.STEM}.pkl"; rel = S.rel
    arc = archi_usati()
    assert 2 + 1 + len(ALTRE_PENSILINE) + len(arc) <= 50, "troppi ricevitori per compute_shadow (massimo 50)"
    pens, u, edge_strada = posto_pensilina()
    attesa = pens.buffer(1.0, join_style=2)
    prof = {"speed_m_s": 1.2, "crossing_penalty_s": 0, "stairs": "allowed"}; ref = {}
    for q in sorted((A.OUT_VERS / "manifest").glob("job_*.job.json")):
        j = json.loads(q.read_text()); pr = j["params"]
        if j["tool"] == "compute_walk_access" and pr["profile"] == {**prof, "snap_limit_m": 40.0} and pr["thresholds_min"] == [5.0, 10.0, 15.0] and pr["destination_ids"][0] in (POLO, FERMATA_T2):
            ref[pr["destination_ids"][0]] = {"job_id": j["job_id"], "entrance_ids": pr["entrance_ids"]}
    assert set(ref) == {POLO, FERMATA_T2}, ref
    b = {"baseline_id": S.BASELINE_ID, "version": 1, "frozen_at": CREATED, "aoi_id": S.AOI_ID,
         "descrizione": "Stato congelato di snapshot, grafo, geometrie, vegetazione LiDAR, motori e condizioni su cui ogni scenario aggiunge SOLO gli interventi dichiarati. "
                        "Ostacoli di riferimento: edifici documentati, alberi censiti e vegetazione LiDAR (base di confronto principale); sensibilità sulle altezze degli edifici e sulle chiome.",
         "snapshot": snapshot,
         "grafo": {"graph_id": man["graph_id"], "file": rel(grafo), "sha256": sha_file(grafo), "regole": "network/regole.json", "regole_sha256": sha_file(ROOT / "network/regole.json"),
                   "archi": man["archi"], "nodi": man["nodi"]},
         "geometrie": {"file": rel(O.GPKG), "sha256": sha_file(O.GPKG), "parametri_chiome": "geometry/parametri_chiome.json", "parametri_chiome_sha256": sha_file(ROOT / "geometry/parametri_chiome.json"),
                       "volumi_usati": len(D["v"]), "alberi_esistenti_disponibili": len(D["a"])},
         "vegetazione_lidar": {"file": rel(O.VEG_GPKG), "poligoni_sha256": D["veg_sha256"], "cluster_usati": len(veg), "frazione_z_lo_di_h95": O.VEG_FRAZIONE,
                               "nota": "hash del contenuto dei poligoni (il file GeoPackage non è identico byte per byte a ogni ricostruzione)"},
         "motori": {"ombre": {"name": "geometric_ray", "version": O.VERSIONE, "file": "shadow/ombre.py", "file_sha256": sha_file(ROOT / "shadow/ombre.py")},
                    "accessibilita": {"name": "shortest_path_walk_time", "version": A.VERSIONE, "file": "analysis/accessibilita.py", "file_sha256": sha_file(ROOT / "analysis/accessibilita.py")}},
         "origini": {"kind": "address_points", "file": rel(RL.OUT / "origini_snap.gpkg"), "sha256": sha_file(RL.OUT / "origini_snap.gpkg"),
                     "nota": "civici del Comune di Firenze (punti d'indirizzo, non residenti): le quote sono quote di civici"},
         "accessibilita_riferimento": {"profilo": prof, "snap_limit_m": 40, "soglie_min": [5, 10, 15], "job": ref},
         "ricevitori": {"percorsi_file": f"network/{O.SLUG}/percorsi_campione.geojson", "percorsi_sha256": sha_file(ROOT / f"network/{O.SLUG}/percorsi_campione.geojson"), "route_ids": ROTTE,
                        "archi_usati": {d: {"file": f"analysis/{O.SLUG}/accessibilita_{d}.geojson", "sha256": sha_file(ROOT / f"analysis/{O.SLUG}/accessibilita_{d}.geojson")} for d in (POLO, FERMATA_T2)},
                        "archi": arc,
                        "archi_nota": f"primi {N_ARCHI} archi per destinazione (Polo e fermata T2 San Donato - Università) di archi_piu_usati (F06, profilo 1,2 m/s); n_origini = civici che li usano (non persone, nessun flusso misurato)",
                        "area_attesa": {"receiver_id": "sfc_fi_attesa_polo", "kind": "surface", "descrizione": f"area di attesa della fermata bus {FERMATA_ATTESA}: "
                                        f"impronta della pensilina S2 allargata di 1 m per lato (8 m x 4 m), parallela alla strada {edge_strada}", "geometry": mapping(shapely.set_precision(attesa, 0.01))},
                        "aree_attesa_altre": aree_attesa_altre(),
                        "aree_attesa_altre_nota": "aggiunte il 10 ottobre 2026 per le pensiline S5 e S6: baseline ricongelata, tutto il resto identico al record precedente (controllato da costruisci.py)"},
         "condizioni": {"date": DATA_SCELTA, "dates": DATE, "timezone": "Europe/Rome", "times": ORARI, "fasce": FASCE,
                        "method": {"name": "geometric_ray", "space_step_m": 1.0, "time_step_min": 5.0}, "walk_speed_m_s": 1.2, "el_min_deg": 5.0,
                        "nota": "stesse date, fasce, orari, passi e velocità di shadow/run.py (F07); il 15 luglio è la data di scelta del tratto di S1"},
         "limiti": ["Percorsi sull'asse della rete: il lato del marciapiede non è noto.",
                    "Ombra binaria da edifici documentati, alberi censiti e vegetazione LiDAR; nessuna conversione in gradi, comfort o domanda pedonale.",
                    "Civici del Comune non sono residenti; nessun flusso pedonale misurato; velocità 1,2 m/s ipotesi.",
                    "Nessuna validazione locale."]}
    b = json.loads(json.dumps(b, ensure_ascii=False))   # tuple -> liste, come nel file
    if p.exists():
        old = json.loads(p.read_text())
        if old == b: return old
        nuove = ("aree_attesa_altre", "aree_attesa_altre_nota")   # ricongelamento ammesso solo per aggiungere le aree di attesa di S5 e S6
        senza = lambda x: {**x, "ricevitori": {k: v for k, v in x["ricevitori"].items() if k not in nuove}}
        assert senza(old) == senza(b), "baseline.json: il record esistente differisce oltre alle aree di attesa nuove (baseline immutabile)"
        print("baseline ricongelata: aggiunte le aree di attesa", [a["receiver_id"] for a in b["ricevitori"]["aree_attesa_altre"]], "(resto identico)")
    p.write_text(json.dumps(b, ensure_ascii=False, indent=1)); return b


def aree_attesa_altre():
    """Ricevitori delle pensiline S5 e S6: impronta allargata di 1 m per lato, come l'area di attesa di S2."""
    f = fermate_pensilina(); assert f[0][3] == PIATTAFORMA_ATTESA, f"la regola di S2 non sceglie più Guidoni Barsanti: {f[0]}"; out = []
    for i, (k, rid, n) in enumerate(ALTRE_PENSILINE, 1):
        d, oid, nome, xy = f[i]; pens, u, edge = posto_pensilina(xy)
        out.append({"receiver_id": rid, "kind": "surface", "scenario": ID[k], "descrizione": f"area di attesa della fermata bus {nome} (OSM {oid}, shelter=no), {n} della regola di S2 a {d:g} m da un ingresso del Polo: "
                    f"impronta della pensilina {k.upper()} allargata di 1 m per lato (8 m x 4 m), parallela alla strada {edge}", "geometry": mapping(shapely.set_precision(pens.buffer(1.0, join_style=2), 0.01))})
    return out


def op_albero(i, xy, dim, classe):
    src = f"classe scenario '{CLASSE}', valore {classe} di geometry/parametri_chiome.json (stima di classe, non misura né progetto)"
    return {"op_id": f"op_albero_{i:02d}", "op": "add", "target_type": "tree", "geometry": {"type": "Point", "coordinates": [round(xy[0], 2), round(xy[1], 2)]},
            "dimensions": {k: {"value": v, "unit": "m", "classification": "scenario", "dimension_source": src} for k, v in dim.items()},
            "hypothesis_status": "feasibility_unknown", "note": "Fattibilità ignota: sottoservizi, spazio radicale, proprietà del suolo e specie non verificati."}


def dimensioni_classe(caso):
    c = json.loads((ROOT / "geometry/parametri_chiome.json").read_text())["classi"][CLASSE]
    h, d, imp = {"min": ("min", "min", "max"), "tipico": ("tipico",) * 3, "max": ("max", "max", "min")}[caso]
    H, D, I = c["altezza_m"][h], c["diametro_chioma_m"][d], c["altezza_imposta_m"][imp]
    return {"height_m": H, "crown_diameter_m": D, "crown_base_m": min(I, 0.5 * H)}   # imposta <= metà altezza, come F07


def trova_tratto(b, rotta="R01", linea=None, archi=None):
    """Tratto di FINESTRA_M del percorso campione `rotta` (R01 per S1) con massima frazione media al sole nelle fasce di mezzogiorno, fra quelli dove tutti gli N_ALBERI trovano posto (posto_albero).
    Con `linea` e `archi` (edge_id) usa quella linea al posto del percorso campione. Ritorna dict con s0, s1, sole_medio, passi."""
    cond = b["condizioni"]; L = S.linea_percorso(rotta) if linea is None else linea
    lat, lon = O.SOLE_LAT, O.SOLE_LON
    n = int(L.length); s = np.arange(n) + 0.5; pt = shapely.line_interpolate_point(L, s); x, y = shapely.get_x(pt), shapely.get_y(pt)
    scena = O.scena_caso("veg_lidar_tipico"); fin = box(*L.bounds).buffer(1.0); orari = ["12:30", "12:45", "13:00", "13:15", "13:30"]; om = np.zeros(n)
    for t in orari:
        st, az, el, U = O.ombra_a_istante(scena, O.locale_a_utc(DATA_SCELTA, t), lat, lon, cond["el_min_deg"], fin)
        om += shapely.contains_xy(U, x, y) if U is not None and not U.is_empty else 0
    sole = 1 - om / len(orari)
    giorno = np.zeros(n); ore = [f"{h:02d}:00" for h in range(8, 19)]   # spareggio: esposizione media 8-18 (ogni ora)
    for t_ in ore:
        st, az, el, U = O.ombra_a_istante(scena, O.locale_a_utc(DATA_SCELTA, t_), lat, lon, cond["el_min_deg"], fin)
        giorno += shapely.contains_xy(U, x, y) if U is not None and not U.is_empty else 0
    giorno = 1 - giorno / len(ore)
    # archi del percorso da escludere: attraversamenti, ponti, sottopassi, scale
    G = S._grafo(); geo = {e["edge_id"]: e for _, _, e in G.edges(data=True)}
    pc = {"archi": archi} if linea is not None else [r for r in json.loads((ROOT / f"network/{O.SLUG}/percorsi_campione.json").read_text()) if r["id"] == rotta][0]
    esc = [geo[e]["geom"] for e in pc["archi"] if e in geo and (geo[e]["tipo_arco"] in ("attraversamento", "ponte", "sottopasso", "scala") or geo[e].get("scala"))]
    bad = shapely.union_all(esc).buffer(1.0) if esc else Polygon()
    male = np.array([bad.contains(Point(a, c)) for a, c in zip(x, y)]) if not bad.is_empty else np.zeros(n, bool)
    W = int(FINESTRA_M); cs = np.concatenate([[0], np.cumsum(sole)]); cb = np.concatenate([[0], np.cumsum(male)])
    cg = np.concatenate([[0], np.cumsum(giorno)])
    sun, _ = sole_13(lat, lon); posto = {sk: posto_albero(L, sk, sun) is not None for sk in range(n + 1)}   # stazioni a metri interi: mid = i + W/2, interasse intero
    stazioni = lambda i: [i + W // 2 + k * int(INTERASSE_M) for k in range(-(N_ALBERI // 2), N_ALBERI // 2 + 1)]
    pieno = [all(posto.get(sk, False) for sk in stazioni(i)) for i in range(n - W + 1)]
    punteggi = [((round((cs[i + W] - cs[i]) / W, 9), round((cg[i + W] - cg[i]) / W, 9)) if cb[i + W] - cb[i] == 0 and pieno[i] else (-1, -1)) for i in range(n - W + 1)]
    i0 = max(range(len(punteggi)), key=lambda i: (punteggi[i], -i))   # massimo a mezzogiorno, poi sull'intera giornata, poi la prima lungo il percorso
    return {"s0": i0, "s1": i0 + W, "sole_medio": float(punteggi[i0][0]), "sole_giorno": float(punteggi[i0][1]), "sole_medio_R01": float(sole.mean()), "finestre_valide": int(sum(1 for p in punteggi if p[0] >= 0)),
            "finestre_pari_a_mezzogiorno": int(sum(1 for p in punteggi if p[0] == punteggi[i0][0])), "finestre_senza_posto": int(sum(1 for i, p in enumerate(pieno) if not p and cb[i + W] - cb[i] == 0)), "L": L, "lat": lat, "lon": lon, "sole_t": sole}


@lru_cache(maxsize=1)
def _suolo():
    """Aree di circolazione pedonale del Comune ristrette di MARGINE_AREA_M (dove un tronco può stare) ed edifici della baseline, preparati."""
    ped = shapely.union_all(pyogrio.read_dataframe(S.AREE_PEDONALI).geometry.values).buffer(-MARGINE_AREA_M); bld = shapely.union_all(S._contesto_geo()["bld"])
    shapely.prepare(ped); shapely.prepare(bld); return ped, bld


def posto_albero(L, sk, sun, opposto=False):
    """Posto di un albero alla progressiva sk di L: punto più vicino all'asse fra OFFSET_MIN_M e OFFSET_MAX_M sul lato del sole (o sull'opposto) dentro l'area pedonale ristretta
    e fuori dagli edifici. Ritorna (xy, lato, offset) o None se non c'è posto."""
    ped, bld = _suolo()
    a, c = L.interpolate(sk - 1.5), L.interpolate(sk + 1.5); v = np.array([c.x - a.x, c.y - a.y]); v /= np.linalg.norm(v)
    nrm = np.array([-v[1], v[0]]); p = np.array(L.interpolate(sk).coords[0]); sg = (1 if nrm @ sun >= 0 else -1) * (-1 if opposto else 1)
    for d in np.arange(OFFSET_MIN_M, OFFSET_MAX_M + 1e-9, PASSO_OFFSET_M):
        xy = p + sg * d * nrm
        if shapely.contains_xy(ped, *xy) and not shapely.contains_xy(bld, *xy): return xy, sg, float(d)
    return None


def sole_13(lat, lon):
    az, el = O.sole(O.locale_a_utc(DATA_SCELTA, "13:00"), lat, lon); return np.array([math.sin(math.radians(az)), math.cos(math.radians(az))]), (az, el)


def posizioni_filare(b, t, opposto=False):
    """Posizioni degli alberi di S1: N_ALBERI stazioni a INTERASSE_M centrate nel tratto, ognuna con posto_albero (None dove non c'è posto)."""
    L = t["L"]; mid = (t["s0"] + t["s1"]) / 2; sun, sole = sole_13(t["lat"], t["lon"])
    return [posto_albero(L, mid + k * INTERASSE_M, sun, opposto) for k in range(-(N_ALBERI // 2), N_ALBERI // 2 + 1)], sole


def scrivi(scn):
    p = SC / f"{scn['scenario_id']}.json"
    if p.exists():
        old = json.loads(p.read_text())
        assert old == scn, f"{p.name}: esiste con contenuto diverso (scenari immutabili)"
        return False
    p.write_text(json.dumps(scn, ensure_ascii=False, indent=1)); return True


def interventi_geojson(scenari):
    """interventi.geojson per la scena (EPSG:4326): Point per gli alberi nuovi (id, scenario, h, chioma_d, imposta), Polygon per le coperture (id, scenario, z_lo, z_hi)."""
    from pyproj import Transformer
    tr = Transformer.from_crs(7791, 4326, always_xy=True).transform; feats = []
    ll = lambda g: mapping(shapely.transform(g, lambda a: np.round(np.column_stack(tr(a[:, 0], a[:, 1])), 7)))
    for scn in scenari:
        for op in scn["operations"]:
            d = {k: v["value"] for k, v in op["dimensions"].items()}; g = shape(op["geometry"]); oid = f"{scn['scenario_id']}:{op['op_id']}"
            if op["target_type"] == "tree":
                pr = {"id": oid, "scenario": scn["scenario_id"], "h": d["height_m"], "chioma_d": d["crown_diameter_m"], "imposta": d["crown_base_m"]}
            else:
                pr = {"id": oid, "scenario": scn["scenario_id"], "z_lo": d["canopy_base_m"], "z_hi": d["roof_height_m"]}
            feats.append({"type": "Feature", "geometry": ll(g), "properties": pr})
    return {"type": "FeatureCollection", "features": feats}


def main():
    b = congela_baseline(); t = trova_tratto(b); L = t["L"]
    def nuovo(sid, titolo, ops, versione=1):
        s = {"scenario_id": sid, "version": versione, "baseline_id": b["baseline_id"], "title": titolo, "author": "agente F08 (scenario dimostrativo)", "created_at": CREATED, "operations": ops}
        S.valida(s, geometrie=False); return s
    scn = [nuovo(ID["s0"], "S0 baseline: nessun intervento (delta atteso zero)", [])]
    regola = (f"regola dichiarata: tratto di {FINESTRA_M:g} m di R01 (da {t['s0']} a {t['s1']} m dall'origine) con massima frazione media al sole, 15 luglio 12:30-13:30 (a parità: media 8-18, poi la prima lungo il percorso), "
              f"caso con vegetazione LiDAR, asse della rete, solo tratti dove tutti gli alberi trovano posto; {N_ALBERI} alberi, interasse {INTERASSE_M:g} m, ognuno sul punto più vicino all'asse "
              f"fra {OFFSET_MIN_M:g} e {OFFSET_MAX_M:g} m dentro le aree di circolazione pedonale del Comune ristrette di {MARGINE_AREA_M:g} m e fuori dagli edifici")
    scartati = {}
    for sid, nome, caso in ((ID["s1"], "S1 filare di alberi tipici", "tipico"), (ID["min"], "S1v variante sensibilità: chioma minima", "min"),
                            (ID["max"], "S1v variante sensibilità: chioma massima", "max")):
        pos, sole13 = posizioni_filare(b, t); ops2 = []
        for i, x in enumerate(pos, 1):
            if x is None: scartati.setdefault(sid, []).append(i); continue   # non succede: trova_tratto tiene solo finestre dove tutti trovano posto
            ops2.append(op_albero(i, x[0], dimensioni_classe(caso), caso))
        titolo = f"{nome} su R01: {regola}; lato del sole alle 13:00"
        scn.append(nuovo(sid, titolo, ops2, VERSIONE_S1))
    def op_pensilina(xy, fermata):
        pens, u, edge = posto_pensilina(xy)
        src = "ipotesi di dimensione tipica di una pensilina da fermata (6 m x 2 m, intradosso 2,5 m, tetto 3,0 m): non da progetto"
        dims = {"roof_height_m": PENSILINA["tetto_m"], "canopy_base_m": PENSILINA["intradosso_m"], "length_m": PENSILINA["lunghezza_m"], "depth_m": PENSILINA["profondita_m"]}
        return {"op_id": "op_pensilina_01", "op": "add", "target_type": "shelter", "geometry": json.loads(json.dumps(mapping(shapely.set_precision(pens, 0.01)))),
                "dimensions": {k: {"value": v, "unit": "m", "classification": "scenario", "dimension_source": src} for k, v in dims.items()},
                "hypothesis_status": "feasibility_unknown", "note": f"Alla fermata bus {fermata}, entro {RAGGIO_FERMATA_M:g} m dal punto OSM, dentro le aree pedonali del Comune con {PASSAGGIO_LIBERO_M:g} m di passaggio libero, lato lungo parallelo alla strada {edge}. "
                                                                    "Fattibilità ignota: sottoservizi, proprietà del suolo, larghezza libera del marciapiede."}
    scn.append(nuovo(ID["s2"], "S2 pensilina alla fermata bus Guidoni Barsanti, la più vicina al Polo dove c'è posto (dimensione dichiarata)", [op_pensilina(PIATTAFORMA_ATTESA, FERMATA_ATTESA)], 2))
    f = fermate_pensilina()
    for i, (k, rid, n) in enumerate(ALTRE_PENSILINE, 1):
        d, oid, nome, xy = f[i]
        scn.append(nuovo(ID[k], f"{k.upper()} pensilina alla fermata bus {nome}, la {n} più vicina al Polo dove c'è posto con la regola di S2 (dimensione dichiarata; area di attesa {rid})",
                         [op_pensilina(xy, f"{nome} (OSM {oid}, shelter=no; scelta solo dai dati, senza controllo a vista)")]))
    for s in scn: print(("scritto " if scrivi(s) else "invariato ") + s["scenario_id"], f"({len(s['operations'])} interventi)")
    print(f"tratto R01 {t['s0']}-{t['s1']} m: sole medio {t['sole_medio']:.3f} (R01 intera {t['sole_medio_R01']:.3f}); finestre valide {t['finestre_valide']}; alberi senza posto: {scartati or 'nessuno'}")
    (SC / "tratto_s1.json").write_text(json.dumps({"regola": regola, "data_scelta": DATA_SCELTA, "s0_m": t["s0"], "s1_m": t["s1"], "sole_medio_finestra": round(t["sole_medio"], 4), "sole_medio_R01": round(t["sole_medio_R01"], 4),
                                                   "sole_medio_finestra_8_18": round(t["sole_giorno"], 4), "finestre_valide": t["finestre_valide"], "finestre_pari_a_mezzogiorno": t["finestre_pari_a_mezzogiorno"],
                                                   "finestre_senza_posto": t["finestre_senza_posto"], "versione": VERSIONE_S1, "aree_pedonali": {"file": S.rel(S.AREE_PEDONALI), "sha256": sha_file(S.AREE_PEDONALI)},
                                                   "alberi_senza_posto": scartati}, ensure_ascii=False, indent=1))
    (SC / "interventi.geojson").write_text(json.dumps(interventi_geojson([s for s in scn if s["operations"]]), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
