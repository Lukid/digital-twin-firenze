"""T05: edifici e verde per Z2 (+500 m). Eseguire da build.sh. Nessuna ombra (T09).
Input: data/norm/{rt_unita_volumetriche,osm_pisa}.gpkg, rt_dsm2021_1m.tif, rt_dtm10_10m.tif, DBT10K (alberi 2010).
Output: data/norm/geometry/geometrie_z2.gpkg (buffer completo), geometry/{edifici,alberi}_z2.geojson (4326, solo Z2),
geometry/report_z2.json, geometry/sopralluogo_z2.json."""
import glob, json, math
from pathlib import Path
import numpy as np, geopandas as gpd, pandas as pd, rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject, Resampling
from pyproj import Transformer
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import Point, box, LineString
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
NORM, OUT = ROOT / "data/norm", ROOT / "geometry"
(NORM / "geometry").mkdir(exist_ok=True)
PAR = json.load(open(OUT / "parametri_chiome.json"))
CRS = 7791

# ---- parametri di metodo (tutti dichiarati nel report) ----
BUF = 500.0
MIN_AREA_CONF = 40.0      # sotto questa area il confronto DSM/UV non e' affidabile (audit edifici)
EROSIONE_M = 1.0          # erosione del poligono prima di leggere il DSM (bordi, grondaie, alberi adiacenti)
COV_UV_NUOVO = 0.30       # edificio OSM con copertura UV < 30% = candidato post-2010
SOGLIA_DH = 3.0           # scarto DSM-uv_av (dopo bias) segnalato: circa un piano (audit: 3,85 m per piano)
SOGLIA_VEG_M = 2.5        # nDSM minimo fuori dagli edifici per dire "vegetazione"
D_FUSIONE, D_CANDIDATO = 3.0, 6.0   # abbinamento alberi: fusione entro 3 m, candidato fino a 6 m (non fuso)
R_INDIZIO, N_MIN_INDIZIO = 2.5, 6   # indizio altezza DSM: raggio e minimo di pixel vegetazione
H_OSM_OK = (2.0, 40.0)

# ---- area ----
zone = json.load(open(ROOT / "docs/audit/ZONE.json"))["zone"]["Z2"]["bbox"]
tr = Transformer.from_crs(6706, CRS, always_xy=True)
xs, ys = zip(*[tr.transform(lon, lat) for lat in (zone[0], zone[2]) for lon in (zone[1], zone[3])])
Z2 = box(min(xs), min(ys), max(xs), max(ys))
Z2B = Z2.buffer(BUF, join_style=2)

# ---- raster ----
dsm_ds = rasterio.open(NORM / "rt_dsm2021_1m.tif")
dsm = dsm_ds.read(1).astype("float64"); dsm[dsm == dsm_ds.nodata] = np.nan
T = dsm_ds.transform
dtm = np.full(dsm.shape, -9999.0)
reproject(rasterio.open(NORM / "rt_dtm10_10m.tif").read(1), dtm, src_transform=rasterio.open(NORM / "rt_dtm10_10m.tif").transform,
          src_crs=CRS, src_nodata=-9999.0, dst_transform=T, dst_crs=CRS, dst_nodata=-9999.0, resampling=Resampling.bilinear)
bad = dtm == -9999.0
idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
dtm = np.where(bad, dtm[tuple(idx)], dtm)  # nodata DTM (0,5%): riempito col valore piu' vicino


def rc(x, y):
    r, c = rasterio.transform.rowcol(T, x, y)
    return np.clip(r, 0, dsm.shape[0] - 1), np.clip(c, 0, dsm.shape[1] - 1)


def pix(geom, erode=0.0):
    g = geom.buffer(-erode) if erode else geom
    if g.is_empty:
        g = geom
    m = geometry_mask([g], out_shape=dsm.shape, transform=T, invert=True)
    return m


# ---- edifici ----
uv = gpd.read_file(NORM / "rt_unita_volumetriche.gpkg").to_crs(CRS)
uv = uv[uv.intersects(Z2B)].copy()
osm_b = gpd.read_file(NORM / "osm_pisa.gpkg", layer="buildings").to_crs(CRS)
osm_b = osm_b[osm_b.intersects(Z2B)].copy()

# offset terreno: DTM10 vs uv_qs (misurata) sui volumi UV
c = uv.geometry.centroid
r, cc = rc(c.x.values, c.y.values)
res_g = uv.ground_elev_m.values - dtm[r, cc]
OFF_G = float(np.median(res_g))
SIG_G = float(1.4826 * np.median(np.abs(res_g - OFF_G)))
terr = dtm + OFF_G
print(f"terreno: offset DTM10->uv_qs {OFF_G:+.2f} m, sigma robusta {SIG_G:.2f} m, MAE {np.mean(np.abs(res_g-OFF_G)):.2f}")

# alberi (servono subito: vegetazione dentro i poligoni)
dbt = gpd.read_file(glob.glob(str(ROOT / "data/work/rt_dbt10k_pisa/**/060403_albero_3003.shp"), recursive=True)[0],
                    bbox=tuple(gpd.GeoSeries([Z2B], crs=CRS).to_crs(3003).total_bounds))
dbt = dbt.set_crs(3003, allow_override=True).to_crs(CRS)  # nessuno shift (ADR-T02 e pipeline/REPORT.md)
dbt = dbt[dbt.within(Z2B)].reset_index(drop=True)
pts = gpd.read_file(NORM / "osm_pisa.gpkg", layer="points").to_crs(CRS)
osm_t = pts[pts.kind == "natural=tree"]
osm_t = osm_t[osm_t.within(Z2B)].reset_index(drop=True)
tree_xy = np.vstack([np.c_[dbt.geometry.x, dbt.geometry.y], np.c_[osm_t.geometry.x, osm_t.geometry.y]])
tree_pts = [Point(p) for p in tree_xy]
tree_sidx = gpd.GeoSeries(tree_pts, crs=CRS).sindex


def veg_vicino(geom, m=2.0):
    return len(tree_sidx.query(geom.buffer(m), predicate="intersects")) > 0


# statistiche DSM per poligono
def dsm_stats(geom, area):
    ero = EROSIONE_M if area >= MIN_AREA_CONF else 0.0
    m = pix(geom, ero)
    v = dsm[m]; v = v[~np.isnan(v)]
    if len(v) < 6:
        return dict(dsm_n=len(v), dsm_med=np.nan, dsm_p10=np.nan, dsm_p90=np.nan, terr=np.nan)
    rr, c2 = np.where(m)
    return dict(dsm_n=len(v), dsm_med=float(np.median(v)), dsm_p10=float(np.percentile(v, 10)),
                dsm_p90=float(np.percentile(v, 90)), terr=float(np.mean(terr[rr, c2])))


S = pd.DataFrame([dsm_stats(g, a) for g, a in zip(uv.geometry, uv.area_m2)], index=uv.index)
uv = uv.join(S)
uv["veg_vicino"] = [veg_vicino(g) for g in uv.geometry]
uv["h_dsm"] = uv.dsm_med - uv.ground_elev_m           # altezza dal DSM sul suolo misurato
uv["dh"] = uv.h_dsm - uv.height_m
ok = (uv.area_m2 >= MIN_AREA_CONF) & uv.dh.notna() & ~uv.veg_vicino
BIAS = float(uv.dh[ok].median())
R10, R90 = [float(uv.dh[ok].quantile(q)) for q in (0.1, 0.9)]
HW_UV = (R90 - R10) / 2
print(f"calibrazione DSM-uv_av su {ok.sum()} volumi (>=40 m2, senza alberi entro 2 m): bias {BIAS:+.2f}, p10 {R10:+.2f}, p90 {R90:+.2f}")
uv["dh_corr"] = uv.dh - BIAS
conf = (uv.area_m2 >= MIN_AREA_CONF) & uv.dh.notna()
flag = np.full(len(uv), "", dtype=object)
flag[conf & (uv.dh_corr >= SOGLIA_DH) & ~uv.veg_vicino] = "dsm_piu_alto"
flag[conf & (uv.dh_corr <= -SOGLIA_DH) & ~uv.veg_vicino] = "dsm_piu_basso"
flag[conf & (uv.h_dsm < 1.0) & (uv.height_m >= 3.0)] = "demolizione_probabile"
flag[conf & uv.veg_vicino & (uv.dh_corr.abs() >= SOGLIA_DH)] = "scarto_con_vegetazione"
flag[~conf] = "non_confrontato"
uv["flag_dsm"] = flag

# ---- volumi misurati (UV) ----
HU = 0.5  # tolleranza nominale di restituzione 1:2000: ipotesi dichiarata, la fonte non fornisce incertezza
vol_uv = gpd.GeoDataFrame({
    "id": uv.id.values, "tipo": "volume_uv", "classe_h": "measured", "fonte": "uv_rt_2010",
    "z_base": uv.ground_elev_m.round(2).values, "z_base_cls": "measured",
    "h": uv.height_m.round(2).values, "h_min": (uv.height_m - HU).clip(lower=0.3).round(2).values,
    "h_max": (uv.height_m + HU).round(2).values,
    "h_basis": "uv_av; tolleranza +-0,5 m ipotesi (non dichiarata dalla fonte)",
    "area_m2": uv.area_m2.round(1).values, "anno": 2010,
    "dsm_dh": uv.dh_corr.round(2).values, "flag": uv.flag_dsm.values, "veg_vicino": uv.veg_vicino.values,
    "portico": "ignoto", "sospeso": "ignoto"}, geometry=uv.geometry.values, crs=CRS)

# ---- edifici OSM senza UV (post-2010) ----
uv_union = unary_union(uv.geometry.buffer(0.0).values)
osm_b["cov_uv"] = [g.intersection(uv_union).area / g.area if g.area > 0 else 0 for g in osm_b.geometry]
osm_b["stato_osm"] = np.where(osm_b.cov_uv >= 0.8, "con_uv", np.where(osm_b.cov_uv >= COV_UV_NUOVO, "parziale", "senza_uv"))
cand = osm_b[(osm_b.cov_uv < COV_UV_NUOVO)].copy()
cand["geom_nuova"] = [g.difference(uv_union) for g in cand.geometry]  # evita sovrapposizioni con volumi UV
rows = []
dsm_union_b = unary_union(list(uv.geometry.buffer(1.5)) + list(osm_b.geometry.buffer(1.5)))
for i, rw in cand.iterrows():
    g = rw.geom_nuova
    if g.is_empty:
        continue
    parts = [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.area >= 10.0]
    if not parts:
        continue
    g = unary_union(parts)
    a = g.area
    st = dsm_stats(g, a)
    vegf = veg_vicino(g, 2.0)
    rows.append((rw.id, g, a, st, vegf, rw.building, rw.height, rw.building_levels))
cal_hw = math.sqrt(HW_UV ** 2 + SIG_G ** 2)  # intervallo: scarto DSM-UV (ripulito) e errore del terreno da DTM10, in quadratura
der = []
for id_, g, a, st, vegf, btype, ohgt, olev in rows:
    kind = "copertura_osm" if btype == "roof" else "volume_derivato"
    if np.isnan(st["dsm_med"]):
        h = hmin = hmax = np.nan; fl = "dsm_insufficiente"
    else:
        h = st["dsm_med"] - st["terr"] - BIAS
        hw = cal_hw * (1.5 if vegf else 1.0)
        hmin, hmax = max(h - hw, 0.3), max(h + hw, 1.0)
        fl = "vegetazione_possibile" if vegf else ""
        if h < 0.3:
            fl = (fl + ",dsm_non_attendibile").strip(",")
        elif h < 2.5:
            fl = (fl + ",sotto_2_5m").strip(",")
        h = max(h, 0.3)
    der.append(dict(id=id_, tipo=kind, classe_h="derived", fonte="osm+dsm2021", z_base=None if np.isnan(st["terr"]) else round(st["terr"], 2),
                    z_base_cls="derived", h=None if np.isnan(h) else round(h, 2), h_min=None if np.isnan(h) else round(hmin, 2),
                    h_max=None if np.isnan(h) else round(hmax, 2),
                    h_basis=f"DSM2021 mediana (poligono eroso 1 m) - DTM10 calibrato su uv_qs - bias UV {BIAS:+.2f}; +-{cal_hw:.1f} m da scarto UV/DSM e terreno" + (" x1,5 (alberi entro 2 m)" if vegf else ""),
                    area_m2=round(a, 1), anno=2021, dsm_dh=None, flag=fl, veg_vicino=vegf,
                    portico="ignoto", sospeso="ignoto", osm_height=ohgt, osm_levels=olev, geometry=g))
vol_der = gpd.GeoDataFrame(der, geometry="geometry", crs=CRS) if der else None
# edifici senza altezza utilizzabile: restano nel layer con h nulla (altezza "ignota"), non spariscono
volumi = pd.concat([vol_uv, vol_der], ignore_index=True)
volumi["in_z2"] = volumi.geometry.intersects(Z2)

# ---- alberi: fusione per fonti ----
nd, no = len(dbt), len(osm_t)
A = tree_xy[:nd]; B = tree_xy[nd:]
tD, tO = cKDTree(A), cKDTree(B)
d_ab, j_ab = tO.query(A)   # per ogni DBT, OSM piu' vicino
d_ba, i_ba = tD.query(B)   # per ogni OSM, DBT piu' vicino
match, cand_m = {}, {}
for i in range(nd):
    j = j_ab[i]
    if i_ba[j] == i:  # vicini reciproci
        if d_ab[i] <= D_FUSIONE:
            match[i] = (j, float(d_ab[i]))
        elif d_ab[i] <= D_CANDIDATO:
            cand_m[i] = (j, float(d_ab[i]))
used_o = {j for j, _ in match.values()}
cand_o = {j: i for i, (j, _) in cand_m.items()}
# OSM-OSM molto vicini (possibili doppioni nella stessa fonte): solo segnalati
d_oo, _ = cKDTree(B).query(B, k=2) if no > 1 else (np.zeros((0, 2)), None)
oo_dup = set(np.where(d_oo[:, 1] < 1.0)[0]) if no > 1 else set()


def tags_of(r):
    t = r.tags
    return json.loads(t) if isinstance(t, str) else (t or {})


def num(s):
    try:
        return float(str(s).lower().replace("m", "").replace(",", ".").strip())
    except Exception:
        return None


def classe_da_h(h):
    s = PAR["soglie_classe_altezza_m"]
    return "piccolo" if h < s["piccolo"][1] else ("medio" if h < s["medio"][1] else "grande")


# vegetazione da DSM fuori dagli edifici
nd_dsm = dsm - terr
edmask = geometry_mask([dsm_union_b], out_shape=dsm.shape, transform=T, invert=True)
veg = (nd_dsm > SOGLIA_VEG_M) & ~edmask & ~np.isnan(dsm)
yy, xx = np.mgrid[0:dsm.shape[0], 0:dsm.shape[1]]


def indizio(x, y):
    r0, c0 = rc(x, y)
    k = int(math.ceil(R_INDIZIO / T.a))
    r1, r2, c1, c2 = max(r0 - k, 0), min(r0 + k + 1, dsm.shape[0]), max(c0 - k, 0), min(c0 + k + 1, dsm.shape[1])
    sub_v = veg[r1:r2, c1:c2]
    circ = (yy[r1:r2, c1:c2] - r0) ** 2 + (xx[r1:r2, c1:c2] - c0) ** 2 <= (R_INDIZIO / T.a) ** 2
    sel = sub_v & circ
    if sel.sum() < N_MIN_INDIZIO:
        return None, int(sel.sum())
    return float(np.percentile(nd_dsm[r1:r2, c1:c2][sel], 95)), int(sel.sum())


def intervallo(cls_name, key):
    p = PAR["classi"][cls_name][key]
    return p["min"], p["tipico"], p["max"]


alberi = []
for i in range(nd):
    alberi.append(dict(src="dbt", i=i, j=match[i][0] if i in match else None))
for j in range(no):
    if j not in used_o:
        alberi.append(dict(src="osm", i=None, j=j))
rows = []
for a in alberi:
    fonti, ids = [], {}
    if a["i"] is not None:
        r = dbt.iloc[a["i"]]; fonti.append("dbt10k_2010"); ids["dbt"] = r.albero_id; g = r.geometry; pid = f"tre_dbt_{r.albero_id}"
    if a["j"] is not None:
        r2 = osm_t.iloc[a["j"]]; fonti.append("osm"); ids["osm"] = r2.id
        if a["i"] is None:
            g = r2.geometry; pid = f"tre_osm_{r2.id.replace('nod_osm_', '')}"
    t = tags_of(r2) if a["j"] is not None else {}
    d_m = match[a["i"]][1] if a["i"] in match else None
    cand_id = None
    if a["i"] is not None and a["i"] in cand_m:
        cand_id = osm_t.iloc[cand_m[a["i"]][0]].id
    if a["i"] is None and a["j"] in cand_o:
        cand_id = dbt.iloc[cand_o[a["j"]]].albero_id
    x, y = g.x, g.y
    r0, c0 = rc(x, y)
    zb = float(terr[r0, c0])
    h_osm = num(t.get("height")) if t.get("height") else None
    h_osm_ok = h_osm is not None and H_OSM_OK[0] <= h_osm <= H_OSM_OK[1]
    hd, nveg = indizio(x, y)
    if h_osm_ok:
        hcls, hcl, h3, hb = classe_da_h(h_osm), "measured", (h_osm * 0.8, h_osm, h_osm * 1.2), "tag OSM height (non verificato), +-20%"
    elif hd is not None:
        hcls, hcl, hb = classe_da_h(hd), "derived", "DSM2021 - terreno (p95 entro 2,5 m, pixel vegetazione fuori edifici); +-(1,5 m + 10%)"
        h3 = (max(hd - 1.5 - 0.1 * hd, 2.0), hd, hd + 1.5 + 0.1 * hd)
    else:
        hcls, hcl, hb = "ignota", "estimated", "classe ignota: intervallo che copre tutte le classi"
        h3 = intervallo("ignota", "altezza_m")
    cd, ci, ct = (intervallo(hcls, k) for k in ("diametro_chioma_m", "altezza_imposta_m", "diametro_tronco_m"))
    # altezza d'imposta sempre sotto l'altezza totale
    ci = tuple(min(v, 0.7 * hh) for v, hh in zip(ci, h3))
    rows.append(dict(
        id=pid, fonti=",".join(fonti), n_fonti=len(fonti), id_dbt=ids.get("dbt"), id_osm=ids.get("osm"),
        d_fusione_m=None if d_m is None else round(d_m, 2), candidato_altra_fonte=cand_id,
        specie=t.get("species") or t.get("genus"), leaf_type=t.get("leaf_type"),
        z_base=round(zb, 2), z_base_cls="derived", z_base_unc=round(SIG_G, 2),
        classe=hcls, h_cls=hcl, h_min=round(h3[0], 2), h=round(h3[1], 2), h_max=round(h3[2], 2), h_basis=hb,
        dsm_indizio_m=None if hd is None else round(hd, 2),
        chioma_cls="estimated", chioma_d_min=cd[0], chioma_d=cd[1], chioma_d_max=cd[2],
        imposta_cls="estimated", imposta_min=round(ci[0], 2), imposta=round(ci[1], 2), imposta_max=round(ci[2], 2),
        tronco_d_cls="estimated", tronco_d_min=ct[0], tronco_d=ct[1], tronco_d_max=ct[2],
        doppione_osm=bool(a["j"] is not None and a["j"] in oo_dup), geometry=g))
al = gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS)
bld_all = unary_union(list(uv.geometry) + list(osm_b.geometry))
al["in_edificio"] = al.geometry.within(bld_all)
al["in_z2"] = al.geometry.within(Z2)

# vegetazione DSM senza albero puntuale
lab, n = ndimage.label(veg)
sizes = ndimage.sum(veg, lab, range(1, n + 1))
tree_tree = cKDTree(tree_xy) if len(tree_xy) else None
veg_rows = []
objs = ndimage.find_objects(lab)
for k, sl in enumerate(objs, start=1):
    if sizes[k - 1] < 20:
        continue
    m = lab[sl] == k
    rr, c2 = np.where(m); rr += sl[0].start; c2 += sl[1].start
    xs_, ys_ = rasterio.transform.xy(T, rr, c2)
    xs_, ys_ = np.array(xs_), np.array(ys_)
    dmin = float(tree_tree.query(np.c_[xs_, ys_])[0].min())
    h95 = float(np.percentile(nd_dsm[rr, c2], 95))
    veg_rows.append(dict(area_m2=float(sizes[k - 1]), h95=round(h95, 2), d_albero_min_m=round(dmin, 1),
                         geometry=Point(xs_.mean(), ys_.mean())))
vg = gpd.GeoDataFrame(veg_rows, geometry="geometry", crs=CRS)
vg["senza_albero"] = vg.d_albero_min_m > 5.0
vg["in_z2"] = vg.within(Z2)

# ---- salvataggi ----
gp = NORM / "geometry/geometrie_z2.gpkg"
if gp.exists():
    gp.unlink()
osm_b[["id", "cov_uv", "stato_osm", "geometry"]].to_file(gp, layer="osm_stato", driver="GPKG")
volumi.to_file(gp, layer="volumi", driver="GPKG")
al.to_file(gp, layer="alberi", driver="GPKG")
vg.to_file(gp, layer="vegetazione_dsm", driver="GPKG")


def export(gdf, name, cols, cls_map):
    g = gdf[gdf.in_z2].copy()
    g = g[cols + ["geometry"]].to_crs(4326)
    g["geometry"] = g.geometry.simplify(0.0, preserve_topology=True)
    js = json.loads(g.to_json(drop_id=True, na="null"))
    for f in js["features"]:
        f["properties"] = {k: v for k, v in f["properties"].items() if v is not None}
        f["properties"]["cls"] = cls_map
    js["conventions"] = {"crs": "EPSG:4326 (derivato da EPSG:7791 per il client web)", "unit": "m", "vertical_datum": "not_confirmed",
                         "nota": "z_base e h relativi al terreno; datum verticale non confermato; solo anteprima, non validato sul campo"}
    s = json.dumps(js, ensure_ascii=False, separators=(",", ":"))
    s = __import__("re").sub(r"(\d+\.\d{6})\d+", r"\1", s)
    (OUT / name).write_text(s)
    return len(js["features"]), len(s)


ecols = ["id", "tipo", "classe_h", "fonte", "z_base", "h", "h_min", "h_max", "area_m2", "anno", "flag", "portico", "sospeso"]
ecls = {"z_base": "measured|derived (vedi classe_h)", "h": "classe_h", "h_min": "classe_h", "h_max": "classe_h",
        "portico": "ignoto", "sospeso": "ignoto", "area_m2": "derived"}
acols = ["id", "fonti", "id_dbt", "id_osm", "classe", "h_cls", "z_base", "h", "h_min", "h_max", "chioma_d", "chioma_d_min", "chioma_d_max",
         "imposta", "imposta_min", "imposta_max", "tronco_d", "dsm_indizio_m", "in_edificio"]
acls = {"posizione": "measured", "z_base": "derived", "h": "h_cls", "chioma_d": "estimated", "imposta": "estimated", "tronco_d": "estimated",
        "dsm_indizio_m": "derived"}
ne, se_ = export(volumi, "edifici_z2.geojson", ecols, ecls)
na, sa = export(al, "alberi_z2.geojson", acols, acls)
print("export", ne, se_, na, sa)

# ---- report ----
vz = volumi[volumi.in_z2]; az = al[al.in_z2]
cnt = lambda s: {k: int(v) for k, v in s.value_counts().items()}
nx = vz[vz.tipo != "volume_uv"]
alto = az[az.h_cls != "estimated"]
rep = {
    "area": {"Z2_bbox_7791": [round(v, 2) for v in Z2.bounds], "buffer_m": BUF},
    "edifici_Z2": {
        "volumi_totali": len(vz), "measured_uv_2010": int((vz.tipo == "volume_uv").sum()),
        "derived_post2010_osm_dsm": int((vz.tipo == "volume_derivato").sum()), "coperture_osm_derived": int((vz.tipo == "copertura_osm").sum()),
        "derived_senza_altezza_dsm": int(nx.h.isna().sum()),
        "flag_derivati": cnt(nx.flag.replace("", "nessuno")),
        "flag_confronto_dsm_uv": cnt(vz[vz.tipo == "volume_uv"].flag.replace("", "ok")),
        "osm_stato_buffer": cnt(osm_b.stato_osm), "osm_stato_Z2": cnt(osm_b[osm_b.intersects(Z2)].stato_osm),
        "portico_sospeso": "ignoto su tutti i volumi (nessuna fonte)",
    },
    "edifici_buffer": {"volumi_totali": len(volumi), "measured": int((volumi.tipo == "volume_uv").sum()),
                       "derived": int((volumi.tipo != "volume_uv").sum())},
    "calibrazione": {"terreno_offset_dtm10_uvqs_m": round(OFF_G, 2), "terreno_sigma_m": round(SIG_G, 2),
                     "bias_dsm_meno_uv_av_m": round(BIAS, 2), "dh_p10": round(R10, 2), "dh_p90": round(R90, 2), "n_volumi": int(ok.sum()),
                     "intervallo_derivati_pm_m": round(cal_hw, 2), "soglia_flag_m": SOGLIA_DH},
    "dh_uv_Z2": {k: round(float(v), 2) for k, v in pd.to_numeric(vz[vz.tipo == "volume_uv"].dsm_dh, errors="coerce").dropna().describe(percentiles=[.1, .5, .9]).items()},
    "alberi_Z2": {
        "totale": len(az), "per_combinazione_fonti": cnt(az.fonti),
        "chioma_solo_stimata": int((az.chioma_cls == "estimated").sum()),
        "altezza_per_classe": cnt(az.h_cls), "classe_chioma": cnt(az.classe),
        "con_specie": int(az.specie.notna().sum()), "con_altezza_osm_plausibile": int((az.h_cls == "measured").sum()),
        "in_edificio_posizione_sospetta": int(az.in_edificio.sum()),
        "candidati_altra_fonte_non_fusi": int(az.candidato_altra_fonte.notna().sum()),
        "doppioni_osm_entro_1m": int(az.doppione_osm.sum()),
        "copernicus": "nessun oggetto: solo conteggi poligoni nei campioni dell'audit, geometrie non scaricate",
    },
    "alberi_buffer": {"totale": len(al), "per_combinazione_fonti": cnt(al.fonti),
                      "dbt_nel_buffer": nd, "osm_nel_buffer": no, "fusi": len(match), "candidati_3_6m": len(cand_m)},
    "regole": {"fusione": f"vicini reciproci entro {D_FUSIONE} m: un solo albero con entrambe le fonti; {D_FUSIONE}-{D_CANDIDATO} m: restano due alberi con candidato_altra_fonte; oltre: separati",
               "post2010": f"edificio OSM con copertura UV < {COV_UV_NUOVO:.0%}, geometria = OSM meno unione UV, parti < 10 m2 scartate",
               "pulizia_vegetazione": f"DSM mediana su poligono eroso {EROSIONE_M} m (non il massimo); alberi di qualunque fonte entro 2 m dal poligono: flag vegetazione_possibile e intervallo x1,5; altezza < 2,5 m flaggata",
               "vegetazione_dsm": f"nDSM > {SOGLIA_VEG_M} m fuori da UV e OSM bufferizzati 1,5 m; indizio altezza = p95 entro {R_INDIZIO} m, almeno {N_MIN_INDIZIO} pixel"},
    "vegetazione_dsm": {"cluster_ge_20px_Z2": int(vg.in_z2.sum()), "senza_albero_entro_5m_Z2": int((vg.in_z2 & vg.senza_albero).sum()),
                        "area_m2_senza_albero_Z2": round(float(vg[vg.in_z2 & vg.senza_albero].area_m2.sum()), 0)},
    "verifica_classi": {"alberi_con_altezza_da_osm_o_dsm": int(len(alto)),
                        "quota_sopra_10m_su_questi": round(float((alto.h > 10).mean()), 3) if len(alto) else None,
                        "riferimento_censimento_2017": 0.37},
}
(OUT / "report_z2.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))

# ---- sopralluogo: corridoio Pellico -> ingresso scuola Battisti (retta provvisoria, tracciato da fissare sul posto) ----
corr = LineString([(612589.5, 4840660.91), (613152.54, 4840302.55)]).buffer(60)
def dist_c(g): return float(g.distance(LineString([(612589.5, 4840660.91), (613152.54, 4840302.55)])))
lst = []
for _, r in az[az.in_z2 & az.geometry.intersects(corr)].iterrows():
    pr = 1 if r.fonti == "osm" else 2
    lst.append(dict(prio=pr, oggetto=r.id, tipo="albero", fonti=r.fonti, d_corridoio_m=round(dist_c(r.geometry), 1),
                    cosa="posizione, specie, altezza, diametro chioma, altezza d'imposta, trasparenza stagionale",
                    perche=f"altezza {r.h_cls}, chioma estimated (intervallo {r.chioma_d_min}-{r.chioma_d_max} m)"))
for _, r in vz[vz.in_z2 & vz.geometry.intersects(corr)].iterrows():
    f = r.flag
    if r.tipo != "volume_uv":
        lst.append(dict(prio=1, oggetto=r.id, tipo="edificio_" + r.tipo, d_corridoio_m=round(dist_c(r.geometry), 1), cosa="esistenza, altezza gronda/colmo, eventuale portico",
                        perche=f"post-2010, altezza derived {r.h}+-{(r.h_max - r.h_min) / 2 if pd.notna(r.h) else 'n.d.'} m {f}"))
    elif f in ("dsm_piu_alto", "dsm_piu_basso", "demolizione_probabile"):
        lst.append(dict(prio=1, oggetto=r.id, tipo="edificio_uv", d_corridoio_m=round(dist_c(r.geometry), 1), cosa="altezza attuale",
                        perche=f"scarto DSM-UV {r.dsm_dh} m ({f})"))
    elif r.h >= 9 and dist_c(r.geometry) <= 25:
        lst.append(dict(prio=2, oggetto=r.id, tipo="edificio_uv", d_corridoio_m=round(dist_c(r.geometry), 1),
                        cosa="altezza di controllo e portico/sporti al piano terra", perche="edificio alto vicino al percorso: portico ignoto"))
    elif dist_c(r.geometry) <= 15:
        lst.append(dict(prio=3, oggetto=r.id, tipo="edificio_uv", d_corridoio_m=round(dist_c(r.geometry), 1), cosa="portico o sporto sul fronte strada (si/no)",
                        perche="attributo ignoto"))
lst.sort(key=lambda d: (d["prio"], d["d_corridoio_m"]))
(OUT / "sopralluogo_z2.json").write_text(json.dumps({
    "nota": "corridoio provvisorio: retta fermata Pellico PI4390 - ingresso scuola Battisti, fascia 60 m; il tracciato reale si fissa al sopralluogo",
    "priorita": {"1": "alberi solo-OSM, post-2010, scarti DSM/UV grandi", "2": "alberi con 2010, edifici alti vicini", "3": "portici sul fronte strada"},
    "conteggio_per_priorita": {str(k): sum(1 for d in lst if d["prio"] == k) for k in (1, 2, 3)},
    "oggetti": lst}, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
print("sopralluogo", {k: sum(1 for d in lst if d["prio"] == k) for k in (1, 2, 3)})
