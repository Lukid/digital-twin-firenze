"""F07: analisi d'ombra sui percorsi pedonali T2 -> Polo delle Scienze Sociali (Novoli), 15 luglio e 15 settembre 2026, ogni 30 min fra 8:00 e 19:00.
Casi: edifici (h_min/h/h_max), edifici e alberi (min/tipico/max), più vegetazione LiDAR senza albero censito (min/tipico/max).
Output piccoli (versionati): shadow/firenze_novoli/{manifest/, sintesi.json, tratti_ombra_<data>.geojson}. Output grandi: data/norm/<area>/shadow/.
Uso: pipeline/.venv/bin/python shadow/run.py [--rapido]   (richiede shadow/veg_lidar.py già eseguito)"""
import json, pathlib, sys, time
import shapely
from pyproj import Transformer
from shapely.geometry import shape, mapping
import shapely.ops
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ombre as O

ROOT, AQUI = O.ROOT, pathlib.Path(__file__).resolve().parent
OUT = AQUI / O.SLUG
MAN = OUT / "manifest"
DATE = ["2026-07-15", "2026-09-15"]
FASCE = [{"id": "punta_12_30_13_30", "from": "12:30", "to": "13:30"}, {"id": "giornata_8_19", "from": "08:00", "to": "19:00"}]
ORARI = [f"{m // 60:02d}:{m % 60:02d}" for m in range(8 * 60, 19 * 60 + 1, 30)]
PERCORSI = ["R01", "R02"]    # da network/<area>/percorsi_campione.geojson: fermate T2 San Donato - Università e Regione Toscana -> ingresso del Polo più vicino per rete (D19, D20)
METODO = {"name": "geometric_ray", "space_step_m": 1.0, "time_step_min": 5.0, "obstacles": "buildings_and_trees"}
CASI = ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max", "veg_lidar_min", "veg_lidar_tipico", "veg_lidar_max"]
CASI_TRATTI = ["base", "alberi_tipico", "veg_lidar_tipico"]
_to = Transformer.from_crs(4326, 7791, always_xy=True)


def ricevitori():
    """Percorsi di network/<area>/percorsi_campione.geojson in 7791, sull'asse della rete (centerline): il lato del marciapiede non è noto."""
    out = []; src = ROOT / "network" / O.SLUG / "percorsi_campione.geojson"
    for f in json.load(open(src))["features"]:
        i = f["properties"]["id"]
        if i not in PERCORSI or f["properties"].get("stato", "reachable") != "reachable": continue
        g = shapely.ops.transform(lambda x, y, z=None: _to.transform(x, y), shape(f["geometry"]))
        out.append({"receiver_id": f"pth_fi_{i}", "kind": "path", "geometry": mapping(shapely.set_precision(g, 0.01)),
                    "_descrizione": f["properties"]["descrizione"], "_lunghezza_m": f["properties"]["lunghezza_totale_m"]})
    assert len(out) == len(PERCORSI), "percorsi mancanti in percorsi_campione.geojson"
    return out


def esegui(data, rec, casi=CASI, metodo=METODO, tratti=True):
    w = {"date": data, "timezone": "Europe/Rome", "times": ORARI}
    rec = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rec]
    return O.compute_shadow(O.BASELINE_ID, rec, w, metodo, casi=casi, fasce=FASCE, out_dir=O.OUT_GRANDI, tratti_casi=CASI_TRATTI if tratti else ())


def compatta(sint):
    """Riga per (ricevitore, fascia): frazione e minuti al sole per edifici (intervallo h_min/h_max), edifici e alberi (min/max), con vegetazione LiDAR (min/max)."""
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
                    "el_deg": [g("base", "el_min_deg"), g("base", "el_max_deg")], "edifici": blocco("base", ["base_h_min", "base_h_max"]),
                    "edifici_e_alberi": blocco("alberi_tipico", ["alberi_min", "alberi_max"]), "edifici_alberi_e_vegetazione_lidar": blocco("veg_lidar_tipico", ["veg_lidar_min", "veg_lidar_max"])})
    return out


def per_ora(righe):
    """{ricevitore: {caso: {HH:MM: frazione d'ombra o stato del sole}}}."""
    o = {}
    for r in righe: o.setdefault(r["receiver_id"], {}).setdefault(r["caso"], {})[r["time_local"]] = r.get("shade_fraction", r["stato"])
    return o


def main(rapido=False):
    MAN.mkdir(parents=True, exist_ok=True); O.OUT_GRANDI.mkdir(parents=True, exist_ok=True)
    rec = ricevitori()
    riepilogo = {"versione_motore": O.VERSIONE, "baseline_id": O.BASELINE_ID, "aoi_id": O.AOI_ID, "velocita_m_s": 1.2, "passo_temporale_min": METODO["time_step_min"],
                 "passo_spaziale_m": METODO["space_step_m"], "orari": ORARI, "ricevitore": "centerline della rete (lato del marciapiede non noto)",
                 "percorsi": {r["receiver_id"]: {"descrizione": r["_descrizione"], "lunghezza_m": r["_lunghezza_m"]} for r in rec},
                 "vegetazione_lidar": {"frazione_z_lo_di_h95": O.VEG_FRAZIONE, "z_hi": "h95", "cluster_usati": None, "cluster_liscia_esclusi": None}, "date": {}, "frazione_per_ora": {}, "job": {}}
    for data in (DATE[:1] if rapido else DATE):
        t = time.time(); r = esegui(data, rec)
        jid = r["job"]["job_id"]
        (MAN / f"{jid}.job.json").write_text(json.dumps(r["job"], ensure_ascii=False, indent=1))
        (MAN / f"{jid}.manifest.json").write_text(json.dumps(r["manifest"], ensure_ascii=False, indent=1))
        (O.OUT_GRANDI / f"{jid}_sintesi.json").write_text(json.dumps(r["sintesi"], ensure_ascii=False, indent=0))
        (OUT / f"tratti_ombra_{data}.geojson").write_text(json.dumps(r["tratti"], ensure_ascii=False, separators=(",", ":")))
        riepilogo["date"][data] = compatta(r["sintesi"]); riepilogo["frazione_per_ora"][data] = per_ora(r["righe"]); riepilogo["job"][data] = jid
        print(data, jid, f"{time.time() - t:.0f} s", flush=True)
    D = O.dati(); riepilogo["vegetazione_lidar"].update(cluster_usati=len(D["veg"]), cluster_liscia_esclusi=D["n_veg_lisce"], area_usata_m2=round(float(D["veg"].area_m2.sum()), 1))
    riepilogo["volumi_usati"] = len(D["v"]); riepilogo["volumi_demoliti_esclusi"] = D["n_volumi_demoliti"]; riepilogo["alberi_usati"] = len(D["a"])
    (OUT / "sintesi.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1))
    print("sintesi scritta:", OUT / "sintesi.json")


if __name__ == "__main__":
    main("--rapido" in sys.argv)
