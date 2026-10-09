"""Test delle geometrie F05 (Firenze Novoli) su geometry/firenze_novoli/{edifici,alberi}_fp.geojson, report_firenze_novoli.json, parametri_chiome.json. Uscita 0 = tutto ok."""
import json
from pathlib import Path
from shapely.geometry import shape
from shapely.strtree import STRtree

G = Path(__file__).resolve().parent
F = G / "firenze_novoli"
E = json.load(open(F / "edifici_fp.geojson"))["features"]
A = json.load(open(F / "alberi_fp.geojson"))["features"]
P = json.load(open(G / "parametri_chiome.json"))
R = json.load(open(F / "report_firenze_novoli.json"))
ok = lambda c, m: (_ for _ in ()).throw(AssertionError(m)) if not c else None

# edifici
ids = [f["properties"]["id"] for f in E]
ok(len(ids) == len(set(ids)), "id edifici duplicati")
ok(len(E) == R["edifici"]["fp"]["volumi"], "conteggio edifici diverso dal report")
n_lidar = 0
for f in E:
    p = f["properties"]
    ok(p["classe_h"] in ("measured", "derived"), f"{p['id']}: classe_h")
    ok(p["portico"] == "ignoto" and p["sospeso"] == "ignoto", f"{p['id']}: portico/sospeso devono essere ignoto")
    ok(set(p["cls"]) >= {"h", "h_min", "h_max"}, f"{p['id']}: cls mancante")
    ok(p["tipo"] in ("volume_uv", "volume_nuovo", "copertura_osm"), f"{p['id']}: tipo")
    ok(p["tipo"] != "volume_uv" or ("h_uv" in p and p["id"].startswith("bld_rt_")), f"{p['id']}: UV senza h_uv")
    ok((p["classe_h"] == "measured") == (p["tipo"] == "volume_uv" and p["anno"] == 2011), f"{p['id']}: measured solo per altezza uv_av 2011")
    if p["classe_h"] == "derived":
        n_lidar += 1
        ok("h_lidar" in p, f"{p['id']}: derived senza h_lidar")
    if "h" not in p:
        continue
    ok(0.3 <= p["h_min"] <= p["h"] <= p["h_max"] <= 80, f"{p['id']}: altezza/intervallo assurdo {p['h_min']} {p['h']} {p['h_max']}")
    ok(p["h_max"] > p["h_min"], f"{p['id']}: stima senza intervallo")
    ok(20 <= p["z_base"] <= 90, f"{p['id']}: quota base assurda {p['z_base']}")
    ok(p["area_m2"] > 0, f"{p['id']}: area")
    ok(p["flag"] != "demolizione_probabile" or p["presente_2023"] is False, f"{p['id']}: demolizione senza presente_2023 falso")
    ok(p["flag"] == "demolizione_probabile" or p["presente_2023"], f"{p['id']}: presente_2023 falso senza demolizione")
ok(sum(1 for f in E if "h" not in f["properties"]) == R["edifici"]["fp"]["senza_altezza"], "volumi senza altezza non dichiarati")
ok(n_lidar == R["edifici"]["fp"]["classe_h"]["derived"], "classe derived diversa dal report")
ok(R["edifici"]["fp"]["flag_uv"].get("demolizione_probabile", 0) == R["edifici"]["fp"]["non_presenti_2023"], "demolizioni e non presenti non coincidono")
geoms = [shape(f["geometry"]) for f in E]
ok(all(g.is_valid and not g.is_empty for g in geoms), "geometria edificio non valida")
tree = STRtree(geoms)
dup = sum(1 for i, g in enumerate(geoms) for j in tree.query(g) if j > i and g.intersection(geoms[j]).area > 0.5 * min(g.area, geoms[j].area))
ok(dup == 0, f"{dup} coppie di volumi sovrapposte oltre il 50%")

# alberi: misurati (derived) e stimati (estimated) separati e contati
aid = [f["properties"]["id"] for f in A]
ok(len(aid) == len(set(aid)), "id alberi duplicati")
ok(len(A) == R["alberi"]["fp"]["totale"], "conteggio alberi diverso dal report")
mis = [f for f in A if f["properties"]["chioma_cls"] == "derived"]
sti = [f for f in A if f["properties"]["chioma_cls"] == "estimated"]
ok(len(mis) == R["alberi"]["fp"]["chioma_misurata"] and len(sti) == R["alberi"]["fp"]["chioma_stimata"], "chiome misurate/stimate diverse dal report")
ok(len(mis) + len(sti) == len(A) and len(mis) > 0 and len(sti) > 0, "misurate + stimate non sommano al totale")
ok(sum(R["alberi"]["fp"]["motivo_stima"].values()) == len(sti), "motivi di stima non sommano alle stimate")
for f in A:
    p = f["properties"]
    ok(p["id"].startswith("tre_fi_"), f"{p['id']}: id")
    ok(p["h_cls"] == p["chioma_cls"], f"{p['id']}: h_cls e chioma_cls devono coincidere")
    ok(p["h_cls"] in ("derived", "estimated"), f"{p['id']}: h_cls")
    ok((p["h_cls"] == "estimated") == bool(p.get("motivo_stima")), f"{p['id']}: motivo di stima incoerente con la classe")
    ok(2 <= p["h_min"] <= p["h"] <= p["h_max"] <= 60 and p["h_max"] > p["h_min"], f"{p['id']}: altezza albero {p['h_min']} {p['h']} {p['h_max']}")
    ok(0 < p["chioma_d_min"] <= p["chioma_d"] <= p["chioma_d_max"] and p["chioma_d_max"] > p["chioma_d_min"], f"{p['id']}: chioma senza intervallo")
    ok(0 < p["imposta_min"] <= p["imposta"] <= p["imposta_max"] < p["h_max"], f"{p['id']}: imposta")
    ok(p["imposta_max"] <= 0.7 * p["h_max"] + 0.006 and p["imposta_min"] < p["h_min"], f"{p['id']}: imposta oltre la chioma")
    ok("tronco_d" not in p or 0 < p["tronco_d"] <= 1.5, f"{p['id']}: tronco")
    ok(20 <= p["z_base"] <= 90, f"{p['id']}: quota base")
    ok(set(p["cls"]) >= {"chioma_d", "imposta", "tronco_d"} and p["cls"]["imposta"] == "estimated", f"{p['id']}: cls")
    if p["h_cls"] == "estimated":
        ok(p["motivo_stima"] in R["alberi"]["fp"]["motivo_stima"], f"{p['id']}: motivo sconosciuto")
    else:
        ok(not p["in_edificio"], f"{p['id']}: chioma misurata di un albero dentro un edificio")
        ok(p["chioma_d_max"] > 1.2 * p["chioma_d"] - 1e-6, f"{p['id']}: intervallo chioma misurata troppo stretto")

# parametri: min <= tipico <= max
for n, c in P["classi"].items():
    for k, v in c.items():
        ok(0 < v["min"] <= v["tipico"] <= v["max"], f"classe {n}.{k} non ordinata")

# verifica Escapos: solo aggregati (CC BY-NC 4.0), campione dichiarato, limite di indipendenza scritto
V = R["verifica_escapos"]
ok(V["fp"]["n_alberi"] == 24 and V["allargata_50"]["n_alberi"] == 50, "campione Escapos: 24 in FP e 50 nell'area allargata")
for k in ("fp", "allargata_50"):
    s = V[k]["altezza_chm_p95_misurati"]
    ok(s["n"] == V[k]["n_chioma_misurata"] and s["n"] > 10, f"{k}: n del confronto")
    ok(abs(s["mediana_scarto_m"]) < 1.0 and s["mae_m"] < 1.5 and s["r"] > 0.8, f"{k}: scarto di altezza fuori da ogni plausibilità {s}")
    ok(V[k]["n_chioma_misurata"] + V[k]["n_chioma_stimata"] == V[k]["n_alberi"], f"{k}: misurate + stimate")
ok("indipendenza" in V and "non prova" in V["indipendenza"], "manca il limite di indipendenza di h_m")
ESC = {"h_m", "crn_w_m", "dbh_cm", "lai", "can_h_m", "canopy_area_m2", "cens_id", "seg_id", "tre_escapos"}
ok(not any(ESC & set(f["properties"]) for f in A + E) and "tre_escapos" not in json.dumps(R), "valori o id Escapos in file versionati")
ok(all(not isinstance(x, list) for v in (V["fp"], V["allargata_50"]) for x in v.values()), "verifica Escapos: solo aggregati, nessun elenco per albero")
print(f"OK: {len(E)} volumi ({n_lidar} con altezza LiDAR), {len(A)} alberi ({len(mis)} chiome misurate, {len(sti)} stimate), Escapos solo aggregati")
