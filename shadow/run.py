"""T09: esegue le analisi d'ombra su R01 e R03-R08 (3 date, fasce scuola e 8-18), convergenza e sensibilità su R01. Output: shadow/out, shadow/manifest,
data/norm/shadow. Uso: pipeline/.venv/bin/python shadow/run.py [--rapido]"""
import json, pathlib, sys, time
import numpy as np, shapely
from pyproj import Transformer
from shapely.geometry import shape, mapping
import shapely.ops
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ombre as O

ROOT, AQUI = O.ROOT, pathlib.Path(__file__).resolve().parent
OUT, MAN = AQUI / "out", AQUI / "manifest"
DATE = ["2026-06-21", "2026-09-15", "2026-10-01"]
FASCE = [{"id": "ingresso_mattina", "from": "07:45", "to": "08:30"}, {"id": "uscita_mezzogiorno", "from": "12:30", "to": "13:30"},
         {"id": "uscita_pomeriggio", "from": "16:00", "to": "16:30"}, {"id": "giornata_8_18", "from": "08:00", "to": "18:00"}]
ORARI = ["07:45"] + [f"{m // 60:02d}:{m % 60:02d}" for m in range(8 * 60, 18 * 60 + 1, 15)]
ROTTE = ["R01", "R03", "R04", "R05", "R06", "R07", "R08"]
METODO = {"name": "geometric_ray", "space_step_m": 1.0, "time_step_min": 5.0, "obstacles": "buildings_and_trees"}
CASI = ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max", "alberi_tipico_cilindro"]
ASSET = {"2026-09-15": ["08:00", "13:00", "16:30"]}
_to = Transformer.from_crs(4326, 7791, always_xy=True)


def ricevitori(offset=0.0, solo=None):
    """Percorsi di network/percorsi_campione.geojson in 7791. Asse della rete (centerline): il lato del marciapiede non è noto (R01: marciapiede_dichiarato false).
    offset > 0 sposta di offset m a sinistra rispetto al verso di marcia (sensibilità sul lato), < 0 a destra."""
    out = []
    for f in json.load(open(ROOT / "network/percorsi_campione.geojson"))["features"]:
        i = f["properties"]["id"]
        if i not in (solo or ROTTE) or f["properties"].get("stato", "reachable") != "reachable": continue
        g = shapely.ops.transform(lambda x, y, z=None: _to.transform(x, y), shape(f["geometry"]))
        if offset: g = g.offset_curve(offset)
        suf = "" if not offset else ("_sx" if offset > 0 else "_dx")
        out.append({"receiver_id": f"pth_t04_{i}{suf}", "kind": "path", "geometry": mapping(shapely.set_precision(g, 0.01))})
    return out


def esegui(data, rec, casi, metodo, asset=True, **kw):
    w = {"date": data, "timezone": "Europe/Rome", "times": ORARI}
    bb = (612028.0, 4839892.0, 613234.0, 4841035.0)   # Z2 (estensione dei volumi in_z2)
    return O.compute_shadow(O.BASELINE_ID, rec, w, metodo, casi=casi, fasce=FASCE, asset_times=ASSET.get(data, []) if asset else [],
                            asset_casi=("base", "alberi_tipico"), asset_bbox=bb, out_dir=OUT if asset else None, **kw)


def compatta(sint):
    """Riga per (ricevitore, data, fascia): frazione e minuti al sole per baseline (intervallo h_min/h_max) e alberi (intervallo min/max)."""
    ix = {(s["receiver_id"], s["fascia"], s["caso"]): s for s in sint}; out = []
    for (rid, f) in sorted({(s["receiver_id"], s["fascia"]) for s in sint}):
        g = lambda c, k: (ix.get((rid, f, c)) or {}).get(k)
        def blocco(centrale, estremi):
            r = {}
            for k, nome in (("shade_fraction_mean", "frazione"), ("walk_sun_min_mean", "min_sole"), ("shaded_m_mean", "m_ombra"), ("walk_shade_m_mean", "m_ombra_camminando")):
                v = g(centrale, k)
                if v is None: continue
                e = [g(c, k) for c in estremi if g(c, k) is not None]
                r[nome] = {"valore": v, "min": min(e + [v]), "max": max(e + [v])}
            return r
        out.append({"receiver_id": rid, "fascia": f, "lunghezza_m": g("base", "length_m"), "n_orari": g("base", "n_orari_calcolati"), "n_orari_walk": g("base", "n_orari_walk"),
                    "el_deg": [g("base", "el_min_deg"), g("base", "el_max_deg")], "edifici_documentati": blocco("base", ["base_h_min", "base_h_max"]),
                    "edifici_e_alberi": blocco("alberi_tipico", ["alberi_min", "alberi_max"]) if g("alberi_tipico", "shade_fraction_mean") is not None else {},
                    "chioma_cilindro_tipico": blocco("alberi_tipico_cilindro", []) if g("alberi_tipico_cilindro", "shade_fraction_mean") is not None else {}})
    return out


def main(rapido=False):
    OUT.mkdir(exist_ok=True); MAN.mkdir(exist_ok=True); (ROOT / "data/norm/shadow").mkdir(parents=True, exist_ok=True)
    rec = ricevitori(); riepilogo = {"versione": O.VERSIONE, "baseline_id": O.BASELINE_ID, "velocita_m_s": 1.2, "passo_temporale_min": METODO["time_step_min"],
                                     "passo_spaziale_m": METODO["space_step_m"], "ricevitore": "centerline della rete (lato del marciapiede non noto)", "date": {}, "job": {}}
    for data in (DATE[:1] if rapido else DATE):
        t = time.time(); r = esegui(data, rec, CASI, METODO)
        (MAN / f"{r['job']['job_id']}.job.json").write_text(json.dumps(r["job"], ensure_ascii=False, indent=1))
        (MAN / f"{r['job']['job_id']}.manifest.json").write_text(json.dumps(r["manifest"], ensure_ascii=False, indent=1))
        (ROOT / "data/norm/shadow" / f"{r['job']['job_id']}_sintesi.json").write_text(json.dumps(r["sintesi"], ensure_ascii=False, indent=0))
        riepilogo["date"][data] = compatta(r["sintesi"]); riepilogo["job"][data] = r["job"]["job_id"]
        print(data, r["job"]["job_id"], f"{time.time() - t:.0f} s", [a["path"] for a in r["assets"] if a["role"] == "result_geometry"], flush=True)
    # sensibilità sul lato del marciapiede: R01 spostata di 3 m a sinistra e a destra, solo baseline e alberi tipico
    sens = {}
    for data in (DATE[:1] if rapido else DATE):
        r = esegui(data, ricevitori(3.0, ["R01"]) + ricevitori(-3.0, ["R01"]) + ricevitori(0, ["R01"]), ["base", "alberi_tipico"], METODO, asset=False)
        sens[data] = compatta(r["sintesi"])
    riepilogo["sensibilita_lato_3m_R01"] = sens
    # convergenza su R01 (15 settembre): passo temporale 15/5/1 min a passo spaziale 1 m, passo spaziale 2/1/0,5 m a passo temporale 5 min; solo baseline
    conv = {"temporale": {}, "spaziale": {}}; r01 = ricevitori(0, ["R01"])
    for dtm in (15.0, 5.0, 1.0):
        t = time.time(); r = esegui("2026-09-15", r01, ["base"], {**METODO, "time_step_min": dtm, "obstacles": "documented_buildings_only"}, asset=False)
        conv["temporale"][str(dtm)] = {s["fascia"]: {k: s.get(k) for k in ("shade_fraction_mean", "walk_sun_min_mean", "walk_sun_min_min", "walk_sun_min_max")} for s in r["sintesi"]}
        print("conv t", dtm, f"{time.time() - t:.0f} s", flush=True)
    for ds in (2.0, 1.0, 0.5):
        r = esegui("2026-09-15", r01, ["base"], {**METODO, "space_step_m": ds, "obstacles": "documented_buildings_only"}, asset=False)
        conv["spaziale"][str(ds)] = {s["fascia"]: {k: s.get(k) for k in ("shade_fraction_mean", "walk_sun_min_mean")} for s in r["sintesi"]}
        conv["spaziale"][str(ds)]["sampled_vs_esatta_pp"] = round(100 * float(np.mean([abs(x["sampled_fraction"] - x["shade_fraction"]) for x in r["righe"] if x.get("sampled_fraction") is not None])), 3)
    riepilogo["convergenza_R01_2026_09_15"] = conv
    (OUT / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1))
    print("riepilogo scritto")


if __name__ == "__main__":
    main("--rapido" in sys.argv)
