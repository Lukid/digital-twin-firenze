"""F08: confronto fra scenari e baseline su Firenze Novoli, su condizioni comuni.

    r = confronta(["scn_fi_s1_filare_r01", "scn_fi_s2_pensilina_attesa_polo"])    # riepilogo, nessun punteggio unico

Per ogni scenario e per ciascuna data (15 luglio e 15 settembre), sugli stessi ricevitori, orari, fasce, passi e metodo della baseline (S0 = scenario senza interventi):
 - delta di frazione d'ombra e di minuti al sole camminando su R01 (fermata T2 Torre degli Agli -> ingresso predefinito del Polo) e R02 (fermata Regione Toscana), per fascia e per ora;
 - tre contesti del motore, ciascuno con caso centrale e due estremi: solo edifici (h, h_min, h_max), con alberi censiti (tipico, min, max), con vegetazione LiDAR
   (tipico, min, max). Il contesto con vegetazione LiDAR è la base di confronto principale (D14). L'intervallo di ogni delta è il minimo e il massimo dei delta accoppiati
   (stesso ricevitore, stessa ora, stesso caso) sui tre casi;
 - area di attesa (superficie) della fermata bus Forlanini Polo Scienze Sociali;
 - beneficio sui tratti più usati di F06 (verso il Polo e verso la fermata T2), pesato per il numero di CIVICI che li usano: sono indirizzi, non persone, e non ci sono
   flussi pedonali misurati;
 - effetto sull'accessibilità: nullo per costruzione (alberi e pensiline non cambiano il grafo), verificato con hash e ricalcolo;
 - superficie e numero degli interventi, segnalazioni di validazione, fattibilità ignota, robustezza alle varianti.
Indicatori separati: nessun punteggio unico."""
import concurrent.futures as cf, json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S
from scenari import O, ROOT, SC

VERSIONE = "0.2.0"
S0 = "scn_fi_s0_baseline"
S1, S2 = "scn_fi_s1_filare_r01", "scn_fi_s2_pensilina_attesa_polo"
VARIANTI = {S1: ["scn_fi_s1v_chioma_min", "scn_fi_s1v_chioma_max", "scn_fi_s1v_lato_opposto"]}
CASI_VARIANTI = ["base", "veg_lidar_tipico"]   # le varianti si calcolano solo sul caso centrale di due contesti (costo: un caso con vegetazione LiDAR vale circa un minuto)
TOL = 1e-6   # tolleranza numerica per "delta nullo"
METRICHE = {"frazione_ombra": "shade_fraction_mean", "minuti_sole": "walk_sun_min_mean"}
POLO, FERMATA_T2 = "dst_university_w83537185", "dst_tram_fm9057"
PRINCIPALE = S.CONTESTO_PRINCIPALE
DICHIARAZIONI = ["I pesi dei tratti sono numeri di civici (punti d'indirizzo del Comune che passano dall'arco nel cammino minimo): non sono persone e non esistono flussi pedonali misurati.",
                 "Base di confronto principale: edifici documentati, alberi censiti e vegetazione LiDAR (D14). Gli altri due contesti (solo edifici, con alberi censiti) sono riportati come sensibilità.",
                 "Ombra geometrica binaria: nessuna conversione in gradi, comfort, salute o domanda pedonale; nessun anno di crescita.",
                 "Un albero nuovo è un'ombra aggiunta: dove la chioma esistente ombreggia già il punto il beneficio può solo calare rispetto ai soli edifici.",
                 "Vegetazione LiDAR come prisma opaco pieno (limite superiore dell'ombra esistente): tende a ridurre il beneficio di un nuovo albero.",
                 "Percorsi sull'asse della rete: il lato del marciapiede è ignoto e non è stato misurato; la variante 'lato opposto' di S1 è l'unica sensibilità sul lato.",
                 "Dimensioni degli interventi dichiarate come ipotesi di classe scenario; fattibilità (sottoservizi, spazio radicale, proprietà del suolo, permessi, specie) ignota per tutti.",
                 "Nessuna validazione locale: risultati not_validated_locally."]


# ---------------------------------------------------------------- condizioni comuni
CAMPI_COMUNI = ("receivers", "when", "walk_speed_m_s", "fasce", "el_min_deg", "sun_reference_lonlat", "geometrie_sha256", "method_version")


def incompatibilita(ja, jb):
    """Differenze fra due job che impediscono il confronto (lista di {code, text}; vuota = condizioni comuni). I casi possono essere un sottoinsieme l'uno dell'altro."""
    out = []
    for k in CAMPI_COMUNI:
        if ja["params"].get(k) != jb["params"].get(k): out.append({"code": f"{k}_diverso", "text": f"Il parametro '{k}' non coincide fra i due calcoli: il confronto non è su condizioni comuni."})
    ca, cb = set(ja["params"]["casi"]), set(jb["params"]["casi"])
    if not (ca <= cb or cb <= ca): out.append({"code": "casi_diverso", "text": "I casi del motore non coincidono e nessuno contiene l'altro."})
    ma = {k: v for k, v in ja["params"]["method"].items() if k != "obstacles"}; mb = {k: v for k, v in jb["params"]["method"].items() if k != "obstacles"}
    if ma != mb: out.append({"code": "method_diverso", "text": "Passi spaziale/temporale o metodo diversi."})
    if ja["inputs"]["baseline_id"] != jb["inputs"]["baseline_id"]: out.append({"code": "baseline_diversa", "text": "Baseline diverse."})
    if ja["inputs"]["snapshot_ids"] != jb["inputs"]["snapshot_ids"]: out.append({"code": "snapshot_diversi", "text": "Snapshot diversi."})
    return out


# ---------------------------------------------------------------- estrazione
def indice(res):
    return {(s["receiver_id"], s["caso"], s["fascia"]): s for s in res["sintesi"]}


def _v(ix, rid, caso, f, k):
    return (ix.get((rid, caso, f)) or {}).get(k)


def _delta(ixb, ixs, rid, f, chiave, casi):
    """Delta accoppiato scenario - baseline: centrale e due estremi del contesto. Ritorna dict o None se il valore non c'è (sole fuori supporto, caso non calcolato)."""
    c0, c1, c2 = casi; b, x = _v(ixb, rid, c0, f, chiave), _v(ixs, rid, c0, f, chiave)
    if b is None or x is None: return None
    d = {"baseline": round(b, 4), "scenario": round(x, 4), "delta": round(x - b, 4)}
    alt = [round(_v(ixs, rid, c, f, chiave) - _v(ixb, rid, c, f, chiave), 4) for c in (c1, c2)
           if _v(ixs, rid, c, f, chiave) is not None and _v(ixb, rid, c, f, chiave) is not None]
    d["delta_estremi"] = alt
    d["intervallo"] = [min(alt + [d["delta"]]), max(alt + [d["delta"]])]
    d["discrimina"] = bool(d["intervallo"][0] > TOL or d["intervallo"][1] < -TOL)   # l'intero intervallo ha lo stesso segno e non è nullo
    return d


def _fasce(cond): return [f["id"] for f in cond["fasce"]]


def tabella_percorsi(ixb, ixs, cond, casi):
    return {r: {f: {k: _delta(ixb, ixs, f"pth_fi_{r}", f, ch, casi) for k, ch in METRICHE.items()} for f in _fasce(cond)} for r in S.baseline()["ricevitori"]["route_ids"]}


def beneficio_archi(ixb, ixs, cond, b, casi):
    """Per destinazione e fascia: media pesata (per civici) del delta di frazione d'ombra, civici x minuti al sole evitati, archi e civici toccati."""
    out = {}
    for dest in (POLO, FERMATA_T2):
        archi = [a for a in b["ricevitori"]["archi"] if dest in a["n_origini"]]; W = sum(a["n_origini"][dest] for a in archi); out[dest] = {"archi": len(archi), "civici_uso_totali": W, "fasce": {}}
        for f in _fasce(cond):
            dd = [(a, _delta(ixb, ixs, a["receiver_id"], f, "shade_fraction_mean", casi), _delta(ixb, ixs, a["receiver_id"], f, "walk_sun_min_mean", casi)) for a in archi]
            dd = [(a, df, dm) for a, df, dm in dd if df and dm]
            if not dd: continue
            n = lambda a: a["n_origini"][dest]
            media = sum(n(a) * df["delta"] for a, df, dm in dd) / W
            minuti = sum(n(a) * -dm["delta"] for a, df, dm in dd)   # minuti al sole evitati, sommati sui civici
            est = [sum(n(a) * -dm["intervallo"][i] for a, df, dm in dd) for i in (0, 1)]
            toccati = [a for a, df, dm in dd if abs(df["delta"]) > TOL or abs(dm["delta"]) > TOL]
            out[dest]["fasce"][f] = {"delta_frazione_ombra_media_pesata": round(media, 5), "civici_minuti_sole_evitati": round(minuti, 2),
                                     "civici_minuti_sole_evitati_intervallo": [round(min(est), 2), round(max(est), 2)],
                                     "archi_toccati": len(toccati), "civici_uso_toccati": sum(n(a) for a in toccati), "edge_id_toccati": [a["edge_id"] for a in toccati][:10]}
    return out


def area_attesa(ixb, ixs, cond, b, casi):
    rid = b["ricevitori"]["area_attesa"]["receiver_id"]
    return {f: _delta(ixb, ixs, rid, f, "shade_fraction_mean", casi) for f in _fasce(cond)}


def per_ora(rb, rs, b, casi):
    """Delta per ricevitore e ora nel contesto dato: {ricevitore: {HH:MM: {frazione_ombra: [centrale, estremo, estremo], minuti_sole: [...]}}} (ore con sole sotto 5 gradi assenti)."""
    ib = {(r["receiver_id"], r["time_local"], r["caso"]): r for r in rb["righe"]}; is_ = {(r["receiver_id"], r["time_local"], r["caso"]): r for r in rs["righe"]}
    rids = [f"pth_fi_{r}" for r in b["ricevitori"]["route_ids"]] + [b["ricevitori"]["area_attesa"]["receiver_id"]]; out = {}
    for rid in rids:
        for t in sorted({k[1] for k in is_ if k[0] == rid}):
            e = {}
            for nome, k in (("frazione_ombra", "shade_fraction"), ("minuti_sole", "walk_sun_min")):
                v = [(is_[(rid, t, c)][k] - ib[(rid, t, c)][k]) if (rid, t, c) in is_ and (rid, t, c) in ib and k in is_[(rid, t, c)] and k in ib[(rid, t, c)] else None for c in casi]
                if v[0] is not None: e[nome] = [round(x, 4) for x in v if x is not None]
            if e: out.setdefault(rid, {})[t] = e
    return out


_ACC = {}


def accessibilita(scn, b):
    """Effetto sull'accessibilità. Per costruzione nullo: il motore usa solo grafo, origini e profilo, che alberi e pensiline non modificano.
    Verifica: hash di grafo, regole e origini uguali a quelli congelati; ricalcolo delle due destinazioni di riferimento con lo stesso profilo = job_id e metriche di F06."""
    if not _ACC:
        import accessibilita as A
        for dest, ref in b["accessibilita_riferimento"]["job"].items():
            r = A.compute_walk_access(dest, profile=b["accessibilita_riferimento"]["profilo"], thresholds_min=b["accessibilita_riferimento"]["soglie_min"],
                                      snap_limit_m=b["accessibilita_riferimento"]["snap_limit_m"], entrance_ids=ref["entrance_ids"])
            rif = json.loads((A.OUT_VERS / "manifest" / f"{ref['job_id']}.manifest.json").read_text())
            metr = {m["metric_id"]: m["value"] for m in r["manifest"]["metrics"]}; metr_rif = {m["metric_id"]: m["value"] for m in rif["metrics"]}
            _ACC[dest] = {"job_id": r["job"]["job_id"], "job_id_riferimento": ref["job_id"], "stesso_job": r["job"]["job_id"] == ref["job_id"], "metriche_identiche": metr == metr_rif,
                          "quota_10min": next(m["value"] for m in r["manifest"]["metrics"] if m["metric_id"] == "served_share_10min")}
    st = S.stato_baseline(); h = st["riferimenti"]; ref = S.baseline()
    ok_hash = h["grafo"] == ref["grafo"]["sha256"] and h["regole"] == ref["grafo"]["regole_sha256"] and h["origini"] == ref["origini"]["sha256"]
    seg = [w for w in S.valida(scn)["warnings"] if w["code"] == "su_arco_molto_usato"]
    return {"delta_quota_servita": 0.0, "delta_tempo_mediano_min": 0.0, "nullo": bool(ok_hash and all(v["stesso_job"] and v["metriche_identiche"] for v in _ACC.values())),
            "motivo": "per costruzione: il motore di accessibilità usa grafo, origini e profilo, che gli interventi non modificano; verificato con hash e ricalcolo",
            "hash_grafo_regole_origini_invariati": bool(ok_hash), "ricalcolo": _ACC,
            "ostruzione_passaggio_non_modellata": [{"op_id": w["op_id"], "text": w["text"]} for w in seg]}


def fasce_utili(tab):
    """Fasce in cui R01 ha un delta di minuti al sole che discrimina (intervallo non nullo)."""
    return [f for f, m in tab["R01"].items() if m["minuti_sole"] and m["minuti_sole"]["discrimina"]]


# ---------------------------------------------------------------- calcolo (con cache)
def _casi(sid): return None if sid == S0 or sid in (S1, S2) else CASI_VARIANTI


def esegui(sid, data, rec=None):
    scn = S.carica(sid)
    return scn, S.ombra_con_cache(scn, rec=rec or S.ricevitori(), cond={**S.condizioni(), "date": data}, casi=_casi(sid))


def _lavoro(args):
    sid, data = args; _, r = esegui(sid, data); return sid, data, r["job"]["job_id"], r["cached"]


def precalcola(scenario_ids, con_varianti=True, log=None, lavoratori=6):
    """Calcola in parallelo (un processo per scenario e data) i job mancanti della cache. Ritorna l'elenco dei job calcolati."""
    log = log or (lambda *a: None); cond = S.condizioni()
    ids = [S0] + list(scenario_ids) + [v for s in scenario_ids for v in (VARIANTI.get(s, []) if con_varianti else [])]
    lavori = [(sid, d) for sid in ids for d in cond["dates"]]
    with cf.ProcessPoolExecutor(max_workers=min(lavoratori, len(lavori))) as ex:
        for sid, d, jid, cached in ex.map(_lavoro, lavori): log(sid, d, jid, "cache" if cached else "calcolato")


# ---------------------------------------------------------------- confronto
def confronta(scenario_ids, con_varianti=True, log=None, parallelo=True):
    """Riepilogo del confronto di ciascuno scenario con S0 (baseline). Ritorna dict serializzabile; non produce un punteggio unico."""
    log = log or (lambda *a: None)
    dif = S.verifica_baseline()
    if dif: raise S.ScenarioError("incompatible_baseline", "La baseline non coincide con il record congelato: " + "; ".join(dif))
    stato0 = S.stato_baseline(); b = S.baseline(); cond = S.condizioni(); rec = S.ricevitori()
    if parallelo: precalcola(scenario_ids, con_varianti, log)
    CC = S.CASI_CONTESTO
    base = {d: esegui(S0, d, rec)[1] for d in cond["dates"]}
    out = {"versione": VERSIONE, "baseline_id": b["baseline_id"], "baseline_invariata": True,
           "condizioni_comuni": {"date": cond["dates"], "fasce": cond["fasce"], "orari": cond["times"], "method": cond["method"], "walk_speed_m_s": cond["walk_speed_m_s"], "el_min_deg": cond["el_min_deg"],
                                 "ricevitori": [r["receiver_id"] for r in rec], "motore_ombre": f"geometric_ray {O.VERSIONE}", "geometrie_sha256": base[cond["dates"][0]]["job"]["params"]["geometrie_sha256"],
                                 "origini_e_percorsi": "stesse origini (civici del Comune), stessi percorsi campione, stesso grafo (hash in baseline.json)",
                                 "contesti": {"solo_edifici": "edifici documentati, sensibilità altezze h_min/h_max", "con_alberi_esistenti": "edifici e alberi censiti, chioma tipica (intervallo: min e max)",
                                              "con_vegetazione_lidar": "edifici, alberi censiti e vegetazione LiDAR senza albero censito (base di confronto principale; intervallo: min e max)"},
                                 "contesto_principale": PRINCIPALE},
           "riferimento": {"scenario_id": S0, "job_id": {d: r["job"]["job_id"] for d, r in base.items()}}, "scenari": {}, "dichiarazioni": DICHIARAZIONI}
    for sid in scenario_ids:
        scn = S.carica(sid); res = {d: esegui(sid, d, rec)[1] for d in cond["dates"]}
        v = S.valida(scn)
        e = {"titolo": scn["title"], "job_id": {d: r["job"]["job_id"] for d, r in res.items()}, "manifest_id": {d: r["manifest"]["manifest_id"] for d, r in res.items()},
             "interventi": S.riepilogo_interventi(scn), "segnalazioni": v["warnings"], "fattibilita": v["feasibility"]}
        inc = [i for d in cond["dates"] for i in incompatibilita(base[d]["job"], res[d]["job"])]
        if inc: e["stato"] = "respinto"; e["incompatibilita"] = inc; out["scenari"][sid] = e; continue
        e["stato"] = "confrontato"; e["incompatibilita"] = []
        e["percorsi"], e["area_attesa_polo"], e["archi_usati"], e["per_ora"], e["fasce_utili_R01"] = {}, {}, {}, {}, {}
        for d in cond["dates"]:
            ib, is_ = indice(base[d]), indice(res[d])
            e["percorsi"][d] = {c: tabella_percorsi(ib, is_, cond, CC[c]) for c in S.CONTESTI}
            e["area_attesa_polo"][d] = {c: area_attesa(ib, is_, cond, b, CC[c]) for c in S.CONTESTI}
            e["archi_usati"][d] = beneficio_archi(ib, is_, cond, b, CC[PRINCIPALE])
            e["per_ora"][d] = per_ora(base[d], res[d], b, CC[PRINCIPALE])
            e["fasce_utili_R01"][d] = fasce_utili(e["percorsi"][d][PRINCIPALE])
        e["accessibilita"] = accessibilita(scn, b)
        if scn["operations"] and scn["operations"][0]["target_type"] == "tree": e["sovrapposizioni_alberi_esistenti"] = S.sovrapposizioni_alberi_esistenti(scn)
        if con_varianti:
            e["robustezza"] = {}
            for vid in VARIANTI.get(sid, []):
                rv = {d: esegui(vid, d, rec)[1] for d in cond["dates"]}
                if any(incompatibilita(base[d]["job"], rv[d]["job"]) for d in cond["dates"]): e["robustezza"][vid] = "respinto: condizioni non comuni"; continue
                e["robustezza"][vid] = {"titolo": S.carica(vid)["title"].split(":")[0], "casi_calcolati": CASI_VARIANTI,
                                        "percorsi": {d: {c: tabella_percorsi(indice(base[d]), indice(rv[d]), cond, CC[c]) for c in ("solo_edifici", PRINCIPALE)} for d in cond["dates"]}}
        out["scenari"][sid] = e
    assert S.stato_baseline() == stato0, "la baseline è cambiata durante il confronto"
    return out


# ---------------------------------------------------------------- uscite
def scrivi_out(riep):
    SC.mkdir(parents=True, exist_ok=True)
    (SC / "confronto.json").write_text(json.dumps(riep, ensure_ascii=False, separators=(",", ":")))
    return riep


def main():
    r = confronta([S1, S2], log=lambda *a: print(*a, flush=True)); scrivi_out(r)
    for sid, e in r["scenari"].items():
        for d in r["condizioni_comuni"]["date"]:
            m = e["percorsi"][d][PRINCIPALE]["R01"]["punta_12_30_13_30"]["minuti_sole"]
            print(sid, d, e["stato"], "R01 minuti al sole in punta (base LiDAR):", m and (m["delta"], m["intervallo"]))
    print(f"riepilogo scritto in {SC / 'confronto.json'}")


if __name__ == "__main__":
    main()
