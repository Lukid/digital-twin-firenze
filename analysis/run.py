#!/usr/bin/env python3
"""F06: accessibilità verso ogni destinazione dell'area (DT_AOI) con 4 profili e le sensibilità (snapping, ingressi).
Scrive manifest, riepilogo e asset mappa in analysis/<area>/ (versionati) e i dati grandi in data/norm/<area>/analysis/."""
import json, pathlib, shutil, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import accessibilita as A
from shapely.geometry import Point, mapping

OUT = A.OUT_VERS; MAN = OUT / "manifest"
shutil.rmtree(MAN, ignore_errors=True); MAN.mkdir(parents=True); A.OUT_DATI.mkdir(parents=True, exist_ok=True)
c = A.contesto()
RIFUGI = sorted(d for d in c["dest"] if c["dest"][d]["categoria"] == "cooling_refuge")   # D32: un solo job verso il più vicino dei 7, in fondo
DEST = sorted(set(c["dest"]) - set(RIFUGI))
dump = lambda o, p, **k: pathlib.Path(p).write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":"), allow_nan=False, **k))
FAM = "address_points"; ORIG = A.agganci_origini(FAM, 40.0)
TCOL = (("base_1_2", "t"), ("lento_0_8", "t_lento"), ("rapido_1_4", "t_rapido"), ("ridotta_0_8_senza_scale", "t_ridotta"))

def sintesi(res):
    a = res["aggregati"]
    return {"job_id": res["job"]["job_id"], "conteggi": a["conteggi"], "quote": {k: v["quota"] for k, v in a["quote_soglie"].items()}, "tempo_min": a["tempo_min"],
            "rete_m_p50": a["rete_m"]["p50"], "deviazione_alta": a["deviazione_alta"]["n"], "quota_ignoto": a["quota_metri_marciapiede_ignoto"],
            "top10_archi": [x["edge_id"] for x in a["archi_piu_usati"][:10]]}

riepilogo = {"aoi_id": A.AOI_ID, "baseline_id": A.BASELINE_ID, "graph_id": A.GRAPH_ID, "origini": {"kind": FAM, "count": len(ORIG)},
             "profili": {k: dict(v) for k, v in A.PROFILI.items()}, "soglie_min": [5, 10, 15], "destinazioni": {}, "sensibilita": {}}
ris = {}
for did in DEST:
    ris[did] = {}; d = c["dest"][did]
    for pid, prof in A.PROFILI.items():
        res = A.compute_walk_access(did, origin_family=FAM, profile=prof, out_dir=A.OUT_DATI / did); ris[did][pid] = res
        job, man = res["job"], res["manifest"]
        (MAN / f"{job['job_id']}.manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
        (MAN / f"{job['job_id']}.job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
        a = res["aggregati"]
        riepilogo["destinazioni"].setdefault(did, {"nome": d["nome"], "categoria": d["categoria"]})[pid] = {**sintesi(res), "distribuzione": a["istogramma_tempo_min"], "deviazione": a["deviazione"],
            "attraversamenti_mediana": a["attraversamenti_mediana"], "origini_con_scale": a["origini_con_scale"], "origini_con_barriera": a["origini_con_barriera"], "deviazione_alta_regola": a["deviazione_alta"]["regola"]}
    base = ris[did]["base_1_2"]["aggregati"]
    riepilogo["destinazioni"][did]["archi_piu_usati"] = [{k: v for k, v in x.items() if k != "geom"} for x in base["archi_piu_usati"][:15]]
    riepilogo["destinazioni"][did]["archi_ignoti_piu_usati"] = [{k: v for k, v in x.items() if k != "geom"} for x in base["archi_ignoti_piu_usati"][:15]]

    # asset mappa: civici, destinazione, archi usati (EPSG:4326)
    e0s = [e for e in d["ingressi"] if e["entrance_id"] in (d.get("ingressi_predefiniti") or [d["ingresso_predefinito"]])]; feats = []
    for oid in sorted(ris[did]["base_1_2"]["origini"]):
        r = ris[did]["base_1_2"]["origini"][oid]; g = A._ll(ORIG[oid][0]); ind = c["civ"].loc[oid, "indirizzo"]
        pr = {"layer": "origine", "id": oid, "ind": ind if isinstance(ind, str) else None, "stato": r["stato"]}
        for pid, k in TCOL:
            x = ris[did][pid]["origini"][oid]
            if x["stato"] == "reachable": pr[k] = round(x["tempo_s"] / 60, 1)
        rid = ris[did]["ridotta_0_8_senza_scale"]["origini"][oid]["stato"]
        if rid != r["stato"]: pr["stato_ridotta"] = rid
        if r["stato"] == "reachable": pr.update(d=r["totale_m"], dev=r["deviazione"], att=r["attraversamenti"], ign=r["m_marciapiede_ignoto"], ing=r["entrance_id"])
        elif r.get("motivo"): pr["motivo"] = r["motivo"]
        feats.append({"type": "Feature", "geometry": A.arrotonda(mapping(g)), "properties": pr})
    for e0 in e0s:
        g = A._ll(Point(e0["xy"]))
        feats.append({"type": "Feature", "geometry": A.arrotonda(mapping(g)), "properties": {"layer": "destinazione", "id": did, "ingresso": e0["entrance_id"], "nome": d["nome"], "stato_verifica": d["stato_verifica"]}})
    for grp, chiave in (("piu_usati", "archi_piu_usati"), ("ignoti_piu_usati", "archi_ignoti_piu_usati")):
        for x in base[chiave]:
            feats.append({"type": "Feature", "geometry": A.arrotonda(mapping(A._ll(x["geom"]))),
                          "properties": {"layer": "arco_usato", "gruppo": grp, "id": x["edge_id"], "n_origini": x["n_origini"], "marciapiede": x["marciapiede_stato"], "nome": x["nome"], "tipo": x["tipo_arco"]}})
    dump({"type": "FeatureCollection", "name": f"accessibilita_{did}",
          "nota": "EPSG:4326 solo per la mappa; calcolo in EPSG:7791. t = minuti a 1,2 m/s (lento 0,8, rapido 1,4, ridotta 0,8 senza scale con 10 s per attraversamento). Civici: punti d'indirizzo, non residenti. Rete OSM non verificata sul posto.",
          "job_id": ris[did]["base_1_2"]["job"]["job_id"], "features": feats}, OUT / f"accessibilita_{did}.geojson")

# sensibilità, profilo base: snapping per ogni destinazione, ingressi per le destinazioni con più di un ingresso
base_p = A.PROFILI["base_1_2"]
for did in DEST:
    riepilogo["sensibilita"][f"snapping_{did}"] = {str(s): sintesi(A.compute_walk_access(did, origin_family=FAM, profile=base_p, snap_limit_m=s)) for s in (20, 40, 60)}
for did in DEST:
    d = c["dest"][did]
    if len(d["ingressi"]) < 2: continue
    main = sorted(d.get("ingressi_predefiniti") or [d["ingresso_predefinito"]]); tutti = sorted(e["entrance_id"] for e in d["ingressi"])
    ing = {"predefinito": main} | ({f"tutti_i_{len(tutti)}": tutti} if tutti != main else {}) | {f"solo_{i}": [i] for i in tutti}
    out = riepilogo["sensibilita"][f"ingressi_{did}"] = {}
    for k, ids in ing.items():
        res = A.compute_walk_access(did, origin_family=FAM, profile=base_p, entrance_ids=ids); s = sintesi(res); s["ingressi"] = ids
        s["origini_per_ingresso"] = {i: sum(1 for r in res["origini"].values() if r.get("entrance_id") == i) for i in ids} if len(ids) > 1 else None
        s["descrizione"] = {i: next(e["fonte_ingresso"] for e in d["ingressi"] if e["entrance_id"] == i) for i in ids}
        out[k] = s
    base10 = set(out["predefinito"]["top10_archi"])
    for s in out.values(): s["sovrapposizione_top10_con_predefinito"] = len(base10 & set(s["top10_archi"]))

# rifugi climatici (D32): accessibilità verso il più vicino dei 7, profilo base; sensibilità 0,8-1,4 m/s negli intervalli del manifest
res = A.compute_walk_access(RIFUGI, origin_family=FAM, profile=base_p, out_dir=A.OUT_DATI / "rifugi")
(MAN / f"{res['job']['job_id']}.manifest.json").write_text(json.dumps(res["manifest"], ensure_ascii=False, indent=1))
(MAN / f"{res['job']['job_id']}.job.json").write_text(json.dumps(res["job"], ensure_ascii=False, indent=1))
dest_di = {e["entrance_id"]: did for did in RIFUGI for e in c["dest"][did]["ingressi"]}; a = res["aggregati"]
riepilogo["rifugi"] = {**sintesi(res), "destinazioni": RIFUGI, "intervallo_velocita": {k: v["intervallo_velocita"] for k, v in a["quote_soglie"].items()},
                       "piu_vicino": {did: sum(1 for r in res["origini"].values() if r.get("entrance_id") and dest_di[r["entrance_id"]] == did) for did in RIFUGI}}
dump(riepilogo, OUT / "riepilogo.json", sort_keys=True)
print(json.dumps({n: {p: {"conteggi": v["conteggi"], "quote": v["quote"], "t": v["tempo_min"]} for p, v in d.items() if isinstance(v, dict) and "quote" in v} for n, d in riepilogo["destinazioni"].items()}, ensure_ascii=False, indent=1))
