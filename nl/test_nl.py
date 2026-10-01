#!/usr/bin/env python3
"""T12: controlli sul registro delle domande NL (giro1.json, giro2.json).
Replay di ogni job, confronto con i job della mappa, errori attesi, nessuna percentuale senza job.
Uso: service/.venv/bin/python nl/test_nl.py"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "service"))
import core, replay

log = [q for f in ("giro1.json", "giro2.json") for q in json.loads((ROOT / "nl" / f).read_text())]
jobs = {c["job_id"]: q["n"] for q in log for c in q["chiamate"] if c["esito"] == "ok" and c["job_id"]}

# 1. nessuna percentuale o minuto calcolato in una risposta senza un job riuscito
for q in log:
    if re.search(r"\d+,\d+ ?(%|minut)", q["risposta"]):
        assert any(c["job_id"] for c in q["chiamate"]) or "job_" in q["risposta"], q["n"]

# 2. ogni job del client ha manifest; replay identico (il 19 è una richiesta oggi respinta, il confronto scenari non ha replay)
for job_id, n in jobs.items():
    m = core._read_job(job_id, "manifest"); assert m, job_id
    if n == "19" or m["tool"] not in ("compute_walk_access", "compute_shadow"): continue
    r = replay.replay(job_id); assert r.get("match"), (n, r); print("replay ok", n, job_id)

# 3. stesso numero della mappa (scene/data/manifest) a parità di destinazione, velocità e soglia
def val(job_id, metric):
    p = ROOT / "scene/data/manifest" / f"{job_id}.manifest.json"
    m = json.loads(p.read_text()) if p.exists() else core._read_job(job_id, "manifest")
    return next(x["value"] for x in m["metrics"] if x["metric_id"] == metric)
for client, mappa, metric in (("job_0aa2e2b7eb66d9a3", "job_4d23232eb780b0c1", "served_share_10min"),   # Battisti 1,2
                              ("job_3501de141b1a1fdd", "job_e75df500a3191354", "served_share_10min"),   # Battisti 0,8
                              ("job_69ce2bf070e45d8e", "job_9cc7481bc4f55863", "served_share_10min"),   # Pellico 1,2
                              ("job_82611e96ad366647", "job_9cc7481bc4f55863", "served_share_15min")):  # Pellico 1,2, 15 min
    assert val(client, metric) == val(mappa, metric), (client, mappa, metric)

# 4. errori attesi, oggi
A = {"baseline_id": "bas_z2_20261001", "origins": {"kind": "civici_sit_z2"}, "destination_ids": ["dst_school_piee82101p"], "profile": {"speed_m_s": 1.2}, "thresholds_min": [10]}
S = {"baseline_id": "bas_z2_20261001", "receivers": [{"route_id": "R01"}], "when": {"date": "2026-10-25", "timezone": "Europe/Rome", "times": ["02:30"]},
     "method": {"name": "geometric_ray", "space_step_m": 2, "time_step_min": 10, "obstacles": "buildings_and_trees"}}
code = lambda r: r.get("error", {}).get("code")
assert code(core.run_tool("compute_walk_access", {**A, "thresholds_min": [10, 10.0]})) == "invalid_params"
assert code(core.run_tool("compute_walk_access", {**A, "destination_ids": ["dst_school_piee82101p", "dst_stop_pi4390"]})) == "limit_exceeded"
assert code(core.run_tool("compute_shadow", S)) == "invalid_params"
assert core.run_tool("list_destinations", {"aoi_id": "aoi_z2", "category": "hospital"})["destinations"] == []
print(f"TUTTO OK: {len(log)} domande, {len(jobs)} job")
