#!/usr/bin/env python3
"""Test dell'indicatore di costo del filare S1 (D33): ricalcola costo e indicatore dalle voci versionate e l'ombra guadagnata a mezzogiorno di luglio.
Uso: pipeline/.venv/bin/python scenarios/test_costo_filare.py (circa 20 s; richiede data/)"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import costo_filare as C
import scenari as S

r = json.loads(C.OUT.read_text()); V = json.loads(C.VOCI.read_text())
# 1. voci: solo codici del prezzario 2026, fonte con licenza e sha256 dello zip; il costo si ricalcola dalle voci
assert V["fonte"]["licenza"].startswith("CC BY 4.0") and len(V["fonte"]["zip_sha256"]) == 64 and all(v["codice"].startswith("TOS26_") and v["prezzo"] > 0 for v in V["voci"])
assert {v["codice"] for v in V["voci"] if v["tipo"] == "piantagione"} == set(C.PIANTAGIONE)
c = C.costo(V["voci"], r["alberi"]); assert c == r["costo"] and r["alberi"] == 7
assert abs(c["minimo_eur"] - sum(x["quantita"] * x["prezzo"] for x in c["righe"] if x["estremo"] == "minimo")) < 0.05 and c["minimo_eur"] < c["massimo_eur"]
print("1 ok: costo", c["minimo_eur"], "-", c["massimo_eur"], "euro da", len(V["voci"]), "voci")
# 2. indicatore = m2 / migliaia di euro, per ogni data e fascia
for d, fd in r["ombra"]["m2"].items():
    for f, v in fd.items():
        lo, hi = r["m2_per_mille_euro"][d][f]["centrale"]
        assert abs(lo - v["centrale"] / c["massimo_eur"] * 1000) < 0.01 and abs(hi - v["centrale"] / c["minimo_eur"] * 1000) < 0.01, (d, f)
        assert v["intervallo"][0] <= v["centrale"] <= v["intervallo"][1] and v["centrale"] > 0
assert r["riferimento"]["m2_per_mille_euro"] == r["m2_per_mille_euro"]["2026-07-15"]["punta_12_30_13_30"]["centrale"]
print("2 ok: indicatore", r["riferimento"])
# 3. ombra guadagnata ricalcolata: 15 luglio, 12:30-13:30, caso centrale; non supera l'area delle chiome di S1 (zenit) e il job_id è lo stesso
s0, s1 = S.carica(C.S0), S.carica(C.S1); _, alberi = S.volumi_scenario(s1); cond = {**S.condizioni(), "times": ["12:30", "13:00", "13:30"], "date": "2026-07-15"}
R = C.ricevitore(alberi, S.condizioni()); rec = [{"receiver_id": "sfc_fi_s1_ombra_alberi", "kind": "surface", "geometry": __import__("shapely").geometry.mapping(R)}]
assert abs(R.area - r["ombra"]["ricevitore_m2"]) < 0.1
a0, a1 = ({x["time_local"]: x["shaded_m2"] for x in S.calcola_ombra(s, rec, cond, casi=["veg_lidar_tipico"])["righe"]} for s in (s0, s1))
m2 = sum(a1[t] - a0[t] for t in a0) / len(a0)
assert abs(m2 - r["riferimento"]["m2"]) < 0.06 and 0 < m2 <= sum(3.141592653589793 * t["a"] ** 2 for t in alberi), m2
print("3 ok: ombra guadagnata", round(m2, 1), "m2")
print("TUTTO OK")
