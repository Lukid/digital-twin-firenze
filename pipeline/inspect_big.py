"""Ispezione di DBT10K Pisa (7z) e grafo Iter.net (zip) sull'AOI. Scrive pipeline/ispezione_big.json. Non bloccante.
Estrae in data/work/ (gli originali in data/raw restano intatti). Le coordinate dei shapefile sono in EPSG:3003 nominale:
si confrontano con l'AOI nello stesso modo adottato per il SIT (nessuno shift di datum, vedi checks.py)."""
import glob, json, sys, zipfile, pathlib, traceback
import py7zr, pyogrio, shapely
from pyproj import Transformer
import lib
from lib import AOI, RAW, ROOT

WORK = ROOT / "data/work"; WORK.mkdir(exist_ok=True)
inv = Transformer.from_crs(7791, 3003, always_xy=True)
b = AOI["buf_en"]; xs, ys = zip(*[inv.transform(x, y) for x in (b[0], b[2]) for y in (b[1], b[3])])
BB3003 = (min(xs), min(ys), max(xs), max(ys))

def scan(root, out):
    res = {}
    for shp in sorted(pathlib.Path(root).rglob("*.shp")):
        try:
            info = pyogrio.read_info(shp); n = pyogrio.read_info(shp, force_total_bounds=False)["features"]
            g = pyogrio.read_dataframe(shp, bbox=BB3003)
            res[shp.name] = {"crs": str(info["crs"]), "geometria": info["geometry_type"], "oggetti_totali": int(n), "oggetti_in_AOI": int(len(g)), "campi": [c for c in g.columns if c != "geometry"][:25]}
        except Exception as ex: res[shp.name] = {"errore": str(ex)[:150]}
    return res

def dbt():
    f = glob.glob(str(RAW / "rt_dbt10k_pisa/*/*.7z"))[0]; d = WORK / "rt_dbt10k_pisa"
    if not d.exists():
        with py7zr.SevenZipFile(f) as z:
            names = [i.filename for i in z.list() if "vestizione" not in i.filename and "shp_dbt" in i.filename or i.filename.endswith((".xls", "pdf"))]
            z.extract(path=d, targets=names)
    r = scan(d, "dbt"); return {k: v for k, v in r.items()}

def iternet():
    f = glob.glob(str(RAW / "rt_iternet/*/*.zip"))[0]; d = WORK / "rt_iternet"
    if not d.exists():
        d.mkdir()
        with zipfile.ZipFile(f) as z:
            z.extractall(d)
        for zz in list(d.rglob("*.zip")):
            with zipfile.ZipFile(zz) as z: z.extractall(zz.parent / zz.stem)
    files = [str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()]
    r = scan(d, "iter")
    for gdb in d.rglob("*.gdb"):
        for name, kind in pyogrio.list_layers(gdb):
            try:
                n = pyogrio.read_info(gdb, layer=name)["features"]; g = pyogrio.read_dataframe(gdb, layer=name, bbox=BB3003)
                r[f"{gdb.name}:{name}"] = {"oggetti_totali": int(n), "oggetti_in_AOI": len(g), "campi": [c for c in g.columns if c != "geometry"][:25]}
            except Exception as ex: r[f"{gdb.name}:{name}"] = {"errore": str(ex)[:150]}
    return {"file_estratti": files[:40], "layer": r}

if __name__ == "__main__":
    out = {"bbox_AOI_3003_nominale": [round(v, 1) for v in BB3003]}
    for k, fn in (("dbt10k_pisa", dbt), ("iternet", iternet)):
        try: out[k] = fn()
        except Exception as ex: out[k] = {"errore": str(ex)[:300], "traceback": traceback.format_exc()[-400:]}
    json.dump(out, open(ROOT / "pipeline/ispezione_big.json", "w"), indent=1, ensure_ascii=False)
    for k in ("dbt10k_pisa", "iternet"):
        v = out[k]; print(k, v.get("errore") or "ok")
        for n, i in (v.items() if k == "dbt10k_pisa" else v.get("layer", {}).items()):
            if isinstance(i, dict) and i.get("oggetti_in_AOI"): print("  ", n, i["oggetti_in_AOI"], "/", i["oggetti_totali"], i.get("geometria", ""))
