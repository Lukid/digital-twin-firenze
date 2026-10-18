#!/usr/bin/env python3
"""F4, compito 2 (D45): residenti stimati per civico e quota di residenti raggiunti entro le soglie di un job di accessibilità.

Stima dichiarata: i residenti 2011 di ogni sezione di censimento (src_rt_censimento2011 su src_fi_sezioni2011) sono ripartiti in parti uguali
sui civici della sezione (src_fi_civici, tutti i civici dentro la sezione, anche fuori dal riquadro delle origini). Civici senza abitazioni
(negozi, uffici, civici rossi) contati come gli altri. Le quote si calcolano sui civici-origine del job con un dato di sezione.

Uso: pipeline/.venv/bin/python analysis/residenti.py   scrive analysis/<area>/residenti_rifugi.json per il job dei 7 rifugi (D32)
Come libreria (strumento estimate_residents del servizio): stima(manifest) -> dict."""
import csv, json, pathlib, sys
from functools import lru_cache
import geopandas as gpd
from shapely.geometry import box

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import accessibilita as A  # noqa: E402

NORM = A.RL.OUT.parent
SEZIONI, CIVICI = NORM / "fi_sezioni2011.gpkg", NORM / "fi_civici.gpkg"
JOB_RIFUGI = "job_e1e75455f7511f7d"   # 7 rifugi insieme, profilo base 1,2 m/s (D32, analysis/run.py)
LIMITI = [("stima_2011", "Residenti del censimento 2011, quindici anni fa: Novoli è cambiato da allora (nuove residenze e studentati)."),
          ("ripartizione_uniforme", "Residenti di ogni sezione ripartiti in parti uguali sui civici della sezione: un condominio e un negozio valgono uguale."),
          ("civici_senza_abitazioni", "Civici senza abitazioni (negozi, uffici, civici rossi) contati come gli altri: tolgono residenti ai civici con abitazioni."),
          ("sezioni_senza_dato", "Sezioni senza riga nel censimento: i loro civici restano fuori dalle quote dei residenti (conteggio nel campo civici_senza_dato)."),
          ("sezioni_tagliate", "Le sezioni che escono dall'area allargata dei civici (campo sezioni_tagliate_dal_ritaglio_dei_civici) hanno civici mancanti: i loro residenti per civico sono sovrastimati."),
          ("civici_non_residenti", "La quota dei civici resta accanto: è il numero calcolato dal motore, i residenti sono una stima sopra di esso.")]


def _snap(p):
    return sorted(set(gpd.read_file(p, columns=["snapshot_id"], ignore_geometry=True)["snapshot_id"]))


@lru_cache(maxsize=1)
def residenti_per_civico():
    """({id civico: residenti stimati o None}, {id civico: residenti con la ripartizione sui soli civici neri}, sezioni tagliate, snapshot)."""
    s = gpd.read_file(SEZIONI)[["CODSEZ2011", "residenti_2011", "geometry"]]
    c = gpd.read_file(CIVICI)[["id", "TIPO", "geometry"]]
    cs = gpd.sjoin(c, s, predicate="within", how="left")
    assert not cs["id"].duplicated().any(), "civico in più sezioni"
    n, n_neri = cs.groupby("CODSEZ2011").size(), cs[cs.TIPO != "R"].groupby("CODSEZ2011").size()
    ha = lambda r: r.residenti_2011 == r.residenti_2011 and r.CODSEZ2011 == r.CODSEZ2011   # NaN: sezione senza riga nel censimento o civico fuori dalle sezioni
    per = {r.id: float(r.residenti_2011) / n[r.CODSEZ2011] if ha(r) else None for r in cs.itertuples()}
    neri = {r.id: float(r.residenti_2011) / n_neri[r.CODSEZ2011] for r in cs.itertuples() if ha(r) and r.TIPO != "R"}   # sensibilità: i rossi in genere non sono abitazioni
    copertura = box(*c.total_bounds)   # i civici sono ritagliati sull'area allargata: una sezione che ne esce ha civici mancanti
    tagliate = {int(x) for x in s[~s.within(copertura)].CODSEZ2011}
    return per, neri, {k: int(v) for k, v in zip(cs["id"], cs["CODSEZ2011"]) if v == v}, tagliate, _snap(SEZIONI) + _snap(CIVICI)


def _origini(manifest):
    a = next((x for x in manifest["assets"] if x["asset_id"] == "ast_origini_csv"), None)
    p = ROOT / a["path"] if a else None
    if not p or not p.exists(): return None
    with open(p) as f: return list(csv.DictReader(f))


def stima(manifest):
    """Residenti stimati raggiunti entro le soglie del job (manifest di compute_walk_access), accanto ai civici. None se mancano le righe per origine."""
    righe = _origini(manifest)
    if righe is None: return None
    per, neri, sez_di, tagliate, snap = residenti_per_civico(); p = manifest["params"]; v0 = p["profile"]["speed_m_s"]
    def minuti(r, v):   # stesso percorso a velocità v, attese invariate (come la sensibilità dei civici in accessibilita.py)
        t, L = float(r["tempo_s"]), float(r["totale_m"]); return (L / v + t - L / v0) / 60
    con = [r for r in righe if per.get(r["origin_id"]) is not None]
    tot, tot_n = sum(per[r["origin_id"]] for r in con), sum(neri.get(r["origin_id"], 0) for r in con); ok = [r for r in con if r["stato"] == "reachable"]
    soglie = []
    for T in p["thresholds_min"]:
        dentro = lambda v, rr=ok: [r for r in rr if minuti(r, v) <= T]
        res = sum(per[r["origin_id"]] for r in dentro(v0))
        soglie.append({"minuti": T, "residenti_stimati": round(res), "quota_residenti": round(res / tot, 4),
                       "intervallo_velocita": [round(sum(per[r["origin_id"]] for r in dentro(v)) / tot, 4) for v in A.SENS_VELOCITA],
                       "quota_civici": round(sum(1 for r in righe if r["stato"] == "reachable" and minuti(r, v0) <= T) / len(righe), 4),
                       "sensibilita_solo_civici_neri": round(sum(neri.get(r["origin_id"], 0) for r in dentro(v0)) / tot_n, 4)})
    sez = {sez_di[r["origin_id"]] for r in con}
    return {"job_id": manifest["job_id"], "destination_ids": p["destination_ids"], "speed_m_s": v0, "civici": len(righe), "civici_con_dato": len(con), "civici_senza_dato": len(righe) - len(con),
            "residenti_stimati_totali": round(tot), "sezioni": len(sez), "sezioni_tagliate_dal_ritaglio_dei_civici": sorted(tagliate & sez),
            "soglie": soglie, "classification": "estimated",
            "metodo": "Residenti 2011 di ogni sezione di censimento divisi in parti uguali fra i civici della sezione; per ogni soglia, somma sui civici-origine raggiunti dal job. "
                      "Quote sui civici con un dato di sezione. Sensibilità: stessi residenti ripartiti solo sui civici neri (i rossi in genere non sono abitazioni).",
            "snapshot_ids": sorted(set(snap) | {"snp_rt_censimento2011_20261010"}),
            "fonti": [{"source_id": "src_rt_censimento2011", "licenza": "CC BY (versione non indicata), Regione Toscana su dati Istat", "data_del_dato": "2011-10-09"},
                      {"source_id": "src_fi_sezioni2011", "licenza": "CC BY 4.0, Comune di Firenze", "data_del_dato": "2011-10-09"},
                      {"source_id": "src_fi_civici", "licenza": "CC BY 4.0, Comune di Firenze", "data_del_dato": "stato alla data di scarico (2026-10-09)"}],
            "limits": [{"code": a, "text": b} for a, b in LIMITI] + [{"code": x["code"], "text": x["text"]} for x in manifest["limits"] if x["code"] != "civici_non_residenti"]}


if __name__ == "__main__":
    m = json.loads((A.OUT_VERS / "manifest" / f"{JOB_RIFUGI}.manifest.json").read_text())
    r = stima(m); assert r, "righe per origine del job dei rifugi mancanti: rieseguire analysis/run.py"
    assert all(s["quota_civici"] == next(x["value"] for x in m["metrics"] if x["metric_id"] == f"served_share_{s['minuti']:g}min".replace(".", "_")) for s in r["soglie"])   # stessi civici del motore
    (A.OUT_VERS / "residenti_rifugi.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n")
    for s in r["soglie"]: print(f"{s['minuti']:g} min: residenti {s['residenti_stimati']} ({s['quota_residenti']:.1%}), civici {s['quota_civici']:.1%}")
