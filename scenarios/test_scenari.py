"""Test T10. Uso: pipeline/.venv/bin/python scenarios/test_scenari.py
Richiede costruisci.py e confronto.py già eseguiti (baseline, scenari e cache dei job in data/norm/scenarios/jobs; se mancano li calcola, alcuni minuti)."""
import copy, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S, confronto as C
from scenari import O, ScenarioError
from shapely.geometry import Point, shape

st0 = S.stato_baseline()
cond = S.condizioni()
leggero = {**cond, "times": ["08:00", "12:30", "13:00", "13:30", "16:30"], "fasce": [{"id": "mezzogiorno", "from": "12:30", "to": "13:30"}, {"id": "tutto", "from": "08:00", "to": "16:30"}]}
rec = [r for r in S.ricevitori() if r["receiver_id"] in ("pth_t04_R01", "sfc_t10_pell")]
assert len(rec) == 2


def albero(i, x, y, h=11.0, d=6.0, base=2.5, **kw):
    src = "test: classe scenario di prova"
    return {"op_id": f"op_t_{i}", "op": "add", "target_type": "tree", "geometry": {"type": "Point", "coordinates": [x, y]},
            "dimensions": {"height_m": {"value": h, "unit": "m", "classification": "scenario", "dimension_source": src},
                           "crown_diameter_m": {"value": d, "unit": "m", "classification": "scenario", "dimension_source": src},
                           "crown_base_m": {"value": base, "unit": "m", "classification": "scenario", "dimension_source": src}},
            "hypothesis_status": kw.get("stato", "feasibility_unknown")}


def codice(f):
    try: f()
    except ScenarioError as e: return e.code
    return None


# 1. baseline congelata: il record corrisponde ai file e alle versioni correnti
assert S.verifica_baseline() == [], S.verifica_baseline()
b = S.baseline()
assert b["motori"]["ombre"]["version"] == O.VERSIONE and b["baseline_id"] == "bas_z2_20261001" and b["condizioni"]["date"] == "2026-09-15"
assert {"snapshot", "grafo", "geometrie", "motori", "origini", "condizioni"} <= set(b)
print("ok 1 baseline congelata")

# 2. validazione: schema, tipi non supportati, fattibilità, dimensioni; segnalazioni che non bloccano
base_scn = S.carica("scn_z2_s1_filare_r01"); op4 = [o for o in base_scn["operations"] if o["op_id"] == "op_albero_04"][0]
x4, y4 = op4["geometry"]["coordinates"]
S.valida(base_scn)
mk = lambda ops: S.crea_scenario(b["baseline_id"], "scenario di prova", ops)
assert codice(lambda: S.valida(mk([albero(1, x4, y4, stato="feasibility_checked")]))) == "invalid_params"           # la fattibilità non risulta mai verificata
assert codice(lambda: S.valida(mk([{**albero(1, x4, y4), "op": "remove", "target_id": "tre_osm_1"}]))) == "outside_capability"
assert codice(lambda: S.valida(mk([{**albero(1, x4, y4), "target_type": "building_volume"}]))) == "outside_capability"
nodim = albero(1, x4, y4); del nodim["dimensions"]["crown_base_m"]
assert codice(lambda: S.valida(mk([nodim]))) == "invalid_params"
assert codice(lambda: S.valida(mk([albero(1, x4, y4, h=5, base=4)]))) == "invalid_params"                          # imposta oltre metà altezza
misurata = albero(1, x4, y4); misurata["dimensions"]["height_m"]["classification"] = "measured"
assert codice(lambda: S.valida(mk([misurata]))) == "invalid_params"                                                # solo classe scenario
assert codice(lambda: S.valida({**mk([albero(1, x4, y4)]), "baseline_id": "bas_altra"})) == "incompatible_baseline"
c = S._contesto_geo(); px = c["bld"][0].representative_point()
w = S.valida(mk([albero(1, px.x, px.y)]))["warnings"]                                                              # dentro un edificio: segnala, non blocca
assert any(x["code"] == "dentro_edificio" for x in w), w
g_ass, _, _, _ = next(s for s in c["strade"] if s[1] == "assente"); pm = g_ass.interpolate(0.5, normalized=True)
w = S.valida(mk([albero(1, pm.x, pm.y)]))["warnings"]
assert any(x["code"] == "su_carreggiata_senza_marciapiede" for x in w), w
print("ok 2 validazione e segnalazioni")

# 3. fattibilità sempre ignota (nel risultato di validazione e in ogni scenario dimostrativo)
for sid in S.elenco():
    if sid.startswith("scn_z2_s"):
        f = S.valida(S.carica(sid), geometrie=False)["feasibility"]
        assert set(f.values()) == {"ignota"} and {"sottoservizi", "spazio_radicale", "permessi"} <= set(f), sid
        assert all(o["hypothesis_status"] != "feasibility_checked" and all(d["classification"] == "scenario" for d in o["dimensions"].values()) for o in S.carica(sid)["operations"])
print("ok 3 fattibilità ignota")

# 4. stesso input = stesso id di scenario e stesso job_id; contenuto diverso = altro scenario e altro job
un_albero = mk([albero(1, x4, y4)]); assert S.crea_scenario(b["baseline_id"], "scenario di prova", [albero(1, x4, y4)])["scenario_id"] == un_albero["scenario_id"]
assert mk([albero(1, x4, y4, h=12)])["scenario_id"] != un_albero["scenario_id"]
r1 = S.calcola_ombra(un_albero, rec, leggero); r2 = S.calcola_ombra(un_albero, rec, leggero)
assert r1["job"]["job_id"] == r2["job"]["job_id"] and r1["sintesi"] == r2["sintesi"]
r3 = S.calcola_ombra(mk([albero(1, x4, y4, h=12)]), rec, leggero)
assert r3["job"]["job_id"] != r1["job"]["job_id"]
assert r1["job"]["inputs"]["scenario_id"] == un_albero["scenario_id"] and r1["job"]["params"]["method"]["obstacles"] == "buildings_and_scenario"
print("ok 4 stesso input stesso job_id")

# 5. scenario senza interventi = baseline: delta nullo su ogni riga (ricevitore, ora, caso)
vuoto = mk([]); rv = S.calcola_ombra(vuoto, rec, leggero)
rb = O.compute_shadow(b["baseline_id"], rec, {"date": cond["date"], "timezone": "Europe/Rome", "times": leggero["times"]}, {**cond["method"], "obstacles": "documented_buildings_only"},
                      walk_speed_m_s=cond["walk_speed_m_s"], fasce=leggero["fasce"], el_min=cond["el_min_deg"])
assert rv["job"]["params"]["method"]["obstacles"] == "documented_buildings_only" and len(rv["righe"]) == len(rb["righe"]) > 0
chiavi = ("shade_fraction", "walk_sun_min", "shaded_m", "shaded_m2")
for a, c_ in zip(rb["righe"], rv["righe"]):
    assert (a["receiver_id"], a["time_local"], a["caso"], a["stato"]) == (c_["receiver_id"], c_["time_local"], c_["caso"], c_["stato"])
    for k in chiavi:
        if k in a: assert abs(a[k] - c_[k]) <= C.TOL, (k, a, c_)
print("ok 5 scenario nullo = baseline")

# 6. un albero aggiunto non riduce mai l'ombra (né aumenta i minuti al sole), per ogni ora e ogni caso di altezze; e su R01 la aumenta in almeno un'ora
ra = S.calcola_ombra(un_albero, rec, leggero); rz = S.calcola_ombra(vuoto, rec, leggero); piu = 0
for a, z in zip(ra["righe"], rz["righe"]):
    assert (a["receiver_id"], a["time_local"], a["caso"]) == (z["receiver_id"], z["time_local"], z["caso"])
    if "shade_fraction" in a:
        assert a["shade_fraction"] >= z["shade_fraction"] - 1e-9, (a, z)
        piu += a["shade_fraction"] > z["shade_fraction"] + 1e-6
    if a.get("walk_sun_min") is not None: assert a["walk_sun_min"] <= z["walk_sun_min"] + 1e-9, (a, z)
assert piu > 0
print("ok 6 un albero non riduce l'ombra")

# 7. condizioni comuni: confronto respinto se date, orari o ricevitori differiscono
assert C.incompatibilita(rz["job"], ra["job"]) == []
for campo, nuovo in (("when", {**rz["job"]["params"]["when"], "date": "2026-06-21"}), ("receivers", rz["job"]["params"]["receivers"][:1]), ("walk_speed_m_s", 1.0), ("geometrie_sha256", "0" * 64)):
    j = copy.deepcopy(ra["job"]); j["params"][campo] = nuovo
    assert any(i["code"] == f"{campo}_diverso" for i in C.incompatibilita(rz["job"], j)), campo
j = copy.deepcopy(ra["job"]); j["inputs"]["baseline_id"] = "bas_altra"; assert C.incompatibilita(rz["job"], j)
j = copy.deepcopy(ra["job"]); j["params"]["method"]["time_step_min"] = 15.0; assert C.incompatibilita(rz["job"], j)
print("ok 7 condizioni comuni")

# 8. baseline invariata dopo scenari, calcoli e confronto; S0 contro S0 = delta zero su tutto; nessun ordinamento senza pesi
riep = C.confronta([C.S0, "scn_z2_s2_pensilina_pellico"], con_varianti=False)
assert S.verifica_baseline() == [] and S.stato_baseline() == st0 and riep["baseline_invariata"] is True
e0 = riep["scenari"][C.S0]; assert e0["stato"] == "confrontato" and not e0["interventi"]["alberi"] and not e0["interventi"]["pensiline"]
for r_, tab in e0["percorsi"].items():
    for f, m in tab.items():
        for k, d in m.items():
            if d: assert abs(d["delta"]) <= C.TOL and d["discrimina"] is False and all(abs(x) <= C.TOL for x in d["intervallo"]), (r_, f, k, d)
assert all(abs(d["delta"]) <= C.TOL for d in e0["area_attesa_pellico"].values() if d)
assert all(v["archi_toccati"] == 0 for dd in e0["archi_usati"].values() for v in dd["fasce"].values())
assert "ordine" not in riep and "ordine" not in riep["indicatori"] and codice(lambda: C.ordina(riep, None)) == "invalid_params"
assert codice(lambda: C.ordina(riep, {"indicatore_inventato": 1})) == "invalid_params"
o = C.ordina(riep, {"area_attesa_ombra_mezzogiorno": 1.0}); assert o["ordine"][0] == "scn_z2_s2_pensilina_pellico" or o["punteggi"][C.S0] == o["punteggi"]["scn_z2_s2_pensilina_pellico"]
print("ok 8 baseline invariata, S0 = baseline, nessun ordinamento senza pesi")

# 9. accessibilità: effetto nullo, verificato
s2 = riep["scenari"]["scn_z2_s2_pensilina_pellico"]; acc = s2["accessibilita"]
assert acc["nullo"] is True and acc["delta_quota_servita"] == 0 and acc["hash_grafo_regole_origini_invariati"] is True
assert all(v["stesso_job"] and v["metriche_identiche"] for v in acc["ricalcolo"].values())
assert set(s2["fattibilita"].values()) == {"ignota"} and s2["stato"] == "confrontato"
print("ok 9 accessibilità invariata")

# 10. interventi in EPSG:4326 e asset di scena
g = S.geojson_interventi(base_scn)
assert {f["properties"]["layer"] for f in g["features"]} == {"intervento", "chioma_proiezione"}
assert all(10.3 < f["geometry"]["coordinates"][0] < 10.5 and 43.6 < f["geometry"]["coordinates"][1] < 43.8 for f in g["features"] if f["geometry"]["type"] == "Point")
for sid in ("scn_z2_s0_baseline", "scn_z2_s1_filare_r01", "scn_z2_s2_pensilina_pellico"):
    for hh in ("0800", "1300", "1630"):
        p = S.OUT / f"ombre_{sid}_2026-09-15_{hh}.geojson"; assert p.exists(), p
        fc = json.loads(p.read_text()); assert fc["features"][0]["properties"]["scenario_id"] == sid and fc["features"][0]["properties"]["caso"] == "base"
        pt = shape(fc["features"][0]["geometry"]).representative_point(); assert 10.3 < pt.x < 10.5 and 43.6 < pt.y < 43.8
assert S.stato_baseline() == st0
print("ok 10 asset di scena")
print("TUTTO OK")
