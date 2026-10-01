#!/usr/bin/env python3
"""Test T06 (assert). Esegue dopo analysis/run.py: pipeline/.venv/bin/python analysis/test_accessibilita.py"""
import hashlib, json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import accessibilita as A
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from shapely.geometry import Point

ROOT = A.ROOT; c = A.contesto(); BAT, PEL = "dst_school_piee82101p", "dst_stop_pi4390"
base = A.PROFILI["base_1_2"]
r = A.compute_walk_access(BAT, profile=base); O = r["origini"]; n = len(O)

# 1. somma degli stati = numero di origini; stati attesi da T04
cnt = r["aggregati"]["conteggi"]
assert sum(cnt.values()) == n == 2224, cnt
assert cnt["insufficient_data"] == 55 and cnt["reachable"] == 2148 and cnt["forbidden"] + cnt["isolated"] == 21 and cnt["outside_model"] == 0, cnt
assert r["manifest"]["coverage"]["accessibility_counts"] == cnt
print("1 ok", cnt)

# 2. nessun reachable con distanza infinita, vuota o incoerente; tempo = distanza / velocità
for o in O.values():
    if o["stato"] != "reachable": assert "totale_m" not in o; continue
    assert math.isfinite(o["totale_m"]) and o["totale_m"] > 0 and math.isfinite(o["tempo_s"]) and o["tempo_s"] >= 0, o
    assert abs(o["tempo_s"] - o["totale_m"] / 1.2) < 0.35, o
    assert o["totale_m"] >= o["diretta_m"] - 1.0, o   # la rete non è più corta della linea d'aria (tolleranza raccordi)
print("2 ok")

# 3. stessi percorsi campione di T04 (R01-R09), V01 forbidden
camp = {x["id"]: x for x in json.load(open(ROOT / "network/percorsi_campione.json"))}
ent = {e["entrance_id"]: e for d in c["dest"].values() for e in d["ingressi"]}
stop_ent = {d["destination_id"]: d["ingressi"][0] for d in c["dest"].values() if d["categoria"] == "stop"}
snap_e = lambda e: (Point(e["xy"]), {**e["aggancio"], "proj": tuple(e["aggancio"]["proj"])})
orig40 = A.agganci_origini("civici_sit_z2", 40.0)
def punto(s):
    tok = s.split()[0]
    return snap_e(stop_ent[tok]) if tok.startswith("dst_stop") else snap_e(ent[tok]) if tok.startswith("ent_") else orig40[tok]
import rete_lib as RL
def invertito(sn):   # l'arco è memorizzato nel grafo in ordine (u, v) opposto alla geometria
    e = c["G"].edges[sn["u"], sn["v"], sn["edge_id"]]; return (sn["u"], sn["v"]) != (e["nod_da"], e["nod_a"])
def corretto(sn):    # snap con l'offset riportato al verso (u, v) del grafo, per far girare il percorso() di T04 senza il suo difetto
    if not invertito(sn): return sn
    return {**sn, "offset_m": round(c["G"].edges[sn["u"], sn["v"], sn["edge_id"]]["geom"].length - sn["offset_m"], 2)}
differenti = []
for rid, t in sorted(camp.items()):
    po, so = punto(t["origine"]); pd_, sd = punto(t["destinazione"])
    eid = t["destinazione"].split()[0]; eid = stop_ent[eid]["entrance_id"] if eid.startswith("dst_stop") else eid
    righe, _ = A.calcola({eid: (pd_, sd)}, {rid: (po, so)}, base); x = righe[rid]
    if rid == "V01":
        assert t["stato"] == "forbidden" and x["stato"] == "forbidden" and abs(x["permissivo_m"] - t["permissivo_lunghezza_m"]) < 1.5, (t, x)
        continue
    assert x["stato"] == "reachable" == t["stato"], (rid, x)
    # riferimento indipendente: il percorso() di T04 con gli snap riportati al verso del grafo
    H, nodi, archi = RL.percorso(c["G"], corretto(so), corretto(sd)); att = {e.get("parte_di", e["edge_id"]) for e in archi if e["tipo_arco"] == "attraversamento"}
    atteso = sum(e["length_m"] for e in archi) + so["dist_m"] + sd["dist_m"]
    assert abs(x["totale_m"] - atteso) < 0.3 and x["attraversamenti"] == len(att), (rid, x["totale_m"], atteso)
    assert abs(x["diretta_m"] - t["diretta_m"]) < 0.15 and x["totale_m"] >= x["diretta_m"], (rid, x)
    if invertito(so) or invertito(sd):
        differenti.append(rid); assert t["lunghezza_totale_m"] > x["totale_m"] + 5, (rid, t["lunghezza_totale_m"], x["totale_m"])   # T04 sovrastima
    else:
        assert abs(x["totale_m"] - t["lunghezza_totale_m"]) < 0.3 and x["attraversamenti"] == t["attraversamenti"] and abs(x["m_marciapiede_ignoto"] - t["m_marciapiede_ignoto"]) < 0.3, (rid, x, t)
    print(f"  {rid} {x['totale_m']} m (T04 {t['lunghezza_totale_m']} m){' [snap su arco invertito]' if rid in differenti else ''}, attr {x['attraversamenti']}")
print("3 ok: R01-R09 uguali a T04 salvo", differenti, "(difetto di orientamento in rete_lib.con_agganci), V01 forbidden")
# V01 anche dentro la funzione di libreria
assert O["adr_sit_11884"]["stato"] == "forbidden"

# 4. agganci a 40 m = origini_snap.gpkg di T04
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
for f in sorted((ROOT / "analysis/manifest").glob("*.manifest.json")):
    m = json.load(open(f)); assert not list(Draft202012Validator(S["manifest"], registry=reg).iter_errors(m)), f.name
    assert m["assets"] and all((ROOT / a["path"]).exists() and hashlib.sha256((ROOT / a["path"]).read_bytes()).hexdigest() == a["sha256"] for a in m["assets"]), f.name
    assert sum(m["coverage"]["accessibility_counts"].values()) == m["params"]["origins"]["count"]
print("6 ok: manifest/job validi, asset con sha256 corretto")

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

# 9. asset mappa: EPSG:4326, conteggi uguali al manifest
for nome, did in (("battisti", BAT), ("pellico", PEL)):
    g = json.load(open(ROOT / f"analysis/out/accessibilita_{nome}.geojson")); F = g["features"]
    org = [f for f in F if f["properties"]["layer"] == "origine"]
    assert len(org) == 2224 and all(10.3 < f["geometry"]["coordinates"][0] < 10.5 and 43.6 < f["geometry"]["coordinates"][1] < 43.8 for f in org)
    ref = A.compute_walk_access(did, profile=base)["aggregati"]["conteggi"]
    assert {s: sum(1 for f in org if f["properties"]["stato"] == s) for s in ref} == ref
    assert any(f["properties"]["layer"] == "arco_usato" for f in F) and sum(f["properties"]["layer"] == "destinazione" for f in F) == 1
    assert (ROOT / f"analysis/out/accessibilita_{nome}.geojson").stat().st_size < 1_000_000
print("9 ok: asset mappa")

# 10. input non validi respinti
for bad in (dict(profile={"speed_m_s": 5, "crossing_penalty_s": 0, "stairs": "allowed"}), dict(destination_id="dst_x")):
    try: A.compute_walk_access(bad.pop("destination_id", BAT), **bad); raise SystemExit("doveva fallire")
    except ValueError: pass
print("10 ok: tutti i test passati")
