"""F07: poligoni della chioma LiDAR senza albero censito (D14).
Il layer `vegetazione_lidar` di F05 ha solo il baricentro di ogni cluster (punto), area e h95: per le ombre serve l'impronta.
Qui si rifà la stessa maschera di F05 (geometry/build_firenze.py, sola lettura): CHM 2023 >= 2,5 m, fuori da edifici UV e OSM (buffer 0,5 m),
a più di 7,5 m da ogni albero censito non in edificio, componenti connesse (8 vicini) di almeno 20 m2. Ogni poligono è abbinato per baricentro
alla riga del layer di F05 (h95, liscia). Il controllo di coerenza (numero, area totale, abbinamenti) è scritto nel JSON accanto al file.
Output: data/norm/<area>/shadow/vegetazione_lidar_poligoni.gpkg (+ .json). Uso: pipeline/.venv/bin/python shadow/veg_lidar.py"""
import json, pathlib, sys
import numpy as np, geopandas as gpd, rasterio, shapely
from rasterio.features import rasterize, shapes
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import lib

N = lib.NORM
SLUG = lib.AOI["aoi_id"].removeprefix("aoi_")
USCITA = N / "shadow" / "vegetazione_lidar_poligoni.gpkg"
SOGLIA_VEG_M, RMAX_CHIOMA, MIN_CELLE, BUF_EDIF, SEMPLIFICA_M = 2.5, 7.5, 80, 0.5, 0.3


def costruisci():
    gp = N / "geometry" / f"geometrie_{SLUG}.gpkg"
    layer = gpd.read_file(gp, layer="vegetazione_lidar"); alberi = gpd.read_file(gp, layer="alberi")
    rd = lambda p: np.where((a := rasterio.open(p).read(1)) == -9999.0, np.nan, a)
    T = rasterio.open(N / "fi_dsm2023_0.5m.tif").transform
    chm = rd(N / "fi_dsm2023_0.5m.tif") - rd(N / "fi_dtm2023_0.5m.tif"); H, W = chm.shape; C = T.a
    uv = gpd.read_file(N / "rt_uv_firenze_novoli.gpkg", layer="building_volume"); osm_b = gpd.read_file(N / "osm_firenze.gpkg", layer="buildings")
    edif = rasterize([(g, 1) for g in list(uv.geometry.buffer(BUF_EDIF)) + list(osm_b.geometry.buffer(BUF_EDIF))], out_shape=(H, W), transform=T, dtype="uint8").astype(bool)
    seme = np.zeros((H, W), bool); s = alberi[~alberi.in_edificio]
    seme[np.clip(((T.f - s.geometry.y.values) // C).astype(int), 0, H - 1), np.clip(((s.geometry.x.values - T.c) // C).astype(int), 0, W - 1)] = True
    libera = (chm >= SOGLIA_VEG_M) & ~edif & (ndimage.distance_transform_edt(~seme) * C > RMAX_CHIOMA)
    lab, n = ndimage.label(libera, structure=np.ones((3, 3)))
    sizes = ndimage.sum(libera, lab, range(1, n + 1)); keep = np.flatnonzero(sizes >= MIN_CELLE) + 1
    rr, cc = np.indices((H, W), sparse=True)
    ok = np.isin(lab, keep)
    cy = ndimage.mean(np.broadcast_to(rr, (H, W)), lab, keep); cx = ndimage.mean(np.broadcast_to(cc, (H, W)), lab, keep)
    pts = np.column_stack([T.c + (cx + 0.5) * C, T.f - (cy + 0.5) * C])
    geo = {}
    for g, v in shapes(lab.astype("int32"), mask=ok, transform=T, connectivity=8): geo.setdefault(int(v), []).append(shape(g))
    polys = [unary_union(geo[int(k)]) for k in keep]
    d, j = cKDTree(np.column_stack([layer.geometry.x.values, layer.geometry.y.values])).query(pts)
    m = d < 0.05
    out = gpd.GeoDataFrame({"id": [f"veg_{SLUG}_{i:05d}" for i in range(len(keep))], "area_m2": (sizes[keep - 1] * C * C).round(2),
                            "h95": np.where(m, layer.h95.values[j], np.nan), "liscia": np.where(m, layer.liscia.values[j], False),
                            "abbinata_f05": m}, geometry=shapely.make_valid(shapely.simplify(np.array(polys, dtype=object), SEMPLIFICA_M)), crs=7791)
    chk = {"cluster_ricostruiti": int(len(out)), "cluster_layer_f05": int(len(layer)), "abbinati_per_baricentro": int(m.sum()),
           "area_ricostruita_m2": round(float(sizes[keep - 1].sum() * C * C), 1), "area_layer_f05_m2": round(float(layer.area_m2.sum()), 1),
           "area_poligoni_semplificati_m2": round(float(out.area.sum()), 1), "semplificazione_m": SEMPLIFICA_M,
           "senza_abbinamento_scartati": int((~m).sum())}
    out = out[out.abbinata_f05].reset_index(drop=True)
    USCITA.parent.mkdir(parents=True, exist_ok=True); USCITA.unlink(missing_ok=True)
    out.to_file(USCITA, layer="vegetazione_lidar_poligoni", driver="GPKG")
    USCITA.with_suffix(".json").write_text(json.dumps(chk, indent=1)); print(chk)
    return out


if __name__ == "__main__":
    costruisci()
