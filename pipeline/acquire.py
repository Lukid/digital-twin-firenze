"""Acquisizione: scarica le fonti in data/raw/<fonte>/<AAAAMMGG>/ e scrive lo snapshot in pipeline/snapshots/.
Uso: acquire.py [fonte ...]   (senza argomenti: tutte)"""
import csv, io, json, sys, zipfile, pathlib, subprocess
import lib
from lib import AOI, ROOT, get, download, record, rawdir

WFS = "https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato"
WMS = "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia"
SIT = "https://sit.comune.pisa.it/arcgis/rest/services/Hosted"
OSM_URL = __import__("os").environ.get("OSM_URL", "https://download.geofabrik.de/europe/italy/centro-260930.osm.pbf")
BUF = AOI["buf_en"]

def gtfs(slug, url, name):
    def f():
        d = rawdir(slug); p = download(url, d / name)
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            if "feed_info.txt" in names:
                r = next(csv.DictReader(io.TextIOWrapper(z.open("feed_info.txt"), "utf-8-sig")))
                a, b = r["feed_start_date"], r["feed_end_date"]; note = "feed_start_date e feed_end_date da feed_info.txt"
            else:   # nessun feed_info: periodo dalle date di servizio in calendar_dates
                ds = sorted({row["date"] for row in csv.DictReader(io.TextIOWrapper(z.open("calendar_dates.txt"), "utf-8-sig"))})
                a, b = ds[0], ds[-1]; note = "feed senza feed_info.txt: minimo e massimo di calendar_dates.txt"
        iso = lambda s: f"{s[:4]}-{s[4:6]}-{s[6:]}"
        return {"files": [p], "url": url, "media_type": "application/zip", "content_period": {"start": iso(a), "end": iso(b), "note": note},
                "expires_at": iso(b)}
    return f

def osm():
    d = rawdir("osm_pisa"); p = download(OSM_URL, d / OSM_URL.rsplit("/", 1)[1])
    return {"files": [p], "url": OSM_URL, "media_type": "application/x-osm+pbf", "license_state": "clear",
            "content_period": {"note": "estratto regionale Centro Italia da distributore di estratti OSM, timestamp nel nome del file (ore 00 UTC del 2026-09-30 circa); il ritaglio all'AOI avviene in normalizzazione, il file originario resta intatto"}}

def wfs_uv(slug="rt_unita_volumetriche"):
    d = rawdir(slug); crs = "urn:ogc:def:crs:EPSG::7791"; files = []; st = 0
    def chk(r):
        if b"ExceptionReport" in r.content[:2000] or b"FeatureCollection" not in r.content[:4000]: raise ValueError("risposta WFS non valida: " + r.text[:200])
    while True:
        p = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "rt_edif.unitavolumetriche", "COUNT": 500, "STARTINDEX": st,
             "SRSNAME": crs, "BBOX": ",".join(map(str, BUF)) + "," + crs}
        r = get(WFS, params=p, check=chk)
        f = d / f"uv_{st:05d}.gml"; f.write_bytes(r.content); files.append(f)
        n = r.text.count("<wfs:member>")
        if n < 500: break
        st += 500
    url = WFS + "&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=rt_edif.unitavolumetriche&SRSNAME=" + crs + "&BBOX=" + ",".join(map(str, BUF)) + "," + crs
    return {"files": files, "multi": True, "url": url, "media_type": "application/gml+xml", "license_state": "clear_with_reserve",
            "content_period": {"note": "volo 2010 (campo anno nei dati); il servizio non dichiara la data di aggiornamento"}}

def wms_raster(slug, layer, res_m):
    def f():
        d = rawdir(slug); w, h = round((BUF[2] - BUF[0]) / res_m), round((BUF[3] - BUF[1]) / res_m)
        # BBOX allineato alla risoluzione: larghezza/altezza intere, pixel esattamente res_m
        bb = [BUF[0], BUF[1], BUF[0] + w * res_m, BUF[1] + h * res_m]
        p = {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": layer, "STYLES": "", "CRS": "EPSG:7791",
             "BBOX": ",".join(map(str, bb)), "WIDTH": w, "HEIGHT": h, "FORMAT": "image/tiff"}
        def chk(r):
            if r.content[:4] not in (b"II*\x00", b"MM\x00*"): raise ValueError("GetMap non ha restituito un TIFF: " + r.text[:200])
        r = get(WMS, params=p, check=chk, timeout=300)
        out = d / f"{slug}_{res_m}m.tif"; out.write_bytes(r.content)
        return {"files": [out], "url": WMS + "&" + "&".join(f"{k}={v}" for k, v in p.items()), "media_type": "image/tiff",
                "license_state": "clear_with_reserve",
                "content_period": {"note": "letto via WMS (surrogato del download ufficiale, che richiede la Cartoteca regionale); data di acquisizione nei metadati del layer"}}
    return f

def sit(slug, service, layer, out_sr):
    """Layer ArcGIS. Coordinate nel CRS nativo del layer (outSR), filtro per riquadro in lon/lat."""
    def f():
        d = rawdir(slug); s, w, n, e = AOI["buf_ll_SWNE"]; feats = []; off = 0; base = f"{SIT}/{service}/FeatureServer/{layer}/query"
        meta = get(f"{SIT}/{service}/FeatureServer/{layer}", params={"f": "json"}, check=lambda r: "error" in r.json() and (_ for _ in ()).throw(ValueError(r.text[:200])))
        (d / "layer_info.json").write_bytes(meta.content)
        while True:
            p = {"where": "1=1", "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                 "outFields": "*", "returnGeometry": "true", "outSR": out_sr, "f": "geojson", "resultOffset": off, "resultRecordCount": 1000}
            def chk(r):
                j = r.json()
                if "error" in j or "features" not in j: raise ValueError("risposta ArcGIS non valida: " + r.text[:200])
            j = get(base, params=p, check=chk).json(); feats += j["features"]
            if len(j["features"]) < 1000 and not j.get("exceededTransferLimit"): break
            off += 1000
        out = d / f"{slug}.geojson"
        out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False))
        return {"files": [out, d / "layer_info.json"], "multi": True, "url": base + f"?where=1%3D1&geometry={w},{s},{e},{n}&inSR=4326&outSR={out_sr}&f=geojson",
                "media_type": "application/geo+json", "license_state": "unproven",
                "content_period": {"note": "stato del servizio alla data di scarico (data di modifica solo se dichiarata nel layer)"}}
    return f

def big(slug, url, name, lic, note):
    def f():
        d = rawdir(slug); p = download(url, d / name)
        return {"files": [p], "url": url, "media_type": "application/zip" if name.endswith("zip") else "application/x-7z-compressed",
                "license_state": lic, "content_period": {"note": note}}
    return f

SRC = {   # fonte -> (source_id, slug, funzione, license_state)
    "gtfs_at": ("src_gtfs_at_toscana", "gtfs_at_toscana", gtfs("gtfs_at_toscana", "https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs", "gtfs.zip"), "clear_with_reserve"),
    "gtfs_tren": ("src_gtfs_trenitalia", "gtfs_trenitalia", gtfs("gtfs_trenitalia", "https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/4f85393b-357d-443d-8378-65de4198505f/download/trenitalia.gtfs", "trenitalia.gtfs.zip"), "clear_with_reserve"),
    "osm": ("src_osm_pisa", "osm_pisa", osm, "clear"),
    "uv": ("src_rt_unita_volumetriche", "rt_unita_volumetriche", wfs_uv, "clear_with_reserve"),
    "dsm": ("src_rt_dsm2021", "rt_dsm2021", wms_raster("rt_dsm2021", "rt_morfologia.iddsm2021.1m.rt", 1), "clear_with_reserve"),
    "dtm10": ("src_rt_dtm10", "rt_dtm10", wms_raster("rt_dtm10", "rt_morfologia.iddtm.10m.rt", 10), "clear_with_reserve"),
    "civici": ("src_sit_civici", "sit_civici", sit("sit_civici", "Civici_puntuali_View", 0, 3857), "unproven"),
    "scuole": ("src_sit_scuole", "sit_scuole", sit("sit_scuole", "Scuole_infanzia_materne_primarie_e_secondarie", 0, 3003), "unproven"),
    "edscol": ("src_sit_edifici_scolastici", "sit_edifici_scolastici", sit("sit_edifici_scolastici", "edifici_scolastici", 4, 3003), "unproven"),
    "dbt10k": ("src_rt_dbt10k_pisa", "rt_dbt10k_pisa", big("rt_dbt10k_pisa", "http://www502.regione.toscana.it/geoscopio/download/dbtopografico/dbt10k/7z/DBT10K_050_PISA_2010_2010.7z", "DBT10K_050_PISA_2010_2010.7z", "clear", "dati 2010, scala 1:10.000; file del 2025-10-10 (Last-Modified)"), "clear"),
    "iternet": ("src_rt_iternet", "rt_iternet", big("rt_iternet", "http://www502.regione.toscana.it/geoscopio/download/grafo_stradale/iternet.zip", "iternet.zip", "clear_with_reserve", "grafo stradale regionale, file del 2025-10-10 (Last-Modified); epoca dei dati non dichiarata, StatPortal indica aprile 2015"), "clear_with_reserve"),
}

if __name__ == "__main__":
    for k in sys.argv[1:] or SRC:
        sid, slug, fn, lic = SRC[k]
        def run(fn=fn, lic=lic):
            r = fn(); r.setdefault("license_state", lic); return r
        record(sid, slug, run)
