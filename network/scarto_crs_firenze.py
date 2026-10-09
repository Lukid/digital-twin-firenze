#!/usr/bin/env python3
"""F04: scarto 3003 -> 7791 su Firenze, stesso metodo di pipeline/checks.check_3003: poligoni degli edifici scolastici della Città metropolitana
(3003 nativo, trasformati senza shift di datum come in normalizzazione) contro le unità volumetriche regionali (7791 nativo). Scrive network/firenze_novoli/scarto_crs.json.
Non è una misura pura della trasformazione: i due dati sono disegnati a mano da fonti diverse, quindi lo scarto contiene anche la differenza di digitalizzazione.
Uso: python network/scarto_crs_firenze.py"""
import glob, json, os, sys
import geopandas as gpd, numpy as np, shapely
from pyproj import Transformer
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare lib e rete_lib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "pipeline"))
from lib import RAW, NORM
from checks import stats
from rete_lib import RES, ROOT
uv = gpd.read_file(NORM / "rt_uv_firenze_novoli.gpkg")
ed = gpd.read_file("/vsizip/" + glob.glob(str(RAW / "cm_edscol_firenze/*/form_ed_scolastici.zip"))[0]).set_crs(3003, allow_override=True)
t = Transformer.from_crs(3003, 7791, always_xy=True)
g = shapely.transform(ed.geometry.values, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))
sidx = uv.sindex; cen, vert, iou = [], [], []
for geom in g:
    cand = list(sidx.query(geom.buffer(30)))
    if not cand: continue
    u = uv.geometry.values[cand[int(np.argmin([uv.geometry.values[i].distance(geom.centroid) for i in cand]))]]
    i = geom.intersection(u).area / geom.union(u).area; iou.append(i)
    if i < 0.5: continue          # solo coppie con sovrapposizione chiara (stesso edificio)
    cen.append((u.centroid.x - geom.centroid.x, u.centroid.y - geom.centroid.y))
    uvv = np.array([c for p in (u.geoms if hasattr(u, "geoms") else [u]) for c in p.exterior.coords])
    for x, y in [c for p in (geom.geoms if hasattr(geom, "geoms") else [geom]) for c in p.exterior.coords]:
        k = np.hypot(uvv[:, 0] - x, uvv[:, 1] - y); j = k.argmin()
        if k[j] <= 3: vert.append((uvv[j, 0] - x, uvv[j, 1] - y))   # vertici entro 3 m: stesso angolo di edificio
pisa = json.load(open(ROOT / "pipeline/crs_check.json"))["A_3003_to_7791"]["nessuno_shift_di_datum (adottata)"]["vertici_entro_3m"]
out = {"metodo": "poligoni Città metropolitana (3003 nativo) -> 7791 senza shift di datum, contro unità volumetriche regionali (7791 nativo); vertici entro 3 m, coppie con IoU >= 0,5",
       "edifici_cm_nel_dato": len(g), "con_unità_volumetrica_vicina": len(iou), "coppie_iou_ge_0.5": len(cen), "iou_mediano": round(float(np.median(iou)), 2),
       "centroidi": stats(cen) if cen else None, "vertici_entro_3m": stats(vert) if vert else None, "pisa_vertici_entro_3m_per_confronto": pisa,
       "nota": "Differenza = unità volumetrica meno poligono CM trasformato. A Pisa lo stesso confronto (edifici SIT, 128 vertici) dava modulo mediano 1,43 m; con lo stesso dato in due CRS (DBT10K) 0,35 m. Qui il confronto è tra dati disegnati a mano da fonti diverse (volo regionale del 2011), quindi è un limite superiore dello scarto di trasformazione."}
json.dump(out, open(RES / "scarto_crs.json", "w"), ensure_ascii=False, indent=1); print(json.dumps(out, ensure_ascii=False, indent=1))
