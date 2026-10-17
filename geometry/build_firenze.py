"""F05: edifici e verde di Firenze Novoli (riquadro FP + 700 m). Eseguire da build_firenze.sh. Nessuna ombra (F06-F10).
Script a parte rispetto a build_geometrie.py (Pisa): quello è uno script lineare con fonti e area scritte dentro (DSM 1 m, DTM 10 m
via WMS, alberi OSM/DBT) e non si può importare senza rieseguirlo; qui le fonti sono altre (LiDAR 0,5 m, censimento). Si riusano
parametri_chiome.json e la stessa forma degli output, in geometry/firenze_novoli/ per non collidere con Pisa.
Input (data/norm/firenze_novoli/): rt_uv_firenze_novoli, osm_firenze, fi_alberi, fi_dsm2023_0.5m, fi_dtm2023_0.5m.
Output: data/norm/firenze_novoli/geometry/geometrie_firenze_novoli.gpkg (non versionati),
geometry/firenze_novoli/{edifici,alberi}_fp.geojson (4326, solo FP) e report_firenze_novoli.json."""
import json, math, os, re, sys
from pathlib import Path
os.environ.setdefault("DT_AOI", "aoi_firenze_novoli")
import numpy as np, geopandas as gpd, pandas as pd, rasterio
from affine import Affine
from rasterio.features import geometry_mask, rasterize
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import lib  # AOI e cartella dati da DT_AOI (sola lettura)
from coordinate import arrotonda  # noqa: E402
assert lib.AOI["aoi_id"] == "aoi_firenze_novoli", "script solo per Firenze Novoli"
N = lib.NORM
OUT = ROOT / "geometry/firenze_novoli"
(N / "geometry").mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
PAR = json.load(open(ROOT / "geometry/parametri_chiome.json"))
FP, ALL = box(*lib.AOI["z2_en"]), box(*lib.AOI["buf_en"])
CRS = 7791

# ---- parametri di metodo (tutti dichiarati nel report) ----
MIN_AREA_CONF = 40.0      # sotto questa area il confronto nDSM/UV non è affidabile (audit F01)
N_MIN_CELLE = 20          # celle nDSM valide minime dentro l'impronta (0,25 m2 l'una)
EROSIONE_M = 1.0          # erosione dell'impronta prima di leggere l'nDSM
COV_UV_NUOVO = 0.30       # edificio OSM coperto da UV per meno del 30% = candidato post-2011
SOGLIA_DH = 3.0           # scarto nDSM-uv_av (dopo bias) segnalato: circa un piano
HU = 0.5                  # tolleranza UV: ipotesi, la fonte non dichiara incertezza
SOGLIA_VEG_M = 2.5        # CHM minimo per dire "chioma"
RMAX_CHIOMA = 7.5         # m: raggio massimo di una chioma (metà del massimo di parametri_chiome.json)
R_ALTEZZA = 3.0           # m: l'altezza è il p95 del CHM entro 3 m dal tronco, nelle celle dell'albero
N_MIN_CHIOMA = 12         # celle (3 m2) minime entro 3 m per dire "chioma misurata"
FRAC_EDIF_MAX = 0.5       # oltre metà della finestra 3 m sotto edificio il CHM non è dell'albero
HW_H_A, HW_H_B = 1.0, 0.1 # intervallo altezza misurata: +-(1 m + 10%), ipotesi (DTM sotto chioma, foglie)
HW_CHIOMA = 0.30          # intervallo diametro chioma misurata +-30% (x1,6 verso l'alto se confinante/vicina a edificio)
H_MAX_OK = 40.0
D_TRONCO_MAX = 1.5        # m: circonferenze oltre 4,7 m = dato anomalo
N_SPECIE = 30             # alberi misurati minimi per usare la statistica specie+classe nella stima

# ---- raster (float32, una copia sola ciascuno) ----
def leggi(p):
    a = rasterio.open(p).read(1)
    a[a == -9999.0] = np.nan
    return a
T = rasterio.open(N / "fi_dsm2023_0.5m.tif").transform
dsm, dtm = leggi(N / "fi_dsm2023_0.5m.tif"), leggi(N / "fi_dtm2023_0.5m.tif")
chm = dsm - dtm  # nDSM = CHM: stessa differenza, per edifici e per chiome
del dsm
H, W = chm.shape
CELLA = T.a


def finestra(g, pad=1):
    x0, y0, x1, y1 = g.bounds
    c0, c1 = max(int((x0 - T.c) // CELLA) - pad, 0), min(int((x1 - T.c) // CELLA) + pad + 1, W)
    r0, r1 = max(int((T.f - y1) // CELLA) - pad, 0), min(int((T.f - y0) // CELLA) + pad + 1, H)
    return slice(r0, r1), slice(c0, c1), T * Affine.translation(c0, r0)


def stats(geom, area):
    g = geom.buffer(-EROSIONE_M) if area >= MIN_AREA_CONF else geom
    if g.is_empty:
        g = geom
    rs, cs, t = finestra(g)
    sub = chm[rs, cs]
    if sub.size == 0:  # impronta fuori dal raster
        return dict(n=0, med=np.nan, p10=np.nan, p90=np.nan, terr=np.nan)
    m = geometry_mask([g], out_shape=sub.shape, transform=t, invert=True)
    v = sub[m]; v = v[~np.isnan(v)]
    if len(v) < 6:
        return dict(n=len(v), med=np.nan, p10=np.nan, p90=np.nan, terr=np.nan)
    return dict(n=len(v), med=float(np.median(v)), p10=float(np.percentile(v, 10)), p90=float(np.percentile(v, 90)),
                terr=float(np.nanmedian(dtm[rs, cs][m])))


# ---- alberi: posizioni (servono subito: vegetazione vicino agli edifici) ----
al0 = gpd.read_file(N / "fi_alberi.gpkg").reset_index(drop=True)
tx, ty = al0.geometry.x.values, al0.geometry.y.values
tr_ = np.clip(((T.f - ty) // CELLA).astype(int), 0, H - 1)
tc_ = np.clip(((tx - T.c) // CELLA).astype(int), 0, W - 1)
tree_sidx = al0.geometry.sindex

# ---- edifici ----
uv = gpd.read_file(N / "rt_uv_firenze_novoli.gpkg", layer="building_volume")
osm_b = gpd.read_file(N / "osm_firenze.gpkg", layer="buildings")
uv_union = unary_union(uv.geometry.buffer(0.0).values)
osm_union = unary_union(osm_b.geometry.buffer(0.0).values)
uv["osm_cov"] = [g.intersection(osm_union).area / g.area for g in uv.geometry]
S = pd.DataFrame([stats(g, a) for g, a in zip(uv.geometry, uv.area_m2)], index=uv.index)
uv = uv.join(S)
uv["veg_vicino"] = [len(tree_sidx.query(g.buffer(2.0), predicate="intersects")) > 0 for g in uv.geometry]
uv["dh"] = uv.med - uv.height_m
conf = (uv.area_m2 >= MIN_AREA_CONF) & uv.dh.notna() & (uv.n >= N_MIN_CELLE)
cal = conf & ~uv.veg_vicino
BIAS = float(uv.dh[cal].median())
R10, R90 = [float(uv.dh[cal].quantile(q)) for q in (0.1, 0.9)]
HW_UV = (R90 - R10) / 2  # include l'errore delle UV stesse: per l'altezza LiDAR è prudente
uv["dh_corr"] = uv.dh - BIAS
res_g = (uv.ground_elev_m - uv.terr).dropna()  # quota di spiccato UV contro DTM 2023: coerenza del datum
OFF_G = float(res_g.median()); SIG_G = float(1.4826 * (res_g - OFF_G).abs().median())
print(f"calibrazione nDSM-uv_av su {cal.sum()} impronte: bias {BIAS:+.2f}, p10 {R10:+.2f}, p90 {R90:+.2f}; uv_qs-DTM {OFF_G:+.2f} sigma {SIG_G:.2f}")
flag = np.full(len(uv), "", dtype=object)
big = conf & (uv.dh_corr.abs() >= SOGLIA_DH)
flag[big & (uv.dh_corr >= 0) & ~uv.veg_vicino] = "lidar_piu_alto"
flag[big & (uv.dh_corr < 0) & ~uv.veg_vicino] = "lidar_piu_basso"
flag[conf & (uv.med < 1.0) & (uv.height_m < 3.0)] = "lidar_sotto_1m"  # volume basso: nDSM indistinguibile dal terreno, resta uv_av
flag[conf & (uv.med < 1.0) & (uv.height_m >= 3.0)] = "demolizione_probabile"
flag[big & uv.veg_vicino] = "scarto_con_vegetazione"
flag[~conf] = "non_confrontato"
uv["flag"] = flag
usa_lidar = conf & uv.flag.isin(["", "lidar_piu_alto", "lidar_piu_basso"]).values
hL = uv.med.where(usa_lidar, uv.height_m)
concorde = usa_lidar & (uv.flag == "")  # nDSM e UV d'accordo: intervallo = fascia fra i due valori +- HU
lo = np.where(concorde, np.minimum(uv.height_m, uv.med) - HU, np.where(usa_lidar, uv.med - HW_UV, uv.height_m - HU))
hi = np.where(concorde, np.maximum(uv.height_m, uv.med) + HU, np.where(usa_lidar, uv.med + HW_UV, uv.height_m + HU))
vol_uv = gpd.GeoDataFrame({
    "id": uv.id.values, "tipo": "volume_uv", "classe_h": np.where(usa_lidar, "derived", "measured"),
    "fonte": np.where(usa_lidar, "lidar_2023+uv_rt_2011", "uv_rt_2011"),
    "z_base": uv.ground_elev_m.round(2).values, "z_base_cls": "measured",
    "h": hL.round(2).values, "h_min": np.maximum(lo, 0.3).round(2), "h_max": hi.round(2),
    "h_basis": np.where(usa_lidar, "nDSM 2023 mediana (impronta erosa 1 m); fascia UV/nDSM +-0,5 m se concordi, altrimenti +-metà p10-p90 dello scarto",
                        "uv_av 2011; tolleranza +-0,5 m ipotesi (non dichiarata dalla fonte)"),
    "h_uv": uv.height_m.round(2).values, "h_lidar": uv.med.round(2).values, "dh_corr": uv.dh_corr.round(2).values,
    "area_m2": uv.area_m2.round(1).values, "anno": np.where(usa_lidar, 2023, 2011), "flag": uv.flag.values,
    "presente_2023": uv.flag.values != "demolizione_probabile", "osm_cov": uv.osm_cov.round(2).values, "veg_vicino": uv.veg_vicino.values,
    "portico": "ignoto", "sospeso": "ignoto"}, geometry=uv.geometry.values, crs=CRS)

# edifici OSM con poca UV (nuovi dopo il 2011, o UV mancante): geometria = OSM meno UV, parti sotto 10 m2 scartate
osm_b["cov_uv"] = [g.intersection(uv_union).area / g.area for g in osm_b.geometry]
osm_b["stato_osm"] = np.where(osm_b.cov_uv >= 0.8, "con_uv", np.where(osm_b.cov_uv >= COV_UV_NUOVO, "parziale", "senza_uv"))
der = []
for _, rw in osm_b[osm_b.cov_uv < COV_UV_NUOVO].iterrows():
    g = rw.geometry.difference(uv_union)
    parts = [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.area >= 10.0]
    if not parts:
        continue
    g = unary_union(parts); st = stats(g, g.area)
    vegf = len(tree_sidx.query(g.buffer(2.0), predicate="intersects")) > 0
    if np.isnan(st["med"]):
        h = hmin = hmax = None; fl = "lidar_insufficiente"
    else:
        hw = HW_UV * (1.5 if vegf else 1.0)
        fl = "vegetazione_possibile" if vegf else ""
        if st["med"] < SOGLIA_VEG_M:
            fl = (fl + ",sotto_2_5m").strip(",")  # probabile baracca, pensilina o impronta senza edificio
        h = max(st["med"], 0.3); hmin, hmax = max(st["med"] - hw, 0.3), max(st["med"] + hw, 1.0)
    der.append(dict(id=rw.id, tipo="copertura_osm" if rw.building == "roof" else "volume_nuovo", classe_h="derived", fonte="osm+lidar_2023",
                    z_base=None if np.isnan(st["terr"]) else round(st["terr"], 2), z_base_cls="derived",
                    h=None if h is None else round(h, 2), h_min=None if h is None else round(hmin, 2), h_max=None if h is None else round(hmax, 2),
                    h_basis=f"nDSM 2023 mediana (parti OSM fuori da UV); +-{HW_UV:.1f} m da scarto nDSM/UV" + (" x1,5 (alberi entro 2 m)" if vegf else ""),
                    h_uv=None, h_lidar=None if h is None else round(st["med"], 2), dh_corr=None, area_m2=round(g.area, 1), anno=2023, flag=fl,
                    presente_2023=True, osm_cov=1.0, veg_vicino=bool(vegf), portico="ignoto", sospeso="ignoto", geometry=g))
volumi = pd.concat([vol_uv, gpd.GeoDataFrame(der, geometry="geometry", crs=CRS)], ignore_index=True)
volumi["in_fp"] = volumi.geometry.intersects(FP)

# ---- alberi: chiome da CHM ----
edif = rasterize([(g, 1) for g in list(uv.geometry.buffer(0.5)) + list(osm_b.geometry.buffer(0.5))], out_shape=(H, W), transform=T, dtype="uint8").astype(bool)
in_edif = edif[tr_, tc_]
frac_edif = ndimage.uniform_filter(edif.astype("float32"), size=int(2 * R_ALTEZZA / CELLA) + 1)[tr_, tc_]  # finestra quadrata 3 m di raggio
veg = (chm >= SOGLIA_VEG_M) & ~edif
# ogni cella di chioma va all'albero censito più vicino (Voronoi): le chiome vicine si dividono, l'unione non cambia.
# Gli alberi dentro edifici non fanno da seme: non tolgono celle ai vicini.
seme = ~in_edif
lab = np.zeros((H, W), dtype="int32")
lab[tr_[seme], tc_[seme]] = np.flatnonzero(seme) + 1
idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
vr, vc = np.nonzero(veg)
ir, ic = idx[0][vr, vc], idx[1][vr, vc]
del idx
d = np.hypot(vr - ir, vc - ic) * CELLA
own = lab[ir, ic] - 1
ok = d <= RMAX_CHIOMA
cv = chm[vr, vc]
cel = pd.DataFrame({"own": own[ok], "chm": cv[ok], "near": d[ok] <= R_ALTEZZA})
n_cel = cel.groupby("own").size()
nr = cel[cel.near].groupby("own").chm
n_near, h95, hmax_ = nr.size(), nr.quantile(0.95), nr.max()
al = al0.copy()
al["n_chioma"] = n_near.reindex(range(len(al))).fillna(0).astype(int).values
al["h_chm"] = h95.reindex(range(len(al))).values
al["h_chm_max"] = hmax_.reindex(range(len(al))).values
al["r_chioma"] = np.sqrt(n_cel.reindex(range(len(al))).fillna(0).values * CELLA ** 2 / math.pi)
al["in_edificio"], al["frac_edif_3m"] = in_edif, frac_edif.round(2)
dnn = cKDTree(np.c_[tx, ty]).query(np.c_[tx, ty], k=2)[0][:, 1]
al["d_vicino_m"] = dnn.round(2)
al["z_base"] = dtm[tr_, tc_].round(2)

# regole: misurata solo se l'albero non è dentro/sotto un edificio, ha celle di chioma e un'altezza plausibile
# CHM massimo entro 3 m (finestra quadrata, fuori edifici): distingue "nessuna chioma alta" (giovane, tolto) da "chioma troppo piccola o rubata"
k3 = int(2 * R_ALTEZZA / CELLA) + 1
al["chm_max_3m"] = ndimage.maximum_filter(np.where(edif | np.isnan(chm), 0, chm), size=k3)[tr_, tc_].round(2)
motivo = np.full(len(al), "", dtype=object)
motivo[al.n_chioma < N_MIN_CHIOMA] = "poche_celle_chioma"
motivo[(al.n_chioma < N_MIN_CHIOMA).values & (al.chm_max_3m < SOGLIA_VEG_M).values] = "sotto_2_5m"
motivo[(al.h_chm > H_MAX_OK).values] = "altezza_anomala"
motivo[frac_edif >= FRAC_EDIF_MAX] = "coperto_da_edificio"
motivo[in_edif] = "in_edificio"
al["motivo_stima"] = motivo
al["misurata"] = motivo == ""
al["vicino_edificio"] = (frac_edif > 0.05) & al.misurata
al["chioma_confinante"] = (dnn < 2 * al.r_chioma.values) & al.misurata
al["doppione_1m"] = dnn < 1.0

# classe da circonferenza (tronco = circ/pi): soglie a metà fra i diametri tipici di parametri_chiome.json
cl = PAR["classi"]
dt_ = al.CIRCONF_CM / math.pi / 100
anom = dt_ > D_TRONCO_MAX
al["circ_anomala"] = anom
dt_ = dt_.where((dt_ > 0) & ~anom)
s1 = (cl["piccolo"]["diametro_tronco_m"]["tipico"] + cl["medio"]["diametro_tronco_m"]["tipico"]) / 2
s2 = (cl["medio"]["diametro_tronco_m"]["tipico"] + cl["grande"]["diametro_tronco_m"]["tipico"]) / 2
al["classe"] = np.where(dt_.isna(), "ignota", np.where(dt_ < s1, "piccolo", np.where(dt_ < s2, "medio", "grande")))
al["tronco_d"] = dt_.round(3)
mis = al[al.misurata]
emp = {}  # specie + classe: p10/p50/p90 di h e diametro chioma sugli alberi misurati (se almeno N_SPECIE)
for (sp, c), g in mis.groupby(["SPECIE", "classe"]):
    if len(g) >= N_SPECIE and c != "ignota":
        emp[(sp, c)] = (len(g),) + tuple(np.percentile(g.h_chm, [10, 50, 90])) + tuple(np.percentile(2 * g.r_chioma, [10, 50, 90]))


def stima(r):
    """h e chioma stimati: statistica specie+classe se c'è, altrimenti classe di parametri_chiome.json."""
    e = emp.get((r.SPECIE, r.classe))
    if e:
        return (e[1], e[2], e[3]), (e[4], e[5], e[6]), f"specie+classe da {e[0]} alberi misurati (p10-p50-p90)"
    p = cl[r.classe]
    return tuple(p["altezza_m"][k] for k in ("min", "tipico", "max")), tuple(p["diametro_chioma_m"][k] for k in ("min", "tipico", "max")), "classe da circonferenza (parametri_chiome.json)"


rows = []
for r in al.itertuples():
    if r.misurata:
        hw = HW_H_A + HW_H_B * r.h_chm
        h3 = (max(r.h_chm - hw, 2.0), r.h_chm, r.h_chm + hw)
        dc = 2 * r.r_chioma; up = 1.6 if (r.chioma_confinante or r.vicino_edificio) else 1 + HW_CHIOMA
        c3 = (dc * (1 - HW_CHIOMA), dc, dc * up)
        hb, cb, hcl = "CHM 2023 p95 entro 3 m, celle dell'albero (Voronoi); +-(1 m + 10%) ipotesi", "area celle chioma dell'albero (CHM >= 2,5 m, fuori edifici, Voronoi), cerchio equivalente; +-30%", "derived"
    elif r.motivo_stima == "sotto_2_5m":  # nessuna cella sopra 2,5 m entro 3 m: albero giovane o tolto; chioma della classe più piccola
        h3, c3, hcl = (2.0, 2.5, 4.0), tuple(cl["piccolo"]["diametro_chioma_m"][k] for k in ("min", "tipico", "max")), "estimated"
        hb = cb = "stima: CHM sotto 2,5 m entro 3 m dal punto (albero giovane o tolto); altezza 2-4 m, chioma della classe piccola"
    else:
        h3, c3, b = stima(r); hcl = "estimated"
        hb, cb = f"stima: {b}; motivo {r.motivo_stima}", f"stima: {b}"
    h3 = tuple(max(v, 2.0) for v in h3)
    ci = tuple(min(v, 0.7 * hh) for v, hh in zip((cl[r.classe]["altezza_imposta_m"][k] for k in ("min", "tipico", "max")), h3))
    rows.append(dict(h_cls=hcl, h_min=round(h3[0], 2), h=round(h3[1], 2), h_max=round(h3[2], 2), h_basis=hb,
                     chioma_cls="derived" if r.misurata else "estimated", chioma_d_min=round(c3[0], 2), chioma_d=round(c3[1], 2),
                     chioma_d_max=round(c3[2], 2), chioma_basis=cb, imposta_min=round(ci[0], 2), imposta=round(ci[1], 2), imposta_max=round(ci[2], 2)))
al = pd.concat([al.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
al = gpd.GeoDataFrame(al, geometry="geometry", crs=CRS)
al["z_base_unc"] = round(SIG_G, 2)
al["in_fp"] = al.within(FP)
al["tronco_cls"] = np.where(al.tronco_d.notna(), "derived", "estimated")

# chiome senza albero censito (giardini privati, parchi, siepi, tetti non mappati): componenti non assegnate
veg_libera = np.zeros((H, W), dtype=bool)
veg_libera[vr[~ok], vc[~ok]] = True
lab2, n2 = ndimage.label(veg_libera, structure=np.ones((3, 3)))
sizes = ndimage.sum(veg_libera, lab2, range(1, n2 + 1))
vrows = []
for k, sl in enumerate(ndimage.find_objects(lab2), start=1):
    if sizes[k - 1] < 80:  # 20 m2
        continue
    m = lab2[sl] == k
    sub = chm[sl]
    gy, gx = np.gradient(np.nan_to_num(sub), CELLA)
    rr, cc = np.nonzero(m)
    vrows.append(dict(area_m2=float(sizes[k - 1] * CELLA ** 2), h95=round(float(np.percentile(sub[m], 95)), 2),
                      pendenza_med=round(float(np.median(np.hypot(gx, gy)[m])), 2),
                      geometry=Point(T.c + (cc.mean() + sl[1].start + 0.5) * CELLA, T.f - (rr.mean() + sl[0].start + 0.5) * CELLA)))
vg = gpd.GeoDataFrame(vrows, geometry="geometry", crs=CRS)
vg["liscia"] = vg.pendenza_med < 0.35   # tetti piani/falde: candidati edifici non mappati; chioma = rugosa
vg["in_fp"] = vg.within(FP)





# ---- salvataggi ----
gp = N / "geometry/geometrie_firenze_novoli.gpkg"
if gp.exists():
    gp.unlink()
osm_b[["id", "cov_uv", "stato_osm", "geometry"]].to_file(gp, layer="osm_stato", driver="GPKG")
volumi.to_file(gp, layer="volumi", driver="GPKG")
al.to_file(gp, layer="alberi", driver="GPKG")
vg.to_file(gp, layer="vegetazione_lidar", driver="GPKG")


def export(gdf, name, cols, cls_map):
    g = gdf[gdf.in_fp][cols + ["geometry"]].to_crs(4326)
    js = json.loads(g.to_json(drop_id=True, na="null"))
    for f in js["features"]:
        f["properties"] = {k: v for k, v in f["properties"].items() if v is not None}
        f["properties"] = json.loads(re.sub(r"(\d+\.\d{6})\d+", r"\1", json.dumps(f["properties"])))   # numeri delle proprietà a 6 decimali troncati, come prima
        f["properties"]["cls"] = cls_map
    js = arrotonda(js)   # coordinate D39
    js["conventions"] = {"crs": "EPSG:4326 (derivato da EPSG:7791 per il client web)", "unit": "m", "vertical_datum": "not_confirmed",
                         "nota": "z_base e h relativi al terreno; datum verticale non confermato; solo anteprima, non validato sul campo"}
    s = json.dumps(js, ensure_ascii=False, separators=(",", ":"))
    (OUT / name).write_text(s)
    return len(js["features"]), len(s)


ecols = ["id", "tipo", "classe_h", "fonte", "z_base", "h", "h_min", "h_max", "h_uv", "h_lidar", "area_m2", "anno", "flag", "presente_2023", "portico", "sospeso"]
ecls = {"z_base": "measured|derived (vedi classe_h)", "h": "classe_h", "h_min": "classe_h", "h_max": "classe_h", "h_uv": "measured",
        "h_lidar": "derived", "portico": "ignoto", "sospeso": "ignoto", "area_m2": "derived"}
acols = ["id", "SPECIE", "CIRCONF_CM", "h_cls", "chioma_cls", "z_base", "h", "h_min", "h_max", "chioma_d", "chioma_d_min", "chioma_d_max",
         "imposta", "imposta_min", "imposta_max", "tronco_d", "motivo_stima", "vicino_edificio", "chioma_confinante", "in_edificio"]
acls = {"posizione": "measured", "SPECIE": "measured", "CIRCONF_CM": "measured", "z_base": "derived", "h": "h_cls", "chioma_d": "chioma_cls",
        "imposta": "estimated", "tronco_d": "tronco_cls"}
ne, se_ = export(volumi, "edifici_fp.geojson", ecols, ecls)
na, sa = export(al, "alberi_fp.geojson", acols, acls)
print("export", ne, se_, na, sa)

# ---- report ----
cnt = lambda s: {k: int(x) for k, x in s.value_counts().items()}
vf, af, gf = volumi[volumi.in_fp], al[al.in_fp], vg[vg.in_fp]
uvf = vf[vf.tipo == "volume_uv"]; nvf = vf[vf.tipo != "volume_uv"]; uva = volumi[volumi.tipo == "volume_uv"]
nva = volumi[volumi.tipo != "volume_uv"]
dh = uv.loc[cal, "dh"]
area_pix = lambda m: round(float(m.sum()) * CELLA ** 2, 0)
own_area = n_cel.reindex(range(len(al))).fillna(0).values * CELLA ** 2   # m2 di chioma LiDAR assegnati a ogni albero
inside_fp = al.in_fp.values
rep = {
    "area": {"fp_bbox_7791": [round(x, 2) for x in FP.bounds], "allargata_bbox_7791": [round(x, 2) for x in ALL.bounds], "margine_m": lib.AOI["buffer_m"]},
    "edifici": {
        "fp": {"volumi": len(vf), "uv_2011": len(uvf), "nuovi_osm": int((nvf.tipo == "volume_nuovo").sum()), "coperture_osm": int((nvf.tipo == "copertura_osm").sum()),
               "classe_h": cnt(vf.classe_h), "flag_uv": cnt(uvf.flag.replace("", "ok")), "flag_nuovi": cnt(nvf.flag.replace("", "nessuno")),
               "senza_altezza": int(vf.h.isna().sum()), "non_presenti_2023": int((~vf.presente_2023).sum())},
        "allargata": {"volumi": len(volumi), "uv_2011": len(uva), "nuovi_osm": int((nva.tipo == "volume_nuovo").sum()), "coperture_osm": int((nva.tipo == "copertura_osm").sum()),
                      "classe_h": cnt(volumi.classe_h), "flag_uv": cnt(uva.flag.replace("", "ok")), "flag_nuovi": cnt(nva.flag.replace("", "nessuno")),
                      "senza_altezza": int(volumi.h.isna().sum()), "non_presenti_2023": int((~volumi.presente_2023).sum())},
        "osm_stato_allargata": cnt(osm_b.stato_osm),
        "nuovi_confermati_lidar_ge_2_5m": int(((nva.h_lidar >= SOGLIA_VEG_M)).sum()), "nuovi_sotto_2_5m_o_senza_lidar": int(((nva.h_lidar < SOGLIA_VEG_M) | nva.h_lidar.isna()).sum()),
        "uv_non_coperte_da_osm_osm_cov_lt_0_3": {"totale": int((uv.osm_cov < 0.3).sum()), "di_cui_demolizione_probabile": int(((uv.osm_cov < 0.3) & (uv.flag == "demolizione_probabile")).sum()),
                                                  "di_cui_nDSM_alto_ge_2_5m": int(((uv.osm_cov < 0.3) & (uv.med >= SOGLIA_VEG_M)).sum())},
        "demolizione_probabile_con_osm_cov_ge_0_8": int(((uv.flag == "demolizione_probabile") & (uv.osm_cov >= 0.8)).sum()),
        "calibrazione": {"n_impronte": int(cal.sum()), "bias_ndsm_meno_uv_av_m": round(BIAS, 2), "p10_m": round(R10, 2), "p90_m": round(R90, 2),
                         "mae_m": round(float(dh.abs().mean()), 2), "mediana_m": round(float(dh.median()), 2),
                         "intervallo_lidar_pm_m": round(HW_UV, 2), "soglia_flag_m": SOGLIA_DH},
        "datum_verticale": {"stato": "non_confermato", "uv_qs_meno_dtm_2023_mediana_m": round(OFF_G, 2), "sigma_robusta_m": round(SIG_G, 2),
                            "mae_m": round(float(res_g.abs().mean()), 2), "n": int(len(res_g))},
        "portico_sospeso": "ignoto su tutti i volumi (nessuna fonte)",
    },
    "alberi": {
        "fp": {"totale": len(af), "chioma_misurata": int(af.misurata.sum()), "chioma_stimata": int((~af.misurata).sum()), "motivo_stima": cnt(af[~af.misurata].motivo_stima),
               "stima_da_specie_classe": int((~af.misurata & af.h_basis.str.contains("specie\\+classe")).sum()), "vicino_edificio": int(af.vicino_edificio.sum()),
               "chioma_confinante": int(af.chioma_confinante.sum()), "doppioni_entro_1m": int(af.doppione_1m.sum()), "circ_anomala_o_nulla": int((af.classe == "ignota").sum())},
        "allargata": {"totale": len(al), "chioma_misurata": int(al.misurata.sum()), "chioma_stimata": int((~al.misurata).sum()), "motivo_stima": cnt(al[~al.misurata].motivo_stima),
                      "stima_da_specie_classe": int((~al.misurata & al.h_basis.str.contains("specie\\+classe")).sum()), "vicino_edificio": int(al.vicino_edificio.sum()),
                      "chioma_confinante": int(al.chioma_confinante.sum()), "doppioni_entro_1m": int(al.doppione_1m.sum()), "circ_anomala": int(al.circ_anomala.sum()),
                      "circ_nulla_o_anomala_classe_ignota": int((al.classe == "ignota").sum())},
        "classe_circonferenza_fp": cnt(af.classe),
        "altezza_misurata_fp_p10_p50_p90_m": [round(float(x), 1) for x in np.percentile(af[af.misurata].h, [10, 50, 90])],
        "diametro_chioma_misurata_fp_p10_p50_p90_m": [round(float(x), 1) for x in np.percentile(af[af.misurata].chioma_d, [10, 50, 90])],
        "area_chioma_lidar_allargata_m2": {"totale_ge_2_5m_fuori_edifici": area_pix(veg), "assegnata_ad_alberi_misurati": round(float(own_area[al.misurata.values].sum()), 0),
                                           "assegnata_ad_alberi_stimati": round(float(own_area[~al.misurata.values].sum()), 0), "senza_albero_censito": round(float(veg_libera.sum()) * CELLA ** 2, 0)},
        "specie_classe_empiriche": len(emp),
        "vegetazione_senza_albero": {"cluster_ge_20m2_fp": int(len(gf)), "area_m2_fp": round(float(gf.area_m2.sum()), 0), "di_cui_lisci_candidati_edifici_fp": int(gf.liscia.sum()),
                                     "cluster_allargata": int(len(vg)), "area_m2_allargata": round(float(vg.area_m2.sum()), 0)},
    },
    "regole": {
        "altezza_edificio": f"nDSM 2023 (DSM-DTM) mediana sull'impronta UV erosa {EROSIONE_M} m, se area >= {MIN_AREA_CONF:.0f} m2 e >= {N_MIN_CELLE} celle; altrimenti uv_av 2011. Con vegetazione vicina e scarto grande, o demolizione probabile, resta uv_av",
        "flag": f"scarto nDSM-uv_av dopo bias >= {SOGLIA_DH} m: lidar_piu_alto/basso; nDSM < 1 m con uv_av >= 3 m: demolizione_probabile (presente_2023 falso); alberi entro 2 m: scarto_con_vegetazione",
        "edifici_nuovi": f"edificio OSM con UV < {COV_UV_NUOVO:.0%}: geometria = OSM meno UV; altezza nDSM mediana; sotto {SOGLIA_VEG_M} m flag sotto_2_5m",
        "alberi_misurati": f"posizione = censimento; celle CHM >= {SOGLIA_VEG_M} m fuori edifici assegnate all'albero più vicino entro {RMAX_CHIOMA} m (Voronoi, alberi dentro edifici esclusi); altezza = p95 entro {R_ALTEZZA} m; diametro = cerchio equivalente dell'area celle",
        "alberi_stimati": f"in_edificio; >= {FRAC_EDIF_MAX:.0%} della finestra 3 m sotto edificio; < {N_MIN_CHIOMA} celle di chioma entro 3 m; altezza > {H_MAX_OK:.0f} m. Classe da circonferenza, valori da specie+classe (>= {N_SPECIE} misurati) o da parametri_chiome.json",
        "intervalli": f"altezza misurata +-({HW_H_A} m + {HW_H_B:.0%}), diametro +-{HW_CHIOMA:.0%} (ipotesi, non tarati su misure indipendenti); imposta sempre estimated"},
}
(OUT / "report_firenze_novoli.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
