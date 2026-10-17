#!/usr/bin/env python3
"""F2 (D33): indicatore "metri quadri d'ombra al suolo per mille euro" del filare S1, con le voci del Prezzario dei Lavori della Regione Toscana 2026 (Firenze, CC BY 4.0).

Ombra guadagnata: superficie al suolo in ombra con S1 meno quella della baseline S0, stesse condizioni di F07/F08 (15 luglio e 15 settembre, fasce 12:30-13:30 e 8-19),
contesto principale (edifici, alberi censiti, vegetazione LiDAR: caso tipico, intervallo sui casi min e max). Il ricevitore è una superficie: l'unione delle ombre dei soli
alberi di S1 in tutti gli istanti, più 1 m; fuori da lì l'ombra non cambia. Sotto gli edifici il suolo conta già come ombra (impronta), quindi non è un guadagno.
Costo: 7 x (fornitura dell'albero + piantagione in sede stradale). Specie e circonferenza dalla regola D36: platano orientale 18/20 (TOS26_PR.P45.003.A91), un numero solo.
Sensibilità: intervallo sulle altre voci candidate (alberi in contenitore, circonferenza 16/18, 18/20, 20/25 cm; piantagione in sede stradale, 4 voci).
Nessuna voce di scavo adatta (solo voci forestali).
Uso: pipeline/.venv/bin/python scenarios/costo_filare.py [--prezzario Firenze-Articolo-2026.csv]
Output: scenarios/firenze_novoli/costo_filare.json; con --prezzario rigenera anche l'estratto delle voci costo_voci.json."""
import csv, json, pathlib, re, sys
import numpy as np, shapely
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S
from scenari import O, SC

S0, S1 = "scn_fi_s0_baseline", "scn_fi_s1_filare_r01"
VOCI = SC / "costo_voci.json"; OUT = SC / "costo_filare.json"
CIRCONFERENZE = ("16/18", "18/20", "20/25")   # classi del vivaio considerate: lo scenario non dichiara la circonferenza
PIANTAGIONE = ("TOS26_09.V03.005.003", "TOS26_09.V03.005.004", "TOS26_09.V03.005.007", "TOS26_09.V03.005.008")   # in sede stradale (gli alberi di S1 stanno nelle aree pedonali)
SCELTA = {"fornitura": "TOS26_PR.P45.003.A91",     # D36: platano orientale, circonferenza 18/20
          "piantagione": "TOS26_09.V03.005.004"}   # scelta dell'agente (da confermare): in sede stradale, 2-3 tutori, 1 m3 di terra nuova; le altre 3 restano nella sensibilità
REGOLA_SPECIE = ("D36: specie da ombra più piantata dal Comune entro 400 m dal tratto fra gli alberi del censimento con circonferenza fino a 25 cm, escluse le forme colonnari "
                 "(cipressi, pioppi cipressini e tremuli): platano orientale, 29 alberi, circonferenza mediana 17 cm (32 alberi e 18,8 cm entro 800 m); classe di vivaio 18/20")
REGOLA_PIANTAGIONE = ("voce in sede stradale con 2-3 tutori e terra nuova 100 x 100 x 100 cm (TOS26_09.V03.005.004): scelta dell'agente per un albero da 18/20 cm, "
                      "da confermare; le altre tre voci in sede stradale sono nella sensibilità")
FONTE = {"titolo": "Prezzario dei Lavori della Regione Toscana 2026, file di Firenze (CSV, articoli)", "editore": "Regione Toscana",
         "atto": "Delibera di Giunta regionale n. 1676 del 15/12/2025; valido dal 1/1/2026 al 31/12/2026",
         "scheda": "https://dati.toscana.it/dataset/prezzario-lavori-2026",
         "risorsa": "https://dati.toscana.it/dataset/7d0fd279-fbae-44a8-8f71-6986514acf0c/resource/925a8190-ea9d-407e-a05d-9a19c2850e3d/download/2026-firenze-csv.zip",
         "licenza": "CC BY 4.0 (campo license_type della risorsa: https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40)",
         "scaricato": "2026-10-17", "zip_sha256": "56faa24c02d3062d63b43a94f86efae23db7c2e8488c79be49fb982a9a3c812d",
         "revisione_1": "XML 'rev 1' del 25/05/2026: stessi prezzi per tutte le voci (controllato il 17/10/2026)",
         "prezzo": "colonna Prezzo: comprende spese generali e utili d'impresa, IVA esclusa"}


def estrai_voci(csv_path):
    """Voci candidate dal CSV del prezzario: alberi in contenitore (tipologia A) nelle circonferenze considerate e le 4 piantagioni in sede stradale."""
    R = [r for r in csv.reader(open(csv_path, encoding="utf-8"), delimiter="|") if len(r) > 8 and r[0].startswith("TOS26_")]
    tip = lambda t: (m := re.match(r"[^,]+,\s*([A-Z](?:\s*,\s*[A-Z])*)\s*,", t)) and "A" in re.split(r"\s*,\s*", m.group(1))   # A = albero, C = cespuglio, ...
    circ = lambda t: (m := re.search(r"circonferenza (\d+/\d+)", t)) and m.group(1) in CIRCONFERENZE
    forn = [r for r in R if r[0].startswith("TOS26_PR.P45.003") and tip(r[5]) and circ(r[5])]
    pian = [r for r in R if r[0] in PIANTAGIONE]; assert len(pian) == 4
    riga = lambda r, tipo: {"codice": r[0], "tipo": tipo, "descrizione": re.sub(r"\s+", " ", (r[5] if tipo == "fornitura" else f"{r[4]} {r[5]}")).strip(), "unita": r[6], "prezzo": float(r[8])}
    voci = [riga(r, "fornitura") for r in forn] + [riga(r, "piantagione") for r in pian]
    VOCI.write_text(json.dumps({"fonte": FONTE, "regola": f"fornitura: PR.P45.003, piante in contenitore di tipologia A, circonferenza {', '.join(CIRCONFERENZE)} cm; piantagione: {', '.join(PIANTAGIONE)}",
                                "voci": voci}, ensure_ascii=False, indent=1))


def costo(voci, n):
    """Costo per n alberi con le voci di SCELTA (D36): un numero solo. Una riga per voce usata."""
    v = {x["codice"]: x for x in voci}
    righe = [{**{k: v[c][k] for k in ("codice", "tipo", "descrizione", "unita", "prezzo")}, "quantita": n, "importo": round(n * v[c]["prezzo"], 2)} for c in SCELTA.values()]
    return {"eur": round(sum(r["importo"] for r in righe), 2), "righe": righe, "regola_specie": REGOLA_SPECIE, "regola_piantagione": REGOLA_PIANTAGIONE}


def intervallo(voci, n):
    """Sensibilità sulle altre specie: voce più economica e più cara di fornitura e di piantagione fra tutte le candidate. Una riga per voce usata."""
    f = sorted((v for v in voci if v["tipo"] == "fornitura"), key=lambda v: (v["prezzo"], v["codice"]))
    p = sorted((v for v in voci if v["tipo"] == "piantagione"), key=lambda v: (v["prezzo"], v["codice"]))
    righe = lambda vv, lato: [{**{k: v[k] for k in ("codice", "tipo", "descrizione", "unita", "prezzo")}, "quantita": n, "importo": round(n * v["prezzo"], 2), "estremo": lato} for v in vv]
    lo, hi = righe([f[0], p[0]], "minimo"), righe([f[-1], p[-1]], "massimo")
    return {"minimo_eur": round(sum(r["importo"] for r in lo), 2), "massimo_eur": round(sum(r["importo"] for r in hi), 2), "righe": lo + hi,
            "voci_candidate": {"fornitura": len(f), "piantagione": len(p)}}


def ricevitore(alberi, cond):
    """Unione delle ombre dei soli alberi di S1 in tutti gli istanti con sole utile (le due date), più 1 m: l'unica superficie dove l'ombra può cambiare."""
    T = O.scena_da_alberi(alberi); pezzi = []
    for d in cond["dates"]:
        for hhmm in cond["times"]:
            st, az, el, U = O.ombra_a_istante(T, O.locale_a_utc(d, hhmm), O.SOLE_LAT, O.SOLE_LON, cond["el_min_deg"])
            if U is not None: pezzi.append(U)
    return shapely.set_precision(shapely.union_all(pezzi).buffer(1.0), 0.01)


def ombra_guadagnata():
    cond = S.condizioni(); s0, s1 = S.carica(S0), S.carica(S1); _, alberi = S.volumi_scenario(s1)
    R = ricevitore(alberi, cond); rec = [{"receiver_id": "sfc_fi_s1_ombra_alberi", "kind": "surface", "geometry": shapely.geometry.mapping(R)}]
    casi = S.CASI_CONTESTO[S.CONTESTO_PRINCIPALE]; out = {"ricevitore_m2": round(R.area, 1), "casi": list(casi), "job_id": {}, "m2": {}}
    for d in cond["dates"]:
        c = {**cond, "date": d}; r0, r1 = (S.calcola_ombra(s, rec, c, casi=list(casi)) for s in (s0, s1))
        out["job_id"][d] = {S0: r0["job"]["job_id"], S1: r1["job"]["job_id"]}
        idx = {(r["time_local"], r["caso"]): r for r in r0["righe"]}
        out["m2"][d] = {}
        for f in cond["fasce"]:
            per_caso = {}
            for caso in casi:
                dd = [r["shaded_m2"] - idx[(r["time_local"], caso)]["shaded_m2"] for r in r1["righe"]
                      if r["caso"] == caso and f["from"] <= r["time_local"] <= f["to"] and "shaded_m2" in r and "shaded_m2" in idx[(r["time_local"], caso)]]
                per_caso[caso] = round(float(np.mean(dd)), 1)
            out["m2"][d][f["id"]] = {"centrale": per_caso[casi[0]], "intervallo": [min(per_caso.values()), max(per_caso.values())], "per_caso": per_caso}
    return out


def indicatore(m2, eur):
    """m2 per mille euro."""
    return round(m2 / (eur / 1000), 2)


if __name__ == "__main__":
    if "--prezzario" in sys.argv: estrai_voci(sys.argv[sys.argv.index("--prezzario") + 1])
    s1 = S.carica(S1); n = sum(1 for op in s1["operations"] if op["target_type"] == "tree")
    voci = json.loads(VOCI.read_text())["voci"]; c, alt = costo(voci, n), intervallo(voci, n); og = ombra_guadagnata()
    ind = {d: {f: {"valore": indicatore(v["centrale"], c["eur"]), "estremi_casi": [indicatore(v["intervallo"][0], c["eur"]), indicatore(v["intervallo"][1], c["eur"])],
                   "altre_specie": [indicatore(v["centrale"], alt["massimo_eur"]), indicatore(v["centrale"], alt["minimo_eur"])]} for f, v in fd.items()} for d, fd in og["m2"].items()}
    res = {"scenario_id": S1, "scenario_version": s1["version"], "baseline_id": s1["baseline_id"], "alberi": n,
           "indicatore": "metri quadri di suolo che passano dal sole all'ombra (media sugli orari della fascia) per mille euro di fornitura e piantagione",
           "riferimento": {"data": "2026-07-15", "fascia": "punta_12_30_13_30", "m2": og["m2"]["2026-07-15"]["punta_12_30_13_30"]["centrale"],
                           "m2_per_mille_euro": ind["2026-07-15"]["punta_12_30_13_30"]["valore"], "costo_eur": c["eur"], "regola_specie": REGOLA_SPECIE},
           "ombra": og, "costo": c, "sensibilita_altre_specie": alt, "m2_per_mille_euro": ind, "fonte_prezzi": FONTE,
           "non_compreso": ["scavo della buca (nessuna voce adatta nel prezzario: solo voci forestali)", "demolizione e ripristino della pavimentazione", "spostamento di sottoservizi",
                            "manutenzione e irrigazione negli anni di attecchimento e dopo", "potature", "progettazione, direzione lavori, sicurezza oltre gli oneri già nei prezzi", "IVA"],
           "limiti": ["Ombra della chioma di classe 'medio' (11 m, chioma 6 m): albero adulto. Il prezzo è di un albero da vivaio (circonferenza 18/20 cm, chioma molto più piccola): "
                      "l'indicatore confronta l'ombra a maturità con il costo d'impianto, senza anni di crescita.",
                      "Specie e circonferenza dalla regola D36 (platano orientale 18/20), non da un progetto; voce di piantagione scelta dall'agente. "
                      "Sensibilità: con le altre specie e piantagioni candidate il costo va dalla voce più economica alla più cara (campo sensibilita_altre_specie).",
                      "Ombra geometrica binaria su suolo piano, chiome opache; nessuna validazione sul posto.",
                      "Pensiline e tende: nessun prezzo pubblico con licenza di riuso trovato (D33); l'indicatore non si calcola per S2, S5 e S6."]}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res["riferimento"], ensure_ascii=False), "sensibilità", alt["minimo_eur"], alt["massimo_eur"])
