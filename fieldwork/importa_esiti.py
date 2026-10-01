#!/usr/bin/env python3
"""Importa un CSV di esiti del sopralluogo T11 e lo valida contro fieldwork/protocollo.json.
Separa le verifiche (misura dell'errore) dalle correzioni proposte. Non scrive mai in network/correzioni.geojson.

  python3 fieldwork/importa_esiti.py esiti.csv [--out fieldwork/out]    importa e valida
  python3 fieldwork/importa_esiti.py --congela                          scrive lo sha256 delle tolleranze nel protocollo

Uscite in --out: verifiche.json (righe valutate, riepilogo per grandezza, errori), correzioni_proposte.geojson.
Codice di uscita 1 se ci sono errori di validazione."""
import argparse, csv, hashlib, json, math, sys
from datetime import date, datetime
from pathlib import Path

FW = Path(__file__).resolve().parent
COLONNE = ["id_punto", "grandezza", "slot", "valore_misurato", "valore_modello", "unita", "lon_misurato", "lat_misurato", "accuratezza_gps_m",
           "ora_locale", "bordo", "cielo", "foto", "rilevatore", "strumento", "note", "correzione_azione", "correzione_valore", "correzione_motivo"]
AZIONI = {"aggiungi_arco", "togli_arco", "cambia_attributo", "aggiungi_connessione", "correggi_geometria", "correggi_altezza", "correggi_parametro_chioma", "correggi_posizione"}
BBOX = (10.35, 43.68, 10.44, 43.73)  # Pisa, controllo di plausibilità delle coordinate
GPS_MAX_M = 10.0


def sha_grandezze(prot):
    return hashlib.sha256(json.dumps(prot["grandezze"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def num(s):
    try: return float(str(s).strip().replace(",", "."))
    except ValueError: return None


def dist_m(lon1, lat1, lon2, lat2):
    r = 6371008.8; p1, p2 = math.radians(lat1), math.radians(lat2); dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def valuta(g, misura, riga, punto):
    """Ritorna (ok, errore, nota). ok None = non valutabile (informativa o senza modello)."""
    k = g["kind"]; v = riga["valore_misurato"]; mod = misura.get("valore_modello")
    if riga.get("valore_modello") not in (None, ""): mod = riga["valore_modello"]
    if k == "informativa": return None, None, "informativa"
    if k == "distanza":
        d = num(v)
        if d is None and riga["lon_misurato"] and riga["lat_misurato"]:
            d = dist_m(num(riga["lon_misurato"]), num(riga["lat_misurato"]), *punto["lon_lat"])
        return (d <= g["tol_m"], d, None) if d is not None else (None, None, "distanza non calcolabile")
    if mod in (None, ""): return None, None, "valore del modello mancante"
    if k == "categorica":
        eq = g.get("ammessi_equivalenti")
        ok = v == str(mod) or bool(eq and v in eq and str(mod) in eq)
        return ok, None, None
    x, mo = num(v), num(mod)
    if k == "assoluta":
        tol = g.get("tol_abs", (g.get("tol_abs_per_classe") or {}).get(misura.get("classe"), None))
        if tol is None: return None, None, "tolleranza per classe mancante"
        return abs(x - mo) <= tol, x - mo, None
    if k == "rel_o_abs":
        return abs(x - mo) <= max(g["tol_rel"] * abs(x), g["tol_abs"]), x - mo, None
    if k == "intervallo":
        lo, hi = misura.get("vmin"), misura.get("vmax")
        return (lo - g["margine_m"] <= x <= hi + g["margine_m"]), x - mo, None
    return None, None, "kind sconosciuto"


def importa(csv_path, prot, punti, out_dir=None):
    P = {p["id"]: p for p in punti}; GR = prot["grandezze"]
    errori, scartate, righe, corr, visti, vuote = [], [], [], [], set(), 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        mancanti = [c for c in COLONNE if c not in (rd.fieldnames or [])]
        if mancanti: return {"errori": [f"colonne mancanti: {mancanti}"], "righe": [], "riepilogo": {}, "correzioni": [], "scartate": [], "n_righe_valide": 0, "righe_non_compilate": 0}
        for n, r in enumerate(rd, 2):
            r = {k: (v or "").strip() for k, v in r.items()}
            def err(m): errori.append(f"riga {n} ({r['id_punto']}/{r['grandezza']}): {m}")
            p = P.get(r["id_punto"])
            if not p: err("id_punto sconosciuto"); continue
            if r["grandezza"] not in GR: err("grandezza non prevista dal protocollo"); continue
            g = GR[r["grandezza"]]; ms = [m for m in p["misure"] if m["grandezza"] == r["grandezza"] and m.get("slot", "") == r["slot"]]
            if not ms: err("grandezza o slot non previsti per questo punto"); continue
            if not r["valore_misurato"] and not (r["lon_misurato"] and r["lat_misurato"]): vuote += 1; continue  # riga dello scheletro non ancora compilata
            key = (r["id_punto"], r["grandezza"], r["slot"])
            if key in visti: err("riga duplicata"); continue
            visti.add(key)
            ok_riga = True
            if g.get("valori_ammessi") and r["valore_misurato"] and r["valore_misurato"] not in g["valori_ammessi"]:
                err(f"valore non ammesso (ammessi: {g['valori_ammessi']})"); ok_riga = False
            if g["kind"] in ("assoluta", "rel_o_abs", "intervallo") and num(r["valore_misurato"]) is None: err("valore numerico mancante o non valido"); ok_riga = False
            if g["kind"] == "categorica" and not r["valore_misurato"]: err("valore mancante"); ok_riga = False
            if g["kind"] == "distanza" and num(r["valore_misurato"]) is None and not (r["lon_misurato"] and r["lat_misurato"]): err("servono valore_misurato (m) oppure lon e lat"); ok_riga = False
            for c in ("lon_misurato", "lat_misurato"):
                if r[c] and num(r[c]) is None: err(f"{c} non numerico"); ok_riga = False
            if r["lon_misurato"] and r["lat_misurato"] and num(r["lon_misurato"]) is not None and num(r["lat_misurato"]) is not None:
                if not (BBOX[0] <= num(r["lon_misurato"]) <= BBOX[2] and BBOX[1] <= num(r["lat_misurato"]) <= BBOX[3]): err("coordinate fuori da Pisa (lon e lat invertite?)"); ok_riga = False
            if r["grandezza"] == "ombra_osservata":
                try:
                    t = datetime.fromisoformat(r["ora_locale"])
                    if t.tzinfo is None: raise ValueError
                except ValueError: err("ora_locale richiede data e fuso, es. 2026-10-14T12:35:00+02:00"); ok_riga = False
                if not r["foto"]: err("foto obbligatoria per le osservazioni d'ombra"); ok_riga = False
                if r["bordo"] not in ("si", "no"): err("bordo deve essere si o no"); ok_riga = False
                if r["cielo"] not in ("sereno", "velato", "coperto"): err("cielo deve essere sereno, velato o coperto"); ok_riga = False
            if r["correzione_azione"] and r["correzione_azione"] not in AZIONI: err(f"correzione_azione non ammessa ({sorted(AZIONI)})"); ok_riga = False
            if not ok_riga: continue
            scarto = None
            acc = num(r["accuratezza_gps_m"])
            if g["kind"] == "distanza" and acc is not None and acc > GPS_MAX_M: scarto = f"accuratezza GPS {acc} m oltre {GPS_MAX_M} m: ripetere"
            if r["grandezza"] == "ombra_osservata" and r["cielo"] == "coperto": scarto = "cielo coperto: ripetere"
            ok, e, nota = (None, None, scarto) if scarto else valuta(g, ms[0], r, p)
            riga = {"id_punto": r["id_punto"], "grandezza": r["grandezza"], "slot": r["slot"], "uso": p["uso"], "valore_misurato": r["valore_misurato"], "ok": ok,
                    "errore": None if e is None else round(e, 2), "bordo": r["bordo"] == "si", "scartata": bool(scarto), "nota": nota or r["note"], "foto": r["foto"]}
            righe.append(riga)
            if scarto: scartate.append(f"{r['id_punto']}/{r['grandezza']}: {scarto}")
            if r["correzione_azione"]:
                if p["uso"] == "verifica":
                    err("correzione proposta su oggetto uso=verifica: non ammessa (vedi protocollo, separazione_correzioni_verifiche); registrata solo come errore di verifica")
                else:
                    ll = [num(r["lon_misurato"]), num(r["lat_misurato"])] if r["lon_misurato"] and r["lat_misurato"] else p["lon_lat"]
                    corr.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": ll}, "properties": {
                        "azione": r["correzione_azione"], "target": p["id_modello"], "valore": r["correzione_valore"], "motivo": r["correzione_motivo"] or "(da compilare)",
                        "fonte_evidenza": f"sopralluogo T11, foto {r['foto'] or 'n.d.'}", "autore": r["rilevatore"], "data": (r["ora_locale"] or date.today().isoformat())[:10],
                        "osservazione_id": f"{r['id_punto']}:{r['grandezza']}:{r['slot']}", "stato": "proposta_non_applicata"}})
    # riepilogo: solo oggetti di verifica sono indipendenti; gli altri sono descrittivi
    riep = {}
    for gname, g in GR.items():
        for blocco in ("verifica", "correzione"):
            rr = [x for x in righe if x["grandezza"] == gname and x["uso"] == blocco and not x["scartata"] and not (gname == "ombra_osservata" and x["bordo"])]
            val = [x for x in rr if x["ok"] is not None]
            if not rr: continue
            quota = sum(x["ok"] for x in val) / len(val) if val else None
            s = {"n_righe": len(rr), "n_valutate": len(val), "quota_entro_tolleranza": None if quota is None else round(quota, 3), "n_min": g["n_min"], "soglia_quota": g["soglia_quota"],
                 "bordo_esclusi": sum(1 for x in righe if x["grandezza"] == gname and x["uso"] == blocco and x["bordo"])}
            errs = sorted(abs(x["errore"]) for x in val if x["errore"] is not None)
            if errs: s["errore_assoluto_mediano"] = round(errs[len(errs) // 2], 2); s["errore_assoluto_max"] = errs[-1]
            if blocco == "correzione": s["esito"] = "descrittivo_non_indipendente"
            elif g["soglia_quota"] is None: s["esito"] = "informativa"
            elif quota is None: s["esito"] = "in_attesa_valore_modello"
            elif len(val) < g["n_min"]: s["esito"] = "campione_insufficiente"
            else:
                ok = quota >= g["soglia_quota"]
                if g["kind"] == "distanza" and "mediana_max_m" in g: ok = ok and s["errore_assoluto_mediano"] <= g["mediana_max_m"]
                s["esito"] = "validato" if ok else "non_validato"
            riep.setdefault(gname, {})[blocco] = s
    ris = {"protocollo": prot["protocollo_id"], "stato_protocollo": prot["stato"], "n_righe_valide": len(righe), "righe_non_compilate": vuote, "scartate": scartate, "errori": errori, "riepilogo": riep, "righe": righe}
    if out_dir:
        out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
        json.dump(ris, open(out_dir / "verifiche.json", "w"), ensure_ascii=False, indent=1)
        json.dump({"type": "FeatureCollection", "name": "correzioni_proposte_t11", "nota": "Proposte da rivedere. Non applicate e non ancora in network/correzioni.geojson. Solo da oggetti uso=correzione.", "features": corr},
                  open(out_dir / "correzioni_proposte.geojson", "w"), ensure_ascii=False, indent=1)
    ris["correzioni"] = corr
    return ris


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?"); ap.add_argument("--protocollo", default=str(FW / "protocollo.json")); ap.add_argument("--punti", default=str(FW / "punti.json"))
    ap.add_argument("--out", default=str(FW / "out")); ap.add_argument("--congela", action="store_true")
    a = ap.parse_args(argv)
    prot = json.load(open(a.protocollo))
    if a.congela:
        prot["sha256_grandezze"] = sha_grandezze(prot); prot["stato"] = "congelato"; prot["data_congelamento"] = date.today().isoformat()
        json.dump(prot, open(a.protocollo, "w"), ensure_ascii=False, indent=2); print("congelato:", prot["sha256_grandezze"]); return 0
    if not a.csv: ap.error("serve il CSV degli esiti")
    if prot["sha256_grandezze"] and prot["sha256_grandezze"] != sha_grandezze(prot):
        print("ERRORE: le tolleranze sono state modificate dopo il congelamento (sha256 diverso). Registrare una deroga o ripristinare.", file=sys.stderr); return 2
    if not prot["sha256_grandezze"]: print("ATTENZIONE: protocollo non congelato (esegui --congela prima del sopralluogo).", file=sys.stderr)
    ris = importa(a.csv, prot, json.load(open(a.punti))["punti"], a.out)
    print(f"righe valide {ris['n_righe_valide']}, non compilate {ris['righe_non_compilate']}, scartate {len(ris['scartate'])}, errori {len(ris['errori'])}, correzioni proposte {len(ris['correzioni'])}")
    for e in ris["errori"]: print("  -", e)
    for g, b in ris["riepilogo"].items():
        v = b.get("verifica")
        if v: print(f"  {g}: {v['esito']} (n {v['n_valutate']}, quota {v['quota_entro_tolleranza']}, soglia {v['soglia_quota']})")
    return 1 if ris["errori"] else 0


if __name__ == "__main__":
    sys.exit(main())
