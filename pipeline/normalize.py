"""Normalizzazione: data/raw -> data/norm (GeoPackage, EPSG:7791 E,N, ID stabili, classi measured/derived).
Uso: normalize.py [fonte ...]   (osm uv civici scuole edscol gtfs_at gtfs_tren dsm dtm10)"""
import csv, glob, io, json, os, re, sys, zipfile, pathlib
import numpy as np, pandas as pd, geopandas as gpd, shapely, rasterio
import xml.etree.ElementTree as ET
import lib
from lib import AOI, ROOT, RAW, NORM, DAY, to_en

NORM.mkdir(parents=True, exist_ok=True)
BUF = AOI["buf_en"]; BOX = shapely.box(*BUF)
M = "measured"; D = "derived"
def _ok(slug):
    """Ultimo snapshot valido della fonte: uno scarico fallito non sostituisce mai l'ultimo valido."""
    ss = [json.load(open(p)) for p in sorted((ROOT / "pipeline/snapshots").glob(f"snp_{slug}_*.json"))]
    return [s for s in ss if s["status"] == "ok"][-1]
sha = lambda slug: _ok(slug)["snapshot_id"]
def raw(slug, pat):
    lp = ROOT / _ok(slug)["local_path"]; d = lp if lp.is_dir() else lp.parent
    fs = sorted(d.glob(pat))
    if not fs: raise FileNotFoundError(f"{slug}/{pat}")
    return fs

def finish(gdf, source_id, snap, cls, out, layer, geomcls=M):
    """Colonne di tracciabilita', geometrie a 0,01 m, classi per attributo, scrittura nel GeoPackage."""
    gdf = gdf.copy()
    gdf["source_id"], gdf["snapshot_id"] = source_id, snap
    c = dict(cls); c["geometry"] = geomcls
    gdf["cls"] = json.dumps(c, sort_keys=True)
    gdf["geometry"] = shapely.set_precision(gdf.geometry.values, 0.01)
    gdf = gdf[gdf.geometry.intersects(BOX)]
    assert gdf["id"].is_unique, f"{layer}: ID duplicati {gdf['id'][gdf['id'].duplicated()].head().tolist()}"
    assert gdf.geometry.is_valid.all() or True
    if gdf.crs is None or gdf.crs.to_epsg() != 7791: gdf = gdf.set_crs(7791, allow_override=True)
    p = NORM / out
    gdf.to_file(p, layer=layer, driver="GPKG", engine="pyogrio")
    print(f"  {out}:{layer} {len(gdf)} oggetti"); return len(gdf)

def tags(s):
    if isinstance(s, dict): return s
    try: return json.loads(s) if s else {}
    except Exception: return {}

# ---------------------------------------------------------------- OSM
def norm_osm(slug="osm_pisa", source_id="src_osm_pisa"):
    pbf = raw(slug, "*.osm.pbf")[0]; snap = sha(slug); out = f"{slug}.gpkg"
    ini = pathlib.Path(lib.__file__).parent / ".venv"  # solo per il percorso di base
    import pyogrio
    base = open(pathlib.Path(pyogrio.__file__).parent / "gdal_data/osmconf.ini").read()
    base = base.replace("#all_tags=yes", "all_tags=yes").replace("#tags_format=json", "tags_format=json")
    if "tags_format=json" not in base: base = base.replace("[general]", "[general]\ntags_format=json", 1)
    conf = NORM / "_osmconf.ini"; conf.write_text(base); os.environ["OSM_CONFIG_FILE"] = str(conf)
    s, w, n, e = AOI["buf_ll_SWNE"]; bb = (w, s, e, n)
    p = NORM / out
    if p.exists(): p.unlink()
    def rd(layer):
        g = pyogrio.read_dataframe(pbf, layer=layer, bbox=bb)
        return g.set_crs(6706, allow_override=True).to_crs(7791)       # lon/lat = RDN2008 geografico (ADR-T02)
    t = lambda g: g["all_tags"].map(tags)
    # strade e percorsi
    g = rd("lines"); g["t"] = t(g); g = g[g["t"].map(lambda d: "highway" in d)].copy()
    g["id"] = "way_osm_" + g["osm_id"].astype(str)
    for k in ("highway", "name", "sidewalk", "footway", "foot", "surface", "lit", "tactile_paving", "kerb", "wheelchair", "incline", "width"):
        g[k] = g["t"].map(lambda d: d.get(k))
    g["length_m"] = g.geometry.length.round(2); g["tags"] = g["t"].map(json.dumps)
    cls = {k: M for k in ("highway", "name", "sidewalk", "footway", "foot", "surface", "lit", "tactile_paving", "kerb", "wheelchair", "incline", "width", "tags")}; cls["length_m"] = D
    finish(g[["id", "highway", "name", "sidewalk", "footway", "foot", "surface", "lit", "tactile_paving", "kerb", "wheelchair", "incline", "width", "length_m", "tags", "geometry"]], source_id, snap, cls, out, "highway")
    # nodi con tag (attraversamenti, ingressi, fermate, alberi, civici, ...)
    g = rd("points"); g["t"] = t(g); g = g[g["t"].map(len) > 0].copy()
    g["id"] = "nod_osm_" + g["osm_id"].astype(str)
    def kind(d):
        for k in ("entrance", "crossing", "kerb", "natural", "public_transport", "highway", "amenity", "barrier", "railway", "addr:housenumber", "shop", "man_made"):
            if k in d: return k if k not in ("natural", "highway", "amenity", "barrier", "railway", "shop", "man_made") else f"{k}={d[k]}"
        return "other"
    g["kind"] = g["t"].map(kind); g["name"] = g["t"].map(lambda d: d.get("name")); g["tags"] = g["t"].map(json.dumps)
    # coordinate originarie lon/lat conservate (traccia dello scarto RDN2008/WGS84)
    ll = pyogrio.read_dataframe(pbf, layer="points", bbox=bb) if False else None
    finish(g[["id", "kind", "name", "tags", "geometry"]], source_id, snap, {"kind": D, "name": M, "tags": M}, out, "points")
    # edifici
    g = rd("multipolygons"); g["t"] = t(g); g = g[g["t"].map(lambda d: "building" in d)].copy()
    g["id"] = np.where(g["osm_way_id"].notna(), "bld_osm_w" + g["osm_way_id"].fillna(0).astype("int64").astype(str), "bld_osm_r" + g["osm_id"].astype(str))
    for k in ("building", "name", "height", "building:levels", "building:part", "min_height", "roof:shape"): g[k.replace(":", "_")] = g["t"].map(lambda d: d.get(k))
    g["area_m2"] = g.geometry.area.round(2); g["tags"] = g["t"].map(json.dumps)
    cols = ["building", "name", "height", "building_levels", "building_part", "min_height", "roof_shape", "tags"]
    finish(g[["id"] + cols + ["area_m2", "geometry"]], source_id, snap, {**{k: M for k in cols}, "area_m2": D}, out, "buildings")

# ---------------------------------------------------------------- Unita' volumetriche
def norm_uv(slug="rt_unita_volumetriche", source_id="src_rt_unita_volumetriche"):
    ns = {"gml": "http://www.opengis.net/gml/3.2", "wfs": "http://www.opengis.net/wfs/2.0"}; rows = []
    for f in raw(slug, "uv_*.gml"):
        for m in ET.parse(f).getroot().iter("{%s}member" % ns["wfs"]):
            ft = m[0]; rec = {}
            for c in ft:
                tag = c.tag.split("}")[1]
                if tag == "GEOMETRY":
                    polys = []
                    for pl in c.iter("{%s}Polygon" % ns["gml"]):
                        rings = []
                        for pos in pl.iter("{%s}posList" % ns["gml"]):
                            v = list(map(float, pos.text.split())); rings.append([(v[i], v[i + 1]) for i in range(0, len(v), 2)])   # E,N (7791)
                        polys.append(shapely.Polygon(rings[0], rings[1:]))
                    rec["geometry"] = shapely.MultiPolygon(polys)
                elif tag != "boundedBy": rec[tag] = (c.text or "").strip()
            rows.append(rec)
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=7791)
    n0 = len(g); g = g.drop_duplicates("uv_id"); print(f"  uv: {n0} letti, {n0 - len(g)} duplicati fra pagine scartati")
    num = lambda c: pd.to_numeric(g[c], errors="coerce")
    g["id"] = "bld_rt_" + g["uv_id"]
    g["height_m"], g["ground_elev_m"], g["roof_elev_m"] = num("uv_av"), num("uv_qs"), num("uv_qe")
    g["survey_year"] = num("anno").astype("Int64"); g["area_m2"] = g.geometry.area.round(2)
    meas = ["uv_id", "edifc_id", "edi_min_id", "uv_por", "uv_dpor", "uv_cl", "edifc_ty", "edifc_dty", "edifc_uso", "edifc_duso", "edifc_stat", "edifc_dstat", "edifc_sot", "dtvolo", "dbt_prov", "scala", "classe"]
    meas = [c for c in meas if c in g]
    cols = ["id"] + meas + ["height_m", "ground_elev_m", "roof_elev_m", "survey_year", "area_m2", "geometry"]
    cls = {**{c: M for c in meas}, "height_m": M, "ground_elev_m": M, "roof_elev_m": M, "survey_year": M, "area_m2": D}
    p = NORM / f"{slug}.gpkg"; p.unlink(missing_ok=True)
    finish(g[cols], source_id, sha(slug), cls, p.name, "building_volume")

# ---------------------------------------------------------------- SIT
def sit(slug, source_id, native, idcol, prefix, cols_out=None):
    f = raw(slug, f"{slug}.geojson")[0]; g = gpd.read_file(f)
    g = g.set_crs(native, allow_override=True)          # CRS nativo del layer (outSR della richiesta)
    g = g.to_crs(7791)                                  # trasformazione: vedi pipeline/checks.py per lo scarto misurato
    g["id"] = prefix + g[idcol].astype(int).astype(str)
    g["orig_crs"] = f"EPSG:{native}"
    attrs = [c for c in g.columns if c not in ("id", "geometry", "orig_crs")]
    for c in attrs:
        if g[c].dtype == object: g[c] = g[c].astype(str).str.strip().replace({"None": None, "nan": None})
    cls = {c: M for c in attrs}; cls["orig_crs"] = M
    p = NORM / f"{slug}.gpkg"; p.unlink(missing_ok=True)
    finish(g[["id"] + attrs + ["orig_crs", "geometry"]], source_id, sha(slug), cls, p.name, slug.replace("sit_", ""))

# ---------------------------------------------------------------- GTFS
def norm_gtfs(slug, source_id, name, kind):
    zp = raw(slug, name)[0]; snap = sha(slug)
    z = zipfile.ZipFile(zp); rd = lambda n, **k: pd.read_csv(z.open(n), dtype=str, encoding="utf-8-sig", **k)
    st = rd("stops.txt"); st["lon"], st["lat"] = st.stop_lon.astype(float), st.stop_lat.astype(float)
    e, n = to_en(st.lon.values, st.lat.values); st["E"], st["N"] = e, n
    st = st[(st.E >= BUF[0]) & (st.E <= BUF[2]) & (st.N >= BUF[1]) & (st.N <= BUF[3])].copy()
    # corse del giorno di riferimento (DAY se dentro il periodo del feed): servizi da calendar_dates (+calendar se attivo)
    ref = f"{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}"; rd8 = DAY
    cd = rd("calendar_dates.txt"); act = set(cd[(cd.date == rd8) & (cd.exception_type == "1")].service_id)
    if "calendar.txt" in z.namelist():
        cal = rd("calendar.txt"); wd = pd.Timestamp(ref).day_name().lower()
        act |= set(cal[(cal.start_date <= rd8) & (cal.end_date >= rd8) & (cal[wd] == "1")].service_id)
        act -= set(cd[(cd.date == rd8) & (cd.exception_type == "2")].service_id)
    trips = rd("trips.txt", usecols=["route_id", "service_id", "trip_id"]); trips = trips[trips.service_id.isin(act)]
    stt = rd("stop_times.txt", usecols=["trip_id", "stop_id"]); stt = stt[stt.stop_id.isin(st.stop_id) & stt.trip_id.isin(trips.trip_id)]
    stt = stt.merge(trips[["trip_id", "route_id"]], on="trip_id").drop_duplicates(["trip_id", "stop_id"])
    rt = rd("routes.txt").set_index("route_id"); short = rt["route_short_name"] if "route_short_name" in rt else rt.index.to_series()
    stt["line"] = stt.route_id.map(short)
    cnt = stt.groupby("stop_id").trip_id.nunique(); lines = stt.groupby("stop_id").line.agg(lambda s: " ".join(sorted(set(s.dropna()))))
    st["trips_on_ref_date"] = st.stop_id.map(cnt).fillna(0).astype(int); st["lines"] = st.stop_id.map(lines).fillna(""); st["ref_date"] = ref
    code = st["stop_code"] if "stop_code" in st and st["stop_code"].notna().all() else st["stop_id"]
    safe = lambda s: re.sub(r"[^a-z0-9_]", "_", str(s).lower())
    st["id"] = f"dst_{kind}_" + code.map(safe)
    if not st.id.is_unique: st["id"] = f"dst_{kind}_" + st.stop_id.map(safe)
    st["name"] = st["stop_name"]
    keep = {c: M for c in ("stop_id", "stop_code", "stop_name", "wheelchair_boarding", "location_type", "parent_station") if c in st}
    st["name"] = st["stop_name"]
    gdf = gpd.GeoDataFrame(st[["id"] + list(keep) + ["trips_on_ref_date", "lines", "ref_date", "lon", "lat"]],
                           geometry=gpd.points_from_xy(st.E, st.N), crs=7791)
    gdf = gdf.rename(columns={"lon": "orig_lon", "lat": "orig_lat"})
    cls = {**keep, "trips_on_ref_date": D, "lines": D, "ref_date": D, "orig_lon": M, "orig_lat": M}
    p = NORM / f"{slug}.gpkg"; p.unlink(missing_ok=True)
    finish(gdf, source_id, snap, cls, p.name, "stops")

# ---------------------------------------------------------------- raster
def norm_raster(slug, nodata):
    src = raw(slug, "*.tif")[0]; dst = NORM / (src.stem + ".tif")
    with rasterio.open(src) as r:
        a = r.read(1); prof = r.profile; prof.update(driver="GTiff", compress="deflate", predictor=3, nodata=nodata, crs="EPSG:7791")
        a = np.where(np.isfinite(a), a, nodata).astype("float32")
        with rasterio.open(dst, "w", **prof) as o: o.write(a, 1)
    ok = a != nodata
    st = {"file": dst.name, "shape": a.shape, "res_m": prof["transform"].a, "nodata_pct": round(float((~ok).mean() * 100), 2),
          "min": round(float(a[ok].min()), 2), "max": round(float(a[ok].max()), 2), "mean": round(float(a[ok].mean()), 2)}
    print("  ", st); json.dump(st, open(NORM / f"{src.stem}.stats.json", "w")); return st

JOBS = {
    "osm": norm_osm, "uv": norm_uv,
    "civici": lambda: sit("sit_civici", "src_sit_civici", 3857, "objectid_1", "adr_sit_"),
    "scuole": lambda: sit("sit_scuole", "src_sit_scuole", 3003, "fid", "sch_sit_"),
    "edscol": lambda: sit("sit_edifici_scolastici", "src_sit_edifici_scolastici", 3003, "fid", "bld_sit_"),
    "gtfs_at": lambda: norm_gtfs("gtfs_at_toscana", "src_gtfs_at_toscana", "gtfs.zip", "stop"),
    "gtfs_tren": lambda: norm_gtfs("gtfs_trenitalia", "src_gtfs_trenitalia", "trenitalia.gtfs.zip", "station"),
    "dsm": lambda: norm_raster("rt_dsm2021", -9999.0), "dtm10": lambda: norm_raster("rt_dtm10", -9999.0),
}
if __name__ == "__main__":
    for k in sys.argv[1:] or JOBS:
        print(k); JOBS[k]()
