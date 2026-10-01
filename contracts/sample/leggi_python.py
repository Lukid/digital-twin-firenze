"""Lettore A: json + shapely (geometrie) + pyproj e GDAL via rasterio (CRS). Stampa un riepilogo JSON.
Uso: docs/audit/edifici/.venv/bin/python leggi_python.py"""
import json, pathlib, sys
from shapely.geometry import shape
from pyproj import Transformer, CRS
import rasterio.warp, rasterio.crs

fc = json.load(open(pathlib.Path(__file__).with_name("z2_campione.geojson")))
crs_urn = fc["crs"]["properties"]["name"]
gdal_crs = rasterio.crs.CRS.from_string(crs_urn)          # GDAL legge l'URN dichiarato nel file
inv = Transformer.from_crs(CRS.from_user_input(crs_urn), 4326, always_xy=True)
byl, geoms = {}, {}
for f in fc["features"]:
    g = shape(f["geometry"]); l = f["properties"]["layer"]
    byl[l] = byl.get(l, 0) + 1; geoms[f["properties"]["id"]] = g
from shapely.ops import unary_union
allb = unary_union(list(geoms.values())).bounds
sch, pel = geoms["dst_school_piee82101p"], geoms["dst_stop_pi4390"]
lon, lat = inv.transform(sch.x, sch.y)
gl = rasterio.warp.transform(gdal_crs, "EPSG:4326", [sch.x], [sch.y])   # GDAL: ordine E,N
# errore massimo del ritorno a lon/lat rispetto ai valori originali delle fonti
err = 0.0
for f in fc["features"]:
    o = f["properties"].get("orig_wgs84")
    if o:
        x, y = f["geometry"]["coordinates"]; lo, la = inv.transform(x, y)
        err = max(err, abs(lo - o[0]), abs(la - o[1]))
# trappola: EPSG:6707 ha assi N,E; senza always_xy pyproj scambia E con N
bad = Transformer.from_crs(6707, 4326).transform(sch.x, sch.y)   # (lat, lon) se i dati fossero N,E
print(json.dumps({
    "reader": "python-shapely-pyproj-gdal", "crs_declared": crs_urn, "crs_name": CRS.from_user_input(crs_urn).name,
    "axes": [a.direction for a in CRS.from_user_input(crs_urn).axis_info],
    "counts": byl, "bbox": [round(v, 2) for v in allb],
    "network_length_m": round(sum(geoms[k].length for k in geoms if k.startswith("way_")), 2),
    "building_area_m2": round(sum(geoms[k].area for k in geoms if k.startswith("bld_")), 2),
    "school_to_pellico_m": round(sch.distance(pel), 2),
    "school_lonlat_pyproj": [round(lon, 7), round(lat, 7)], "school_lonlat_gdal": [round(gl[0][0], 7), round(gl[1][0], 7)],
    "max_roundtrip_err_deg": err,
    "trap_if_read_as_EPSG6707_NE": [round(bad[0], 4), round(bad[1], 4)]}, indent=1))
