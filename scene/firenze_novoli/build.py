"""F09: asset precotti della scena 3D di Firenze Novoli (sito statico, nessun server a runtime).

Uso: pipeline/.venv/bin/python scene/firenze_novoli/build.py [--out DIR] [--analysis DIR] [--shadow DIR]

Piano del motore (metri): x = est, y = alto, z = -nord; origine = centro del riquadro FP in EPSG:7791
(lon/lat degli open data trattati come RDN2008, come nel resto della pipeline).
Ogni asset è JSON compresso gzip (.json.gz); i vettori numerici grandi sono Float32 in base64.
L'indice assets/index.json riporta sha256 e dimensione di ogni asset, le fonti e i limiti.
"""
import argparse, base64, glob, gzip, hashlib, json, math, pathlib, sys, datetime as dt
import numpy as np, geopandas as gpd, rasterio, rasterio.windows, shapely
from rasterio.enums import Resampling
from shapely.geometry import box, Polygon
from shapely.geometry.polygon import orient
from pyproj import Transformer

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from lib import AOI, NORM  # area predefinita Firenze (D15)

STEP = 10.0          # passo del terreno, m
MARGINE = 60.0       # terreno oltre il riquadro, m
ARR = 2              # decimali delle coordinate (cm)
BASSO = 1.5          # i volumi scendono 1,5 m sotto la quota di base (pendenze del terreno a 10 m)

E0, N0, E1, N1 = AOI["z2_en"]
CE, CN = (E0 + E1) / 2, (N0 + N1) / 2
to_en = Transformer.from_crs(6706, 7791, always_xy=True)
to_ll = Transformer.from_crs(7791, 6706, always_xy=True)
LON0, LAT0 = to_ll.transform(CE, CN)
FP = box(E0, N0, E1, N1)

# livelli della scena: etichetta e fonti (id di pipeline/sources) mostrate nella scheda
LIVELLI = {
    "terreno": {"etichetta": "Terreno", "fonti": ["src_fi_dtm2023"]},
    "edifici": {"etichetta": "Edifici", "fonti": ["src_rt_uv_firenze_novoli", "src_fi_dsm2023", "src_fi_dtm2023", "src_osm_firenze"]},
    "alberi": {"etichetta": "Alberi", "fonti": ["src_fi_alberi", "src_fi_dsm2023", "src_fi_dtm2023"]},
    "rete": {"etichetta": "Rete pedonale", "fonti": ["src_osm_firenze"]},
    "destinazioni": {"etichetta": "Destinazioni e ingressi", "fonti": ["src_osm_firenze", "src_cm_edscol_firenze", "src_fi_scuole_statali", "src_gtfs_gest_firenze"]},
    "tram": {"etichetta": "Fermate tram", "fonti": ["src_fi_tram_fermate"]},
    "scuole": {"etichetta": "Scuole statali", "fonti": ["src_fi_scuole_statali"]},
    "rifugi": {"etichetta": "Rifugi climatici", "fonti": ["src_fi_rifugi_aree"]},
    "barriere": {"etichetta": "Barriere architettoniche", "fonti": ["src_fi_barriere"]},
    "accessibilita": {"etichetta": "Accessibilità (minuti a piedi)", "fonti": ["src_fi_civici", "src_osm_firenze"]},
    "ombra": {"etichetta": "Ombra sui percorsi", "fonti": ["src_osm_firenze", "src_fi_dsm2023"]},
}

LIMITI = [
    "Altezze degli edifici: quota LiDAR 2023 (DSM meno DTM) confrontata con le unità volumetriche regionali del 2011. Sono volumi, non modelli architettonici: nessun tetto a falde, nessun portico.",
    "Portici e volumi sospesi: nessuna fonte, restano \"ignoto\" e non sono disegnati. I volumi scendono di 1,5 m sotto la quota di base per seguire la pendenza del terreno a 10 m.",
    "Edifici non più presenti nel 2023 (probabili demolizioni) sono disegnati in grigio scuro e segnalati nella scheda.",
    "Alberi: il censimento comunale non riporta altezza né chioma. Altezza e chioma sono misurate dal LiDAR dove ci sono celle sufficienti, altrimenti stimate (classe indicata nella scheda). Il tronco è disegnato con almeno 25 cm di diametro per renderlo visibile.",
    "Terreno: DTM LiDAR 2023 ricampionato a passo 10 m, senza ortofoto né texture.",
    "Ombre: sono quelle del motore grafico (sole calcolato per posizione e data), a scopo illustrativo. Non sono un calcolo analitico: gli alberi proiettano chiome piene.",
    "Destinazioni e ingressi: tutti da verificare sul campo. Condizioni di accesso, orari e cancelli non sono noti.",
    "Rete pedonale da OpenStreetMap: stato del marciapiede \"ignoto\" dove non dichiarato, nessuna inferenza.",
    "Barriere architettoniche: rilievo del 2013, grado di accessibilità dell'edificio, non dell'ostacolo sul percorso.",
    "Livelli Accessibilità e Ombra sui percorsi: mostrano solo i dati prodotti dai moduli di analisi, se presenti. Non sono calcolati dalla scena.",
]

USO = {
    "src_fi_dtm2023": "Terreno e quota di base degli alberi",
    "src_fi_dsm2023": "Altezza degli edifici e delle chiome",
    "src_rt_uv_firenze_novoli": "Impronte e volumi degli edifici",
    "src_osm_firenze": "Rete pedonale, impronte nuove, ingressi",
    "src_fi_alberi": "Alberi pubblici",
    "src_fi_tram_fermate": "Fermate tram",
    "src_fi_scuole_statali": "Scuole statali",
    "src_cm_edscol_firenze": "Accessi delle scuole",
    "src_gtfs_gest_firenze": "Punti delle fermate T2",
    "src_fi_rifugi_aree": "Rifugi climatici (aree)",
    "src_fi_barriere": "Barriere architettoniche",
    "src_fi_civici": "Civici dei livelli analitici",
}


def loc(e, n):
    """EPSG:7791 -> piano del motore (x, z)."""
    return round(e - CE, ARR), round(-(n - CN), ARR)


def loc_ll(lon, lat):
    return loc(*to_en.transform(lon, lat))


def f32b64(a):
    return base64.b64encode(np.asarray(a, dtype="<f4").tobytes()).decode()


def r(v, n=ARR):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), n)


def s(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)


# --- terreno -----------------------------------------------------------------
def terreno():
    x0, y0, x1, y1 = E0 - MARGINE, N0 - MARGINE, E1 + MARGINE, N1 + MARGINE
    nx, ny = math.ceil((x1 - x0) / STEP), math.ceil((y1 - y0) / STEP)
    x1, y1 = x0 + nx * STEP, y0 + ny * STEP
    with rasterio.open(NORM / "fi_dtm2023_0.5m.tif") as ds:
        win = rasterio.windows.from_bounds(x0, y0, x1, y1, ds.transform)
        z = ds.read(1, window=win, out_shape=(ny, nx), resampling=Resampling.average, boundless=True, fill_value=np.nan)
    z = np.where(np.isfinite(z) & (z > -100), z, np.nan)
    if np.isnan(z).any():
        z = np.where(np.isnan(z), np.nanmean(z), z)
    zref = round(float(z[ny // 2, nx // 2]), 1)
    # x = est, z = -nord: la riga 0 del raster è il nord, quindi z cresce con la riga
    return zref, {
        "nx": nx, "ny": ny, "passo": STEP, "x0": round(x0 + STEP / 2 - CE, 2), "z0": round(-(y1 - STEP / 2 - CN), 2),
        "quote_cm": np.round((z - zref) * 100).astype(int).ravel().tolist(),
        "min_m": round(float(z.min()), 1), "max_m": round(float(z.max()), 1),
    }


# --- edifici ------------------------------------------------------------------
def tris(poly):
    g = shapely.constrained_delaunay_triangles(poly)
    return [t for t in g.geoms] if hasattr(g, "geoms") else [g]


def edifici(zref):
    g = json.load(open(ROOT / "geometry/firenze_novoli/edifici_fp.geojson"))
    pos, meta = [], []
    for f in g["features"]:
        p = f["properties"]
        geom = shapely.transform(shapely.from_geojson(json.dumps(f["geometry"])), lambda c: np.array([to_en.transform(*q) for q in c]))
        zb, zt = p["z_base"] - zref - BASSO, p["z_base"] - zref + p["h"]
        v = []
        for poly in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
            poly = orient(poly.buffer(0), 1.0) if not poly.is_valid else orient(poly, 1.0)  # esterno antiorario
            if poly.is_empty or poly.area < 0.5:
                continue
            for t in tris(poly):  # tetto
                c = list(orient(t, 1.0).exterior.coords)[:3]
                for e, n in c:
                    x, z = loc(e, n); v += [x, zt, z]
            for ring in [poly.exterior, *poly.interiors]:
                c = list(ring.coords)
                for (e1_, n1_), (e2_, n2_) in zip(c[:-1], c[1:]):  # esterno antiorario, buchi orari: la normale esce sempre dal solido
                    a, b = loc(e1_, n1_), loc(e2_, n2_)
                    A, B = [a[0], zb, a[1]], [b[0], zb, b[1]]
                    At, Bt = [a[0], zt, a[1]], [b[0], zt, b[1]]
                    v += A + B + Bt + A + Bt + At
        if not v:
            continue
        pos += v
        meta.append({"id": p["id"], "n": len(v) // 3, "h": r(p["h"]), "h_min": r(p["h_min"]), "h_max": r(p["h_max"]),
                     "z_base": r(p["z_base"]), "classe_h": p["classe_h"], "tipo": p["tipo"], "fonte": p["fonte"],
                     "area_m2": r(p["area_m2"], 1), "presente_2023": bool(p["presente_2023"]), "flag": p.get("flag") or "",
                     "h_uv": r(p.get("h_uv")), "h_lidar": r(p.get("h_lidar"))})
    return {"n": len(meta), "edifici": meta, "posizioni": f32b64(pos)}


# --- alberi --------------------------------------------------------------------
def alberi(zref):
    g = json.load(open(ROOT / "geometry/firenze_novoli/alberi_fp.geojson"))
    out = []
    for f in g["features"]:
        p = f["properties"]
        x, z = loc_ll(*f["geometry"]["coordinates"])
        out.append({"id": p["id"], "x": x, "z": z, "y": r(p["z_base"] - zref), "h": r(p["h"], 1), "h_min": r(p["h_min"], 1), "h_max": r(p["h_max"], 1),
                    "d": r(p["chioma_d"], 1), "d_min": r(p["chioma_d_min"], 1), "d_max": r(p["chioma_d_max"], 1),
                    "imp": r(p.get("imposta"), 1), "td": r(p.get("tronco_d"), 2), "specie": s(p.get("SPECIE")), "circ": r(p.get("CIRCONF_CM"), 1),
                    "h_cls": p["h_cls"], "ch_cls": p["chioma_cls"], "motivo": p.get("motivo_stima") or ""})
    return {"n": len(out), "alberi": out}


# --- rete e punti --------------------------------------------------------------
def rete():
    d = gpd.read_file(NORM / "network/rete_firenze_novoli.gpkg", layer="archi")
    d = d[d.intersects(FP)]
    out = []
    for _, row in d.iterrows():
        gs = row.geometry.geoms if row.geometry.geom_type == "MultiLineString" else [row.geometry]
        for ln in gs:
            pts = [loc(e, n) for e, n in ln.coords]
            out.append({"id": row.edge_id, "nome": s(row["name"]), "hw": s(row.highway), "tipo": s(row.tipo_arco), "marc": s(row.marciapiede_stato),
                        "m": r(row.length_m, 1), "p": [c for q in pts for c in q]})
    return {"n": len(out), "archi": out}


def in_fp(gdf):
    return gdf[gdf.intersects(FP)]


def punti():
    out = []
    # destinazioni e ingressi
    dest = {d["destination_id"]: d for d in json.load(open(ROOT / "network/firenze_novoli/destinazioni.json"))["destinazioni"]}
    g = json.load(open(ROOT / "network/firenze_novoli/destinazioni_ingressi.geojson"))
    for f in g["features"]:
        p = f["properties"]
        if f["geometry"]["type"] != "Point":
            continue
        d = dest.get(p["destinazione"], {})
        x, z = loc_ll(*f["geometry"]["coordinates"])
        out.append({"livello": "destinazioni", "id": p["id"], "nome": p["nome"], "x": x, "z": z,
                    "attr": {"Destinazione": d.get("nome"), "Indirizzo": d.get("indirizzo"), "Categoria": d.get("categoria"), "Classe dell'ingresso": p["classe"],
                             "Aggancio alla rete": p["stato"], "Raccordo (m)": p["raccordo_m"], "Verifica": p["verifica"],
                             "Condizioni di accesso": d.get("condizioni_accesso"), "Fonte dei dati": d.get("fonte")}})
    n = NORM
    for _, row in in_fp(gpd.read_file(n / "fi_tram_fermate.gpkg")).iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "tram", "id": row.id, "nome": "Fermata tram " + row.nome_ferma.title(), "x": x, "z": z,
                    "attr": {"Linea": row.linea, "Pensilina": "sì" if row.pensilina == 1 else "no"}})
    for _, row in in_fp(gpd.read_file(n / "fi_scuole_statali.gpkg")).iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "scuole", "id": row.id, "nome": row.nome.title(), "x": x, "z": z,
                    "attr": {"Codice": row.codicescuo, "Tipologia": row.tipologia.title(), "Indirizzo": row.indirizzo.title(), "Anno scolastico": "2026/27"}})
    for _, row in in_fp(gpd.read_file(n / "fi_barriere.gpkg")).iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "barriere", "id": row.id, "nome": "Scheda " + str(row.scheda), "x": x, "z": z,
                    "attr": {"Uso": row.destinaz_u, "Indirizzo": row.indirizzo, "Grado di accessibilità": row.grado_acce,
                             "Scheda PDF": f"http://datigis.comune.fi.it/barriere_architettoniche/scheda_{row.scheda}.pdf", "Rilievo": "2013"}})
    for _, row in in_fp(gpd.read_file(n / "fi_rifugi_aree.gpkg")).iterrows():
        c = row.geometry.centroid
        x, z = loc(c.x, c.y)
        poly = max(row.geometry.geoms, key=lambda q: q.area) if row.geometry.geom_type == "MultiPolygon" else row.geometry
        out.append({"livello": "rifugi", "id": row.id, "nome": row.nome_area, "x": x, "z": z,
                    "contorno": [c_ for q in poly.exterior.coords for c_ in loc(*q)],
                    "attr": {"Ombreggiatura": f"oltre il {row.percentuale_ombreggi}%", "Ingressi": row.ingresso, "Descrizione": row.descrizione, "Dato del": "2026-06-18"}})
    return out


# --- livelli analitici (opzionali) ---------------------------------------------
def _feats(path):
    g = json.load(open(path))
    return g["features"] if g.get("type") == "FeatureCollection" else [g]


STATI = {"ok": "ok", "reachable": "ok", "non_raggiungibile": "non_raggiungibile", "isolated": "non_raggiungibile",
         "dati_insufficienti": "dati_insufficienti", "insufficient_data": "dati_insufficienti", "vietato": "vietato", "forbidden": "vietato"}


def accessibilita(dirpath):
    """Input: <dir>/accessibilita*.geojson, Point EPSG:4326, un file per destinazione.
    Proprietà: id, civico, minuti (null se non raggiungibile), stato (ok | non_raggiungibile | dati_insufficienti | vietato),
    destinazione (id), destinazione_nome, profilo. Alias accettati, per l'output del motore di analisi: t = minuti,
    ind = civico, stato reachable/isolated/insufficient_data/forbidden, layer = origine (gli altri layer sono ignorati)."""
    dnomi = {d["destination_id"]: d["nome"] for d in json.load(open(ROOT / "network/firenze_novoli/destinazioni.json"))["destinazioni"]}
    dst = {}
    for fn in sorted(glob.glob(str(pathlib.Path(dirpath) / "accessibilita*.geojson"))):
        stem = pathlib.Path(fn).stem
        for f in _feats(fn):
            p = f.get("properties", {})
            if f.get("geometry", {}).get("type") != "Point" or p.get("layer", "origine") != "origine":
                continue
            did = p.get("destinazione") or stem.removeprefix("accessibilita").lstrip("_") or "destinazione"
            e = dst.setdefault(did, {"id": did, "nome": p.get("destinazione_nome") or dnomi.get(did, did), "profilo": p.get("profilo"), "punti": []})
            m = p.get("minuti", p.get("t"))
            x, z = loc_ll(*f["geometry"]["coordinates"][:2])
            st = STATI.get(p.get("stato"), "ok" if m is not None else "non_raggiungibile")
            e["punti"].append({"id": p.get("id"), "civico": p.get("civico") or p.get("ind"), "x": x, "z": z,
                               "min": r(m, 1) if m is not None and st == "ok" else None, "stato": st})
    if not dst:
        return None
    return {"n": sum(len(d["punti"]) for d in dst.values()), "destinazioni": list(dst.values())}


def ombra(dirpath):
    """Input: <dir>/ombra_percorsi*.geojson, LineString o MultiLineString EPSG:4326. Proprietà: id, frazione_ombra (0 sole, 1 ombra),
    istante (testo, es. 2026-07-21T15:00), lunghezza_m. Un istante per file (o più istanti nello stesso file)."""
    files = sorted(glob.glob(str(pathlib.Path(dirpath) / "ombra_percorsi*.geojson")))
    ist = {}
    for fn in files:
        for f in _feats(fn):
            gt = f.get("geometry", {}).get("type")
            if gt not in ("LineString", "MultiLineString"):
                continue
            p = f["properties"]
            lines = [f["geometry"]["coordinates"]] if gt == "LineString" else f["geometry"]["coordinates"]
            for ln in lines:
                pts = [c for q in ln for c in loc_ll(*q[:2])]
                key = p.get("istante") or pathlib.Path(fn).stem
                ist.setdefault(key, []).append({"id": p.get("id"), "f": r(p["frazione_ombra"], 3), "m": r(p.get("lunghezza_m"), 1), "p": pts})
    if not ist:
        return None
    return {"n": sum(len(v) for v in ist.values()), "istanti": [{"istante": k, "tratti": v} for k, v in sorted(ist.items())]}


# --- fonti ---------------------------------------------------------------------
def fonti():
    base = json.load(open(ROOT / "pipeline/baselines/bas_firenze_novoli_20261009.json"))
    snaps = {x["source_id"]: x for x in base["snapshot"]}
    out = []
    for sid, uso in USO.items():
        src = json.load(open(ROOT / f"pipeline/sources/{sid}.json"))
        sn = json.load(open(ROOT / f"pipeline/snapshots/{snaps[sid]['snapshot_id']}.json"))
        lic = src["license"]
        cp = src.get("content_period", {})
        out.append({"id": sid, "titolo": src["title"], "ente": src["publisher"], "url": src["dataset_url"],
                    "licenza": lic.get("identifier") or "licenza regionale non scritta sul layer", "stato_licenza": lic["state"],
                    "riserva": lic.get("reserve_note"), "scaricato": sn["retrieved_at"][:10],
                    "periodo": cp.get("note") or cp.get("end"), "sha256_snapshot": snaps[sid]["sha256"], "uso": uso})
    return out


# --- scrittura -----------------------------------------------------------------
def scrivi(out, nome, obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    gz = gzip.compress(raw, 9, mtime=0)
    (out / nome).write_bytes(gz)
    return {"file": nome, "byte": len(gz), "byte_decompressi": len(raw), "sha256": hashlib.sha256(gz).hexdigest(), "n": obj.get("n")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "assets"))
    ap.add_argument("--analysis", default=str(ROOT / "analysis/firenze_novoli"))
    ap.add_argument("--shadow", default=str(ROOT / "shadow/firenze_novoli"))
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json.gz"):
        old.unlink()
    zref, ter = terreno()
    assets = {"terreno": scrivi(out, "terreno.json.gz", {"n": ter["nx"] * ter["ny"], **ter}),
              "edifici": scrivi(out, "edifici.json.gz", edifici(zref)),
              "alberi": scrivi(out, "alberi.json.gz", alberi(zref)),
              "rete": scrivi(out, "rete.json.gz", rete())}
    pt = punti()
    assets["punti"] = scrivi(out, "punti.json.gz", {"n": len(pt), "punti": pt})
    analitici = {}
    for k, fn, d in (("accessibilita", accessibilita, a.analysis), ("ombra", ombra, a.shadow)):
        obj = fn(d)
        analitici[k] = {"presente": obj is not None}
        if obj:
            assets[k] = scrivi(out, f"{k}.json.gz", obj)
    idx = {"versione": 1, "generato": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "aoi_id": AOI["aoi_id"],
           "area": {"nome": "Firenze, Novoli - Firenze Nova (riquadro FP, 2 km²)", "crs_origine": "EPSG:7791", "origine_e_n": [round(CE, 2), round(CN, 2)],
                    "lon_lat_centro": [round(LON0, 6), round(LAT0, 6)], "semiassi_m": [round((E1 - E0) / 2, 1), round((N1 - N0) / 2, 1)],
                    "quota_riferimento_m": zref, "piano": "x = est, y = alto, z = -nord, in metri dal centro"},
           "baseline": "bas_firenze_novoli_20261009", "assets": assets, "livelli_analitici": analitici,
           "livelli": LIVELLI, "fonti": fonti(), "limiti": LIMITI}
    (out / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    tot = sum(v["byte"] for v in assets.values())
    print({k: (v["byte"], v["n"]) for k, v in assets.items()}, "totale", tot, "byte")


if __name__ == "__main__":
    main()
