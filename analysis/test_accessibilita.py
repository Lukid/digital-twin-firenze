#!/usr/bin/env python3
"""Test F06 su Firenze Novoli (assert). Esegue dopo analysis/run.py: pipeline/.venv/bin/python analysis/test_accessibilita.py"""
import hashlib, json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import accessibilita as A
RL = A.RL
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from shapely.geometry import Point

ROOT = A.ROOT; c = A.contesto(); BAT, PEL = "dst_university_w83537185", "dst_tram_fm9056"   # Polo e fermata T2 (nomi storici delle variabili)
FAM = "address_points"; VERS = A.OUT_VERS
assert A.AOI_ID == "aoi_firenze_novoli", "il test vale per Firenze: DT_AOI non impostata o diversa"
base = A.PROFILI["base_1_2"]
r = A.compute_walk_access(BAT, profile=base); assert r["manifest"]["aoi_id"] == "aoi_firenze_novoli" and r["manifest"]["baseline_id"] == "bas_firenze_novoli_20261009"; O = r["origini"]; n = len(O)

# 1. somma degli stati = numero di origini; stati attesi da F04 (3.112 civici raggiungibili dal Polo)
cnt = r["aggregati"]["conteggi"]
assert sum(cnt.values()) == n == 3296, cnt
assert cnt["insufficient_data"] == 168 and cnt["reachable"] == 3112 and cnt["forbidden"] + cnt["isolated"] == 16 and cnt["outside_model"] == 0, cnt
assert r["manifest"]["coverage"]["accessibility_counts"] == cnt
print("1 ok", cnt)

# 2. nessun reachable con distanza infinita, vuota o incoerente; tempo = distanza / velocità
for o in O.values():
    if o["stato"] != "reachable": assert "totale_m" not in o; continue
    assert math.isfinite(o["totale_m"]) and o["totale_m"] > 0 and math.isfinite(o["tempo_s"]) and o["tempo_s"] >= 0, o
    assert abs(o["tempo_s"] - o["totale_m"] / 1.2) < 0.35, o
    assert o["totale_m"] >= o["diretta_m"] - 1.0, o   # la rete non è più corta della linea d'aria (tolleranza raccordi)
print("2 ok")

# 3. stessi percorsi campione di F04 (R01-R10), V01 e V02 forbidden
camp = {x["id"]: x for x in json.load(open(RL.RES / "percorsi_campione.json"))}
ent = {e["entrance_id"]: e for d in c["dest"].values() for e in d["ingressi"]}
snap_e = lambda e: (Point(e["xy"]), {**e["aggancio"], "proj": tuple(e["aggancio"]["proj"])})
orig40 = A.agganci_origini(FAM, 40.0)
punto = lambda s: snap_e(ent[s.split()[0]]) if s.startswith("ent_") else orig40[s.split()[0]]
for rid, t in sorted(camp.items()):
    po, so = punto(t["origine"]); pd_, sd = punto(t["destinazione"]); eid = t["destinazione"].split()[0]
    righe, _ = A.calcola({eid: (pd_, sd)}, {rid: (po, so)}, base); x = righe[rid]
    if rid.startswith("V"):
        assert t["stato"] == "forbidden" and x["stato"] == "forbidden" and abs(x["permissivo_m"] - t["permissivo_lunghezza_m"]) < 1.5, (t, x)
        continue
    assert x["stato"] == "reachable" == t["stato"], (rid, x)
    H, nodi, archi = RL.percorso(c["G"], so, sd); att = {e.get("parte_di", e["edge_id"]) for e in archi if e["tipo_arco"] == "attraversamento"}
    atteso = sum(e["length_m"] for e in archi) + so["dist_m"] + sd["dist_m"]
    assert abs(x["totale_m"] - atteso) < 0.3 and x["attraversamenti"] == len(att), (rid, x["totale_m"], atteso)
    assert abs(x["diretta_m"] - t["diretta_m"]) < 0.15 and x["totale_m"] >= x["diretta_m"], (rid, x)
    assert abs(x["totale_m"] - t["lunghezza_totale_m"]) < 0.3 and abs(x["m_marciapiede_ignoto"] - t["m_marciapiede_ignoto"]) < 0.3, (rid, x, t)
    print(f"  {rid} {x['totale_m']} m (F04 {t['lunghezza_totale_m']} m), attr {x['attraversamenti']}")
print("3 ok: R01-R10 uguali a F04, V01 e V02 forbidden")
assert O["adr_fi_31825"]["stato"] == "forbidden"

# 4. agganci a 40 m = origini_snap.gpkg di F04
for oid, row in c["civ"].iterrows():
    s = orig40[oid][1]
    assert (s["stato"] == "agganciato") == (row.stato == "reachable_candidate") and (s["stato"] != "agganciato" or s["edge_id"] == row.edge_id), oid
print("4 ok: snapping uguale a T04")

# 5. riproducibilità: stesso input = stesso job_id e stessi numeri; input diverso = job diverso
r2 = A.compute_walk_access(BAT, profile=dict(base))
assert r["job"]["job_id"] == r2["job"]["job_id"] and r["origini"] == r2["origini"] and r["aggregati"] == r2["aggregati"] and r["archi_usati"] == r2["archi_usati"]
assert r["manifest"]["metrics"] == r2["manifest"]["metrics"]
h = hashlib.sha256(A.canon({"tool": "compute_walk_access", "inputs": r["job"]["inputs"], "params": r["job"]["params"]}).encode()).hexdigest()[:16]
assert r["job"]["job_id"] == "job_" + h and r["manifest"]["manifest_id"] == "man_" + h
others = [A.compute_walk_access(BAT, profile=A.PROFILI["lento_0_8"]), A.compute_walk_access(BAT, profile=base, snap_limit_m=20), A.compute_walk_access(PEL, profile=base),
          A.compute_walk_access(BAT, profile=base, thresholds_min=(5, 10))]
assert len({r["job"]["job_id"]} | {o["job"]["job_id"] for o in others}) == 5
print("5 ok: job_id", r["job"]["job_id"])

# 6. manifest e job validi per gli schemi di contracts/
S = {p.name.split(".")[0]: json.load(open(p)) for p in (ROOT / "contracts/schemas").glob("*.schema.json")}
reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in S.values()])
for key in ("manifest", "job"):
    errs = list(Draft202012Validator(S[key], registry=reg).iter_errors(r[key]))
    assert not errs, (key, errs[0].message, list(errs[0].path))
mans = sorted((VERS / "manifest").glob("*.manifest.json")); assert len(mans) == 4 * len(c["dest"]) == 20, len(mans)
for f in mans:
    m = json.load(open(f)); assert not list(Draft202012Validator(S["manifest"], registry=reg).iter_errors(m)), f.name
    assert m["assets"] and all((ROOT / a["path"]).exists() and hashlib.sha256((ROOT / a["path"]).read_bytes()).hexdigest() == a["sha256"] for a in m["assets"]), f.name
    assert sum(m["coverage"]["accessibility_counts"].values()) == m["params"]["origins"]["count"] == 3296
    assert m["aoi_id"] == "aoi_firenze_novoli" and m["baseline_id"] == "bas_firenze_novoli_20261009" and m["params"]["graph"]["graph_id"] == "grf_firenze_novoli_osm_20261009", f.name
    assert m["params"]["origins"] == {"kind": "address_points", "aoi_id": "aoi_firenze_novoli", "count": 3296}
    ids = {d["snapshot_id"] for d in m["datasets"]}; assert "snp_osm_firenze_20261009" in ids and "snp_fi_civici_20261009" in ids, f.name
for f in list((VERS / "manifest").glob("*.json")) + list(VERS.glob("*.json")) + list(VERS.glob("*.geojson")):   # nessun residuo del primo pilota
    txt = f.read_text().lower(); assert "pisa" not in txt and "z2" not in txt and "sit di" not in txt, f.name
print("6 ok: 20 manifest/job validi, asset con sha256 corretto, nessuna stringa Pisa/z2")

# 7. coerenza fra profili: tempi monotoni; profilo senza scale non usa scale
res = {k: A.compute_walk_access(BAT, profile=p) for k, p in A.PROFILI.items()}
q = lambda k, T: res[k]["aggregati"]["quote_soglie"][T]["quota"]
for T in ("5", "10", "15"): assert q("lento_0_8", T) <= q("base_1_2", T) <= q("rapido_1_4", T), T
assert q("base_1_2", "5") <= q("base_1_2", "10") <= q("base_1_2", "15")
assert all(o["scale"] == 0 for o in res["ridotta_0_8_senza_scale"]["origini"].values() if o["stato"] == "reachable")
assert res["ridotta_0_8_senza_scale"]["aggregati"]["tempo_min"]["p50"] >= res["lento_0_8"]["aggregati"]["tempo_min"]["p50"]
print("7 ok: monotonia profili")

# 8. più ingressi: il tempo al più vicino non supera quello del singolo ingresso
tutti = sorted(e["entrance_id"] for e in c["dest"][BAT]["ingressi"])
rt = A.compute_walk_access(BAT, profile=base, entrance_ids=tutti)
for k, o in O.items():
    if o["stato"] == "reachable": assert rt["origini"][k]["tempo_s"] <= o["tempo_s"] + 1e-6, k
print("8 ok: ingressi multipli")

# 9. asset mappa: EPSG:4326, conteggi uguali al manifest, uno per destinazione
for did in sorted(c["dest"]):
    fp = VERS / f"accessibilita_{did}.geojson"; g = json.load(open(fp)); F = g["features"]
    org = [f for f in F if f["properties"]["layer"] == "origine"]
    assert len(org) == 3296 and all(11.1 < f["geometry"]["coordinates"][0] < 11.3 and 43.7 < f["geometry"]["coordinates"][1] < 43.9 for f in org)
    ref = A.compute_walk_access(did, profile=base)
    assert g["job_id"] == ref["job"]["job_id"]
    assert {s: sum(1 for f in org if f["properties"]["stato"] == s) for s in ref["aggregati"]["conteggi"]} == ref["aggregati"]["conteggi"]
    assert any(f["properties"]["layer"] == "arco_usato" for f in F) and sum(f["properties"]["layer"] == "destinazione" for f in F) == 1
    assert fp.stat().st_size < 2_000_000
# riepilogo: sensibilità ingressi solo per le destinazioni con più di un ingresso (il Polo)
rie = json.load(open(VERS / "riepilogo.json")); multi = {d for d, v in c["dest"].items() if len(v["ingressi"]) > 1}
assert multi == {BAT} and {k for k in rie["sensibilita"] if k.startswith("ingressi_")} == {"ingressi_" + BAT}
assert {k for k in rie["sensibilita"] if k.startswith("snapping_")} == {"snapping_" + d for d in c["dest"]}
print("9 ok: asset mappa e riepilogo")

# 10. input non validi respinti
for bad in (dict(profile={"speed_m_s": 5, "crossing_penalty_s": 0, "stairs": "allowed"}), dict(destination_id="dst_x")):
    try: A.compute_walk_access(bad.pop("destination_id", BAT), **bad); raise SystemExit("doveva fallire")
    except ValueError: pass
print("10 ok: tutti i test passati")
