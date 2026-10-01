"""Misura degli scarti di trasformazione. Scrive pipeline/crs_check.json.
A) EPSG:3003 -> 7791: impronte degli edifici scolastici SIT (3003 nativo) contro le unita' volumetriche regionali (7791 nativo);
   confronto di due operazioni (nessuno shift di datum, disponibile in pyproj senza griglie; Helmert 3 parametri Monte Mario->WGS84).
B) lon/lat (WGS84) -> 7791: stesse unita' volumetriche richieste al servizio in EPSG:4326 e in 7791, scarto di pyproj."""
import json, glob, numpy as np, geopandas as gpd, shapely, xml.etree.ElementTree as ET
from pyproj import Transformer
import lib
from lib import AOI, get, RAW, ROOT

GM = "{http://www.opengis.net/gml/3.2}"
def polys(gml_bytes, swap=False):
    out = {}
    for m in ET.fromstring(gml_bytes).iter("{http://www.opengis.net/wfs/2.0}member"):
        ft = m[0]; uv = ft.find("{http://mapserver.gis.umn.edu/mapserver}uv_id").text; rings = []
        for pos in ft.iter(GM + "posList"):
            v = list(map(float, pos.text.split())); rings.append([(v[i + 1], v[i]) if swap else (v[i], v[i + 1]) for i in range(0, len(v), 2)])
        out[uv] = rings[0]
    return out

def stats(d):
    d = np.asarray(d); r = np.hypot(d[:, 0], d[:, 1])
    return {"n": int(len(d)), "dE_medio_m": round(float(d[:, 0].mean()), 2), "dN_medio_m": round(float(d[:, 1].mean()), 2),
            "dE_mediana_m": round(float(np.median(d[:, 0])), 2), "dN_mediana_m": round(float(np.median(d[:, 1])), 2),
            "modulo_mediano_m": round(float(np.median(r)), 2), "modulo_p95_m": round(float(np.percentile(r, 95)), 2), "modulo_max_m": round(float(r.max()), 2)}

def check_3003():
    uv = gpd.read_file(ROOT / "data/norm/rt_unita_volumetriche.gpkg")
    ed = gpd.read_file(glob.glob(str(RAW / "sit_edifici_scolastici/*/sit_edifici_scolastici.geojson"))[0]).set_crs(3003, allow_override=True)
    ops = {"nessuno_shift_di_datum (adottata)": Transformer.from_crs(3003, 7791, always_xy=True),
           "helmert3_MonteMario_WGS84": Transformer.from_pipeline("+proj=pipeline +step +inv +proj=tmerc +lat_0=0 +lon_0=9 +k=0.9996 +x_0=1500000 +y_0=0 +ellps=intl "
               "+step +proj=cart +ellps=intl +step +proj=helmert +x=-104.1 +y=-49.1 +z=-9.9 +step +inv +proj=cart +ellps=GRS80 +step +proj=utm +zone=32 +ellps=GRS80")}
    res = {}
    for name, t in ops.items():
        g = shapely.transform(ed.geometry.values, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))
        cen, vert, iou = [], [], []
        for geom in g:
            u = uv.geometry.values[uv.distance(geom.centroid).values.argmin()]
            i = geom.intersection(u).area / geom.union(u).area; iou.append(i)
            if i < 0.5: continue          # solo coppie con sovrapposizione chiara (stesso edificio)
            cen.append((u.centroid.x - geom.centroid.x, u.centroid.y - geom.centroid.y))
            uvv = np.array([c for p in (u.geoms if hasattr(u, "geoms") else [u]) for c in p.exterior.coords])
            for x, y in list(geom.exterior.coords)[:-1] if geom.geom_type == "Polygon" else [c for p in geom.geoms for c in p.exterior.coords]:
                k = np.hypot(uvv[:, 0] - x, uvv[:, 1] - y); j = k.argmin()
                if k[j] <= 3: vert.append((uvv[j, 0] - x, uvv[j, 1] - y))   # vertici entro 3 m: stessa angolo di edificio
        res[name] = {"edifici_sit": len(g), "coppie_iou_ge_0.5": len(cen), "iou_mediano": round(float(np.median(iou)), 2),
                     "centroidi": stats(cen) if cen else None, "vertici_entro_3m": stats(vert) if vert else None}
    return res

def check_wgs84():
    s = lib.BUFFER_M; b = AOI["buf_en"]; ctr = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]; bb = [ctr[0] - 400, ctr[1] - 400, ctr[0] + 400, ctr[1] + 400]
    W = "https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato"
    q = lambda crs, box: get(W, params={"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "rt_edif.unitavolumetriche", "COUNT": 300,
        "SRSNAME": crs, "BBOX": box + "," + crs, "SORTBY": "uv_id"}).content
    a = polys(q("urn:ogc:def:crs:EPSG::7791", ",".join(map(str, bb))))
    t = Transformer.from_crs(6706, 7791, always_xy=True); tl = Transformer.from_crs(7791, 6706, always_xy=True)
    ll = [tl.transform(bb[0], bb[1]), tl.transform(bb[2], bb[3])]
    b4 = polys(q("urn:ogc:def:crs:EPSG::4326", f"{ll[0][1]},{ll[0][0]},{ll[1][1]},{ll[1][0]}"), swap=True)   # lat,lon -> lon,lat
    d = []
    for k in set(a) & set(b4):
        if len(a[k]) != len(b4[k]): continue
        for (e, n), (lo, la) in zip(a[k], b4[k]):
            x, y = t.transform(lo, la); d.append((x - e, y - n))
    return {"oggetti_confrontati": len(set(a) & set(b4)), "vertici": len(d), **stats(d),
            "nota": "scarto fra la riproiezione fatta dal servizio (7791 nativo) e quella di pyproj da lon/lat trattati come RDN2008 geografico; le coordinate 4326 hanno 7 decimali (circa 1 cm)"}

def check_dbt10k():
    """Stesso dato in due CRS: unita' volumetriche DBT10K (shapefile 3003) e servizio regionale (7791 nativo), unite per uv_id.
    Lo scarto dei vertici e' la misura diretta della trasformazione 3003 -> 7791 (stessi oggetti, stessi vertici)."""
    shp = glob.glob(str(ROOT / "data/work/rt_dbt10k_pisa/**/020101_un_vol_3003.shp"), recursive=True)
    if not shp: return {"errore": "DBT10K non estratto (eseguire inspect_big.py)"}
    inv = Transformer.from_crs(7791, 3003, always_xy=True); b = AOI["buf_en"]
    xs, ys = zip(*[inv.transform(x, y) for x in (b[0], b[2]) for y in (b[1], b[3])])
    d3 = gpd.read_file(shp[0], bbox=(min(xs), min(ys), max(xs), max(ys))).set_crs(3003, allow_override=True)
    uv = gpd.read_file(ROOT / "data/norm/rt_unita_volumetriche.gpkg").set_index("uv_id")
    res = {}
    for name, t in {"nessuno_shift_di_datum (adottata)": Transformer.from_crs(3003, 7791, always_xy=True)}.items():
        d, ok = [], 0
        for _, r in d3.iterrows():
            if r["un_vol_id"] not in uv.index: continue
            a = np.array(r.geometry.exterior.coords)[:, :2] if r.geometry.geom_type == "Polygon" else None
            u = uv.geometry[r["un_vol_id"]]
            if a is None or u.geom_type != "MultiPolygon" or len(u.geoms) != 1: continue
            bb = np.array(u.geoms[0].exterior.coords)
            x, y = t.transform(a[:, 0], a[:, 1]); ok += 1      # anello con vertice iniziale/senso diversi: si abbina il vertice piu' vicino
            for xi, yi in zip(x, y):
                k = np.hypot(bb[:, 0] - xi, bb[:, 1] - yi); j = k.argmin()
                if k[j] <= 3: d.append((bb[j, 0] - xi, bb[j, 1] - yi))
        res[name] = {"oggetti_uniti": ok, **stats(d)}
    return res

if __name__ == "__main__":
    out = {"data": lib.DAY, "A_3003_to_7791": check_3003(), "B_lonlat_to_7791": check_wgs84(), "C_dbt10k_3003_vs_wfs_7791": check_dbt10k(),
           "nota_griglia": "La griglia IGM Monte Mario->RDN2008 (35160622_47161840_R40_F00.gsb, precisione 0,1 m) non e' in pyproj ne' in PROJ-data (cdn.proj.org): l'operazione ufficiale non e' applicabile in locale."}
    json.dump(out, open(ROOT / "pipeline/crs_check.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(out, indent=1, ensure_ascii=False))
