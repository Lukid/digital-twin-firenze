"""Test delle geometrie T05 su edifici_z2.geojson, alberi_z2.geojson, parametri_chiome.json, report_z2.json. Uscita 0 = tutto ok."""
import json
from pathlib import Path
from shapely.geometry import shape
from shapely.strtree import STRtree

G = Path(__file__).resolve().parent
E = json.load(open(G / "edifici_z2.geojson"))["features"]
A = json.load(open(G / "alberi_z2.geojson"))["features"]
P = json.load(open(G / "parametri_chiome.json"))
R = json.load(open(G / "report_z2.json"))
ok = lambda c, m: (_ for _ in ()).throw(AssertionError(m)) if not c else None

# parametri: min <= tipico <= max, positivi
for n, c in P["classi"].items():
    for k, v in c.items():
        ok(0 < v["min"] <= v["tipico"] <= v["max"], f"classe {n}.{k} non ordinata")
    ok(c["altezza_m"]["min"] > c["altezza_imposta_m"]["max"] or n == "ignota", f"{n}: imposta oltre l'altezza minima")

# edifici
ids = [f["properties"]["id"] for f in E]
ok(len(ids) == len(set(ids)), "id edifici duplicati")
ok(len(E) == R["edifici_Z2"]["volumi_totali"], "conteggio edifici diverso dal report")
n_nonh = 0
for f in E:
    p = f["properties"]
    ok(p["classe_h"] in ("measured", "derived"), f"{p['id']}: classe_h")
    ok(p["portico"] == "ignoto" and p["sospeso"] == "ignoto", f"{p['id']}: portico/sospeso devono essere ignoto")
    ok(set(p["cls"]) >= {"h", "h_min", "h_max"}, f"{p['id']}: cls mancante")
    if "h" not in p:
        n_nonh += 1; continue
    ok(0.3 <= p["h_min"] <= p["h"] <= p["h_max"] <= 60, f"{p['id']}: altezza/intervallo assurdo {p['h_min']} {p['h']} {p['h_max']}")
    ok(p["h_max"] - p["h_min"] > 0, f"{p['id']}: stima senza intervallo")
    ok(-5 <= p["z_base"] <= 30, f"{p['id']}: quota base assurda {p['z_base']}")
    ok(p["area_m2"] > 0, f"{p['id']}: area")
ok(n_nonh == 0 or n_nonh == R["edifici_Z2"]["derived_senza_altezza_dsm"], "volumi senza altezza non dichiarati nel report")
geoms = [shape(f["geometry"]) for f in E]
ok(all(g.is_valid and not g.is_empty for g in geoms), "geometria edificio non valida")
tree = STRtree(geoms)
dup = 0
for i, g in enumerate(geoms):
    for j in tree.query(g):
        if j > i and g.intersection(geoms[j]).area > 0.5 * min(g.area, geoms[j].area):
            dup += 1
ok(dup == 0, f"{dup} coppie di volumi sovrapposte oltre il 50% (duplicati)")

# alberi
aid = [f["properties"]["id"] for f in A]
ok(len(aid) == len(set(aid)), "id alberi duplicati")
ok(len(A) == R["alberi_Z2"]["totale"], "conteggio alberi diverso dal report")
for f in A:
    p = f["properties"]
    ok(p.get("fonti"), f"{p['id']}: albero senza fonte")
    fs = p["fonti"].split(",")
    ok(set(fs) <= {"dbt10k_2010", "osm", "copernicus"}, f"{p['id']}: fonte sconosciuta")
    ok(("dbt10k_2010" in fs) == ("id_dbt" in p) and ("osm" in fs) == ("id_osm" in p), f"{p['id']}: fonti e id originari non coerenti")
    ok(p["h_cls"] in ("measured", "derived", "estimated"), f"{p['id']}: h_cls")
    ok(2 <= p["h_min"] <= p["h"] <= p["h_max"] <= 50 and p["h_max"] > p["h_min"], f"{p['id']}: altezza albero {p['h_min']} {p['h']} {p['h_max']}")
    ok(0 < p["chioma_d_min"] <= p["chioma_d"] <= p["chioma_d_max"] and p["chioma_d_max"] > p["chioma_d_min"], f"{p['id']}: chioma senza intervallo")
    ok(0 < p["imposta_min"] <= p["imposta"] <= p["imposta_max"] < p["h_max"], f"{p['id']}: imposta")
    ok(p["imposta_max"] <= 0.7 * p["h_max"] + 1e-6 and p["imposta_min"] < p["h_min"], f"{p['id']}: imposta oltre la chioma")
    ok(0 < p["tronco_d"] < 1.5, f"{p['id']}: tronco")
    ok(-5 <= p["z_base"] <= 30, f"{p['id']}: quota base")
    ok(set(p["cls"]) >= {"chioma_d", "imposta", "tronco_d"} and p["cls"]["chioma_d"] == "estimated", f"{p['id']}: cls chioma")
ok(sum(R["alberi_Z2"]["per_combinazione_fonti"].values()) == len(A), "combinazioni fonti non sommano al totale")
print(f"OK: {len(E)} volumi, {len(A)} alberi, nessuna sovrapposizione, nessun albero senza fonte")
