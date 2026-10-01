#!/usr/bin/env python3
"""Replay: riesegue un job dal suo manifest (senza cache) e confronta job_id, metriche e conteggi. Uso: replay.py <job_id>"""
import json, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import core


def _input_da_manifest(m):
    p = m["params"]
    return {"baseline_id": m["baseline_id"], "origins": {"kind": p["origins"]["kind"]}, "destination_ids": p["destination_ids"], "entrance_ids": p["entrance_ids"],
            "profile": p["profile"], "thresholds_min": p["thresholds_min"]}


def replay(job_id):
    m = core._read_job(job_id, "manifest")
    if not m: return core.err("unknown_id", f"Nessun manifest per {job_id}.")
    if m["tool"] != "compute_walk_access": return core.err("outside_capability", f"Replay non disponibile per {m['tool']}.")
    args = _input_da_manifest(m); kw = core._risolvi_walk(args)
    if "error" in kw: return kw
    with tempfile.TemporaryDirectory(dir=core.ROOT / "service") as td:   # sotto ROOT: i percorsi degli asset sono relativi a ROOT
        r = core._esegui(kw, store=False, out_dir=pathlib.Path(td))
    if "error" in r: return r
    old = {x["metric_id"]: x for x in m["metrics"]}; new = {x["metric_id"]: x for x in r["headline_metrics"]}
    diffs = [f"metrica {k}: {old.get(k, {}).get('value')} -> {new.get(k, {}).get('value')}" for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
    if r["job_id"] != job_id: diffs.append(f"job_id {job_id} -> {r['job_id']}")
    if r["params"] != m["params"]: diffs.append("parametri diversi")
    return {"job_id": job_id, "match": not diffs, "metrics_compared": len(old), "differences": diffs}


if __name__ == "__main__":
    r = replay(sys.argv[1]); print(json.dumps(r, ensure_ascii=False, indent=1)); sys.exit(0 if r.get("match") else 1)
