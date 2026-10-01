#!/usr/bin/env python3
"""Test del servizio T07. Uso: service/.venv/bin/python service/test_service.py (usa una cache temporanea, tocca solo service/)."""
import asyncio, json, os, pathlib, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
CACHE = HERE / ".cache_test"; shutil.rmtree(CACHE, ignore_errors=True)
os.environ["DT_CACHE_DIR"] = str(CACHE)
os.environ["DT_SCENARIOS_DIR"] = str(CACHE / "scenari")   # scenari creati dal test: nella cache temporanea, non in data/norm
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
for bad in ({**A, "sql": "select 1"}, {**A, "profile": {"speed_m_s": 12}}, {**A, "profile": {"speed_m_s": 1.2, "stairs": "forse"}}, {**A, "thresholds_min": []}, {**A, "thresholds_min": [10, 10.0]},
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

# 5. scenari (T10): input non validi respinti prima di qualunque calcolo
for tool, args in (("create_local_scenario", {"x": 1}), ("compare_scenarios", None), ("compare_scenarios", {"manifest_ids": ["man_0123456789abcdef"] * 2, "metric_ids": ["x"]})):
    assert err_code(core.run_tool(tool, args)) == "invalid_params", tool

# 5b. ombra (T09)
SH = {"baseline_id": "bas_z2_20261001", "receivers": [{"route_id": "R01"}], "when": {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ["08:00", "13:00", "16:30"]},
      "method": {"name": "geometric_ray", "space_step_m": 1, "time_step_min": 5, "obstacles": "buildings_and_trees"}}
s1 = core.run_tool("compute_shadow", SH)
assert s1["status"] == "succeeded" and s1["cached"] is False and core.validate("compute_shadow", "output", s1) == [], s1
assert s1["cases"] == ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max"] and s1["sun_state_counts"] == {"ok": 18}
assert s1["datasets"] and s1["limits"] and s1["params"] and s1["headline_metrics"]
s2 = core.run_tool("compute_shadow", SH); assert s2["cached"] is True and strip(s2) == strip(s1)
assert core.run_tool("get_result_manifest", {"job_id": s1["job_id"]})["tool"] == "compute_shadow"
shw = lambda **k: {**SH, "when": {**SH["when"], **k}}
r = core.run_tool("compute_shadow", shw(date="2026-10-25", times=["02:30"])); assert err_code(r) == "invalid_params" and "ambigua" in r["error"]["message"], r   # fine ora legale
r = core.run_tool("compute_shadow", shw(date="2026-03-29", times=["02:30"])); assert err_code(r) == "invalid_params" and "inesistente" in r["error"]["message"], r
r = core.run_tool("compute_shadow", shw(date="2026-12-21", times=["06:00", "12:00"]))   # inverno: alba sotto l'orizzonte, mezzogiorno sole basso
assert r["status"] == "succeeded" and set(r["sun_state_counts"]) <= {"ok", "sole_sotto_orizzonte", "sole_basso_fuori_supporto"} and r["sun_state_counts"].get("sole_sotto_orizzonte"), r["sun_state_counts"]
big = {**SH, "receivers": [{"route_id": i} for i in ("R01", "R03", "R04", "R05")], "when": {**SH["when"], "times": [f"{m // 60:02d}:{m % 60:02d}" for m in range(0, 1440, 15)]}}
r = core.run_tool("compute_shadow", big); assert err_code(r) == "limit_exceeded" and r["error"]["smaller_request"], r
assert core.validate("compute_shadow", "input", r["error"]["smaller_request"]) == []
assert err_code(core.run_tool("compute_shadow", {**SH, "receivers": [{"route_id": "R99"}]})) == "unknown_id"
assert err_code(core.run_tool("compute_shadow", {**SH, "scenario_id": "scn_x_y", "method": {**SH["method"], "obstacles": "buildings_and_scenario"}})) == "unknown_id"
assert err_code(core.run_tool("compute_shadow", {**SH, "method": {**SH["method"], "obstacles": "buildings_and_scenario"}})) == "invalid_params"   # senza scenario_id
assert err_code(core.run_tool("compute_shadow", {**SH, "scenario_id": "scn_z2_s2_pensilina_pellico"})) == "invalid_params"                         # con scenario_id serve buildings_and_scenario
assert err_code(core.run_tool("compute_shadow", {**SH, "sql": "x"})) == "invalid_params"
assert replay.replay(s1["job_id"])["match"]

# 5c. scenari e confronto (T10)
import copy
from jsonschema import Draft202012Validator
sch, reg = core._registry()
valida_man = lambda m: [e.message for e in Draft202012Validator({"$ref": sch["manifest.schema.json"]["$id"]}, registry=reg).iter_errors(m)]
EX = lambda n: json.loads((HERE.parent / "contracts/examples" / n).read_text())
ALBERO = EX("mcp.create_local_scenario.input.valid.2.json")
sc1 = core.run_tool("create_local_scenario", ALBERO)
assert sc1["version"] == 1 and sc1["scenario_id"].startswith("scn_z2_") and sc1["cached"] is False and core.validate("create_local_scenario", "output", sc1) == [], sc1
assert set(sc1["feasibility"].values()) == {"ignota"} and sc1["interventions"]["alberi"] == 1
sc1b = core.run_tool("create_local_scenario", dict(reversed(list(ALBERO.items()))))
assert sc1b["scenario_id"] == sc1["scenario_id"] and sc1b["cached"] is True                    # stesso input = stesso scenario
op = ALBERO["operations"][0]
bad = copy.deepcopy(ALBERO); bad["operations"][0]["dimensions"]["crown_base_m"]["value"] = 9.0
assert err_code(core.run_tool("create_local_scenario", bad)) == "invalid_params"              # imposta oltre metà altezza
bad = copy.deepcopy(ALBERO); del bad["operations"][0]["dimensions"]["crown_diameter_m"]
assert err_code(core.run_tool("create_local_scenario", bad)) == "invalid_params"
bad = copy.deepcopy(ALBERO); bad["operations"][0].update(op="remove", target_id="tre_osm_1")
assert err_code(core.run_tool("create_local_scenario", bad)) == "outside_capability"           # rimozioni non supportate
bad = copy.deepcopy(ALBERO); bad["operations"][0]["hypothesis_status"] = "feasibility_checked"
assert err_code(core.run_tool("create_local_scenario", bad)) == "invalid_params"              # la fattibilità non è mai verificata qui
assert err_code(core.run_tool("create_local_scenario", EX("mcp.create_local_scenario.input.invalid.json"))) == "invalid_params"
assert err_code(core.run_tool("create_local_scenario", {**ALBERO, "baseline_id": "bas_altra"})) == "incompatible_baseline"
S_, C_ = core._sc(); edif = S_._contesto_geo()["bld"][0].representative_point()
inside = copy.deepcopy(ALBERO); inside["scenario_title"] = "Albero dentro un edificio (prova di segnalazione)"; inside["operations"][0]["geometry"]["coordinates"] = [round(edif.x, 2), round(edif.y, 2)]
r = core.run_tool("create_local_scenario", inside); assert "error" not in r and any(w["code"] == "dentro_edificio" for w in r["warnings"]), r   # segnala, non blocca
nullo = core.run_tool("create_local_scenario", {"baseline_id": "bas_z2_20261001", "scenario_title": "Scenario senza interventi", "operations": []})
assert nullo["interventions"]["alberi"] == 0 and core.validate("create_local_scenario", "output", nullo) == []

ST = {**SH, "method": {**SH["method"], "obstacles": "buildings_and_scenario"}, "scenario_id": sc1["scenario_id"]}
SB = {**SH, "method": {**SH["method"], "obstacles": "documented_buildings_only"}}
pb = core.run_tool("compute_shadow", SB); assert pb["status"] == "succeeded" and core.validate("compute_shadow", "output", pb) == []
ps = core.run_tool("compute_shadow", ST)
assert ps["status"] == "succeeded" and ps["cached"] is False and ps["scenario_id"] == sc1["scenario_id"] and core.validate("compute_shadow", "output", ps) == [], ps
assert ps["job_id"] != pb["job_id"] and ps["cases"] == ["base", "base_h_min", "base_h_max"]
ps2 = core.run_tool("compute_shadow", ST); assert ps2["cached"] is True and ps2["job_id"] == ps["job_id"] and strip(ps2) == strip(ps)   # stesso input = stesso job
assert valida_man(core.run_tool("get_result_manifest", {"job_id": ps["job_id"]})) == []
assert err_code(core.run_tool("compute_shadow", {**ST, "scenario_id": "scn_z2_inesistente"})) == "unknown_id"
nz = core.run_tool("compute_shadow", {**ST, "scenario_id": nullo["scenario_id"]})                                     # scenario nullo = baseline
assert nz["status"] == "succeeded" and {m["metric_id"]: m["value"] for m in nz["headline_metrics"]} == {m["metric_id"]: m["value"] for m in pb["headline_metrics"]}
assert replay.replay(ps["job_id"])["match"]                                                                          # replay del job di scenario
# compare_scenarios, forma 1: delta fra manifest
cmp1 = core.run_tool("compare_scenarios", {"manifest_ids": [pb["result_manifest_id"], ps["result_manifest_id"]], "metric_ids": ["shade_fraction"]})
assert core.validate("compare_scenarios", "output", cmp1) == [] and cmp1["incompatibilities"] == [] and cmp1["deltas"] and cmp1["job_id"].startswith("job_"), cmp1
assert all(d["delta"] >= -1e-9 for d in cmp1["deltas"]) and all(d["delta_low"] <= d["delta"] <= d["delta_high"] for d in cmp1["deltas"])   # un albero non riduce l'ombra
assert cmp1["common_conditions"]["receivers"] and valida_man(core.run_tool("get_result_manifest", {"job_id": cmp1["job_id"]})) == []
assert core.run_tool("compare_scenarios", {"manifest_ids": [pb["result_manifest_id"], ps["result_manifest_id"]], "metric_ids": ["shade_fraction"]})["cached"] is True
cz = core.run_tool("compare_scenarios", {"manifest_ids": [pb["result_manifest_id"], nz["result_manifest_id"]], "metric_ids": ["shade_fraction", "walk_sun_min"]})
assert cz["deltas"] and all(abs(d["delta"]) <= 1e-6 and d["discriminates"] is False for d in cz["deltas"]), cz                # scenario nullo: delta zero, non discrimina
other = core.run_tool("compute_shadow", {**ST, "when": {**ST["when"], "date": "2026-06-21"}})
r = core.run_tool("compare_scenarios", {"manifest_ids": [pb["result_manifest_id"], other["result_manifest_id"]], "metric_ids": ["shade_fraction"]})
assert err_code(r) == "incompatible_baseline" and "when" in r["error"]["message"], r                                      # condizioni non comuni: respinto
assert err_code(core.run_tool("compare_scenarios", {"manifest_ids": [pb["result_manifest_id"], "man_0000000000000000"], "metric_ids": ["shade_fraction"]})) == "unknown_id"
# compare_scenarios, forma 2: confronto multicriterio sugli scenari dimostrativi (ombre in cache di scenarios/, altrimenti qualche minuto)
CS = {"baseline_id": "bas_z2_20261001", "scenario_ids": ["scn_z2_s1_filare_r01", "scn_z2_s2_pensilina_pellico"]}
mc = core.run_tool("compare_scenarios", CS)
assert core.validate("compare_scenarios", "output", mc) == [] and mc["cached"] is False and mc["incompatibilities"] == [] and "ranking" not in mc, mc.get("error")
assert mc["deltas"] and set(mc["scenarios"]) == set(CS["scenario_ids"]) and mc["indicators"]["valori"]
for sid in CS["scenario_ids"]:
    e = mc["scenarios"][sid]; assert e["stato"] == "confrontato" and set(e["fattibilita"].values()) == {"ignota"} and e["accessibilita"]["nullo"] is True
assert "civici" in " ".join(l["text"] for l in mc["limits"]) and "non sono persone" in " ".join(l["text"] for l in mc["limits"])
mc2 = core.run_tool("compare_scenarios", CS); assert mc2["cached"] is True and mc2["job_id"] == mc["job_id"]
w = {"r01_minuti_sole_evitati_mezzogiorno": 2, "area_attesa_ombra_mezzogiorno": 1}
mw = core.run_tool("compare_scenarios", {**CS, "weights": w}); assert mw["ranking"]["pesi"] == w and mw["ranking"]["ordine"] and "non è una raccomandazione" in mw["ranking"]["avvertenza"] and mw["job_id"] == mc["job_id"]   # i pesi non cambiano il job
me = core.run_tool("compare_scenarios", {**CS, "context": "entrambi"})   # secondo contesto: edifici + alberi esistenti (ombre in cache di scenarios/)
assert core.validate("compare_scenarios", "output", me) == [] and me["job_id"] != mc["job_id"] and any(d["metric_id"].endswith("_alb") for d in me["deltas"]), me.get("error")
assert me["scenarios"]["scn_z2_s1_filare_r01"]["con_alberi_esistenti"]["stato"] == "confrontato" and me["scenarios"]["scn_z2_s1_filare_r01"]["sovrapposizioni_alberi_esistenti"]
assert err_code(core.run_tool("compare_scenarios", {**CS, "context": "tutti"})) == "invalid_params"
assert err_code(core.run_tool("compare_scenarios", {**CS, "weights": {"punteggio_unico": 1}})) == "invalid_params"
assert err_code(core.run_tool("compare_scenarios", {**CS, "scenario_ids": ["scn_z2_inesistente"]})) == "unknown_id"
assert err_code(core.run_tool("compare_scenarios", {**CS, "baseline_id": "bas_altra"})) == "incompatible_baseline"
assert valida_man(core.run_tool("get_result_manifest", {"job_id": mc["job_id"]})) == []

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
            res = await s.call_tool("compute_shadow", SH)
            m = json.loads(res.content[0].text); assert not res.isError and m["cached"] is True and strip(m) == strip(s1)
            res = await s.call_tool("compute_shadow", shw(date="2026-10-25", times=["02:30"]))
            assert res.isError and "ambigua" in json.loads(res.content[0].text)["error"]["message"]
            res = await s.call_tool("compute_shadow", big)
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "limit_exceeded"
            res = await s.call_tool("create_local_scenario", {})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "invalid_params"
            res = await s.call_tool("create_local_scenario", ALBERO)
            m = json.loads(res.content[0].text); assert not res.isError and m["scenario_id"] == sc1["scenario_id"] and m["cached"] is True
            res = await s.call_tool("compute_walk_access", {**A, "sql": "drop table x"})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "invalid_params"
            res = await s.call_tool("get_result_manifest", {"job_id": r1["job_id"]})
            assert json.loads(res.content[0].text)["job_id"] == r1["job_id"]
asyncio.run(mcp_test())

shutil.rmtree(CACHE, ignore_errors=True)
print("TUTTO OK")
