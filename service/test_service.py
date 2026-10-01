#!/usr/bin/env python3
"""Test del servizio T07. Uso: service/.venv/bin/python service/test_service.py (usa una cache temporanea, tocca solo service/)."""
import asyncio, json, os, pathlib, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
CACHE = HERE / ".cache_test"; shutil.rmtree(CACHE, ignore_errors=True)
os.environ["DT_CACHE_DIR"] = str(CACHE)
sys.path.insert(0, str(HERE))
import core, replay  # noqa: E402

BATT = "dst_school_piee82101p"
A = {"baseline_id": "bas_z2_20261001", "origins": {"kind": "civici_sit_z2"}, "destination_ids": [BATT], "profile": {"speed_m_s": 1.2}, "thresholds_min": [5, 10, 15]}
err_code = lambda r: r.get("error", {}).get("code")
strip = lambda r: {k: v for k, v in r.items() if k != "cached"}

# 1. stesso input = stesso job_id e cache; ordine delle chiavi irrilevante; default espliciti = default impliciti
r1 = core.run_tool("compute_walk_access", A)
assert r1["status"] == "succeeded" and r1["cached"] is False and r1["job_id"].startswith("job_"), r1
r2 = core.run_tool("compute_walk_access", dict(reversed(list(A.items()))))
assert r2["cached"] is True and r2["job_id"] == r1["job_id"] and strip(r1) == strip(r2)
r3 = core.run_tool("compute_walk_access", {**A, "profile": {"speed_m_s": 1.2, "crossing_penalty_s": 0, "stairs": "allowed", "snap_limit_m": 40}})
assert r3["job_id"] == r1["job_id"] and r3["cached"] is True
r4 = core.run_tool("compute_walk_access", {**A, "profile": {"speed_m_s": 0.8, "crossing_penalty_s": 10, "stairs": "excluded"}})
assert r4["job_id"] != r1["job_id"] and r4["cached"] is False
assert core.validate("compute_walk_access", "output", r1) == []
for k in ("job_id", "datasets", "params", "limits", "headline_metrics"): assert r1[k], k
assert (CACHE / f"{r1['job_id']}.manifest.json").exists() and (CACHE / f"{r1['job_id']}.job.json").exists()
man = core.run_tool("get_result_manifest", {"job_id": r1["job_id"]})
assert man["manifest_id"] == r1["result_manifest_id"] and man["metrics"] == r1["headline_metrics"]
assert core.run_tool("get_job_status", {"job_id": r1["job_id"]})["status"] == "succeeded"
assert err_code(core.run_tool("get_job_status", {"job_id": "job_0000000000000000"})) == "unknown_id"

# 2. input non valido respinto prima del calcolo
for bad in ({**A, "sql": "select 1"}, {**A, "profile": {"speed_m_s": 12}}, {**A, "profile": {"speed_m_s": 1.2, "stairs": "forse"}}, {**A, "thresholds_min": []},
            {**A, "entrance_ids": ["ingresso principale"]}, {k: v for k, v in A.items() if k != "profile"}):
    assert err_code(core.run_tool("compute_walk_access", bad)) == "invalid_params", bad
assert err_code(core.run_tool("compute_walk_access", {**A, "entrance_ids": ["ent_osm_n5278157573"]})) == "invalid_params"   # ingresso di un'altra destinazione
assert err_code(core.run_tool("compute_walk_access", {**A, "destination_ids": ["dst_school_inesistente"]})) == "unknown_id"
assert err_code(core.run_tool("compute_walk_access", {**A, "destination_ids": [BATT, "dst_stop_pi4390"]})) == "limit_exceeded"
assert err_code(core.run_tool("compute_walk_access", {**A, "origins": {"kind": "grid", "aoi_id": "aoi_z2", "spacing_m": 20}})) == "outside_capability"
assert err_code(core.run_tool("compute_walk_access", {**A, "baseline_id": "bas_altra"})) == "incompatible_baseline"

# 3. destinazione ambigua o mancante: errore con alternative, mai scelta implicita
for ids in (["la scuola"], ["stazione"], [], None):
    a = {k: v for k, v in A.items() if k != "destination_ids"}; a.update({} if ids is None else {"destination_ids": ids})
    r = core.run_tool("compute_walk_access", a)
    assert err_code(r) == "ambiguous_destination" and r["error"]["candidates"], (ids, r)
assert len(core.run_tool("compute_walk_access", {**{k: v for k, v in A.items() if k != "destination_ids"}, "destination_ids": ["stazione"]})["error"]["candidates"]) > 1
croce = core.run_tool("list_destinations", {"aoi_id": "aoi_z2", "category": "stop", "name_query": "CROCE 2"})["destinations"]
assert len(croce) == 2   # due fermate con lo stesso nome: l'ambiguità è visibile

# 4. strumenti di lettura
src = core.run_tool("list_approved_sources", {"theme": "trasporto", "aoi_id": "aoi_z2"})
assert core.validate("list_approved_sources", "output", src) == [] and src["sources"] and all(s["permitted_use"] and s["license_state"] for s in src["sources"])
assert core.run_tool("list_approved_sources", {"theme": "verde", "aoi_id": "aoi_z2"})["gaps"]
ins = core.run_tool("inspect_dataset", {"source_id": "src_sit_civici"})
assert core.validate("inspect_dataset", "output", ins) == [] and ins["license"]["state"] == "unproven"
assert core.validate("list_destinations", "output", core.run_tool("list_destinations", {"aoi_id": "aoi_z2", "category": "school"})) == []

# 5. strumenti d'ombra e scenari: fuori capacità finché il motore non c'è
for tool, args in (("compute_shadow", {}), ("create_local_scenario", {"x": 1}), ("compare_scenarios", None)):
    assert err_code(core.run_tool(tool, args)) == "outside_capability", tool

# 6. replay coincide (job appena calcolato e job storico di analysis/manifest)
rp = replay.replay(r4["job_id"]); assert rp["match"] and rp["metrics_compared"] > 10, rp
rp = replay.replay("job_4d23232eb780b0c1"); assert rp["match"], rp

# 7. CLI e MCP stdio reale: stesso risultato, stesso job_id
def cli(*a):
    p = subprocess.run([sys.executable, str(HERE / "cli.py"), *a], capture_output=True, text=True, env=os.environ)
    return json.loads(p.stdout), p.returncode
c, rc = cli("compute_walk_access", json.dumps(A)); assert rc == 0 and strip(c) == strip(r1)
c, rc = cli("compute_walk_access", json.dumps({**A, "destination_ids": ["scuola"]})); assert rc == 1 and err_code(c) == "ambiguous_destination"


async def mcp_test():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "mcp_server.py")], env=dict(os.environ))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name: t for t in (await s.list_tools()).tools}
            assert set(tools) == set(core.TOOLS), set(tools)
            assert all(t.inputSchema.get("additionalProperties") is False for t in tools.values())   # niente campi liberi (SQL, codice)
            res = await s.call_tool("compute_walk_access", A)
            m = json.loads(res.content[0].text); assert not res.isError and strip(m) == strip(r1) and res.structuredContent == m
            res = await s.call_tool("compute_walk_access", {**A, "destination_ids": ["scuola"]})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "ambiguous_destination"
            res = await s.call_tool("compute_shadow", {})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "outside_capability"
            res = await s.call_tool("compute_walk_access", {**A, "sql": "drop table x"})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "invalid_params"
            res = await s.call_tool("get_result_manifest", {"job_id": r1["job_id"]})
            assert json.loads(res.content[0].text)["job_id"] == r1["job_id"]
asyncio.run(mcp_test())

shutil.rmtree(CACHE, ignore_errors=True)
print("TUTTO OK")
