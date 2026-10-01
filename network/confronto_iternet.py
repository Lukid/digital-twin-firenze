#!/usr/bin/env python3
"""Passo 4: confronto con Iter.net (grafo stradale regionale, EPSG:3003) su Z2. Solo report: network/confronto_iternet.json"""
import collections, glob, json, sys, zipfile
import geopandas as gpd, numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from rete_lib import *
sys.path.insert(0, str(ROOT / "pipeline"))
from lib import AOI
Z = AOI["z2_en"]; zb = box(*Z)
SH = OUT / "iternet_shp"
if not (SH / "elem_strad.shp").exists():   # estrae dal pacchetto originale in data/raw solo i due layer che servono
    outer = zipfile.ZipFile(glob.glob(str(ROOT / "data/raw/rt_iternet/*/iternet.zip"))[0]); SH.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(outer.open(outer.namelist()[0]))   # zip dentro zip (memorizzato senza compressione)
    for n in z.namelist():
        b = n.rsplit("/", 1)[-1]
        if "/shp/" in n and b.split(".")[0] in ("elem_strad", "civici", "strade"): open(SH / b, "wb").write(z.read(n))
bb = tuple(gpd.GeoSeries([zb], crs=7791).to_crs(3003).total_bounds)
e = gpd.read_file(SH / "elem_strad.shp", bbox=bb).set_crs(3003, allow_override=True).to_crs(7791)
e = e[e.geometry.centroid.within(zb)]
c = gpd.read_file(SH / "civici.shp", bbox=bb).set_crs(3003, allow_override=True).to_crs(7791); c = c[c.within(zb)]
G, D = carica()
og = gpd.GeoDataFrame([{**{k: v for k, v in d.items() if k != "geom"}, "geometry": d["geom"]} for _, _, d in G.edges(data=True)], crs=7791)
og = og[og.geometry.centroid.within(zb)]
CARR = ["service", "residential", "tertiary", "tertiary_link", "secondary", "secondary_link", "primary", "primary_link", "unclassified", "living_street", "trunk", "trunk_link", "motorway", "motorway_link"]
# strade OSM carrabili (anche quelle escluse a piedi: Iter.net è un grafo veicolare) e dedicate ai pedoni
osm_tutte = gpd.GeoDataFrame([{"highway": r["highway"], "length_m": r["length_m"], "motivo": r["motivo"], "geometry": r["geometry"]} for r in D["esclusi"]] +
                             [{"highway": d["highway"], "length_m": d["length_m"], "motivo": None, "geometry": d["geom"]} for _, _, d in G.edges(data=True)], crs=7791)
osm_tutte = osm_tutte[osm_tutte.geometry.centroid.within(zb)]
osm_car = osm_tutte[osm_tutte.highway.isin(CARR)]; osm_ped = osm_tutte[osm_tutte.highway.isin(["footway", "pedestrian", "path", "steps", "cycleway"])]
def cover(a, b, tol):   # quota della lunghezza di a entro tol m da b
    ub = unary_union(list(b.geometry)).buffer(tol); tot = a.length.sum()
    return float(a.geometry.intersection(ub).length.sum() / tot) if tot else None
r = {"area": "Z2 (senza buffer)", "licenza": "da accertare (CC BY 4.0 nel pacchetto, BY/BY-SA nel catalogo)", "data_aggiornamento_elementi": sorted(set(e.data_agg.dropna().astype(str))) if "data_agg" in e else None,
     "natura": "grafo stradale veicolare del Piano regionale: elementi di carreggiata, piazza, rotatoria; nessun marciapiede, attraversamento, scala, cancello o livello pedonale",
     "iternet": {"elementi": len(e), "km": round(e.length.sum() / 1000, 2), "per_tipo": dict(collections.Counter(e.tipo_ele)), "elementi_pedonali": int((e.tipo_ele == "pedonale").sum()),
                 "elementi_in_sottopasso": int((e.sot_pas != "0500").sum()), "civici": len(c)},
       "osm": {"km_carrabili_incl_escluse_a_piedi": round(osm_car.length.sum() / 1000, 2), "km_dedicati_pedoni": round(osm_ped.length.sum() / 1000, 2), "km_grafo_pedonale": round(og.length.sum() / 1000, 2), "attraversamenti_archi": int((og.tipo_arco == "attraversamento").sum()), "scale_archi": int((og.scala).sum())}}
for tol in (10, 25):
    r[f"quota_iternet_coperta_da_osm_carrabile_{tol}m"] = round(cover(e, osm_car, tol), 3)
    r[f"quota_osm_carrabile_coperta_da_iternet_{tol}m"] = round(cover(osm_car, e, tol), 3)
ub = unary_union(list(e.geometry)).buffer(10)
solo_osm = osm_car[~osm_car.geometry.centroid.within(ub)]
ub2 = unary_union(list(osm_car.geometry)).buffer(10); solo_it = e[~e.geometry.centroid.within(ub2)]
r["solo_osm_carrabile"] = {"km": round(solo_osm.length.sum() / 1000, 2), "per_highway_km": {k: round(v / 1000, 2) for k, v in solo_osm.assign(l=solo_osm.length).groupby("highway").l.sum().items()}}
r["solo_iternet"] = {"elementi": len(solo_it), "km": round(solo_it.length.sum() / 1000, 2), "per_tipo": dict(collections.Counter(solo_it.tipo_ele)), "id_esempio": list(solo_it.cod_ele.head(5))}
r["pedonale_osm_coperto_da_iternet_10m"] = round(cover(osm_ped, e, 10), 3)
# civici: SIT (7606 nel buffer, 2224 in Z2) contro Iter.net, stesso numero entro 25 m
sit = gpd.read_file(ROOT / "data/norm/sit_civici.gpkg").cx[Z[0]:Z[2], Z[1]:Z[3]]
num = lambda s: str(s).strip().lstrip("0").upper()
ic = collections.defaultdict(list)
for g, n in zip(c.geometry, c.civico.astype(str) + c.esponente.fillna("").astype(str)): ic[num(n)].append(g)
vic = lambda g, n: any(g.distance(h) <= 25 for h in ic.get(num(n), []))
tot = gpd.sjoin_nearest(sit, c[["geometry"]], distance_col="d") if False else None
r["civici"] = {"sit_z2": len(sit), "iternet_z2": len(c), "sit_con_pari_numero_iternet_25m": int(sum(vic(g, n + (e_ or "")) for g, n, e_ in zip(sit.geometry, sit.num_civico.astype(str), sit.esp_civico.fillna("")))),
               "nota": "il civico non è un ingresso: entrambe le fonti sono usate solo come origini"}
r["sintesi"] = ["Iter.net è veicolare: copre le carreggiate ma non i marciapiedi, gli attraversamenti, le scale e i cancelli. Non sostituisce OSM per il caso A.",
                "Utile come controllo di completezza della viabilità carrabile e come dato ufficiale per i civici (origine regionale).",
                "Non ha tag foot/access/sidewalk: non può dire se un tratto sia percorribile a piedi."]
json.dump(r, open(NET / "confronto_iternet.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(r, ensure_ascii=False, indent=1))
