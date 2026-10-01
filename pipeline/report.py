"""Report di copertura: conta gli oggetti per fonte/layer in AOI e Z2, legge snapshot e controlli. Scrive pipeline/report.json."""
import json, glob, pyogrio, shapely
import geopandas as gpd
import lib
from lib import AOI, NORM, ROOT
Z2 = shapely.box(*AOI["z2_en"])
out = {"aoi": AOI, "giorno": lib.DAY, "layer": {}, "snapshot": {}}
for p in sorted(NORM.glob("*.gpkg")):
    for name, _ in pyogrio.list_layers(p):
        g = gpd.read_file(p, layer=name)
        out["layer"][f"{p.name}:{name}"] = {"in_AOI_buffer": len(g), "in_Z2": int(g.intersects(Z2).sum())}
for p in sorted(glob.glob(str(ROOT / "pipeline/snapshots/snp_*.json"))):
    s = json.load(open(p)); out["snapshot"][s["snapshot_id"]] = {k: s.get(k) for k in ("status", "bytes", "sha256", "license_state", "expires_at")}
out["crs"] = json.load(open(ROOT / "pipeline/crs_check.json")) if (ROOT / "pipeline/crs_check.json").exists() else None
json.dump(out, open(ROOT / "pipeline/report.json", "w"), indent=1, ensure_ascii=False)
for k, v in out["layer"].items(): print(f"{k:55} AOI {v['in_AOI_buffer']:6}  Z2 {v['in_Z2']:6}")
