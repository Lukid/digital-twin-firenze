"""Test F08 su Firenze Novoli. Uso: pipeline/.venv/bin/python scenarios/test_scenari.py
Richiede costruisci.py e confronto.py già eseguiti (baseline, scenari, scenarios/firenze_novoli/confronto.json e cache dei job in data/norm/firenze_novoli/scenarios/jobs;
se i job mancano li calcola, alcuni minuti ciascuno)."""
import copy, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenari as S, confronto as C
from scenari import O, ScenarioError, ROOT, SC
from shapely.geometry import shape

st0 = S.stato_baseline()
cond = S.condizioni()
leggero = {**cond, "times": ["08:00", "12:30", "13:00", "13:30", "16:30"], "fasce": [{"id": "mezzogiorno", "from": "12:30", "to": "13:30"}, {"id": "tutto", "from": "08:00", "to": "16:30"}]}
RID = "pth_fi_R01"; RAT = S.baseline()["ricevitori"]["area_attesa"]["receiver_id"]
rec = [r for r in S.ricevitori() if r["receiver_id"] in (RID, RAT)]
assert len(rec) == 2
CASI_L = ["base", "alberi_tipico"]   # i test leggeri non calcolano la vegetazione LiDAR (un minuto per caso)


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


# 1. baseline congelata: il record corrisponde ai file e alle versioni correnti, ed è valido sullo schema comune
assert S.verifica_baseline() == [], S.verifica_baseline()
b = S.baseline()
assert b["motori"]["ombre"]["version"] == O.VERSIONE and b["baseline_id"] == "bas_firenze_novoli_20261009" and b["aoi_id"] == "aoi_firenze_novoli"
assert b["condizioni"]["dates"] == ["2026-07-15", "2026-09-15"] and b["condizioni"]["date"] == "2026-07-15"
assert {"snapshot", "grafo", "geometrie", "vegetazione_lidar", "motori", "origini", "condizioni"} <= set(b) and b["origini"]["kind"] == "address_points"
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
sch = {p.name: json.loads(p.read_text()) for p in (ROOT / "contracts/schemas").glob("*.schema.json")}
reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in sch.values()])
assert not list(Draft202012Validator(sch["baseline.schema.json"], registry=reg).iter_errors(b))
print("ok 1 baseline congelata")

# 2. validazione: schema, tipi non supportati, fattibilità, dimensioni; segnalazioni che non bloccano
base_scn = S.carica("scn_fi_s1_filare_r01"); op4 = [o for o in base_scn["operations"] if o["op_id"] == "op_albero_04"][0]
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
x0, y0, x1, y1 = c["riquadro"]; w = S.valida(mk([albero(1, x1 + 50, y1 + 50)]))["warnings"]                        # fuori dal riquadro
assert any(x["code"] == "fuori_riquadro" for x in w), w
ass = next((s for s in c["strade"] if s[1] == "assente"), None)
if ass: w = S.valida(mk([albero(1, *ass[0].interpolate(0.5, normalized=True).coords[0])]))["warnings"]; assert any(x["code"] == "su_carreggiata_senza_marciapiede" for x in w), w
w = S.valida(mk([albero(1, 678652.58, 4851322.23)]))["warnings"]                                                    # vecchio albero 3 di S1 v1, fra carreggiata e binari T2 su Via di Novoli
assert any(x["code"] == "fuori_area_pedonale" for x in w), w
assert not any(x["code"] == "fuori_area_pedonale" for x in S.valida(S.carica("scn_fi_s1_filare_r01"))["warnings"])   # S1 v2: tutti dentro le aree pedonali
print("ok 2 validazione e segnalazioni")

# 3. fattibilità sempre ignota (nel risultato di validazione e in ogni scenario dimostrativo)
dim = [s for s in S.elenco() if s.startswith("scn_fi_s")]; assert len(dim) == 7, dim
for sid in dim:
    f = S.valida(S.carica(sid), geometrie=False)["feasibility"]
    assert set(f.values()) == {"ignota"} and {"sottoservizi", "spazio_radicale", "permessi"} <= set(f), sid
    assert all(o["hypothesis_status"] != "feasibility_checked" and all(d["classification"] == "scenario" for d in o["dimensions"].values()) for o in S.carica(sid)["operations"])
print("ok 3 fattibilità ignota")

# 4. stesso input = stesso id di scenario e stesso job_id; contenuto diverso = altro scenario e altro job
un_albero = mk([albero(1, x4, y4)]); assert S.crea_scenario(b["baseline_id"], "scenario di prova", [albero(1, x4, y4)])["scenario_id"] == un_albero["scenario_id"]
assert un_albero["scenario_id"].startswith("scn_fi_") and mk([albero(1, x4, y4, h=12)])["scenario_id"] != un_albero["scenario_id"]
r1 = S.calcola_ombra(un_albero, rec, leggero, casi=CASI_L); r2 = S.calcola_ombra(un_albero, rec, leggero, casi=CASI_L)
assert r1["job"]["job_id"] == r2["job"]["job_id"] and r1["sintesi"] == r2["sintesi"]
r3 = S.calcola_ombra(mk([albero(1, x4, y4, h=12)]), rec, leggero, casi=CASI_L)
assert r3["job"]["job_id"] != r1["job"]["job_id"]
assert r1["job"]["inputs"]["scenario_id"] == un_albero["scenario_id"] and r1["job"]["params"]["method"]["obstacles"] == "buildings_and_trees"
print("ok 4 stesso input stesso job_id")

# 5. scenario senza interventi = baseline: delta nullo su ogni riga (ricevitore, ora, caso)
vuoto = mk([]); rv = S.calcola_ombra(vuoto, rec, leggero, casi=CASI_L)
rb = O.compute_shadow(b["baseline_id"], rec, {"date": cond["date"], "timezone": "Europe/Rome", "times": leggero["times"]}, {**cond["method"], "obstacles": "buildings_and_trees"},
                      walk_speed_m_s=cond["walk_speed_m_s"], casi=CASI_L, fasce=leggero["fasce"], el_min=cond["el_min_deg"])
assert len(rv["righe"]) == len(rb["righe"]) > 0
chiavi = ("shade_fraction", "walk_sun_min", "shaded_m", "shaded_m2")
for a, c_ in zip(rb["righe"], rv["righe"]):
    assert (a["receiver_id"], a["time_local"], a["caso"], a["stato"]) == (c_["receiver_id"], c_["time_local"], c_["caso"], c_["stato"])
    for k in chiavi:
        if k in a: assert abs(a[k] - c_[k]) <= C.TOL, (k, a, c_)
print("ok 5 scenario nullo = baseline")

# 6. un albero aggiunto non riduce mai l'ombra (né aumenta i minuti al sole), per ogni ora e caso; e su R01 la aumenta in almeno un'ora
# (l'albero di prova è sul filare di S1, tratto 100% al sole a mezzogiorno di luglio: l'effetto si vede il 15 luglio)
ra = S.calcola_ombra(un_albero, rec, leggero, casi=CASI_L); rz = S.calcola_ombra(vuoto, rec, leggero, casi=CASI_L); piu = 0
for a, z in zip(ra["righe"], rz["righe"]):
    assert (a["receiver_id"], a["time_local"], a["caso"]) == (z["receiver_id"], z["time_local"], z["caso"])
    if "shade_fraction" in a:
        assert a["shade_fraction"] >= z["shade_fraction"] - 1e-9, (a, z)
        piu += a["shade_fraction"] > z["shade_fraction"] + 1e-6
    if a.get("walk_sun_min") is not None: assert a["walk_sun_min"] <= z["walk_sun_min"] + 1e-9, (a, z)
assert piu > 0
print("ok 6 un albero non riduce l'ombra")

# 7. condizioni comuni: confronto respinto se date, orari, ricevitori o velocità differiscono; casi ammessi se uno contiene l'altro
assert C.incompatibilita(rz["job"], ra["job"]) == []
for campo, nuovo in (("when", {**rz["job"]["params"]["when"], "date": "2026-06-21"}), ("receivers", rz["job"]["params"]["receivers"][:1]), ("walk_speed_m_s", 1.0), ("geometrie_sha256", "0" * 64)):
    j = copy.deepcopy(ra["job"]); j["params"][campo] = nuovo
    assert any(i["code"] == f"{campo}_diverso" for i in C.incompatibilita(rz["job"], j)), campo
j = copy.deepcopy(ra["job"]); j["inputs"]["baseline_id"] = "bas_altra"; assert C.incompatibilita(rz["job"], j)
j = copy.deepcopy(ra["job"]); j["params"]["method"]["time_step_min"] = 15.0; assert C.incompatibilita(rz["job"], j)
j = copy.deepcopy(ra["job"]); j["params"]["casi"] = ["base"]; assert C.incompatibilita(rz["job"], j) == []
j["params"]["casi"] = ["veg_lidar_max"]; assert any(i["code"] == "casi_diverso" for i in C.incompatibilita(rz["job"], j))
print("ok 7 condizioni comuni")

# 8. S0 contro S0 = delta zero su tutto (percorsi, area di attesa, tratti, tre contesti, entrambe le date); baseline invariata
riep = json.loads((SC / "confronto.json").read_text())
assert riep["baseline_invariata"] is True and set(riep["scenari"]) == {C.S1, C.S2, C.S5, C.S6} and riep["condizioni_comuni"]["contesto_principale"] == "con_vegetazione_lidar"
rec_all = S.ricevitori()
for d in cond["dates"]:
    _, r0 = C.esegui(C.S0, d, rec_all); ix = C.indice(r0)
    assert r0["job"]["job_id"] == riep["riferimento"]["job_id"][d]
    for ctx, casi in S.CASI_CONTESTO.items():
        for r_, tab in C.tabella_percorsi(ix, ix, cond, casi).items():
            for f, m in tab.items():
                for k, dd in m.items():
                    if dd: assert dd["delta"] == 0 and dd["discrimina"] is False and dd["intervallo"] == [0, 0], (d, ctx, r_, f, k, dd)
        assert all(dd["delta"] == 0 for dd in C.area_attesa(ix, ix, cond, b, casi).values() if dd)
        assert all(v["archi_toccati"] == 0 for dest in C.beneficio_archi(ix, ix, cond, b, casi).values() for v in dest["fasce"].values())
    assert all(v["minuti_sole"] == [0.0, 0.0, 0.0] and v["frazione_ombra"] == [0.0, 0.0, 0.0]
               for rid, ore in C.per_ora(r0, r0, b, S.CASI_CONTESTO["con_vegetazione_lidar"]).items() for v in ore.values() if rid.startswith("pth_") and "minuti_sole" in v)
assert S.verifica_baseline() == [] and S.stato_baseline() == st0
print("ok 8 S0 = baseline, baseline invariata")

# 9. accessibilità: effetto nullo, verificato
for sid, e in riep["scenari"].items():
    acc = e["accessibilita"]; assert e["stato"] == "confrontato"
    assert acc["nullo"] is True and acc["delta_quota_servita"] == 0 and acc["hash_grafo_regole_origini_invariati"] is True
    assert all(v["stesso_job"] and v["metriche_identiche"] for v in acc["ricalcolo"].values()) and set(e["fattibilita"].values()) == {"ignota"}
print("ok 9 accessibilità invariata")

# 10. coerenza delle varianti di S1 (R01, punta di mezzogiorno): nessuna variante aumenta il sole; chioma max >= tipica >= min nel beneficio
s1 = riep["scenari"][C.S1]; rob = s1["robustezza"]; PT = "punta_12_30_13_30"
for d in cond["dates"]:
    for ctx in ("solo_edifici", "con_vegetazione_lidar"):
        dm = lambda t: t["R01"][PT]["minuti_sole"]["delta"]
        tip, vmin, vmax = dm(s1["percorsi"][d][ctx]), dm(rob["scn_fi_s1v_chioma_min"]["percorsi"][d][ctx]), dm(rob["scn_fi_s1v_chioma_max"]["percorsi"][d][ctx])
        assert max(tip, vmin, vmax) <= C.TOL, (d, ctx)
        assert vmax <= tip + C.TOL and tip <= vmin + C.TOL, (d, ctx, vmax, tip, vmin)
    # estremi del filare tipico: l'intervallo contiene il delta centrale e le varianti min e max stanno dentro [chioma max, chioma min]
    m = s1["percorsi"][d]["con_vegetazione_lidar"]["R01"][PT]["minuti_sole"]; assert m["intervallo"][0] <= m["delta"] <= m["intervallo"][1]
assert all(set(v) >= {"percorsi", "casi_calcolati"} for v in rob.values())
# frazione d'ombra mai in calo
for sid, e in riep["scenari"].items():
    for d in cond["dates"]:
        for ctx in S.CONTESTI:
            for r_, tab in e["percorsi"][d][ctx].items():
                for f, mm in tab.items():
                    if mm["frazione_ombra"]: assert mm["frazione_ombra"]["intervallo"][0] >= -C.TOL, (sid, d, ctx, r_, f)
print("ok 10 coerenza varianti")

# 11. S2: la scelta dell'area di attesa è documentata nei dati (fermate T2 di Novoli con pensilina; piattaforma bus scelta senza pensilina in OSM) e S2 non tocca R01
import geopandas as gpd
t2 = gpd.read_file(ROOT / "data/norm" / O.SLUG / "fi_tram_fermate.gpkg"); nov = t2[t2.id.str.startswith(("stp_fi_NOVOLI-TORRE", "stp_fi_NOVOLI-REGIONE"))]
assert len(nov) == 2 and set(nov.pensilina.astype(int)) == {1}
pt = gpd.read_file(ROOT / "data/norm" / O.SLUG / "osm_firenze.gpkg", layer="points"); pr = pt[pt.id == "nod_osm_5760828088"].iloc[0]
assert json.loads(pr.tags)["shelter"] == "no" and json.loads(pr.tags)["name"] == "Guidoni Barsanti"
assert not S.valida(S.carica(C.S2))["warnings"] or all(w["code"] != "fuori_area_pedonale" for w in S.valida(S.carica(C.S2))["warnings"])   # S2 v2 dentro le aree pedonali
s2 = riep["scenari"][C.S2]
for d in cond["dates"]:
    m = s2["percorsi"][d]["con_vegetazione_lidar"]["R01"]
    assert all(abs(x["minuti_sole"]["delta"]) <= C.TOL for x in m.values() if x["minuti_sole"])   # la pensilina è lontana da R01
    a = s2["area_attesa_polo"][d]["con_vegetazione_lidar"]
    assert all(x["delta"] >= -C.TOL for x in a.values() if x)
assert max(x["delta"] for d in cond["dates"] for x in s2["area_attesa_polo"][d]["con_vegetazione_lidar"].values() if x) > 0   # almeno una fascia guadagna ombra nell'area di attesa
print("ok 11 S2 area di attesa")

# 12. interventi.geojson per la scena: EPSG:4326, Point per gli alberi, Polygon per le coperture, proprietà dichiarate
g = json.loads((SC / "interventi.geojson").read_text()); pts = [f for f in g["features"] if f["geometry"]["type"] == "Point"]; pol = [f for f in g["features"] if f["geometry"]["type"] == "Polygon"]
assert len(pts) == 21 and len(pol) == 3 and len(pts) + len(pol) == len(g["features"])
assert all(set(f["properties"]) == {"id", "scenario", "h", "chioma_d", "imposta"} for f in pts) and all(set(f["properties"]) == {"id", "scenario", "z_lo", "z_hi"} for f in pol)
assert len({f["properties"]["id"] for f in g["features"]}) == len(g["features"])
assert all(11.1 < f["geometry"]["coordinates"][0] < 11.3 and 43.7 < f["geometry"]["coordinates"][1] < 43.9 for f in pts)
assert all(11.1 < x < 11.3 and 43.7 < y < 43.9 for f in pol for x, y in f["geometry"]["coordinates"][0])
assert {f["properties"]["scenario"] for f in g["features"]} == {s for s in dim if S.carica(s)["operations"]}
assert {f["properties"]["scenario"] for f in pol} == {C.S2, C.S5, C.S6} and all((f["properties"]["z_lo"], f["properties"]["z_hi"]) == (2.5, 3.0) for f in pol)
print("ok 12 interventi.geojson")

# 13. nessuna stringa del pilota precedente nei file prodotti (versionati e cache dei job)
vietate = re.compile(r"pisa|z2|pellico|battisti", re.I)
files = [p for p in SC.iterdir() if p.suffix in (".json", ".geojson")] + list(S.JOBS.glob("*.json"))
assert len(files) > 10
for p in files:
    m = vietate.search(p.read_text()); assert not m, (p.name, m.group(0))
assert S.stato_baseline() == st0
print("ok 13 nessuna stringa del pilota precedente")

# 14. S0, S1, S2 invariati dopo l'aggiunta di S5 e S6 (file immutabili e numeri principali del confronto, base LiDAR, punta 12:30-13:30)
import hashlib
SHA = {"scn_fi_s0_baseline": "e1212793471cca1f392f5ad86931c80d72e1f7d1838b65dcf7a34f990b146e29", "scn_fi_s1_filare_r01": "393da9a7953399553d340e198ac5fd8b9c407a929979cd26011569a09b836320",
       "scn_fi_s1v_chioma_max": "cfbc763db404cabc899b09dd1863d73bd551137ec84f002bc8447cc7a6411b72", "scn_fi_s1v_chioma_min": "613cc0a26e0e12b39ae38ecb842bb349443ce6d2eb9fd6cc251c47ecedcf0589",
       "scn_fi_s2_pensilina_attesa_polo": "f20b11cf92e2fd98df0b5f1329fb1f5aba60567a8e886e3bca7c058567044c96"}
assert all(hashlib.sha256((SC / f"{k}.json").read_bytes()).hexdigest() == v for k, v in SHA.items())
for d, (b0, s0_, a1) in {"2026-07-15": (4.251, 3.886, 0.4011), "2026-09-15": (1.753, 1.346, 0.2062)}.items():
    m = riep["scenari"][C.S1]["percorsi"][d]["con_vegetazione_lidar"]["R01"][PT]["minuti_sole"]; a = riep["scenari"][C.S2]["area_attesa_polo"][d]["con_vegetazione_lidar"][PT]
    assert (m["baseline"], m["scenario"]) == (b0, s0_) and (a["baseline"], a["scenario"]) == (0.0, a1), (d, m, a)
print("ok 14 S0, S1, S2 invariati")

# 15. S5 e S6: seconda e terza fermata della regola di S2, fascia 6 x 3,5 m libera nelle aree pedonali, area di attesa propria fra i ricevitori, ombra mai in calo
import costruisci as K, shapely
f = K.fermate_pensilina(); assert f[0][3] == K.PIATTAFORMA_ATTESA and [x[1] for x in f[1:3]] == ["nod_osm_6027223967", "nod_osm_3216618875"], f[:3]
ped, bld = S._contesto_geo()["ped"], shapely.union_all(S._contesto_geo()["bld"]); altre = {a["scenario"]: a for a in b["ricevitori"]["aree_attesa_altre"]}
for sid, (d_, oid, nome, xy) in zip((C.S5, C.S6), f[1:3]):
    scn = S.carica(sid); pens = shape(scn["operations"][0]["geometry"]); assert oid in scn["operations"][0]["note"] and not S.valida(scn)["warnings"], sid
    assert abs(pens.area - 12) < 0.05 and ped.contains(pens) and not pens.intersects(bld)
    _, u, _ = K.posto_pensilina(xy); n = shapely.geometry.Point(-u[1], u[0]); c = pens.centroid
    fasce = [K.rettangolo((c.x + sg * 0.75 * n.x, c.y + sg * 0.75 * n.y), u, 6.0, 3.5) for sg in (1, -1)]   # pensilina più 1,5 m di passaggio da uno dei due lati
    assert any(ped.contains(fa) and not fa.intersects(bld) for fa in fasce), sid
    att = shape(altre[sid]["geometry"]); assert att.contains(pens) and abs(att.area - 32) < 0.1 and altre[sid]["receiver_id"] in {r["receiver_id"] for r in rec_all}
    e = riep["scenari"][sid]; assert e["stato"] == "confrontato"
    for d in cond["dates"]:
        for rid, v in e["aree_attesa"].items(): assert all(x["delta"] >= -C.TOL for x in v[d]["con_vegetazione_lidar"].values() if x)
        assert all(abs(x["delta"]) <= C.TOL for x in e["area_attesa_polo"][d]["con_vegetazione_lidar"].values() if x)   # lontane da Guidoni Barsanti
    assert max(x["delta"] for d in cond["dates"] for x in e["aree_attesa"][altre[sid]["receiver_id"]][d]["con_vegetazione_lidar"].values() if x) > 0
print("ok 15 S5 e S6 pensiline con passaggio libero")

# 16. S3 e S4 non creati: su R02 la regola di S1 ritrova gli alberi di S1; verso la scuola Vamba (R09, R08) nessuna finestra ha posto per 7 alberi
t2 = K.trova_tratto(b, "R02"); assert t2["finestre_valide"] == 1
s1x = [shape(o["geometry"]) for o in S.carica(C.S1)["operations"]]
assert all(p[0] is not None and min(q.distance(shapely.geometry.Point(p[0])) for q in s1x) < 0.5 for p in K.posizioni_filare(b, t2)[0])
assert K.trova_tratto(b, "R09")["finestre_valide"] == 0 and K.trova_tratto(b, "R08")["finestre_valide"] == 0
assert S.stato_baseline() == st0
print("ok 16 S3 e S4 non creati (nessun posto nuovo)")
print("TUTTO OK")
