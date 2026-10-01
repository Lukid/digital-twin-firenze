"""T10: congela la baseline (scenarios/baseline.json) e costruisce gli scenari dimostrativi S0, S1 (e varianti di sensibilità), S2.
Idempotente: la baseline e gli scenari esistenti non si riscrivono (sono immutabili); con contenuto diverso si ferma.
Uso: pipeline/.venv/bin/python scenarios/costruisci.py

Regole degli scenari (dichiarate prima di guardare i risultati dei confronti, non scelte per far 'vincere' qualcosa):
 S0  nessun intervento = baseline.
 S1  filare di alberi di dimensione tipica (classe 'medio', valori tipici di geometry/parametri_chiome.json) sul tratto di 60 m di R01
     più esposto al sole a mezzogiorno del 15 settembre: massima frazione media al sole nelle fasce 12:30-13:30 (5 istanti da 15 min, caso base
     = edifici documentati, asse della rete, campioni a 1 m; a parità, massima esposizione media 8-18 ogni ora; poi la prima lungo il percorso), escluse le finestre che toccano attraversamenti, ponti, sottopassi o scale.
     Interasse 8 m, 7 alberi centrati nel tratto, a 3 m dall'asse. Lato: IPOTESI, il lato dal quale arriva il sole alle 13:00 (la sola ombra utile
     a mezzogiorno viene da lì). Alberi dentro edifici scartati e dichiarati. Varianti di sensibilità: chioma minima, chioma massima, lato opposto.
 S2  una pensilina 6 m x 2 m (intradosso 2,5 m, tetto 3,0 m) alla fermata Pellico (PI4390), centrata sul punto della piattaforma OSM, lato lungo
     parallelo al marciapiede disegnato su cui si trova."""
import json, math, pathlib, sys
import numpy as np, shapely
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S
from scenari import O, ROOT, SC, sha_file

CREATED = "2026-10-01T20:00:00Z"
FASCE = [{"id": "ingresso_mattina", "from": "07:45", "to": "08:30"}, {"id": "uscita_mezzogiorno", "from": "12:30", "to": "13:30"},
         {"id": "uscita_pomeriggio", "from": "16:00", "to": "16:30"}, {"id": "giornata_8_18", "from": "08:00", "to": "18:00"}]
ORARI = ["07:45"] + [f"{m // 60:02d}:{m % 60:02d}" for m in range(8 * 60, 18 * 60 + 1, 15)]   # come shadow/run.py
ROTTE = ["R01", "R03", "R04", "R05", "R06", "R07", "R08"]
PIATTAFORMA_PELLICO = (612592.17, 4840664.0)   # ent_osm_n7852588815 (piattaforma OSM della fermata PI4390), network/destinazioni.json
FINESTRA_M, INTERASSE_M, OFFSET_M, N_ALBERI = 60.0, 8.0, 3.0, 7
PENSILINA = {"lunghezza_m": 6.0, "profondita_m": 2.0, "intradosso_m": 2.5, "tetto_m": 3.0}
CLASSE = "medio"


def rettangolo(centro, u, lungo, largo):
    """Rettangolo centrato in `centro` con lato lungo `lungo` lungo il versore u e `largo` lungo la normale."""
    n = np.array([-u[1], u[0]]); c = np.array(centro)
    return Polygon([c + sgn_a * lungo / 2 * u + sgn_b * largo / 2 * n for sgn_a, sgn_b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def direzione_marciapiede():
    """Versore del segmento del marciapiede disegnato più vicino alla piattaforma della fermata."""
    G = S._grafo(); p = Point(PIATTAFORMA_PELLICO)
    e = min((e for _, _, e in G.edges(data=True)), key=lambda e: e["geom"].distance(p))
    g = e["geom"]; s = g.project(p); a, b = g.interpolate(max(s - 2, 0)), g.interpolate(min(s + 2, g.length))
    v = np.array([b.x - a.x, b.y - a.y]); return v / np.linalg.norm(v), e["edge_id"]


def congela_baseline():
    import accessibilita as A
    p = SC / "baseline.json"
    if p.exists(): return json.loads(p.read_text())
    snaps = sorted(set(O.SNAPSHOT_IDS["edifici"] + O.SNAPSHOT_IDS["alberi"] + ["snp_osm_pisa_20261001", "snp_sit_civici_20261001", "snp_gtfs_at_toscana_20261001"]))
    snapshot = []
    for sid in snaps:
        s = json.loads((ROOT / "pipeline/snapshots" / f"{sid}.json").read_text()); snapshot.append({"snapshot_id": sid, "source_id": s["source_id"], "sha256": s["sha256"], "license_state": s["license_state"]})
    man = json.loads((ROOT / "network/rete_manifest.json").read_text())
    D = O.dati()
    # archi più usati (T06): primi 20 per destinazione, dedotti dal file degli asset, uniti per edge_id
    archi, ordine = {}, []
    for dest in ("battisti", "pellico"):
        fc = json.loads((ROOT / f"analysis/out/accessibilita_{dest}.geojson").read_text())
        top = [f["properties"] for f in fc["features"] if f["properties"].get("gruppo") == "piu_usati"][:20]
        for pr in top:
            if pr["id"] not in archi: archi[pr["id"]] = {"edge_id": pr["id"], "n_origini": {}}; ordine.append(pr["id"])
            archi[pr["id"]]["n_origini"][dest] = pr["n_origini"]
    arc = [{"receiver_id": f"edg_t06_{i + 1:02d}", **archi[e]} for i, e in enumerate(ordine)]
    assert 7 + 2 + 1 + len(arc) <= 50, "troppi ricevitori per compute_shadow (massimo 50)"
    u, edge_marc = direzione_marciapiede()
    attesa = rettangolo(PIATTAFORMA_PELLICO, u, PENSILINA["lunghezza_m"], PENSILINA["profondita_m"]).buffer(1.0, join_style=2)
    ref = {}
    for q in sorted((ROOT / "analysis/manifest").glob("job_*.job.json")):
        j = json.loads(q.read_text()); pr = j["params"]
        if j["tool"] == "compute_walk_access" and pr["profile"] == {"speed_m_s": 1.2, "crossing_penalty_s": 0, "stairs": "allowed", "snap_limit_m": 40.0} and pr["thresholds_min"] == [5.0, 10.0, 15.0]:
            ref[pr["destination_ids"][0]] = {"job_id": j["job_id"], "entrance_ids": pr["entrance_ids"]}
    b = {"baseline_id": S.BASELINE_ID, "version": 1, "frozen_at": CREATED, "aoi_id": S.AOI_ID,
         "descrizione": "Stato congelato di snapshot, grafo, geometrie, motori e condizioni su cui ogni scenario aggiunge SOLO gli interventi dichiarati. "
                        "Ostacoli di riferimento: edifici documentati (caso base, con sensibilità sulle altezze); alberi esistenti esclusi perché l'inventario è solo stimato e incompleto.",
         "snapshot": [{**s} for s in snapshot],
         "grafo": {"graph_id": man["graph_id"], "file": "data/norm/network/rete_z2.pkl", "sha256": sha_file(ROOT / "data/norm/network/rete_z2.pkl"),
                   "regole": "network/regole.json", "regole_sha256": sha_file(ROOT / "network/regole.json"), "archi": man["archi"], "nodi": man["nodi"]},
         "geometrie": {"file": "data/norm/geometry/geometrie_z2.gpkg", "sha256": sha_file(ROOT / "data/norm/geometry/geometrie_z2.gpkg"),
                       "parametri_chiome": "geometry/parametri_chiome.json", "parametri_chiome_sha256": sha_file(ROOT / "geometry/parametri_chiome.json"),
                       "volumi_usati": len(D["v"]), "alberi_esistenti_disponibili": len(D["a"])},
         "motori": {"ombre": {"name": "geometric_ray", "version": O.VERSIONE, "file": "shadow/ombre.py", "file_sha256": sha_file(ROOT / "shadow/ombre.py")},
                    "accessibilita": {"name": "shortest_path_walk_time", "version": A.VERSIONE, "file": "analysis/accessibilita.py", "file_sha256": sha_file(ROOT / "analysis/accessibilita.py")}},
         "origini": {"kind": "civici_sit_z2", "file": "data/norm/network/origini_snap.gpkg", "sha256": sha_file(ROOT / "data/norm/network/origini_snap.gpkg"),
                     "nota": "civici SIT di Z2 (punti d'indirizzo, non residenti): le quote sono quote di civici"},
         "accessibilita_riferimento": {"profilo": {"speed_m_s": 1.2, "crossing_penalty_s": 0, "stairs": "allowed"}, "snap_limit_m": 40, "soglie_min": [5, 10, 15], "job": ref},
         "ricevitori": {"percorsi_file": "network/percorsi_campione.geojson", "percorsi_sha256": sha_file(ROOT / "network/percorsi_campione.geojson"), "route_ids": ROTTE, "lato_R01_m": 3.0,
                        "archi_usati": {d: {"file": f"analysis/out/accessibilita_{d}.geojson", "sha256": sha_file(ROOT / f"analysis/out/accessibilita_{d}.geojson")} for d in ("battisti", "pellico")},
                        "archi": arc,
                        "archi_nota": "primi 20 archi per destinazione di archi_piu_usati (T06, profilo 1,2 m/s); n_origini = civici SIT che li usano (non persone, nessun flusso misurato)",
                        "area_attesa": {"receiver_id": "sfc_t10_pell", "kind": "surface", "descrizione": "area di attesa della fermata Pellico: impronta della pensilina S2 allargata di 1 m per lato (8 m x 4 m), "
                                        f"orientata come il marciapiede disegnato {edge_marc}", "geometry": mapping(shapely.set_precision(attesa, 0.01))}},
         "condizioni": {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ORARI, "fasce": FASCE,
                        "method": {"name": "geometric_ray", "space_step_m": 1.0, "time_step_min": 5.0}, "walk_speed_m_s": 1.2, "el_min_deg": 5.0,
                        "asset_times": ["08:00", "13:00", "16:30"], "asset_bbox": [612028.0, 4839892.0, 613234.0, 4841035.0],
                        "nota": "stesse date, fasce, passi e velocità di shadow/run.py (T09); orari 07:45 e 08:00-18:00 ogni 15 min"},
         "limiti": ["Percorsi sull'asse della rete: il lato del marciapiede non è noto (incertezza dominante di T09).",
                    "Ombra binaria da edifici documentati; nessuna conversione in gradi, comfort o domanda pedonale.",
                    "Civici SIT non sono residenti; nessun flusso pedonale misurato; velocità 1,2 m/s ipotesi.",
                    "Nessuna validazione locale."]}
    p.write_text(json.dumps(b, ensure_ascii=False, indent=1)); return b


def op_albero(i, xy, dim, classe):
    src = f"classe scenario '{CLASSE}', valore {classe} di geometry/parametri_chiome.json (stima di classe, non misura né progetto)"
    return {"op_id": f"op_albero_{i:02d}", "op": "add", "target_type": "tree", "geometry": {"type": "Point", "coordinates": [round(xy[0], 2), round(xy[1], 2)]},
            "dimensions": {k: {"value": v, "unit": "m", "classification": "scenario", "dimension_source": src} for k, v in dim.items()},
            "hypothesis_status": "feasibility_unknown", "note": "Fattibilità ignota: sottoservizi, spazio radicale, proprietà del suolo e specie non verificati."}


def dimensioni_classe(caso):
    c = json.loads((ROOT / "geometry/parametri_chiome.json").read_text())["classi"][CLASSE]
    h, d, imp = {"min": ("min", "min", "max"), "tipico": ("tipico",) * 3, "max": ("max", "max", "min")}[caso]
    H, D, I = c["altezza_m"][h], c["diametro_chioma_m"][d], c["altezza_imposta_m"][imp]
    return {"height_m": H, "crown_diameter_m": D, "crown_base_m": min(I, 0.5 * H)}   # imposta <= metà altezza, come T09


def trova_tratto(b):
    """Tratto di FINESTRA_M di R01 con massima frazione media al sole nelle fasce di mezzogiorno. Ritorna dict con s0, s1, sole_medio, lato, passi."""
    cond = b["condizioni"]; rec = S.ricevitori(); R = {r["receiver_id"]: shape(r["geometry"]) for r in rec}; L = R["pth_t04_R01"]
    allg = shapely.union_all(list(R.values())); lon, lat = __import__("pyproj").Transformer.from_crs(7791, 4326, always_xy=True).transform(allg.centroid.x, allg.centroid.y)
    lon, lat = round(lon, 4), round(lat, 4)
    n = int(L.length); s = np.arange(n) + 0.5; pt = shapely.line_interpolate_point(L, s); x, y = shapely.get_x(pt), shapely.get_y(pt)
    scena = O.scena_caso("base"); fin = box(*L.bounds).buffer(1.0); orari = ["12:30", "12:45", "13:00", "13:15", "13:30"]; om = np.zeros(n)
    for t in orari:
        st, az, el, U = O.ombra_a_istante(scena, O.locale_a_utc(cond["date"], t), lat, lon, cond["el_min_deg"], fin)
        om += shapely.contains_xy(U, x, y) if U is not None and not U.is_empty else 0
    sole = 1 - om / len(orari)
    giorno = np.zeros(n); ore = [f"{h:02d}:00" for h in range(8, 19)]   # spareggio: esposizione media 8-18 (ogni ora)
    for t_ in ore:
        st, az, el, U = O.ombra_a_istante(scena, O.locale_a_utc(cond["date"], t_), lat, lon, cond["el_min_deg"], fin)
        giorno += shapely.contains_xy(U, x, y) if U is not None and not U.is_empty else 0
    giorno = 1 - giorno / len(ore)
    # archi di R01 da escludere: attraversamenti, ponti, sottopassi, scale
    G = S._grafo(); geo = {e["edge_id"]: e for _, _, e in G.edges(data=True)}
    pc = [r for r in json.loads((ROOT / "network/percorsi_campione.json").read_text()) if r["id"] == "R01"][0]
    esc = [geo[e]["geom"] for e in pc["archi"] if e in geo and (geo[e]["tipo_arco"] in ("attraversamento", "ponte", "sottopasso", "scala") or geo[e].get("scala"))]
    bad = shapely.union_all(esc).buffer(1.0) if esc else Polygon()
    male = np.array([bad.contains(Point(a, c)) for a, c in zip(x, y)]) if not bad.is_empty else np.zeros(n, bool)
    W = int(FINESTRA_M); cs = np.concatenate([[0], np.cumsum(sole)]); cb = np.concatenate([[0], np.cumsum(male)])
    cg = np.concatenate([[0], np.cumsum(giorno)])
    punteggi = [((round((cs[i + W] - cs[i]) / W, 9), round((cg[i + W] - cg[i]) / W, 9)) if cb[i + W] - cb[i] == 0 else (-1, -1)) for i in range(n - W + 1)]
    i0 = max(range(len(punteggi)), key=lambda i: (punteggi[i], -i))   # massimo a mezzogiorno, poi sull'intera giornata, poi la prima lungo il percorso
    return {"s0": i0, "s1": i0 + W, "sole_medio": float(punteggi[i0][0]), "sole_giorno": float(punteggi[i0][1]), "sole_medio_R01": float(sole.mean()), "finestre_valide": int(sum(1 for p in punteggi if p[0] >= 0)), "finestre_pari_a_mezzogiorno": int(sum(1 for p in punteggi if p[0] == punteggi[i0][0])),
            "L": L, "lat": lat, "lon": lon, "sole_t": sole}


def posizioni_filare(b, t, lato=None):
    """Posizioni degli alberi di S1. lato: +1/-1 rispetto alla normale sinistra del verso di marcia; None = lato del sole delle 13:00."""
    L = t["L"]; mid = (t["s0"] + t["s1"]) / 2; az, el = O.sole(O.locale_a_utc(b["condizioni"]["date"], "13:00"), t["lat"], t["lon"])
    sun = np.array([math.sin(math.radians(az)), math.cos(math.radians(az))]); out = []
    for k in range(-(N_ALBERI // 2), N_ALBERI // 2 + 1):
        sk = mid + k * INTERASSE_M; a, c = L.interpolate(sk - 1.5), L.interpolate(sk + 1.5); v = np.array([c.x - a.x, c.y - a.y]); v /= np.linalg.norm(v)
        nrm = np.array([-v[1], v[0]]); p = L.interpolate(sk)
        sg = lato if lato is not None else (1 if nrm @ sun >= 0 else -1)
        out.append((np.array([p.x, p.y]) + sg * OFFSET_M * nrm, sg))
    return out, (az, el)


def scrivi(scn):
    p = SC / f"{scn['scenario_id']}.json"
    if p.exists():
        old = json.loads(p.read_text())
        assert old == scn, f"{p.name}: esiste con contenuto diverso (scenari immutabili)"
        return False
    p.write_text(json.dumps(scn, ensure_ascii=False, indent=1)); return True


def main():
    b = congela_baseline(); t = trova_tratto(b); L = t["L"]
    def nuovo(sid, titolo, ops):
        s = {"scenario_id": sid, "version": 1, "baseline_id": b["baseline_id"], "title": titolo, "author": "agente T10 (scenario dimostrativo)", "created_at": CREATED, "operations": ops}
        S.valida(s, geometrie=False); return s
    scn = [nuovo("scn_z2_s0_baseline", "S0 baseline: nessun intervento (delta atteso zero)", [])]
    regola = (f"regola dichiarata: tratto di {FINESTRA_M:g} m di R01 (da {t['s0']} a {t['s1']} m dall'origine) con massima frazione media al sole, 15 settembre 12:30-13:30 (a parità: media 8-18, poi la prima lungo il percorso), "
              f"caso edifici documentati, asse della rete; {N_ALBERI} alberi, interasse {INTERASSE_M:g} m, a {OFFSET_M:g} m dall'asse")
    scartati = {}
    for sid, nome, caso, lato_inv in (("scn_z2_s1_filare_r01", "S1 filare di alberi tipici", "tipico", False), ("scn_z2_s1v_chioma_min", "S1v variante sensibilità: chioma minima", "min", False),
                                      ("scn_z2_s1v_chioma_max", "S1v variante sensibilità: chioma massima", "max", False), ("scn_z2_s1v_lato_opposto", "S1v variante sensibilità: lato opposto", "tipico", True)):
        pos, sole13 = posizioni_filare(b, t); ops2 = []; v = S._contesto_geo()
        for i, (xy, sg) in enumerate(pos, 1):
            if lato_inv:   # lato opposto: riflessione dell'offset rispetto all'asse
                pr = L.interpolate(L.project(Point(xy))); xy = 2 * np.array([pr.x, pr.y]) - xy
            if any(g.contains(Point(xy)) for g in v["bld"]): scartati.setdefault(sid, []).append(i); continue
            ops2.append(op_albero(i, xy, dimensioni_classe(caso), caso))
        titolo = f"{nome} su R01: {regola}; lato {'opposto a quello del sole alle 13:00' if lato_inv else 'del sole alle 13:00'} (ipotesi, il lato del marciapiede non è noto)"
        scn.append(nuovo(sid, titolo, ops2))
    u, _ = direzione_marciapiede()
    pens = rettangolo(PIATTAFORMA_PELLICO, u, PENSILINA["lunghezza_m"], PENSILINA["profondita_m"])
    src = "ipotesi di dimensione tipica di una pensilina da fermata (6 m x 2 m, intradosso 2,5 m, tetto 3,0 m): non da progetto"
    dims = {"roof_height_m": PENSILINA["tetto_m"], "canopy_base_m": PENSILINA["intradosso_m"], "length_m": PENSILINA["lunghezza_m"], "depth_m": PENSILINA["profondita_m"]}
    op = {"op_id": "op_pensilina_01", "op": "add", "target_type": "shelter", "geometry": json.loads(json.dumps(mapping(shapely.set_precision(pens, 0.01)))),
          "dimensions": {k: {"value": v, "unit": "m", "classification": "scenario", "dimension_source": src} for k, v in dims.items()},
          "hypothesis_status": "feasibility_unknown", "note": "Alla fermata Pellico PI4390, centrata sulla piattaforma OSM, lato lungo parallelo al marciapiede. Fattibilità ignota: sottoservizi, proprietà del suolo, larghezza libera del marciapiede."}
    scn.append(nuovo("scn_z2_s2_pensilina_pellico", "S2 pensilina alla fermata Pellico (dimensione dichiarata)", [op]))
    for s in scn: print(("scritto " if scrivi(s) else "invariato ") + s["scenario_id"], f"({len(s['operations'])} interventi)")
    print(f"tratto R01 {t['s0']}-{t['s1']} m: sole medio {t['sole_medio']:.3f} (R01 intera {t['sole_medio_R01']:.3f}); finestre valide {t['finestre_valide']}; alberi scartati in edificio: {scartati or 'nessuno'}")
    (SC / "tratto_s1.json").write_text(json.dumps({"regola": regola, "s0_m": t["s0"], "s1_m": t["s1"], "sole_medio_finestra": round(t["sole_medio"], 4), "sole_medio_R01": round(t["sole_medio_R01"], 4),
                                                   "sole_medio_finestra_8_18": round(t["sole_giorno"], 4), "finestre_valide": t["finestre_valide"], "finestre_pari_a_mezzogiorno": t["finestre_pari_a_mezzogiorno"], "scartati_in_edificio": scartati}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
