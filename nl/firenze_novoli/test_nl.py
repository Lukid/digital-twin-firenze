#!/usr/bin/env python3
"""F11: controlli sul registro delle domande NL di Firenze Novoli (giro1.json, giro2.json; caldo.json del caso caldo, F4).
Replay di ogni job, confronto con i job della mappa (F06, F07), errori attesi, nessuna percentuale senza job.
Uso: service/.venv/bin/python nl/firenze_novoli/test_nl.py"""
import gzip, json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "service"))
import core, replay

log = [q for f in ("giro1.json", "giro2.json", "caldo.json") for q in json.loads((HERE / f).read_text())]
jobs = {c["job_id"]: q["n"] for q in log for c in q["chiamate"] if c["esito"] == "ok" and c["job_id"]}

# 1. nessuna percentuale o minuto calcolato in una risposta senza un job riuscito
#    (numeri_senza_job ammesso solo per un conteggio ricavato da una quota del job della stessa domanda, domanda 3)
for q in log:
    assert not q["numeri_senza_job"] or any(c["job_id"] for c in q["chiamate"]), q["n"]
    if re.search(r"\d+,\d+ ?(%|minut)", q["risposta"]):
        assert any(c["job_id"] for c in q["chiamate"]) or "job_" in q["risposta"], q["n"]

# 2. ogni job del client ha un manifest versionato (non solo in cache); replay identico per accessibilità e ombra
versionati = [ROOT / d / "firenze_novoli/manifest" for d in ("analysis", "shadow", "nl")]
for job_id, n in jobs.items():
    assert any((d / f"{job_id}.manifest.json").exists() for d in versionati), (n, job_id)
    m = core._read_job(job_id, "manifest")
    if m["tool"] not in ("compute_walk_access", "compute_shadow"): continue   # il confronto scenari non ha replay
    r = replay.replay(job_id); assert r.get("match"), (n, r); print("replay ok", n, job_id)

# 3a. accessibilità: il client riusa i job di F06 che alimentano la mappa (stesso job_id)
f06 = {p.name.split(".")[0] for p in (ROOT / "analysis/firenze_novoli/manifest").glob("*.manifest.json")}
for job_id in ("job_9b2e74744a8d2865", "job_22778e8ad5f27e8c", "job_f5a4969062095f90", "job_b83ab974753edcb9", "job_7ba17d19047e3f5b"):   # Polo (7 ingressi), San Donato - Università, Torre degli Agli, Regione, Vamba a 1,2 m/s
    assert job_id in jobs and job_id in f06, job_id

# 3b. ombra: metri in ombra del client (caso veg_lidar_tipico) = metri dei tratti in ombra nella mappa, stesso istante
mappa = json.loads(gzip.open(ROOT / "scene/firenze_novoli/assets/ombra.json.gz").read())
def m_mappa(ist, rid):
    i = next(x for x in mappa["istanti"] if x["istante"] == ist)
    return {t["m"] for t in i["tratti"] if t["id"] == rid}.pop()
for job_id, ist, rid in (("job_753fc5aff57df501", "2026-07-15T12:00", "pth_fi_R01"), ("job_6c05deb15ab1344c", "2026-09-15T12:30", "pth_fi_R02")):
    met = {x["metric_id"]: x["value"] for x in core._read_job(job_id, "manifest")["metrics"]}
    righe = json.loads((HERE / "manifest" / f"{job_id}.summary.json").read_text())["summary"]
    lung = next(x["length_m"] for x in righe if x["caso"] == "veg_lidar_tipico")
    m = met[f"{rid.lower()}_tutti_shade_fraction_veg"] * lung
    assert abs(m - m_mappa(ist, rid)) < 0.5, (job_id, m, m_mappa(ist, rid))

# 3c. caso caldo (F4): dieci domande, bozza dichiarata; residenti e percorsi esposti uguali ai file versionati
caldo = json.loads((HERE / "caldo.json").read_text())
assert len(caldo) == 10 and all("da validare" in q["origine"] for q in caldo) and sum("Non lo so" in q["risposta"] for q in caldo) >= 2
r = core.run_tool("estimate_residents", {"job_id": "job_e1e75455f7511f7d"}); assert "6.092" in caldo[0]["risposta"] and r["soglie"][1]["residenti_stimati"] == 6092
o = core.run_tool("get_shaded_access", {"job_id": "job_e1e75455f7511f7d", "date": "2026-07-15"})["soglie"]   # F5 (D49): arrivare soprattutto all'ombra
fmt = lambda x: f"{x * 100:.1f}%".replace(".", ",")
assert all(t in caldo[0]["risposta"] for t in (f"circa {o[0]['soprattutto_ombra']['residenti_stimati']} residenti stimati ({fmt(o[0]['soprattutto_ombra']['quota_residenti'])})",
                                               f"{o[0]['sensibilita_soglia']['40%']['residenti_stimati']} ({fmt(o[0]['sensibilita_soglia']['40%']['quota_residenti'])})",
                                               f"{o[1]['soprattutto_ombra']['residenti_stimati']} soprattutto all'ombra ({fmt(o[1]['soprattutto_ombra']['quota_residenti'])})"))
mm = lambda x: f"{x:.1f}".replace(".", ",")   # F6 (D53): indicatore di riserva, senza soglia
assert all(t in caldo[0]["risposta"] for t in (f"in media per il {fmt(o[0]['riserva']['ombra_media'])}", f"{mm(o[0]['riserva']['minuti_sole_quartili'][1])} minuti in mediana",
                                               f"ombra media {fmt(o[1]['riserva']['ombra_media'])}", f"{mm(o[1]['riserva']['minuti_sole_quartili'][1])} minuti al sole in mediana"))
e = core.run_tool("get_route_exposure", {"date": "2026-07-15"}); assert e["classifica"]["14:00"]["per_metri_al_sole"][:3] == ["RC4", "R10", "R03"] and all(e["percorsi"][x]["job_id"] in caldo[1]["risposta"] for x in ("RC4", "R10", "R03"))

# 4. errori attesi, oggi
A = {"baseline_id": "bas_firenze_novoli_20261009", "origins": {"kind": "address_points", "aoi_id": "aoi_firenze_novoli"},
     "destination_ids": ["dst_tram_fm9057"], "profile": {"speed_m_s": 1.2}, "thresholds_min": [10]}
S = {"baseline_id": "bas_firenze_novoli_20261009", "receivers": [{"route_id": "R01"}], "when": {"date": "2026-10-25", "timezone": "Europe/Rome", "times": ["02:30"]},
     "method": {"name": "geometric_ray", "space_step_m": 2, "time_step_min": 10, "obstacles": "buildings_and_trees"}}
code = lambda r: r.get("error", {}).get("code")
assert code(core.run_tool("compute_walk_access", {**A, "thresholds_min": [10, 10.0]})) == "invalid_params"
assert core.run_tool("compute_walk_access", {**A, "destination_ids": ["dst_tram_fm9057", "dst_tram_fm9056"]})["status"] == "succeeded"   # dopo il giro: più destinazioni = almeno una
assert code(core.run_tool("compute_shadow", S)) == "invalid_params"
assert core.run_tool("list_destinations", {"aoi_id": "aoi_firenze_novoli", "category": "hospital"})["destinations"] == []
assert code(core.run_tool("compare_scenarios", {"baseline_id": "bas_firenze_novoli_20261009", "scenario_ids": ["scn_fi_s1_filare_r01"], "weights": {"r01_minuti_sole_evitati_mezzogiorno": 0.7}})) == "invalid_params"   # F5: weights tolto dallo schema
print(f"TUTTO OK: {len(log)} domande, {len(jobs)} job")
