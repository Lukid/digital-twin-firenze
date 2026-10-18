#!/usr/bin/env python3
"""F4, compiti 3 e 5: percorsi campione più esposti al sole in un istante (classifica per metri e per minuti al sole) e tratti in ombra attesi.
Un percorso per esecuzione (memoria del worker: 7,9 GB, nessuno swap), stessi parametri di compute_shadow del servizio con
obstacles=buildings_trees_and_lidar_vegetation, space_step_m 1, time_step_min 5, 1,2 m/s: stesso job_id di una chiamata MCP con gli stessi argomenti.

Uso: pipeline/.venv/bin/python shadow/esposizione.py --data 2026-07-15 --orari 14:00 --percorso R01
     (poi gli altri percorsi, uno alla volta; ogni esecuzione aggiorna classifica e tratti al sole)
Scrive: shadow/<area>/manifest/<job>.{job,manifest}.json, shadow/<area>/esposizione_<data>.json (numeri, classifica e geometrie in EPSG:4326),
        shadow/<area>/tratti_sole_<data>.geojson (tratto al sole più lungo dei tre percorsi più esposti, per la scena).
Guardiano: sotto 700 MB di memoria disponibile il calcolo si ferma (uscita 3)."""
import argparse, json, os, resource, sys, threading, time
import numpy as np, psutil, shapely
from pyproj import Transformer
from shapely.geometry import mapping, shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ombre as O, run as RUN

OUT = RUN.OUT
METODO = {"name": "geometric_ray", "space_step_m": 1, "time_step_min": 5, "obstacles": "buildings_and_trees"}   # interi come li manda il client MCP: entrano nel job_id
CASI = ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max", "veg_lidar_min", "veg_lidar_tipico", "veg_lidar_max"]   # = CASI_VEG del servizio
VEG, EDIFICI = ("veg_lidar_min", "veg_lidar_tipico", "veg_lidar_max"), ("base_h_min", "base", "base_h_max")
N_TRATTI = 3
_to_ll = Transformer.from_crs(7791, 4326, always_xy=True).transform
_da_ll = Transformer.from_crs(4326, 7791, always_xy=True).transform


def guardiano(minimo_mb=700):
    def giro():
        while True:
            if psutil.virtual_memory().available < minimo_mb * 2**20: print(f"memoria disponibile sotto {minimo_mb} MB: calcolo fermato", flush=True); os._exit(3)
            time.sleep(1)
    threading.Thread(target=giro, daemon=True).start()


def ll(g): return O.arrotonda(mapping(shapely.transform(g, lambda c: np.column_stack(_to_ll(c[:, 0], c[:, 1])))))


def sole_e_ombra(L, tratto):
    """Linea in 7791 e Feature dei tratti in ombra (4326) -> (parti in ombra, parti al sole) in 7791."""
    g = tratto["geometry"]
    om = shapely.transform(shape(g), lambda c: np.column_stack(_da_ll(c[:, 0], c[:, 1]))) if g else shapely.LineString()
    sole = L.difference(om.buffer(0.05)) if not om.is_empty else L   # 5 cm: le coordinate in gradi sono arrotondate a 8 decimali
    return om, sole


def calcola(rid, data, orari):
    RUN.PERCORSI = [rid]; rec = RUN.ricevitori()[0]
    L = shape(rec["geometry"]); r0 = {k: v for k, v in rec.items() if not k.startswith("_")}
    t = time.time()
    r = O.compute_shadow(O.BASELINE_ID, [r0], {"date": data, "timezone": "Europe/Rome", "times": orari}, METODO, walk_speed_m_s=1.2, casi=CASI,
                         tratti_casi=["base", "veg_lidar_tipico"], out_dir=O.OUT_GRANDI)
    jid = r["job"]["job_id"]
    for k in ("job", "manifest"): (RUN.MAN / f"{jid}.{k}.json").write_text(json.dumps(r[k], ensure_ascii=False, indent=1))
    righe = {(x["time_local"], x["caso"]): x for x in r["righe"]}; tratti = {(f["properties"]["time_local"], f["properties"]["caso"]): f for f in r["tratti"]["features"]}
    out = {"descrizione": rec["_descrizione"], "lunghezza_m": round(L.length, 1), "stato_verifica": "da_verificare", "job_id": jid, "orari": {}}
    for h in orari:
        x = righe[(h, "veg_lidar_tipico")]
        if x["stato"] != O.STATO_OK: out["orari"][h] = {"stato_sole": x["stato"], "elevazione_deg": x["elevation_deg"]}; continue
        sole_m = lambda c: round(righe[(h, c)]["length_m"] - righe[(h, c)]["shaded_m"], 1)
        wmin = lambda c: righe[(h, c)].get("walk_sun_min")
        o = {"stato_sole": x["stato"], "elevazione_deg": x["elevation_deg"], "azimut_deg": x["azimuth_deg"],
             "m_sole": sole_m("veg_lidar_tipico"), "m_sole_intervallo": sorted(sole_m(c) for c in (VEG[0], VEG[2])),
             "minuti_sole": wmin("veg_lidar_tipico"), "minuti_sole_intervallo": sorted(wmin(c) for c in (VEG[0], VEG[2])) if wmin(VEG[0]) is not None else None,
             "minuti_totali": x.get("walk_total_min"), "frazione_ombra": x["shade_fraction"],
             "solo_edifici": {"m_sole": sole_m("base"), "m_sole_intervallo": sorted(sole_m(c) for c in (EDIFICI[0], EDIFICI[2])), "minuti_sole": wmin("base"), "frazione_ombra": righe[(h, "base")]["shade_fraction"]},
             "geometrie": {}}
        for c in ("base", "veg_lidar_tipico"):
            om, sole = sole_e_ombra(L, tratti[(h, c)])
            parti = sorted((p for p in shapely.get_parts(shapely.line_merge(sole)) if p.length > 0), key=lambda p: -p.length)
            o["geometrie"][c] = {"ombra": ll(om) if not om.is_empty else None, "sole_piu_lungo": ll(parti[0]) if parti else None}
            if c == "veg_lidar_tipico": o["tratto_sole_piu_lungo_m"] = round(parti[0].length, 1) if parti else 0.0
        out["orari"][h] = o
    out["calcolo"] = {"secondi": round(time.time() - t), "memoria_max_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 2)}
    return out


def classifica(E):
    """Per ogni orario: percorsi ordinati per metri al sole e per minuti al sole (contesto con vegetazione LiDAR, caso tipico)."""
    c = {}
    for h in sorted({h for p in E["percorsi"].values() for h in p["orari"]}):
        ok = [(rid, p["orari"][h]) for rid, p in E["percorsi"].items() if p["orari"].get(h, {}).get("m_sole") is not None]
        c[h] = {"per_metri_al_sole": [rid for rid, o in sorted(ok, key=lambda t: (-t[1]["m_sole"], t[0]))],
                "per_minuti_al_sole": [rid for rid, o in sorted(ok, key=lambda t: (-(t[1]["minuti_sole"] or 0), t[0]))]}
    return c


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0]); a.add_argument("--data", required=True); a.add_argument("--orari", required=True); a.add_argument("--percorso", required=True)
    a = a.parse_args(); orari = a.orari.split(","); guardiano()
    f = OUT / f"esposizione_{a.data}.json"
    E = json.loads(f.read_text()) if f.exists() else {"data": a.data, "versione_motore": O.VERSIONE, "baseline_id": O.BASELINE_ID, "ricevitore": "asse della rete (lato del marciapiede non noto)",
                                                      "metodo": {**METODO, "obstacles": "buildings_trees_and_lidar_vegetation", "casi": CASI, "walk_speed_m_s": 1.2},
                                                      "contesto_principale": "edifici, alberi censiti e vegetazione LiDAR, caso tipico (D14); intervallo dai casi min e max; solo edifici a parte",
                                                      "percorsi": {}}
    E["percorsi"][a.percorso] = calcola(a.percorso, a.data, orari)
    E["percorsi"] = dict(sorted(E["percorsi"].items())); E["classifica"] = classifica(E)
    f.write_text(json.dumps(E, ensure_ascii=False, indent=1) + "\n")
    feats = [{"type": "Feature", "geometry": E["percorsi"][rid]["orari"][h]["geometrie"]["veg_lidar_tipico"]["sole_piu_lungo"],
              "properties": {"route_id": rid, "date": a.data, "time_local": h, "posizione_classifica": i + 1, "length_m": E["percorsi"][rid]["orari"][h]["tratto_sole_piu_lungo_m"],
                             "caso": "veg_lidar_tipico", "stato_verifica": "da_verificare"}}
             for h, c in E["classifica"].items() for i, rid in enumerate(c["per_metri_al_sole"][:N_TRATTI])]
    (OUT / f"tratti_sole_{a.data}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")))
    p = E["percorsi"][a.percorso]; print(a.percorso, p["job_id"], p["calcolo"], {h: (o.get("m_sole"), o.get("minuti_sole")) for h, o in p["orari"].items()}, flush=True)


if __name__ == "__main__":
    main()
