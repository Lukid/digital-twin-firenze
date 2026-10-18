#!/usr/bin/env python3
"""F5, compito 1 (D49): quanti civici e residenti stimati arrivano al rifugio climatico più vicino camminando soprattutto all'ombra.

Per ogni civico entro 15 minuti nel job di accessibilità dei 7 rifugi (job_e1e75455f7511f7d, 1,2 m/s) si ricostruisce il suo percorso verso
l'ingresso più vicino (stessa Dijkstra di analysis/accessibilita.py, controllata riga per riga con il CSV del job) e si misura l'ombra
sull'asse del percorso all'istante delle 14:00 del 15 luglio 2026 (motore shadow/ombre.py, stessi casi di compute_shadow).
Riuso: l'ombra si misura una volta per tratto di rete (i pezzi del grafo con gli agganci) e per raccordo; un percorso somma i suoi tratti.
"Soprattutto all'ombra" = almeno il 50% del percorso in ombra (sensibilità 40% e 60%): soglia scelta da noi (D49), da validare con l'ufficio.

Indicatore di riserva (D53), meno sensibile alla soglia: quota media del percorso in ombra e minuti al sole camminando (mediana e quartili).

Lato più in ombra (F7, D60), accanto all'asse e mai al posto suo: ogni tratto del percorso va a sinistra e a destra con la distanza di shadow/lati_strada.py
(marciapiede OSM, aree stradali del Comune, 3 m dichiarati); un civico cammina tutto su un lato, quello più in ombra. Limite superiore, da verificare sul posto.

Uso: pipeline/.venv/bin/python shadow/ombra_rifugi.py [--blocco 500]
     pipeline/.venv/bin/python shadow/ombra_rifugi.py --riserva   (solo l'indicatore di riserva, dal GeoJSON dei civici già calcolato: nessun calcolo d'ombra)
     pipeline/.venv/bin/python shadow/ombra_rifugi.py --lati [--blocco 2000]   (solo il lato più in ombra: aggiunge il campo lato_piu_in_ombra al JSON;
                                                                                  da rifare dopo il calcolo completo, che riscrive il JSON senza)
Scrive: shadow/<area>/ombra_rifugi_<data>.json (numeri, metodo, limiti, tempo e memoria per blocco),
        shadow/<area>/ombra_rifugi_civici_<data>.geojson (un punto per civico entro 15 minuti, per la scena).
Guardiano: sotto 700 MB di memoria disponibile il calcolo si ferma (uscita 3)."""
import argparse, csv, json, os, statistics, sys, time
import networkx as nx, numpy as np, psutil, shapely
from shapely.geometry import LineString, Point, box, mapping
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
import ombre as O, esposizione as ESP  # noqa: E402
import accessibilita as A, residenti as RES  # noqa: E402

JOB = RES.JOB_RIFUGI
DATA, ORA = "2026-07-15", "14:00"
SOGLIE_MIN = (10, 15)
SOGLIA_OMBRA, SENS_OMBRA = 0.5, (0.4, 0.6)
CASI = ["base", "veg_lidar_min", "veg_lidar_tipico", "veg_lidar_max"]   # solo edifici; con alberi censiti e vegetazione LiDAR (caso principale e intervallo, D14)
OUT = ESP.OUT
LIMITI = [("soglia_scelta_da_noi", "La soglia di 'soprattutto all'ombra' (50% del percorso, sensibilità 40% e 60%) è una scelta nostra (D49), da validare con l'ufficio del Comune."),
          ("un_istante", "Ombra all'istante delle 14:00 del 15 luglio 2026, non lungo il cammino: chi parte alle 14 e cammina 15 minuti trova il sole poco più basso."),
          ("asse_della_rete", "Ombra misurata sull'asse della rete pedonale, non sul marciapiede: il lato della strada dove si cammina non è noto."),
          ("percorso_piu_breve", "Il percorso è il più breve per tempo verso l'ingresso del rifugio più vicino: chi cerca l'ombra può scegliere un percorso diverso, più lungo e più ombreggiato."),
          ("vegetazione_prisma", "Vegetazione LiDAR come prisma opaco pieno: limite superiore dell'ombra; alberi censiti come chiome opache."),
          ("rifugi_orari", "Orari dei rifugi non noti: un rifugio raggiunto può essere chiuso alle 14."),
          ("non_validato", "Nessuna validazione sul posto dell'ombra (verifica di R01 prevista il 12 dicembre 2026).")]


def percorsi(m):
    """Stessa Dijkstra di accessibilita.calcola: {origine: (tratti [(chiave, geometria)], raccordo origine, ingresso, tempo_s, totale_m)} per le origini raggiunte."""
    c = A.contesto(); p = m["params"]; prof = {k: v for k, v in p["profile"].items() if k != "snap_limit_m"}; w = A._peso(prof, c["orig_len"])
    ids, ents = A._ingressi(p["destination_ids"], p["entrance_ids"])
    ent = {i: (Point(ents[i]["xy"]), {**ents[i]["aggancio"], "proj": tuple(ents[i]["aggancio"]["proj"])}) for i in sorted(ids)}
    ok = {n: (pt, s) for n, (pt, s) in sorted(A.agganci_origini(p["origins"]["kind"], p["profile"]["snap_limit_m"]).items()) if s["stato"] == "agganciato"}
    sn = {f"E{i}": s for i, (pt, s) in enumerate(ent.values())}; eid = {f"snp_E{i}": k for i, k in enumerate(ent)}
    H = A.con_agganci(c["G"], {**sn, **{"o_" + n: s for n, (pt, s) in ok.items()}}); H.add_node("SRC")
    for i, (k, (pt, s)) in enumerate(ent.items()): H.add_edge("SRC", f"snp_E{i}", key=f"virt_{i}", length_m=s["dist_m"], tipo_arco="virtuale", scala=False, edge_id=f"virt_{i}")
    dist, path = nx.single_source_dijkstra(H, "SRC", weight=w); out = {}
    for n, (pt, s) in ok.items():
        nodi = path.get("snp_o_" + n)
        if nodi is None: continue
        nodi = nodi[1:]; tratti = []
        for a, b in zip(nodi, nodi[1:]):
            k, e = min(H[a][b].items(), key=lambda kv: (A._inf(A._costo(kv[1], prof, c["orig_len"])), kv[1]["edge_id"]))
            tratti.append((tuple(sorted((str(a), str(b)))) + (k,), e["geom"]))
        out[n] = (tratti, LineString([(pt.x, pt.y), s["proj"]]), eid[nodi[0]], dist["snp_o_" + n] + s["dist_m"] / prof["speed_m_s"], s["dist_m"])
    rac_d = {k: LineString([s["proj"], (pt.x, pt.y)]) for k, (pt, s) in ent.items()}
    return out, rac_d, ents


def riserva(P):
    """D53: indicatori meno sensibili alla soglia per i civici P (proprietà del GeoJSON dei civici). Minuti al sole = minuti di cammino x (1 - quota in ombra)."""
    q = lambda v, n=2: [round(float(x), n) for x in np.percentile(v, [25, 50, 75])]
    om, mi = np.array([p["ombra"] for p in P]), np.array([p["minuti"] for p in P]); r = [(p["residenti_stimati"], p["ombra"]) for p in P if p["residenti_stimati"] is not None]
    return {"ombra_media": round(float(om.mean()), 4), "ombra_media_pesata_residenti": round(sum(a * b for a, b in r) / sum(a for a, _ in r), 4),
            "ombra_media_intervallo_vegetazione": [round(float(np.mean([p["ombra_intervallo"][i] for p in P])), 4) for i in (0, 1)],
            "ombra_media_solo_edifici": round(float(np.mean([p["ombra_solo_edifici"] for p in P])), 4), "ombra_quartili": q(om, 4),
            "minuti_sole_quartili": q(mi * (1 - om)), "minuti_cammino_quartili": q(mi),
            "definizione": "quartili [primo, mediana, terzo] sui civici; minuti al sole = minuti di cammino x (1 - quota del percorso in ombra alle 14), caso con vegetazione"}


def solo_riserva():
    """Aggiunge l'indicatore di riserva al risultato già calcolato, dal GeoJSON dei civici (stessi valori arrotondati che usa main)."""
    f = OUT / f"ombra_rifugi_{DATA}.json"; R = json.loads(f.read_text())
    P = [x["properties"] for x in json.loads((OUT / f"ombra_rifugi_civici_{DATA}.geojson").read_text())["features"]]
    for x in R["soglie"]: x["riserva"] = riserva([p for p in P if p["minuti"] <= x["minuti"]])
    f.write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n")
    for x in R["soglie"]: print(x["minuti"], "min:", x["riserva"])


CASI_LATI = {"base": "solo_edifici", "veg_lidar_tipico": "con_vegetazione"}   # come shadow/lati_strada.py
LIMITI_LATI = [("limite_superiore", "Limite superiore: chi cammina sceglie sempre il lato più in ombra per tutto il percorso, senza attraversare; il valore principale resta quello sull'asse."),
               ("da_verificare", "Da verificare sul posto: nessun lato della strada è stato osservato."),
               ("distanza_del_lato", "Distanza del lato dal marciapiede OSM, altrimenti dal bordo delle aree stradali del Comune (stima nostra), altrimenti 3 m dichiarati (metri per fonte nel campo metri)."),
               ("attraversamenti_non_modellati", "Attraversamenti non modellati; raccordi e tratti pedonali restano sull'asse.")]


def _cammino(tr, ro):
    """Tratti nel verso di marcia (dal civico all'ingresso): [(indice nel percorso, True se il cammino segue il verso della geometria)]."""
    cur, out = np.array(ro.coords[-1]), []
    for i in reversed(range(len(tr))):
        c = np.array(tr[i][1].coords); avanti = np.linalg.norm(c[0] - cur) <= np.linalg.norm(c[-1] - cur)
        assert min(np.linalg.norm(c[0] - cur), np.linalg.norm(c[-1] - cur)) < 0.5, "tratti non contigui"
        out.append((i, bool(avanti))); cur = c[-1] if avanti else c[0]
    return out


def solo_lati(blocco):
    """F7 (D60): lato più in ombra sui percorsi dei civici entro 15 minuti, alle 14 del 15 luglio, come limite superiore accanto all'asse.
    Ogni tratto unico si sposta a sinistra e a destra della sua geometria (shadow/lati_strada.py, raccordi esclusi); l'ombra si misura a blocchi di tratti."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "network"))
    import lati_strada as LS, rete_lib as RL
    ESP.guardiano(); t0 = time.time()
    f = OUT / f"ombra_rifugi_{DATA}.json"; R = json.loads(f.read_text())
    m = json.loads((A.OUT_VERS / "manifest" / f"{JOB}.manifest.json").read_text())
    righe = {r["origin_id"]: r for r in csv.DictReader(open(A.ROOT / next(x["path"] for x in m["assets"] if x["asset_id"] == "ast_origini_csv")))}
    P, rac_d, _ = percorsi(m)
    dentro = sorted(o for o, r in righe.items() if r["stato"] == "reachable" and float(r["tempo_s"]) / 60 <= max(SOGLIE_MIN))
    assert len(dentro) == R["civici_entro_15_min"]
    G, _ = RL.carica()
    # pezzi da ombreggiare: per ogni tratto unico i segmenti spostati a sinistra (+1) e a destra (-1) della sua geometria; raccordi sull'asse
    tratti, racc, pezzi, lung, metri = {}, {}, [], [], {}
    for o in dentro:
        tr, ro, e, _, _ = P[o]
        for k, g in tr:
            if k in tratti: continue
            seg = LS.lati(g, G, raccordi=False); tratti[k] = {}
            for lato in (1, -1, 0):   # 0: asse, per il limite superiore max(asse, lato) e per il controllo con il calcolo sull'asse
                ix = []
                for q, _, la in LS.linea(seg, lato): ix.append(len(pezzi)); pezzi.append(q); lung.append(la)
                tratti[k][lato] = np.array(ix, dtype=int)
            metri[k] = {lato: {f: sum(float(np.linalg.norm(b - a)) for a, b, *_, fo in seg if fo != "asse" and fo.split("+")[i] == f) for f in ("osm", "aree", "default")} for i, lato in enumerate((1, -1))}
        for k, g in ((("o", o), ro), (("d", e), rac_d[e])):
            if k not in racc: racc[k] = len(pezzi); pezzi.append(g); lung.append(g.length)
    pezzi = np.array(pezzi, dtype=object); lung = np.array(lung); t_lati = time.time() - t0
    finestra = box(*shapely.total_bounds(pezzi)).buffer(1.0); ombra, blocchi = {}, []
    for caso in CASI_LATI:
        tc = time.time(); st, az, el, U = O.ombra_a_istante(O.scena_caso(caso), O.locale_a_utc(DATA, ORA), O.SOLE_LAT, O.SOLE_LON, finestra=finestra)
        assert st == O.STATO_OK, st; shapely.prepare(U); v = np.zeros(len(pezzi))
        for i in range(0, len(pezzi), blocco):
            v[i:i + blocco] = shapely.length(shapely.intersection(pezzi[i:i + blocco], U))
            blocchi.append({"caso": caso, "pezzi": int(min(blocco, len(pezzi) - i)), "memoria_disponibile_gb": round(psutil.virtual_memory().available / 2**30, 2)})
        ombra[caso] = v; del U
        print(caso, f"{time.time() - tc:.0f} s", f"memoria massima {ESP.memoria_max_gb()} GB", flush=True)
    civ, per = {}, RES.residenti_per_civico()[0]
    asse_f5 = [x["properties"] for x in json.loads((OUT / f"ombra_rifugi_civici_{DATA}.geojson").read_text())["features"]]   # stesso ordine di dentro (main)
    assert len(asse_f5) == len(dentro)
    for o in dentro:   # sinistra e destra nel verso di marcia: un tratto percorso contro il verso della geometria scambia i lati
        tr, ro, e, t, _ = P[o]; lato = {"sinistra": [], "destra": [], "asse": [tratti[k][0] for k, _ in tr]}; mt = {"sinistra": dict.fromkeys(("osm", "aree", "default"), 0.0), "destra": dict.fromkeys(("osm", "aree", "default"), 0.0)}
        for i, avanti in _cammino(tr, ro):
            k = tr[i][0]
            for nome, s in (("sinistra", 1), ("destra", -1)):
                g = s if avanti else -s; lato[nome].append(tratti[k][g])
                for fo, x in metri[k][g].items(): mt[nome][fo] += x
        for nome in lato: lato[nome] = np.concatenate(lato[nome] + [np.array([racc[("o", o)], racc[("d", e)]])])
        L = float(lung[lato["sinistra"]].sum()); assert abs(L - float(lung[lato["asse"]].sum())) < 0.01
        civ[o] = {"minuti": t / 60, "residenti": per.get(o), "metri": mt,
                  **{(nome, c): float(ombra[c][ix].sum()) / L for nome, ix in lato.items() for c in CASI_LATI}}
    # l'asse calcolato qui deve ridare quello di main (GeoJSON dei civici, arrotondato alla quarta cifra)
    scarto = max(max(abs(civ[o][("asse", "veg_lidar_tipico")] - q["ombra"]), abs(civ[o][("asse", "base")] - q["ombra_solo_edifici"])) for o, q in zip(dentro, asse_f5))
    assert scarto < 1e-3, scarto
    # controllo indipendente: il civico di RC4 (come in main) deve ridare i lati di RC4 in lati_strada.json alle 14
    c0 = A.contesto()["civ"]; f4 = next(f for f in json.load(open(A.ROOT / "network" / O.SLUG / "percorsi_campione.geojson"))["features"] if f["properties"]["id"] == "RC4")
    o4 = c0.index[np.argmin(c0.geometry.distance(Point(ESP._da_ll(*f4["geometry"]["coordinates"][0]))))]
    x4 = next(x for x in json.loads((OUT / "lati_strada.json").read_text())["percorsi"]["RC4"]["istanti"] if (x["data"], x["ora"]) == (DATA, ORA))
    controllo = {nome: {"civico": round(civ[o4][(nome, c)], 4), "lati_strada": x4[CASI_LATI[c]][nome]} for nome in ("sinistra", "destra") for c in ("veg_lidar_tipico",)}
    assert all(abs(v["civico"] - v["lati_strada"]) < 0.01 for v in controllo.values()), controllo
    con = [o for o in righe if per.get(o) is not None]; tot_res = sum(per[o] for o in con); n = len(righe)
    piu = lambda o, c: max(civ[o][("sinistra", c)], civ[o][("destra", c)], civ[o][("asse", c)])   # limite superiore: se entrambi i lati hanno meno ombra dell'asse, vale l'asse
    def conta(T, c, s):
        os_ = [o for o in dentro if civ[o]["minuti"] <= T and piu(o, c) >= s]; res = sum(civ[o]["residenti"] for o in os_ if civ[o]["residenti"] is not None)
        return {"civici": len(os_), "quota_civici": round(len(os_) / n, 4), "residenti_stimati": round(res), "quota_residenti": round(res / tot_res, 4)}
    soglie = []
    for T in SOGLIE_MIN:
        dT = [o for o in dentro if civ[o]["minuti"] <= T]
        soglie.append({"minuti": T, "soprattutto_ombra": {f"{s:.0%}": conta(T, "veg_lidar_tipico", s) for s in (SENS_OMBRA[0], SOGLIA_OMBRA, SENS_OMBRA[1])},
                       "solo_edifici": conta(T, "base", SOGLIA_OMBRA),
                       "ombra_media_lato_piu_in_ombra": round(float(np.mean([piu(o, "veg_lidar_tipico") for o in dT])), 4),
                       "ombra_mediana_lato_piu_in_ombra": round(float(np.median([piu(o, "veg_lidar_tipico") for o in dT])), 4),
                       "lato_piu_in_ombra": {k: sum(1 for o in dT if (lambda s, d: "pari" if abs(s - d) < LS.PARI else "sinistra" if s > d else "destra")(civ[o][("sinistra", "veg_lidar_tipico")], civ[o][("destra", "veg_lidar_tipico")]) == k) for k in ("sinistra", "destra", "pari")}})
    mtot = {nome: {fo: round(sum(civ[o]["metri"][nome][fo] for o in dentro)) for fo in ("osm", "aree", "default")} for nome in ("sinistra", "destra")}
    R["lato_piu_in_ombra"] = {
        "classification": "limite superiore", "stato": "da verificare sul posto",
        "valore_principale": "soglie (ombra sull'asse): il lato più in ombra si dà accanto, mai al posto suo",
        "metodo": "Ogni tratto del percorso più breve si sposta a sinistra e a destra nel verso di marcia con la distanza di shadow/lati_strada.py; un civico arriva soprattutto all'ombra "
                  "se almeno la soglia del percorso è in ombra sul suo lato più in ombra (lo stesso lato per tutto il percorso, nessun attraversamento), o sull'asse se entrambi i lati ne hanno meno. "
                  "Caso con vegetazione; solo edifici a parte.",
        "civici_con_lati_sotto_l_asse": {f"{T} min": sum(1 for o in dentro if civ[o]["minuti"] <= T and max(civ[o][("sinistra", "veg_lidar_tipico")], civ[o][("destra", "veg_lidar_tipico")]) < civ[o][("asse", "veg_lidar_tipico")]) for T in SOGLIE_MIN},
        "controllo_asse": f"ombra sull'asse ricalcolata qui uguale a quella del GeoJSON dei civici (scarto massimo {scarto:.4f})",
        "fonte_distanza": "marciapiede OSM; altrimenti bordo delle aree stradali del Comune (src_fi_aree_stradali, CC BY 4.0, stima nostra, D59); altrimenti 3 m dichiarati",
        "metri_per_fonte": {"nota": "metri di strada sommati su tutti i percorsi dei civici entro 15 minuti (un tratto conta una volta per ogni civico che lo usa)", **mtot},
        "soglie": soglie, "controllo_RC4": controllo,
        "fonti": [{"source_id": "src_fi_aree_stradali", "licenza": "CC-BY-4.0", "data_del_dato": "2025-05-26"}],
        "limits": [{"code": k, "text": t} for k, t in LIMITI_LATI],
        "calcolo": {"tratti_unici": len(tratti), "pezzi": len(pezzi), "blocco_pezzi": blocco, "secondi_lati": round(t_lati, 1), "secondi_totali": round(time.time() - t0),
                    "memoria_max_gb": ESP.memoria_max_gb(), "memoria_disponibile_min_gb": min(b["memoria_disponibile_gb"] for b in blocchi)}}
    f.write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n")
    for x in soglie: print(x["minuti"], "min:", x["soprattutto_ombra"], x["lato_piu_in_ombra"], flush=True)
    print("controllo RC4:", controllo, "calcolo:", R["lato_piu_in_ombra"]["calcolo"])


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0]); a.add_argument("--blocco", type=int, default=None); a.add_argument("--riserva", action="store_true")
    a.add_argument("--lati", action="store_true"); a = a.parse_args()
    if a.riserva: return solo_riserva()
    if a.lati: return solo_lati(a.blocco or 2000)
    a.blocco = a.blocco or 500
    ESP.guardiano()
    t0 = time.time()
    m = json.loads((A.OUT_VERS / "manifest" / f"{JOB}.manifest.json").read_text())
    righe = {r["origin_id"]: r for r in csv.DictReader(open(A.ROOT / next(x["path"] for x in m["assets"] if x["asset_id"] == "ast_origini_csv")))}
    P, rac_d, ents = percorsi(m)
    dentro = sorted(o for o, r in righe.items() if r["stato"] == "reachable" and float(r["tempo_s"]) / 60 <= max(SOGLIE_MIN))
    for o in dentro:   # stessi percorsi del job: ingresso, tempo e lunghezza
        r = righe[o]; tr, ro, e, t, _ = P[o]; L = sum(g.length for _, g in tr) + ro.length + rac_d[e].length
        assert e == r["entrance_id"] and abs(t - float(r["tempo_s"])) < 0.1 and abs(L - float(r["totale_m"])) < 0.2, (o, e, t, L, r)
    t_percorsi = time.time() - t0
    # tratti unici nell'ordine dei blocchi: ogni blocco calcola solo i tratti che non ha già visto
    blocchi = [dentro[i:i + a.blocco] for i in range(0, len(dentro), a.blocco)]
    chiavi, geoms, primo = {}, [], []
    for b, bl in enumerate(blocchi):
        for o in bl:
            tr, ro, e, _, _ = P[o]
            for k, g in tr + [(("o", o), ro), (("d", e), rac_d[e])]:
                if k not in chiavi: chiavi[k] = len(geoms); geoms.append(g); primo.append(b)
    primo = np.array(primo); finestra = box(*shapely.total_bounds(np.array(geoms, dtype=object))).buffer(1.0)
    ombra = {}; per_blocco = [{"blocco": b + 1, "civici": len(bl), "tratti_nuovi": int((primo == b).sum()), "secondi": 0.0, "memoria_max_gb": 0.0, "memoria_disponibile_min_gb": 99.0} for b, bl in enumerate(blocchi)]
    for caso in CASI:   # un caso alla volta: una sola unione delle ombre in memoria
        tc = time.time(); U = O.ombra_a_istante(O.scena_caso(caso), O.locale_a_utc(DATA, ORA), O.SOLE_LAT, O.SOLE_LON, finestra=finestra)
        st, az, el, U = U; assert st == O.STATO_OK, st; shapely.prepare(U); t_unione = time.time() - tc
        v = np.zeros(len(geoms))
        for b in range(len(blocchi)):
            tb = time.time(); ix = np.nonzero(primo == b)[0]
            v[ix] = shapely.length(shapely.intersection(np.array([geoms[i] for i in ix], dtype=object), U))
            pb = per_blocco[b]; pb["secondi"] += time.time() - tb + t_unione / len(blocchi)
            pb["memoria_max_gb"] = max(pb["memoria_max_gb"], ESP.memoria_max_gb()); pb["memoria_disponibile_min_gb"] = min(pb["memoria_disponibile_min_gb"], round(psutil.virtual_memory().available / 2**30, 2))
        ombra[caso] = v; del U
        print(caso, f"{time.time() - tc:.0f} s", f"memoria massima {ESP.memoria_max_gb()} GB", flush=True)
    for pb in per_blocco: pb["secondi"] = round(pb["secondi"], 1)
    lung = shapely.length(np.array(geoms, dtype=object))
    per, neri, *_ = RES.residenti_per_civico()
    dest_di = {e: d for d in A.contesto()["dest"].values() for e in (x["entrance_id"] for x in d["ingressi"])}
    civ = {}
    for o in dentro:
        tr, ro, e, t, _ = P[o]; ix = [chiavi[k] for k, _ in tr] + [chiavi[("o", o)], chiavi[("d", e)]]; L = float(lung[ix].sum())
        civ[o] = {"minuti": round(t / 60, 2), "lunghezza_m": round(L, 1), "rifugio": dest_di[e]["destination_id"], "ingresso": e, "residenti_stimati": per.get(o),
                  "ombra": {c: round(float(ombra[c][ix].sum()) / L, 4) if L > 0 else 0.0 for c in CASI}}
    # controllo indipendente: il civico di R05 verso il rifugio più vicino è RC4 (esposizione del compito 3 di F4, stesso istante)
    rc4 = json.loads((OUT / f"esposizione_{DATA}.json").read_text())["percorsi"]["RC4"]
    f4 = next(f for f in json.load(open(A.ROOT / "network" / O.SLUG / "percorsi_campione.geojson"))["features"] if f["properties"]["id"] == "RC4")
    c0 = A.contesto()["civ"]; o4 = c0.index[np.argmin(c0.geometry.distance(Point(ESP._da_ll(*f4["geometry"]["coordinates"][0]))))]   # civico di partenza, senza usare il suo id (D30)
    assert o4 in civ, o4
    f4 = rc4["orari"][ORA]; assert abs(civ[o4]["lunghezza_m"] - rc4["lunghezza_m"]) < 1 and abs(civ[o4]["ombra"]["veg_lidar_tipico"] - f4["frazione_ombra"]) < 0.005 \
        and abs(civ[o4]["ombra"]["base"] - f4["solo_edifici"]["frazione_ombra"]) < 0.005, (civ[o4], f4)
    # numeri
    con = [o for o in righe if per.get(o) is not None]; tot_res = sum(per[o] for o in con); n = len(righe)
    def conta(T, caso, s):
        os_ = [o for o in dentro if civ[o]["minuti"] <= T and (caso is None or civ[o]["ombra"][caso] >= s)]
        res = sum(per[o] for o in os_ if per.get(o) is not None)
        return {"civici": len(os_), "quota_civici": round(len(os_) / n, 4), "residenti_stimati": round(res), "quota_residenti": round(res / tot_res, 4)}
    soglie = []
    for T in SOGLIE_MIN:
        x = {"minuti": T, "arrivano": conta(T, None, 0), "soprattutto_ombra": conta(T, "veg_lidar_tipico", SOGLIA_OMBRA)}
        x["intervallo_vegetazione"] = {k: [conta(T, c, SOGLIA_OMBRA)[k] for c in ("veg_lidar_min", "veg_lidar_max")] for k in ("quota_civici", "quota_residenti")}
        x["sensibilita_soglia"] = {f"{s:.0%}": conta(T, "veg_lidar_tipico", s) for s in SENS_OMBRA}
        x["solo_edifici"] = conta(T, "base", SOGLIA_OMBRA)
        x["ombra_mediana"] = round(statistics.median(civ[o]["ombra"]["veg_lidar_tipico"] for o in dentro if civ[o]["minuti"] <= T), 4)
        soglie.append(x)
    feats = [{"type": "Feature", "geometry": ESP.ll(c0.geometry[o]),
              "properties": {"minuti": c["minuti"], "rifugio": c["rifugio"], "ombra": c["ombra"]["veg_lidar_tipico"], "ombra_intervallo": [c["ombra"]["veg_lidar_min"], c["ombra"]["veg_lidar_max"]],
                             "ombra_solo_edifici": c["ombra"]["base"], "soprattutto_ombra": c["ombra"]["veg_lidar_tipico"] >= SOGLIA_OMBRA,
                             "residenti_stimati": round(c["residenti_stimati"], 2) if c["residenti_stimati"] is not None else None}} for o, c in civ.items()]
    for x in soglie: x["riserva"] = riserva([f["properties"] for f in feats if f["properties"]["minuti"] <= x["minuti"]])
    t_tot = time.time() - t0
    R = {"job_accessibilita": JOB, "destination_ids": m["params"]["destination_ids"], "speed_m_s": m["params"]["profile"]["speed_m_s"], "data": DATA, "ora_locale": ORA,
         "sole": {"azimut_deg": round(az, 2), "elevazione_deg": round(el, 2)}, "versione_motore_ombra": O.VERSIONE, "baseline_id": O.BASELINE_ID,
         "ricevitore": "asse del percorso più breve (rete, raccordi compresi; lato del marciapiede non noto)",
         "soglia_ombra": SOGLIA_OMBRA, "sensibilita_soglia": list(SENS_OMBRA), "soglia_dichiarata": "scelta nostra (D49), da validare con l'ufficio del Comune",
         "casi": {"principale": "veg_lidar_tipico (edifici, alberi censiti e vegetazione LiDAR, caso tipico)", "intervallo": ["veg_lidar_min", "veg_lidar_max"], "solo_edifici": "base"},
         "civici": n, "civici_entro_15_min": len(dentro), "residenti_stimati_totali": round(tot_res), "civici_con_dato_residenti": len(con),
         "soglie": soglie, "classification": "estimated",
         "metodo": "Percorso più breve per tempo di ogni civico verso l'ingresso del rifugio più vicino (stessa Dijkstra del job, controllata con le sue righe); "
                   "ombra sull'asse del percorso all'istante, come frazione della lunghezza; residenti stimati come in estimate_residents (D45, D48).",
         "calcolo": {"blocco_civici": a.blocco, "tratti_unici": len(geoms), "metri_tratti_unici": round(float(lung.sum())), "metri_percorsi": round(sum(c["lunghezza_m"] for c in civ.values())),
                     "secondi_percorsi": round(t_percorsi, 1), "secondi_totali": round(t_tot), "memoria_max_gb": ESP.memoria_max_gb(), "blocchi": per_blocco},
         "snapshot_ids": sorted(set(m["datasets"][i]["snapshot_id"] for i in range(len(m["datasets"]))) | set(O.SNAPSHOT_IDS["edifici"]) | set(O.SNAPSHOT_IDS["alberi"]) | {"snp_rt_censimento2011_20261010"}),
         "fonti": RES.stima(m)["fonti"] + [{"source_id": "edifici, alberi e LiDAR della baseline", "licenza": "vedi get_source_card per ogni snapshot", "data_del_dato": "baseline 2026-10-09"}],
         "limits": [{"code": k, "text": t} for k, t in LIMITI] + [x for x in RES.stima(m)["limits"] if x["code"] not in ("civici_non_residenti",)]}
    (OUT / f"ombra_rifugi_{DATA}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n")
    (OUT / f"ombra_rifugi_civici_{DATA}.geojson").write_text(json.dumps({"type": "FeatureCollection", "name": "civici_ombra_rifugi", "data": DATA, "ora_locale": ORA, "job_accessibilita": JOB,
                                                                       "nota": "Un punto per civico entro 15 minuti dal rifugio più vicino; ombra sull'asse del percorso alle 14:00, caso tipico con vegetazione. Stima, da verificare.",
                                                                       "features": feats}, ensure_ascii=False, separators=(",", ":")))
    for x in soglie: print(x["minuti"], "min:", x["arrivano"], "ombra>=50%:", x["soprattutto_ombra"], flush=True)
    print("calcolo:", {k: v for k, v in R["calcolo"].items() if k != "blocchi"})


if __name__ == "__main__":
    main()
