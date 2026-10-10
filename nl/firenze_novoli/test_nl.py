#!/usr/bin/env python3
"""F11: controlli sul registro delle domande NL di Firenze Novoli (giro1.json, giro2.json).
Replay di ogni job, confronto con i job della mappa (F06, F07), errori attesi, nessuna percentuale senza job.
Uso: service/.venv/bin/python nl/firenze_novoli/test_nl.py"""
import gzip, json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "service"))
import core, replay

log = [q for f in ("giro1.json", "giro2.json") for q in json.loads((HERE / f).read_text())]
jobs = {c["job_id"]: q["n"] for q in log for c in q["chiamate"] if c["esito"] == "ok" and c["job_id"]}

# 1. nessuna percentuale o minuto calcolato in una risposta senza un job riuscito
for q in log:
    assert not q["numeri_senza_job"], q["n"]
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
for job_id in ("job_90ef3449d76b161a", "job_f5a4969062095f90", "job_b83ab974753edcb9", "job_7ba17d19047e3f5b"):   # Polo, Torre degli Agli, Regione, Vamba a 1,2 m/s
    assert job_id in jobs and job_id in f06, job_id

# 3b. ombra: metri in ombra del client (caso veg_lidar_tipico) = metri dei tratti in ombra nella mappa, stesso istante
mappa = json.loads(gzip.open(ROOT / "scene/firenze_novoli/assets/ombra.json.gz").read())
def m_mappa(ist, rid):
    i = next(x for x in mappa["istanti"] if x["istante"] == ist)
    return {t["m"] for t in i["tratti"] if t["id"] == rid}.pop()
for job_id, ist, rid in (("job_3a59d92a2988881b", "2026-07-15T12:00", "pth_fi_R01"), ("job_95ac09c7726dff17", "2026-09-15T12:30", "pth_fi_R02")):
    met = {x["metric_id"]: x["value"] for x in core._read_job(job_id, "manifest")["metrics"]}
    righe = json.loads((HERE / "manifest" / f"{job_id}.summary.json").read_text())["summary"]
    lung = next(x["length_m"] for x in righe if x["caso"] == "veg_lidar_tipico")
    m = met[f"{rid.lower()}_tutti_shade_fraction_veg"] * lung
    assert abs(m - m_mappa(ist, rid)) < 0.5, (job_id, m, m_mappa(ist, rid))

# 4. errori attesi, oggi
A = {"baseline_id": "bas_firenze_novoli_20261009", "origins": {"kind": "address_points", "aoi_id": "aoi_firenze_novoli"},
     "destination_ids": ["dst_tram_fm9057"], "profile": {"speed_m_s": 1.2}, "thresholds_min": [10]}
S = {"baseline_id": "bas_firenze_novoli_20261009", "receivers": [{"route_id": "R01"}], "when": {"date": "2026-10-25", "timezone": "Europe/Rome", "times": ["02:30"]},
     "method": {"name": "geometric_ray", "space_step_m": 2, "time_step_min": 10, "obstacles": "buildings_and_trees"}}
code = lambda r: r.get("error", {}).get("code")
assert code(core.run_tool("compute_walk_access", {**A, "thresholds_min": [10, 10.0]})) == "invalid_params"
assert code(core.run_tool("compute_walk_access", {**A, "destination_ids": ["dst_tram_fm9057", "dst_tram_fm9056"]})) == "limit_exceeded"
assert code(core.run_tool("compute_shadow", S)) == "invalid_params"
assert core.run_tool("list_destinations", {"aoi_id": "aoi_firenze_novoli", "category": "hospital"})["destinations"] == []
assert code(core.run_tool("compare_scenarios", {"baseline_id": "bas_firenze_novoli_20261009", "scenario_ids": ["scn_fi_s1_filare_r01"], "weights": {"r01_minuti_sole_evitati_mezzogiorno": 0.7}})) == "outside_capability"
print(f"TUTTO OK: {len(log)} domande, {len(jobs)} job")
