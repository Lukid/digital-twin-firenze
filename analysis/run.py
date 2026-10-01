#!/usr/bin/env python3
"""T06: esegue Battisti e Pellico con 4 profili, le sensibilità, scrive manifest (analysis/manifest), asset mappa (analysis/out) e dati grandi (data/norm/analysis)."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import accessibilita as A
from shapely.geometry import mapping, Point

ROOT = A.ROOT; OUT = ROOT / "analysis/out"; MAN = ROOT / "analysis/manifest"
DEST = {"battisti": "dst_school_piee82101p", "pellico": "dst_stop_pi4390"}
c = A.contesto()
dump = lambda o, p, **k: pathlib.Path(p).write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":"), **k))
r6 = lambda x: round(x, 6)

def sintesi(res):
    a = res["aggregati"]
    return {"job_id": res["job"]["job_id"], "conteggi": a["conteggi"], "quote": {k: v["quota"] for k, v in a["quote_soglie"].items()}, "tempo_min": a["tempo_min"],
            "rete_m_p50": a["rete_m"]["p50"], "deviazione_alta": a["deviazione_alta"]["n"], "quota_ignoto": a["quota_metri_marciapiede_ignoto"],
            "top10_archi": [x["edge_id"] for x in a["archi_piu_usati"][:10]]}

riepilogo = {"profili": {k: dict(v) for k, v in A.PROFILI.items()}, "soglie_min": [5, 10, 15], "destinazioni": {}, "sensibilita": {}}
risultati = {}
for nome, did in DEST.items():
    risultati[nome] = {}
    for pid, prof in A.PROFILI.items():
        res = A.compute_walk_access(did, profile=prof, out_dir=A.OUT_DATI / nome)
        risultati[nome][pid] = res
        job, man = res["job"], res["manifest"]
        (MAN / f"{job['job_id']}.manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
        (MAN / f"{job['job_id']}.job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
        a = res["aggregati"]
        riepilogo["destinazioni"].setdefault(nome, {})[pid] = {**sintesi(res), "distribuzione": a["istogramma_tempo_min"], "deviazione": a["deviazione"], "attraversamenti_mediana": a["attraversamenti_mediana"],
            "origini_con_scale": a["origini_con_scale"], "origini_con_barriera": a["origini_con_barriera"], "deviazione_alta_regola": a["deviazione_alta"]["regola"]}
    base = risultati[nome]["base_1_2"]["aggregati"]
    riepilogo["destinazioni"][nome]["archi_piu_usati"] = [{k: v for k, v in x.items() if k != "geom"} for x in base["archi_piu_usati"][:15]]
    riepilogo["destinazioni"][nome]["archi_ignoti_piu_usati"] = [{k: v for k, v in x.items() if k != "geom"} for x in base["archi_ignoti_piu_usati"][:15]]

    # asset mappa
    ent = c["dest"][did]; e0 = next(e for e in ent["ingressi"] if e["entrance_id"] == ent["ingresso_predefinito"])
    feats = []
    for oid in sorted(risultati[nome]["base_1_2"]["origini"]):
        r = risultati[nome]["base_1_2"]["origini"][oid]; p = A.agganci_origini("civici_sit_z2", 40.0)[oid][0]; g = A._ll(p)
        pr = {"layer": "origine", "id": oid, "ind": c["civ"].loc[oid, "indirizzo"], "stato": r["stato"]}
        for pid, k in (("base_1_2", "t"), ("lento_0_8", "t_lento"), ("rapido_1_4", "t_rapido"), ("ridotta_0_8_senza_scale", "t_ridotta")):
            x = risultati[nome][pid]["origini"][oid]
            if x["stato"] == "reachable": pr[k] = round(x["tempo_s"] / 60, 1)
        rid = risultati[nome]["ridotta_0_8_senza_scale"]["origini"][oid]["stato"]
        if rid != r["stato"]: pr["stato_ridotta"] = rid
        if r["stato"] == "reachable": pr.update(d=r["totale_m"], dev=r["deviazione"], att=r["attraversamenti"], ign=r["m_marciapiede_ignoto"])
        elif r.get("motivo"): pr["motivo"] = r["motivo"]
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [r6(g.x), r6(g.y)]}, "properties": pr})
    g = A._ll(Point(e0["xy"]))
    feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [r6(g.x), r6(g.y)]}, "properties": {"layer": "destinazione", "id": did, "ingresso": e0["entrance_id"], "nome": ent["nome"], "stato_verifica": ent["stato_verifica"]}})
    for grp in ("piu_usati", "ignoti_piu_usati"):
        for x in base["archi_piu_usati" if grp == "piu_usati" else "archi_ignoti_piu_usati"]:
            gl = A._ll(x["geom"])
            feats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[r6(a), r6(b)] for a, b in gl.coords]},
                          "properties": {"layer": "arco_usato", "gruppo": grp, "id": x["edge_id"], "n_origini": x["n_origini"], "marciapiede": x["marciapiede_stato"], "nome": x["nome"], "tipo": x["tipo_arco"]}})
    dump({"type": "FeatureCollection", "name": f"accessibilita_{nome}",
          "nota": "EPSG:4326 solo per la mappa; calcolo in EPSG:7791. t = minuti a 1,2 m/s (lento 0,8, rapido 1,4, ridotta 0,8 senza scale con 10 s per attraversamento). Civici SIT: punti d'indirizzo, uso interno. Rete OSM non verificata.",
          "job_id": risultati[nome]["base_1_2"]["job"]["job_id"], "features": feats}, OUT / f"accessibilita_{nome}.geojson")

# sensibilità (b) snapping e (c) ingressi, profilo base
base_p = A.PROFILI["base_1_2"]
for nome, did in DEST.items():
    riepilogo["sensibilita"][f"snapping_{nome}"] = {str(s): sintesi(A.compute_walk_access(did, profile=base_p, snap_limit_m=s)) for s in (20, 40, 60)}
batt = c["dest"][DEST["battisti"]]; main = batt["ingresso_predefinito"]
cont = sorted(e["entrance_id"] for e in batt["ingressi"] if e["classe"] == "probabile_edificio_contiguo"); tutti = sorted(e["entrance_id"] for e in batt["ingressi"])
ing = {"probabile": [main], "tutti_contigui": cont, "tutti_i_9": tutti}
for i in cont: ing[f"contiguo_{i}"] = [i]
riepilogo["sensibilita"]["ingressi_battisti"] = {}
for k, ids in ing.items():
    res = A.compute_walk_access(DEST["battisti"], profile=base_p, entrance_ids=ids); s = sintesi(res)
    s["ingressi"] = ids; s["origini_per_ingresso"] = {i: sum(1 for r in res["origini"].values() if r.get("entrance_id") == i) for i in ids} if len(ids) > 1 else None
    s["civico"] = {i: next(e["tags"].get("addr:street", "") + " " + e["tags"].get("addr:housenumber", "") for e in batt["ingressi"] if e["entrance_id"] == i) for i in ids}
    riepilogo["sensibilita"]["ingressi_battisti"][k] = s
base10 = set(riepilogo["destinazioni"]["battisti"]["base_1_2"]["top10_archi"])
for k, s in riepilogo["sensibilita"]["ingressi_battisti"].items(): s["sovrapposizione_top10_con_probabile"] = len(base10 & set(s["top10_archi"]))
dump(riepilogo, OUT / "riepilogo.json", sort_keys=True)
print(json.dumps({n: {p: {"conteggi": v["conteggi"], "quote": v["quote"], "t": v["tempo_min"]} for p, v in d.items() if isinstance(v, dict) and "quote" in v} for n, d in riepilogo["destinazioni"].items()}, ensure_ascii=False, indent=1))
