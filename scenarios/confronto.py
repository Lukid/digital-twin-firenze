"""T10: confronto multicriterio fra scenari e baseline (caso C), su condizioni comuni.

    r = confronta(["scn_z2_s1_filare_r01", "scn_z2_s2_pensilina_pellico"])    # riepilogo, nessun punteggio unico
    ordina(r, pesi)                                                          # solo se il decisore dà i pesi

Per ogni scenario, sugli stessi ricevitori, date, fasce, passi e metodo della baseline (S0 = scenario senza interventi):
 - delta di frazione d'ombra e di minuti al sole camminando su R01 e sui percorsi campione, con intervallo: altezze degli edifici (h_min/h_max di T05,
   delta accoppiato) e, su R01, lato del marciapiede (asse spostato di 3 m a sinistra e a destra, come T09);
 - area di attesa Pellico (superficie);
 - beneficio sui tratti più usati di T06 (archi_piu_usati), pesato per il numero di CIVICI SIT che li usano. Sono civici, non persone, e non ci sono
   flussi pedonali misurati: il peso è un conteggio di indirizzi che passano dall'arco nel cammino minimo verso la destinazione;
 - effetto sull'accessibilità: nullo per costruzione (alberi e pensiline non cambiano il grafo), verificato con hash e ricalcolo;
 - superficie e numero degli interventi, segnalazioni di validazione, fattibilità ignota, robustezza alle varianti.
Indicatori separati. Un ordinamento esiste solo con pesi espliciti del decisore; senza pesi non si inventa."""
import json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S
from scenari import O, ROOT, SC, OUT

VERSIONE = "0.1.0"
S0 = "scn_z2_s0_baseline"
VARIANTI = {"scn_z2_s1_filare_r01": ["scn_z2_s1v_chioma_min", "scn_z2_s1v_chioma_max", "scn_z2_s1v_lato_opposto"]}
TOL = 1e-6   # tolleranza numerica per "delta nullo" (SPEC, sezione 6)
METRICHE = {"frazione_ombra": "shade_fraction_mean", "minuti_sole": "walk_sun_min_mean"}
INDICATORI = {  # id -> (descrizione, segno: +1 se un valore più alto è un beneficio)
    "r01_minuti_sole_evitati_mezzogiorno": "minuti al sole evitati su R01 camminando, partenza 12:30-13:30",
    "r01_minuti_sole_evitati_giornata": "minuti al sole evitati su R01 camminando, partenza 8-18",
    "campione_minuti_sole_evitati_mezzogiorno": "media sui 7 percorsi campione dei minuti al sole evitati, partenza 12:30-13:30",
    "archi_civici_minuti_evitati_mezzogiorno": "somma sui tratti più usati verso la Battisti di (civici x minuti al sole evitati), partenza 12:30-13:30",
    "area_attesa_ombra_mezzogiorno": "aumento della frazione d'ombra dell'area di attesa Pellico, 12:30-13:30"}
DICHIARAZIONI = ["I pesi dei tratti sono numeri di civici SIT (punti d'indirizzo che passano dall'arco nel cammino minimo): non sono persone e non esistono flussi pedonali misurati.",
                 "Baseline = edifici documentati (alberi esistenti esclusi, inventario stimato e incompleto): un albero nuovo non è confrontato con la chioma esistente nello stesso punto.",
                 "Ombra geometrica binaria: nessuna conversione in gradi, comfort, salute o domanda pedonale; nessun anno di crescita.",
                 "Percorsi sull'asse della rete: il lato del marciapiede è ignoto, l'intervallo sul lato (R01 spostata di 3 m) è riportato accanto al delta.",
                 "Dimensioni degli interventi dichiarate come ipotesi di classe scenario; fattibilità (sottoservizi, spazio radicale, proprietà del suolo, permessi, specie) ignota per tutti.",
                 "Nessuna validazione locale: risultati not_validated_locally."]


# ---------------------------------------------------------------- condizioni comuni
CAMPI_COMUNI = ("receivers", "when", "walk_speed_m_s", "casi", "fasce", "el_min_deg", "sun_reference_lonlat", "geometrie_sha256", "method_version")


def incompatibilita(ja, jb):
    """Differenze fra due job che impediscono il confronto (lista di {code, text}; vuota = condizioni comuni)."""
    out = []
    for k in CAMPI_COMUNI:
        if ja["params"].get(k) != jb["params"].get(k): out.append({"code": f"{k}_diverso", "text": f"Il parametro '{k}' non coincide fra i due calcoli: il confronto non è su condizioni comuni."})
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


def _delta(ixb, ixs, rid, f, chiave, extra=()):
    """Delta accoppiato scenario - baseline: centrale (caso base), estremi h_min e h_max e, se richiesto, ricevitori alternativi `extra` (id sostitutivi, es. lato).
    Ritorna dict o None se il valore non c'è (sole fuori supporto)."""
    b, x = _v(ixb, rid, "base", f, chiave), _v(ixs, rid, "base", f, chiave)
    if b is None or x is None: return None
    d = {"baseline": round(b, 4), "scenario": round(x, 4), "delta": round(x - b, 4)}
    alt = [round(_v(ixs, rid, c, f, chiave) - _v(ixb, rid, c, f, chiave), 4) for c in ("base_h_min", "base_h_max")
           if _v(ixs, rid, c, f, chiave) is not None and _v(ixb, rid, c, f, chiave) is not None]
    lati = [round(_v(ixs, r2, "base", f, chiave) - _v(ixb, r2, "base", f, chiave), 4) for r2 in extra if _v(ixs, r2, "base", f, chiave) is not None]
    d["intervallo_altezze"] = [min(alt + [d["delta"]]), max(alt + [d["delta"]])]
    if lati: d["delta_lato_3m"] = lati
    tutti = [d["delta"]] + alt + lati
    d["intervallo"] = [min(tutti), max(tutti)]
    d["discrimina"] = bool(d["intervallo"][0] > TOL or d["intervallo"][1] < -TOL)   # l'intero intervallo ha lo stesso segno e non è nullo
    return d


def _fasce(cond): return [f["id"] for f in cond["fasce"]]


def tabella_percorsi(ixb, ixs, cond):
    out = {}
    for r in S.baseline()["ricevitori"]["route_ids"]:
        rid = f"pth_t04_{r}"; extra = ("pth_t10_R01sx", "pth_t10_R01dx") if r == "R01" else ()
        out[r] = {f: {k: _delta(ixb, ixs, rid, f, ch, extra) for k, ch in METRICHE.items()} for f in _fasce(cond)}
    return out


def beneficio_archi(ixb, ixs, cond, b):
    """Per destinazione e fascia: media pesata (per civici) del delta di frazione d'ombra, civici x minuti al sole evitati, archi e civici toccati."""
    out = {}
    for dest in ("battisti", "pellico"):
        archi = [a for a in b["ricevitori"]["archi"] if dest in a["n_origini"]]; W = sum(a["n_origini"][dest] for a in archi); out[dest] = {"archi": len(archi), "civici_uso_totali": W, "fasce": {}}
        for f in _fasce(cond):
            dd = [(a, _delta(ixb, ixs, a["receiver_id"], f, "shade_fraction_mean"), _delta(ixb, ixs, a["receiver_id"], f, "walk_sun_min_mean")) for a in archi]
            dd = [(a, df, dm) for a, df, dm in dd if df and dm]
            if not dd: continue
            n = lambda a: a["n_origini"][dest]
            media = sum(n(a) * df["delta"] for a, df, dm in dd) / W
            minuti = sum(n(a) * -dm["delta"] for a, df, dm in dd)   # minuti al sole evitati, sommati sui civici
            est = [sum(n(a) * -dm["intervallo_altezze"][i] for a, df, dm in dd) for i in (0, 1)]
            toccati = [a for a, df, dm in dd if abs(df["delta"]) > TOL or abs(dm["delta"]) > TOL]
            out[dest]["fasce"][f] = {"delta_frazione_ombra_media_pesata": round(media, 5), "civici_minuti_sole_evitati": round(minuti, 2),
                                     "civici_minuti_sole_evitati_intervallo_altezze": [round(min(est), 2), round(max(est), 2)],
                                     "archi_toccati": len(toccati), "civici_uso_toccati": sum(n(a) for a in toccati), "edge_id_toccati": [a["edge_id"] for a in toccati][:10]}
    return out


def area_attesa(ixb, ixs, cond, b):
    rid = b["ricevitori"]["area_attesa"]["receiver_id"]
    return {f: _delta(ixb, ixs, rid, f, "shade_fraction_mean") for f in _fasce(cond)}


_ACC = {}


def accessibilita(scn, b):
    """Effetto sull'accessibilità. Per costruzione nullo: il motore legge solo il grafo (e origini e profilo) e alberi/pensiline non li modificano.
    Verifica: hash di grafo, regole e origini uguali a quelli congelati; ricalcolo delle due destinazioni con lo stesso profilo = job_id e metriche di riferimento."""
    if not _ACC:
        import accessibilita as A
        for dest, ref in b["accessibilita_riferimento"]["job"].items():
            r = A.compute_walk_access(dest, profile=b["accessibilita_riferimento"]["profilo"], thresholds_min=b["accessibilita_riferimento"]["soglie_min"],
                                      snap_limit_m=b["accessibilita_riferimento"]["snap_limit_m"], entrance_ids=ref["entrance_ids"])
            rif = json.loads((ROOT / "analysis/manifest" / f"{ref['job_id']}.manifest.json").read_text())
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


# ---------------------------------------------------------------- confronto
def esegui(sid, asset):
    scn = S.carica(sid); cond = S.condizioni()
    return scn, S.ombra_con_cache(scn, cond=cond, asset=asset, asset_times=cond["asset_times"], asset_bbox=cond["asset_bbox"])


def confronta(scenario_ids, con_varianti=True, asset=True, log=None):
    """Riepilogo del confronto di ciascuno scenario con S0 (baseline). Ritorna dict serializzabile; non produce un punteggio unico."""
    log = log or (lambda *a: None)
    dif = S.verifica_baseline()
    if dif: raise S.ScenarioError("incompatible_baseline", "La baseline non coincide con il record congelato: " + "; ".join(dif))
    stato0 = S.stato_baseline(); b = S.baseline(); cond = S.condizioni()
    s0, r0 = esegui(S0, asset); ixb = indice(r0); log("S0", r0["job"]["job_id"], "cache" if r0["cached"] else "calcolato")
    out = {"versione": VERSIONE, "baseline_id": b["baseline_id"], "baseline_invariata": True,
           "condizioni_comuni": {"data": cond["date"], "fasce": cond["fasce"], "n_orari": len(cond["times"]), "method": cond["method"], "walk_speed_m_s": cond["walk_speed_m_s"], "el_min_deg": cond["el_min_deg"],
                                 "ricevitori": [r["receiver_id"] for r in S.ricevitori()], "motore_ombre": f"geometric_ray {O.VERSIONE}", "geometrie_sha256": r0["job"]["params"]["geometrie_sha256"],
                                 "origini_e_percorsi": "stesse origini (civici SIT Z2), stessi percorsi campione, stesso grafo (hash in baseline.json)",
                                 "ostacoli_baseline": "edifici documentati, sensibilità altezze h_min/h_max"},
           "riferimento": {"scenario_id": S0, "job_id": r0["job"]["job_id"], "manifest_id": r0["manifest"]["manifest_id"]}, "scenari": {}, "dichiarazioni": DICHIARAZIONI}
    for sid in scenario_ids:
        scn, r = esegui(sid, asset); log(sid, r["job"]["job_id"], "cache" if r["cached"] else "calcolato")
        inc = incompatibilita(r0["job"], r["job"])
        e = {"titolo": scn["title"], "job_id": r["job"]["job_id"], "manifest_id": r["manifest"]["manifest_id"], "interventi": S.riepilogo_interventi(scn)}
        v = S.valida(scn); e["segnalazioni"] = v["warnings"]; e["fattibilita"] = v["feasibility"]
        if inc: e["stato"] = "respinto"; e["incompatibilita"] = inc; out["scenari"][sid] = e; continue
        ixs = indice(r); e["stato"] = "confrontato"; e["incompatibilita"] = []
        e["percorsi"] = tabella_percorsi(ixb, ixs, cond); e["area_attesa_pellico"] = area_attesa(ixb, ixs, cond, b)
        e["archi_usati"] = beneficio_archi(ixb, ixs, cond, b); e["accessibilita"] = accessibilita(scn, b); e["fasce_utili_R01"] = fasce_utili(e["percorsi"])
        e["assets"] = [a["path"] for a in r["manifest"]["assets"] if a["role"] == "result_geometry"]
        if con_varianti:
            e["robustezza"] = {}
            for vid in VARIANTI.get(sid, []):
                _, rv = esegui(vid, False); log(vid, rv["job"]["job_id"], "cache" if rv["cached"] else "calcolato")
                if incompatibilita(r0["job"], rv["job"]): e["robustezza"][vid] = "respinto: condizioni non comuni"; continue
                tv = tabella_percorsi(ixb, indice(rv), cond); av = area_attesa(ixb, indice(rv), cond, b)
                e["robustezza"][vid] = {"R01": {f: tv["R01"][f] for f in tv["R01"]}, "archi_battisti": beneficio_archi(ixb, indice(rv), cond, b)["battisti"]["fasce"]}
        out["scenari"][sid] = e
    assert S.stato_baseline() == stato0, "la baseline è cambiata durante il confronto"
    out["indicatori"] = indicatori(out)
    return out


def indicatori(out):
    """Indicatori scalari per scenario (positivo = beneficio), per un eventuale ordinamento con pesi del decisore."""
    ind = {}
    for sid, e in out["scenari"].items():
        if e.get("stato") != "confrontato": continue
        g = lambda rid, f: -(e["percorsi"][rid][f]["minuti_sole"] or {"delta": 0.0})["delta"]
        camp = [g(r, "uscita_mezzogiorno") for r in e["percorsi"]]
        arc = e["archi_usati"]["battisti"]["fasce"].get("uscita_mezzogiorno", {}).get("civici_minuti_sole_evitati", 0.0)
        ar = (e["area_attesa_pellico"]["uscita_mezzogiorno"] or {"delta": 0.0})["delta"]
        ind[sid] = {"r01_minuti_sole_evitati_mezzogiorno": round(g("R01", "uscita_mezzogiorno"), 4), "r01_minuti_sole_evitati_giornata": round(g("R01", "giornata_8_18"), 4),
                    "campione_minuti_sole_evitati_mezzogiorno": round(sum(camp) / len(camp), 4), "archi_civici_minuti_evitati_mezzogiorno": round(arc, 2),
                    "area_attesa_ombra_mezzogiorno": round(ar, 4)}
    return {"valori": ind, "descrizioni": INDICATORI, "nota": "Indicatori separati, positivi se c'è un beneficio. Nessun punteggio unico: usare ordina() con pesi esplicitamente scelti dal decisore."}


def ordina(riep, pesi):
    """Ordinamento SOLO con pesi del decisore {indicatore: peso >= 0}. Ogni indicatore è diviso per il massimo valore assoluto fra gli scenari (adimensionale)."""
    ind = riep["indicatori"]["valori"]
    if not pesi or any(k not in INDICATORI or w < 0 for k, w in pesi.items()) or sum(pesi.values()) <= 0:
        raise S.ScenarioError("invalid_params", f"pesi non validi: indicatori ammessi {sorted(INDICATORI)}, pesi >= 0 con somma positiva.")
    mx = {k: max((abs(v[k]) for v in ind.values()), default=0) or 1.0 for k in INDICATORI}
    tot = sum(pesi.values()); pun = {sid: round(sum(w * v[k] / mx[k] for k, w in pesi.items()) / tot, 4) for sid, v in ind.items()}
    return {"pesi": pesi, "punteggi": pun, "ordine": sorted(pun, key=lambda s: (-pun[s], s)), "avvertenza": "L'ordine dipende dai pesi scelti: non è una raccomandazione."}


def sensibilita_pesi(riep):
    """Ordine sotto ciascun indicatore preso da solo e con pesi uguali: mostra se la scelta dei pesi cambia l'ordine."""
    o = {k: ordina(riep, {k: 1.0})["ordine"] for k in INDICATORI}; o["pesi_uguali"] = ordina(riep, {k: 1.0 for k in INDICATORI})["ordine"]
    return {"ordini": o, "ordine_stabile": len({tuple(v) for v in o.values()}) == 1}


# ---------------------------------------------------------------- uscite
def scrivi_out(riep):
    OUT.mkdir(parents=True, exist_ok=True)
    for sid in riep["scenari"]:
        scn = S.carica(sid)
        if scn["operations"]: (OUT / f"interventi_{sid}.geojson").write_text(json.dumps(S.geojson_interventi(scn), ensure_ascii=False, separators=(",", ":")))
    riep["sensibilita_pesi"] = sensibilita_pesi(riep) if len(riep["indicatori"]["valori"]) > 1 else None
    (OUT / "confronto_riepilogo.json").write_text(json.dumps(riep, ensure_ascii=False, indent=1))
    return riep


def main():
    ids = [s for s in ("scn_z2_s1_filare_r01", "scn_z2_s2_pensilina_pellico")]
    r = confronta(ids, log=lambda *a: print(*a, flush=True)); scrivi_out(r)
    for sid, e in r["scenari"].items():
        print(sid, e["stato"], "R01 minuti_sole mezzogiorno:", e["percorsi"]["R01"]["uscita_mezzogiorno"]["minuti_sole"])
    print("riepilogo scritto in scenarios/out/confronto_riepilogo.json")


if __name__ == "__main__":
    main()
