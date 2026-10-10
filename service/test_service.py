#!/usr/bin/env python3
"""Test del servizio (F10, Firenze Novoli). Uso: service/.venv/bin/python service/test_service.py (usa una cache temporanea, tocca solo service/).
Il calcolo dell'ombra usa parametri ridotti (un percorso, pochi orari, passi larghi). I casi degli scenari girano solo se scenarios/firenze_novoli/ ha i file scn_fi_*.json."""
import asyncio, json, os, pathlib, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
CACHE = HERE / ".cache_test"; shutil.rmtree(CACHE, ignore_errors=True)
os.environ["DT_CACHE_DIR"] = str(CACHE)
os.environ["DT_SCENARIOS_DIR"] = str(CACHE / "scenari")   # scenari creati dal test: nella cache temporanea
sys.path.insert(0, str(HERE))
import core, replay  # noqa: E402

AOI, BAS = "aoi_firenze_novoli", "bas_firenze_novoli_20261009"
POLO, VAMBA_P, VAMBA_I, T_REG, T_AGLI = "dst_university_w83537185", "dst_school_fiee86002g", "dst_school_fiaa86002a", "dst_tram_fm9056", "dst_tram_fm9057"
A = {"baseline_id": BAS, "origins": {"kind": "address_points", "aoi_id": AOI}, "destination_ids": [POLO], "profile": {"speed_m_s": 1.2}, "thresholds_min": [5, 10, 15]}
err_code = lambda r: r.get("error", {}).get("code")
strip = lambda r: {k: v for k, v in r.items() if k != "cached"}
RISPOSTE = []   # tutte le risposte, per il controllo finale sui nomi di Pisa


def run(tool, args=None):
    r = core.run_tool(tool, args); RISPOSTE.append(r); return r


# 0. area, baseline e cache dell'area
assert core.AOI_ID == AOI and core.BASELINE_ID == BAS and core.CACHE == CACHE
d = subprocess.run([sys.executable, "-c", "import core; print(core.CACHE)"], capture_output=True, text=True, cwd=HERE, env={k: v for k, v in os.environ.items() if k != "DT_CACHE_DIR"}).stdout.strip()
assert d.endswith("service/cache/firenze_novoli"), d   # cache per area, separata da quella di Pisa

# 1. accessibilità: stesso input = stesso job_id e cache; ordine delle chiavi irrilevante; default espliciti = default impliciti
r1 = run("compute_walk_access", A)
assert r1["status"] == "succeeded" and r1["cached"] is False and r1["job_id"].startswith("job_"), r1
r2 = run("compute_walk_access", dict(reversed(list(A.items()))))
assert r2["cached"] is True and r2["job_id"] == r1["job_id"] and strip(r1) == strip(r2)
r3 = run("compute_walk_access", {**A, "profile": {"speed_m_s": 1.2, "crossing_penalty_s": 0, "stairs": "allowed", "snap_limit_m": 40}})
assert r3["job_id"] == r1["job_id"] and r3["cached"] is True
r4 = run("compute_walk_access", {**A, "profile": {"speed_m_s": 0.8, "crossing_penalty_s": 10, "stairs": "excluded"}})
assert r4["job_id"] != r1["job_id"] and r4["cached"] is False
assert core.validate("compute_walk_access", "output", r1) == [] and core.validate("compute_walk_access", "output", r4) == []
for k in ("job_id", "datasets", "params", "limits", "headline_metrics"): assert r1[k], k
assert r1["job_id"] == "job_90ef3449d76b161a"   # lo stesso job_id del manifest di F06 in analysis/firenze_novoli/manifest
assert (CACHE / f"{r1['job_id']}.manifest.json").exists() and (CACHE / f"{r1['job_id']}.job.json").exists()
man = run("get_result_manifest", {"job_id": r1["job_id"]})
assert man["manifest_id"] == r1["result_manifest_id"] and man["metrics"] == r1["headline_metrics"] and man["aoi_id"] == AOI
assert run("get_job_status", {"job_id": r1["job_id"]})["status"] == "succeeded"
assert core.validate("get_job_status", "output", run("get_job_status", {"job_id": r1["job_id"]})) == [] and core.validate("get_result_manifest", "output", man) == []
assert err_code(run("get_job_status", {"job_id": "job_0000000000000000"})) == "unknown_id"
hist = run("get_job_status", {"job_id": "job_025574916d1aaa54"}); assert hist["tool"] == "compute_walk_access"   # job versionato in analysis/firenze_novoli/manifest
r5 = run("compute_walk_access", {**A, "destination_ids": [VAMBA_P], "entrance_ids": ["ent_cm_FIEE86002G_0"]})
assert r5["status"] == "succeeded" and core.validate("compute_walk_access", "output", r5) == []

# 2. input non valido respinto prima del calcolo
for bad in ({**A, "sql": "select 1"}, {**A, "profile": {"speed_m_s": 12}}, {**A, "profile": {"speed_m_s": 1.2, "stairs": "forse"}}, {**A, "thresholds_min": []}, {**A, "thresholds_min": [10, 10.0]},
            {**A, "entrance_ids": ["ingresso principale"]}, {k: v for k, v in A.items() if k != "profile"}, {**A, "origins": {"kind": "address_points"}}):
    assert err_code(run("compute_walk_access", bad)) == "invalid_params", bad
assert err_code(run("compute_walk_access", {**A, "entrance_ids": ["ent_gtfs_fm9056"]})) == "invalid_params"   # ingresso di un'altra destinazione
assert err_code(run("compute_walk_access", {**A, "destination_ids": ["dst_school_inesistente"]})) == "unknown_id"
assert err_code(run("compute_walk_access", {**A, "destination_ids": [POLO, T_REG]})) == "limit_exceeded"
assert err_code(run("compute_walk_access", {**A, "origins": {"kind": "grid", "aoi_id": AOI, "spacing_m": 20}})) == "outside_capability"
assert err_code(run("compute_walk_access", {**A, "origins": {"kind": "address_points", "aoi_id": "aoi_altra"}})) == "outside_capability"
assert err_code(run("compute_walk_access", {**A, "baseline_id": "bas_altra"})) == "incompatible_baseline"
assert err_code(core.run_tool("compute_walk_access", {**A, "origins": {"kind": "civici_sit_z2"}})) == "outside_capability"   # forma storica del pilota precedente
assert err_code(core.run_tool("compute_walk_access", {**A, "baseline_id": "bas_z2_20261001"})) == "incompatible_baseline"   # la baseline di Pisa non è più ammessa

# 3. destinazione ambigua o mancante: errore con alternative, mai scelta implicita
NOA = {k: v for k, v in A.items() if k != "destination_ids"}
for ids in (["la scuola"], ["vamba"], ["tram"], ["fermata"], ["polo"], [], None):
    r = run("compute_walk_access", {**NOA, **({} if ids is None else {"destination_ids": ids})})
    assert err_code(r) == "ambiguous_destination" and r["error"]["candidates"], (ids, r)
cand = lambda q: [c.split(" | ")[0] for c in run("compute_walk_access", {**NOA, "destination_ids": [q]})["error"]["candidates"]]
assert sorted(cand("vamba")) == sorted([VAMBA_P, VAMBA_I]) and sorted(cand("tram")) == sorted([T_REG, T_AGLI]) and cand("polo") == [POLO]
assert len(cand("sconosciuta")) == 5   # nome senza corrispondenze: tutte le destinazioni dell'area

# 4. alias delle destinazioni (list_destinations, name_query) e categorie
LD = lambda cat, q=None: [x["destination_id"] for x in run("list_destinations", {"aoi_id": AOI, "category": cat, **({"name_query": q} if q else {})})["destinations"]]
for q in ("polo", "Università", "universita", "scienze sociali", "Polo delle Scienze Sociali", "pandette"): assert LD("university", q) == [POLO], q
for q in ("vamba", "scuola vamba", "scuola"): assert sorted(LD("school", q)) == sorted([VAMBA_P, VAMBA_I]), q
assert LD("school", "primaria vamba") == [VAMBA_P] and LD("school", "infanzia vamba") == [VAMBA_I] and LD("school", "FIEE86002G") == [VAMBA_P]
for q in ("fermata regione", "Regione Toscana", "regione"): assert LD("stop", q) == [T_REG], q
for q in ("torre degli agli", "Torre degli Agli", "fermata torre degli agli"): assert LD("stop", q) == [T_AGLI], q
assert sorted(LD("stop", "tram")) == sorted([T_REG, T_AGLI]) and sorted(LD("stop")) == sorted([T_REG, T_AGLI])
assert LD("university") == [POLO] and len(LD("school")) == 2 and LD("hospital") == [] and LD("school", "tram") == []
for cat in ("school", "university", "stop", "station"): assert core.validate("list_destinations", "output", run("list_destinations", {"aoi_id": AOI, "category": cat})) == []
polo = run("list_destinations", {"aoi_id": AOI, "category": "university"})["destinations"][0]
assert len(polo["entrances"]) == 2 and polo["verification"] == "desk_candidate" and polo["access_conditions"]
assert err_code(core.run_tool("list_destinations", {"aoi_id": "aoi_z2", "category": "school"})) == "unknown_id"   # Pisa non è più un'area

# 5. strumenti di lettura: solo fonti della baseline
base_src = {s["source_id"] for s in core.BASELINE["snapshot"]}
for th in ("edifici", "quote", "rete_pedonale", "verde", "destinazioni", "trasporto", "licenze"):
    src = run("list_approved_sources", {"theme": th, "aoi_id": AOI})
    assert core.validate("list_approved_sources", "output", src) == [] and src["sources"], th
    assert all(s["permitted_use"] and s["license_state"] and s["source_id"] in base_src and s["snapshot_id"].endswith("_20261009") for s in src["sources"]), th
assert {s["source_id"] for s in run("list_approved_sources", {"theme": "licenze", "aoi_id": AOI})["sources"]} == base_src
assert run("list_approved_sources", {"theme": "verde", "aoi_id": AOI})["gaps"] and run("list_approved_sources", {"theme": "edifici", "aoi_id": AOI})["gaps"]
assert err_code(core.run_tool("list_approved_sources", {"theme": "verde", "aoi_id": "aoi_z2"})) == "unknown_id"
ins = run("inspect_dataset", {"source_id": "src_fi_alberi"})
assert core.validate("inspect_dataset", "output", ins) == [] and ins["license"]["state"] == "clear" and ins["snapshot_id"] == "snp_fi_alberi_20261009"
assert core.validate("inspect_dataset", "output", run("inspect_dataset", {"snapshot_id": "snp_gtfs_gest_firenze_20261009"})) == []
r = core.run_tool("inspect_dataset", {"source_id": "src_sit_civici"}); assert err_code(r) == "unknown_id" and "src_fi_civici" in r["error"]["candidates"]   # fonte di Pisa: fuori baseline
assert err_code(core.run_tool("inspect_dataset", {"snapshot_id": "snp_sit_civici_20261001"})) == "unknown_id"
assert err_code(run("inspect_dataset", {"source_id": "src_fi_alberi", "snapshot_id": "snp_fi_alberi_20261009"})) == "invalid_params"

# 6. scenari: input non validi respinti prima di qualunque calcolo (non servono i file di scenarios/)
for tool, args in (("create_local_scenario", {"x": 1}), ("compare_scenarios", None), ("compare_scenarios", {"manifest_ids": ["man_0123456789abcdef"] * 2, "metric_ids": ["x"]})):
    assert err_code(run(tool, args)) == "invalid_params", tool

# 7. ombra, parametri ridotti: un percorso (R02, 708 m), un orario, passi larghi
SH = {"baseline_id": BAS, "receivers": [{"route_id": "R02"}], "when": {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ["12:30"]},
      "method": {"name": "geometric_ray", "space_step_m": 5, "time_step_min": 30, "obstacles": "buildings_and_trees"}}
s1 = run("compute_shadow", SH)
assert s1["status"] == "succeeded" and s1["cached"] is False and core.validate("compute_shadow", "output", s1) == [], s1
assert s1["cases"] == ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max"] and s1["sun_state_counts"] == {"ok": 6}
assert s1["datasets"] and s1["limits"] and s1["params"] and s1["headline_metrics"] and s1["params"]["receivers"][0]["receiver_id"] == "pth_fi_R02"
s2 = run("compute_shadow", SH); assert s2["cached"] is True and strip(s2) == strip(s1)
assert run("get_result_manifest", {"job_id": s1["job_id"]})["tool"] == "compute_shadow"
sv = run("compute_shadow", {**SH, "method": {**SH["method"], "obstacles": "buildings_trees_and_lidar_vegetation"}})   # vegetazione LiDAR (D14)
assert sv["status"] == "succeeded" and core.validate("compute_shadow", "output", sv) == [] and sv["cases"][-3:] == ["veg_lidar_min", "veg_lidar_tipico", "veg_lidar_max"] and sv["job_id"] != s1["job_id"], sv
shw = lambda **k: {**SH, "when": {**SH["when"], **k}}
r = run("compute_shadow", shw(date="2026-10-25", times=["02:30"])); assert err_code(r) == "invalid_params" and "ambigua" in r["error"]["message"], r   # fine ora legale
r = run("compute_shadow", shw(date="2026-03-29", times=["02:30"])); assert err_code(r) == "invalid_params" and "inesistente" in r["error"]["message"], r
r = run("compute_shadow", shw(date="2026-12-21", times=["06:00", "12:00"]))   # inverno: alba sotto l'orizzonte
assert r["status"] == "succeeded" and set(r["sun_state_counts"]) <= {"ok", "sole_sotto_orizzonte", "sole_basso_fuori_supporto"} and r["sun_state_counts"].get("sole_sotto_orizzonte"), r["sun_state_counts"]
big = {**SH, "receivers": [{"route_id": f"R{i:02d}"} for i in range(1, 11)], "when": {**SH["when"], "times": [f"{m // 60:02d}:{m % 60:02d}" for m in range(0, 1440, 15)]}}
r = run("compute_shadow", big); assert err_code(r) == "limit_exceeded" and r["error"]["smaller_request"], r
assert core.validate("compute_shadow", "input", r["error"]["smaller_request"]) == []
assert err_code(run("compute_shadow", {**SH, "receivers": [{"route_id": "R99"}]})) == "unknown_id"
assert err_code(run("compute_shadow", {**SH, "receivers": [{"route_id": "V01"}]})) == "invalid_params"   # V01 (percorso vietato) non è un route_id ammesso dallo schema
assert err_code(core.run_tool("compute_shadow", {**SH, "baseline_id": "bas_z2_20261001"})) == "incompatible_baseline"
assert err_code(run("compute_shadow", {**SH, "scenario_id": "scn_fi_x_y", "method": {**SH["method"], "obstacles": "buildings_and_scenario"}})) in ("unknown_id", "outside_capability", "invalid_params")
assert err_code(run("compute_shadow", {**SH, "method": {**SH["method"], "obstacles": "buildings_and_scenario"}})) == "invalid_params"   # senza scenario_id
assert err_code(run("compute_shadow", {**SH, "scenario_id": "scn_fi_s2_prova"})) == "invalid_params"                                 # con scenario_id serve buildings_and_scenario
assert err_code(run("compute_shadow", {**SH, "sql": "x"})) == "invalid_params"

# 8. replay: job appena calcolato, job con vegetazione LiDAR e job storico di F06
assert replay.replay(s1["job_id"])["match"] and replay.replay(sv["job_id"])["match"]
rp = replay.replay(r4["job_id"]); assert rp["match"] and rp["metrics_compared"] > 10, rp
rp = replay.replay("job_90ef3449d76b161a"); assert rp["match"], rp

# 9. scenari e confronto: solo se scenarios/ è già portato su Firenze (nuovi id scn_fi_*, file in scenarios/firenze_novoli/)
SCN_DIR = HERE.parent / "scenarios" / "firenze_novoli"
if SCN_DIR.is_dir() and any(SCN_DIR.glob("scn_fi_*.json")):
    ids = sorted(p.stem for p in SCN_DIR.glob("scn_fi_*.json"))
    cs = run("compare_scenarios", {"baseline_id": BAS, "scenario_ids": ids[:2]})
    assert err_code(cs) is None or err_code(cs) in ("incompatible_baseline", "unknown_id", "invalid_params", "outside_capability"), cs
    if err_code(cs) is None: assert core.validate("compare_scenarios", "output", cs) == [] and cs["deltas"], cs
    print("scenari Firenze presenti:", ids[:2], "->", err_code(cs) or "confronto ok")
else:
    print("SALTATI: casi degli scenari (create_local_scenario, compare_scenarios con scenario_ids, compute_shadow con scenario_id): mancano i file scn_fi_*.json in scenarios/firenze_novoli/")

# 10. nessun riferimento a Pisa o a Z2 in nessuna risposta
testo = json.dumps(RISPOSTE, ensure_ascii=False).lower()
for w in ("pisa", "z2", "pellico", "battisti"): assert w not in testo, (w, testo[testo.index(w) - 80: testo.index(w) + 80])


# 11. CLI e MCP stdio reale: stesso risultato, stesso job_id
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
            init = await s.initialize()
            assert init.serverInfo.name == "dt-firenze" and "Firenze" in init.instructions and "pisa" not in init.instructions.lower()
            tools = {t.name: t for t in (await s.list_tools()).tools}
            assert set(tools) == set(core.TOOLS) == {"list_approved_sources", "inspect_dataset", "list_destinations", "compute_walk_access", "compute_shadow", "get_job_status", "get_result_manifest", "create_local_scenario", "compare_scenarios"}
            assert all(t.inputSchema.get("additionalProperties") is False for t in tools.values())   # niente campi liberi (SQL, codice)
            assert not any(w in json.dumps([t.model_dump() for t in tools.values()]).lower() for w in ("pisa", "z2", "pellico"))
            res = await s.call_tool("compute_walk_access", A)
            m = json.loads(res.content[0].text); assert not res.isError and strip(m) == strip(r1) and res.structuredContent == m
            res = await s.call_tool("compute_walk_access", {**A, "destination_ids": ["scuola"]})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "ambiguous_destination"
            res = await s.call_tool("list_destinations", {"aoi_id": AOI, "category": "university", "name_query": "polo"})
            assert not res.isError and json.loads(res.content[0].text)["destinations"][0]["destination_id"] == POLO
            res = await s.call_tool("compute_shadow", SH)
            m = json.loads(res.content[0].text); assert not res.isError and m["cached"] is True and strip(m) == strip(s1)
            res = await s.call_tool("compute_shadow", shw(date="2026-10-25", times=["02:30"]))
            assert res.isError and "ambigua" in json.loads(res.content[0].text)["error"]["message"]
            res = await s.call_tool("compute_shadow", big)
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "limit_exceeded"
            res = await s.call_tool("create_local_scenario", {})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "invalid_params"
            res = await s.call_tool("compute_walk_access", {**A, "sql": "drop table x"})
            assert res.isError and json.loads(res.content[0].text)["error"]["code"] == "invalid_params"
            res = await s.call_tool("get_result_manifest", {"job_id": r1["job_id"]})
            assert json.loads(res.content[0].text)["job_id"] == r1["job_id"]
asyncio.run(mcp_test())

shutil.rmtree(CACHE, ignore_errors=True)
print("TUTTO OK")
