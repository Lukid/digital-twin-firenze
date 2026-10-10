"""F03: normalizzazione di aoi_firenze_novoli in data/norm/firenze_novoli/ (EPSG:7791 E,N, 0,01 m, classi per attributo in 'cls') e report di copertura.
Riusa le funzioni di Pisa (normalize.norm_osm, norm_uv, norm_gtfs, finish). Uso: norm_firenze.py [lavoro ...] | report   (senza argomenti: tutti i lavori, poi il report)"""
import os, re, sys, json, math, pathlib
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare lib
import numpy as np, geopandas as gpd, pyogrio, rasterio, shapely
from rasterio.merge import merge
import lib
from lib import AOI, ROOT, NORM, SNAP
from normalize import finish, raw, sha, norm_osm, norm_uv, norm_gtfs, M, D
BUF, FP = AOI["buf_en"], shapely.box(*AOI["z2_en"])

def leggi(slug, pat, crs, enc=None):
    """Vettoriale (zip o file) nel CRS dichiarato dalla fonte, convertito in EPSG:7791 (come a Pisa: nessuno shift di datum)."""
    f = raw(slug, pat)[0]; p = f"/vsizip/{f}" if f.suffix == ".zip" else str(f)
    g = pyogrio.read_dataframe(p, **({"encoding": enc} if enc else {}))
    g = g.rename(columns={"id": "fid_src", "ID": "id_orig"})      # 'id' e 'ID' collidono in GeoPackage e 'id' è nostro
    for c in [c for c in g.columns if str(g[c].dtype) in ("object", "str", "string")]: g[c] = g[c].astype(str).str.strip().replace({"None": None, "nan": None})
    return g.set_crs(crs, allow_override=True).to_crs(7791)

def scrivi(g, slug, source_id, layer, idcol, prefix, rango=None, out=None, cls_extra=None, low=False):
    """ID = prefisso + chiave originaria (con rango spaziale se la fonte non ha una chiave unica); attributi misurati, derivati dichiarati in cls_extra."""
    if rango:   # chiave di contenuto: codice + ordine spaziale nel codice (la fonte non ha ID univoco)
        o = g.assign(x=g.geometry.centroid.x, y=g.geometry.centroid.y).sort_values(["x", "y"]); g["_n"] = o.groupby(rango).cumcount().reindex(g.index)
        g["id"] = prefix + g[idcol].astype(str) + "_" + g["_n"].astype(str); g = g.drop(columns="_n")
    else: g["id"] = prefix + g[idcol].astype(str)
    g["id"] = g["id"].map(lambda s: re.sub(r"[^A-Za-z0-9_.-]", "_", s.lower() if low else s))   # ID ammessi dallo schema
    attrs = [c for c in g.columns if c not in ("id", "geometry")]
    finish(g[["id"] + attrs + ["geometry"]], source_id, sha(slug), {**{c: M for c in attrs}, **(cls_extra or {})}, out or f"{slug}.gpkg", layer)

def lidar(slug, out):
    """Mosaico delle tessere ASCII ritagliato su riquadro + margine, sul reticolo da 0,5 m delle tessere, GeoTIFF float32 EPSG:7791."""
    srcs = [rasterio.open(f) for f in raw(slug, "*.ASC")]
    b = (math.floor(BUF[0] * 2) / 2, math.floor(BUF[1] * 2) / 2, math.ceil(BUF[2] * 2) / 2, math.ceil(BUF[3] * 2) / 2)
    a, tr = merge(srcs, bounds=b, res=0.5, nodata=-9999.0); a = a[0].astype("float32")
    ok = a != -9999.0
    with rasterio.open(NORM / out, "w", driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype="float32", crs="EPSG:7791", transform=tr,
                       nodata=-9999.0, compress="deflate", predictor=3, tiled=True) as o: o.write(a, 1)
    st = {"file": out, "tessere": len(srcs), "shape": list(a.shape), "res_m": 0.5, "nodata_pct": round(float((~ok).mean() * 100), 3),
          "min": round(float(a[ok].min()), 2), "max": round(float(a[ok].max()), 2), "mean": round(float(a[ok].mean()), 2), "bounds": list(b)}
    print("  ", st); json.dump(st, open(NORM / (out[:-4] + ".stats.json"), "w"))

def cm():
    (NORM / "cm_edscol_firenze.gpkg").unlink(missing_ok=True)
    ed = leggi("cm_edscol_firenze", "form_ed_scolastici.zip", 3003); ac = leggi("cm_edscol_firenze", "form_ed_scolastici_accessi.zip", 3003)
    scrivi(ed, "cm_edscol_firenze", "src_cm_edscol_firenze", "edifici_scolastici", "COD_MECCAN", "bld_cm_", rango="COD_MECCAN", out="cm_edscol_firenze.gpkg")
    # secondo layer nello stesso GeoPackage: finish riscrive il file, quindi si accoda con pyogrio
    p = NORM / "cm_edscol_firenze.gpkg"; ac["id"] = "acc_cm_" + ac["CODICE"].astype(str)
    o = ac.assign(x=ac.geometry.x, y=ac.geometry.y).sort_values(["x", "y"]); ac["id"] += "_" + o.groupby("CODICE").cumcount().reindex(ac.index).astype(str)
    attrs = [c for c in ac.columns if c not in ("id", "geometry")]; ac = ac[["id"] + attrs + ["geometry"]].copy()
    ac["source_id"], ac["snapshot_id"] = "src_cm_edscol_firenze", sha("cm_edscol_firenze"); ac["cls"] = json.dumps({**{c: M for c in attrs}, "geometry": M}, sort_keys=True)
    ac["geometry"] = shapely.set_precision(ac.geometry.values, 0.01); ac = ac[ac.geometry.intersects(shapely.box(*BUF))]
    assert ac["id"].is_unique; ac.set_crs(7791, allow_override=True).to_file(p, layer="accessi", driver="GPKG", engine="pyogrio", mode="a"); print(f"  {p.name}:accessi {len(ac)} oggetti")


JOBS = {
    "osm": lambda: norm_osm("osm_firenze", "src_osm_firenze"),
    "uv": lambda: norm_uv("rt_uv_firenze_novoli", "src_rt_uv_firenze_novoli"),
    "gtfs_tram": lambda: norm_gtfs("gtfs_gest_firenze", "src_gtfs_gest_firenze", "gest.gtfs.zip", "tram"),
    "gtfs_bus": lambda: norm_gtfs("gtfs_at_firenze", "src_gtfs_at_firenze", "gtfs.zip", "stop"),
    "alberi": lambda: scrivi(leggi("fi_alberi", "alberi_pubblici.json", 6706), "fi_alberi", "src_fi_alberi", "alberi", "id_orig", "tre_fi_"),
    "civici": lambda: scrivi(leggi("fi_civici", "civici.zip", 3003, "ISO-8859-1"), "fi_civici", "src_fi_civici", "civici", "id_orig", "adr_fi_"),
    "barriere": lambda: scrivi(leggi("fi_barriere", "mappa_accessibilita.zip", 3003, "cp850"), "fi_barriere", "src_fi_barriere", "barriere", "pk_id", "bar_fi_"),   # dbf in cp850 (audit rete)
    "aree_pedonali": lambda: scrivi(leggi("fi_aree_pedonali", "acPed_s.zip", 32632).pipe(lambda g: g.set_geometry(shapely.force_2d(g.geometry.values), crs=7791)), "fi_aree_pedonali", "src_fi_aree_pedonali", "aree_pedonali", "acPedId", "ped_fi_"),   # PolygonZ ridotti a 2D
    "rifugi_aree": lambda: scrivi(leggi("fi_rifugi_aree", "rifugi_aree_fresche.json", 6706), "fi_rifugi_aree", "src_fi_rifugi_aree", "rifugi_aree", "cod_area", "rif_fi_"),
    "rifugi_bibl": lambda: scrivi(leggi("fi_rifugi_biblioteche", "rifugi_biblioteche.json", 3003), "fi_rifugi_biblioteche", "src_fi_rifugi_biblioteche", "rifugi_biblioteche", "fid_src", "rib_fi_"),
    "tram_fermate": lambda: scrivi(leggi("fi_tram_fermate", "tram_fermate.zip", 3003), "fi_tram_fermate", "src_fi_tram_fermate", "tram_fermate", "nome_ferma", "stp_fi_", rango="nome_ferma"),
    "scuole": lambda: scrivi(leggi("fi_scuole_statali", "miur_scuole_statali_2026_27.json", 6706), "fi_scuole_statali", "src_fi_scuole_statali", "scuole", "codicescuo", "dst_school_", low=True),
    "cm": cm,
    "dtm": lambda: lidar("fi_dtm2023", "fi_dtm2023_0.5m.tif"), "dsm": lambda: lidar("fi_dsm2023", "fi_dsm2023_0.5m.tif"),
}

def report():
    """Conteggi per layer: area allargata (riquadro + margine) e riquadro (FP); snapshot e raster. Scrive pipeline/report_firenze.json."""
    out = {"aoi": AOI, "giorno": lib.DAY, "layer": {}, "raster": {}, "snapshot": {}}
    for p in sorted(NORM.glob("*.gpkg")):
        for name, _ in pyogrio.list_layers(p):
            g = gpd.read_file(p, layer=name)
            out["layer"][f"{p.name}:{name}"] = {"in_area_allargata": len(g), "in_riquadro": int(g.intersects(FP).sum())}
    for p in sorted(NORM.glob("*.stats.json")): out["raster"][p.name[:-11]] = json.load(open(p))
    for p in sorted(SNAP.glob(f"snp_*_{lib.DAY}.json")):
        s = json.load(open(p))
        if s["source_id"] in {f"src_{d}" for d in FIRENZE}: out["snapshot"][s["snapshot_id"]] = {k: s.get(k) for k in ("status", "bytes", "sha256", "license_state", "expires_at")}
    json.dump(out, open(ROOT / "pipeline/report_firenze.json", "w"), indent=1, ensure_ascii=False)
    for k, v in out["layer"].items(): print(f"{k:58} allargata {v['in_area_allargata']:7}  riquadro {v['in_riquadro']:7}")

if __name__ == "__main__":
    from fonti_firenze import S
    FIRENZE = [d["slug"] for d in S().values()]
    a = sys.argv[1:]
    if a != ["report"]:
        for k in a or JOBS: print(k); JOBS[k]()
    if not a or a == ["report"]: report()
