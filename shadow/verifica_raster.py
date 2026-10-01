"""T09: verifica indipendente del motore vettoriale con un secondo metodo, raster: ray casting da ogni cella di suolo verso il sole su una
griglia di altezze costruita dagli stessi volumi (e dalle chiome come colonne [quota inferiore, quota superiore]). Non condivide il codice
dell'unione di poligoni: confronta la frazione di suolo in ombra su una finestra di Z2. Con il DSM 2021 (informativo) un terzo numero.
Uso: pipeline/.venv/bin/python shadow/verifica_raster.py  -> shadow/out/verifica_raster.json"""
import json, math, pathlib, sys
import numpy as np, shapely
from shapely.geometry import box
import rasterio
from rasterio import features
from rasterio.windows import from_bounds
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ombre as O

ROOT = O.ROOT
FINESTRA = (612950.0, 4840430.0, 613200.0, 4840680.0)   # 250 x 250 m in Z2, vicino alla scuola Battisti (fine di R01)
CELLA, PASSO_RAGGIO = 0.5, 0.25
LAT, LON = 43.7152, 10.4007


def griglie(win, margine, cella):
    x0, y0, x1, y1 = win[0] - margine, win[1] - margine, win[2] + margine, win[3] + margine
    nx, ny = int(round((x1 - x0) / cella)), int(round((y1 - y0) / cella))
    tr = rasterio.transform.from_origin(x0, y1, cella, cella)
    return (x0, y0, x1, y1), nx, ny, tr


def altezze_edifici(v, col, ext, nx, ny, tr):
    sub = v[shapely.intersects(v.geometry.values, box(*ext))].sort_values(col)       # i più alti scrivono per ultimi: vince il massimo
    sh = [(g, float(h)) for g, h in zip(sub.geometry.values, np.clip(sub[col].values.astype(float), 0.3, None))]
    return features.rasterize(sh, out_shape=(ny, nx), transform=tr, fill=0.0, dtype="float32") if sh else np.zeros((ny, nx), "float32")


def colonne_chiome(a, caso, ext, nx, ny, x0, y1, cella):
    """Per ogni cella [CL, CH]: quota minima e massima occupata da un ellissoide (unione verticale approssimata per chiome sovrapposte)."""
    H, D, imp = {"min": ("h_min", "chioma_d_min", "imposta_max"), "tipico": ("h", "chioma_d", "imposta"), "max": ("h_max", "chioma_d_max", "imposta_min")}[caso]
    CL, CH = np.full((ny, nx), np.inf, "float32"), np.full((ny, nx), -np.inf, "float32")
    for g, h, d, i in zip(a.geometry.values, a[H].values, a[D].values, a[imp].values):
        i = min(i, 0.5 * h); r, zc, c = d / 2, (h + i) / 2, (h - i) / 2
        if not (ext[0] - r <= g.x <= ext[2] + r and ext[1] - r <= g.y <= ext[3] + r): continue
        c0, c1 = int((g.x - r - x0) / cella), int((g.x + r - x0) / cella) + 1; r0, r1 = int((y1 - g.y - r) / cella), int((y1 - g.y + r) / cella) + 1
        c0, r0, c1, r1 = max(c0, 0), max(r0, 0), min(c1, nx), min(r1, ny)
        if c0 >= c1 or r0 >= r1: continue
        X = x0 + (np.arange(c0, c1) + 0.5) * cella; Y = y1 - (np.arange(r0, r1) + 0.5) * cella
        rho2 = (X[None, :] - g.x) ** 2 + (Y[:, None] - g.y) ** 2; m = rho2 < r * r
        half = c * np.sqrt(np.clip(1 - rho2 / (r * r), 0, 1))
        sl = (slice(r0, r1), slice(c0, c1))
        CL[sl] = np.where(m, np.minimum(CL[sl], zc - half), CL[sl]); CH[sl] = np.where(m, np.maximum(CH[sl], zc + half), CH[sl])
    return CL, CH


def ray_cast(xs, ys, az, el, sample, rmax, passo=PASSO_RAGGIO):
    """True dove il raggio verso il sole è bloccato. sample(x, y, z) -> bool array, per i punti del raggio."""
    ombra = np.zeros(len(xs), bool); dx, dy = math.sin(math.radians(az)), math.cos(math.radians(az)); t = math.tan(math.radians(el))
    for k in range(1, int(rmax / passo) + 1):
        r = k * passo; idx = np.nonzero(~ombra)[0]
        if len(idx) == 0: break
        ombra[idx] |= sample(xs[idx] + r * dx, ys[idx] + r * dy, r * t)
    return ombra


def verifica(finestra=FINESTRA, istanti=(("2026-06-21", "08:30"), ("2026-09-15", "08:00"), ("2026-09-15", "10:00"), ("2026-09-15", "13:00"), ("2026-10-01", "16:30"))):
    D = O.dati(); v, a = D["v"], D["a"]
    hmax = float(v.h_max.max()); win = box(*finestra)
    out = {"finestra_7791": list(finestra), "cella_m": CELLA, "passo_raggio_m": PASSO_RAGGIO, "risultati": []}
    # Receivers: celle di suolo (fuori dai footprint) al centro delle celle della finestra
    nxw, nyw = int(round((finestra[2] - finestra[0]) / CELLA)), int(round((finestra[3] - finestra[1]) / CELLA))
    X = finestra[0] + (np.arange(nxw) + 0.5) * CELLA; Y = finestra[3] - (np.arange(nyw) + 0.5) * CELLA
    XX, YY = np.meshgrid(X, Y); xs, ys = XX.ravel(), YY.ravel()
    occ = shapely.union_all(v.geometry.values[shapely.intersects(v.geometry.values, win)])
    suolo = ~shapely.contains_xy(occ, xs, ys); xs, ys = xs[suolo], ys[suolo]
    area_suolo_vett = win.difference(occ).area
    out["celle_suolo"] = int(len(xs)); out["edifici_in_finestra"] = int(shapely.intersects(v.geometry.values, win).sum())
    out["alberi_in_finestra"] = int(shapely.contains_xy(win.buffer(10), a.geometry.x.values, a.geometry.y.values).sum())
    # griglia di altezze con margine pari alla portata massima dell'ombra a 10 gradi di elevazione
    marg = 160.0
    ext, nx, ny, tr = griglie(finestra, marg, CELLA); x0, y1 = ext[0], ext[3]
    def idx(x, y): return np.clip(((y1 - y) / CELLA).astype(int), 0, ny - 1), np.clip(((x - x0) / CELLA).astype(int), 0, nx - 1)
    Hb = {c: altezze_edifici(v, col, ext, nx, ny, tr) for c, col in (("h", "h"), ("h_min", "h_min"), ("h_max", "h_max"))}
    CHI = {c: colonne_chiome(a, c, ext, nx, ny, x0, y1, CELLA) for c in ("min", "tipico", "max")}
    for data, hhmm in istanti:
        t = O.locale_a_utc(data, hhmm); az, el = O.sole(t, LAT, LON)
        rmax = min(marg - 5, 38.0 / math.tan(math.radians(el)))
        for nome, col, chi in (("edifici", "h", None), ("edifici_h_min", "h_min", None), ("edifici_h_max", "h_max", None), ("edifici_alberi_tipico", "h", "tipico"), ("edifici_alberi_max", "h", "max")):
            H = Hb[col]
            def sample(x, y, z, H=H, chi=chi):
                r, c = idx(x, y); b = z < H[r, c]
                if chi: CL, CH = CHI[chi]; b |= (z >= CL[r, c]) & (z <= CH[r, c])
                return b
            ras = ray_cast(xs, ys, az, el, sample, rmax)
            caso = {"edifici": "base", "edifici_h_min": "base_h_min", "edifici_h_max": "base_h_max", "edifici_alberi_tipico": "alberi_tipico", "edifici_alberi_max": "alberi_max"}[nome]
            st, _, _, U = O.ombra_a_istante(O.scena_caso(caso), t, LAT, LON, finestra=win.buffer(rmax + 5))
            vet_cells = float(shapely.contains_xy(U, xs, ys).mean())                         # stesse celle di suolo, test punto-in-poligono
            vet_area = float(U.intersection(win).difference(occ).area / area_suolo_vett)   # frazione di area esatta
            out["risultati"].append({"data": data, "ora_locale": hhmm, "azimut_deg": round(az, 2), "elevazione_deg": round(el, 2), "caso": caso,
                                     "frazione_raster": round(float(ras.mean()), 4), "frazione_vettoriale_area": round(vet_area, 4), "frazione_vettoriale_celle": round(vet_cells, 4),
                                     "scarto_raster_vs_vettoriale_area": round(float(ras.mean()) - vet_area, 4), "celle_discordanti": round(float((ras != shapely.contains_xy(U, xs, ys)).mean()), 4)})
            print("  ", out["risultati"][-1], flush=True)
    d = [abs(r["scarto_raster_vs_vettoriale_area"]) for r in out["risultati"]]
    out["scarto_assoluto_max"] = round(max(d), 4); out["scarto_assoluto_medio"] = round(float(np.mean(d)), 4)
    out["dsm"] = verifica_dsm(finestra, xs, ys, istanti, out, win, occ)
    return out


def verifica_dsm(finestra, xs, ys, istanti, out, win, occ):
    """Informativo: ray casting sul DSM 2021 (1 m). Include alberi, auto, pensiline e bias del DSM (+0,47 m rispetto a uv_av): non è un riferimento."""
    import geopandas as gpd
    gv = gpd.read_file(O.GPKG, layer="vegetazione_dsm")
    veg = shapely.union_all(gv.geometry.values[shapely.intersects(gv.geometry.values, win.buffer(5))])
    marg = 160.0; ext = (finestra[0] - marg, finestra[1] - marg, finestra[2] + marg, finestra[3] + marg)
    with rasterio.open(ROOT / "data/norm/rt_dsm2021_1m.tif") as r:
        w = from_bounds(*ext, transform=r.transform); arr = r.read(1, window=w, boundless=True, fill_value=np.nan).astype("float32"); tr = r.window_transform(w)
    arr = np.where(np.isfinite(arr), arr, np.nanmedian(arr)); ny, nx = arr.shape; x0, y1 = tr.c, tr.f; c = abs(tr.a)
    sel = ~shapely.contains_xy(veg, xs, ys) if not veg.is_empty else np.ones(len(xs), bool)      # suolo nudo: fuori da chiome e volumi
    xr, yr = xs[sel], ys[sel]
    def at(x, y): return np.clip(((y1 - y) / c).astype(int), 0, ny - 1), np.clip(((x - x0) / c).astype(int), 0, nx - 1)
    rr, cc = at(xr, yr); z0 = arr[rr, cc]; res = []
    for data, hhmm in istanti:
        t = O.locale_a_utc(data, hhmm); az, el = O.sole(t, LAT, LON); rmax = min(marg - 5, 38 / math.tan(math.radians(el)))
        ombra = np.zeros(len(xr), bool); dx, dy = math.sin(math.radians(az)), math.cos(math.radians(az)); tt = math.tan(math.radians(el))
        for k in range(1, int(rmax / 0.5) + 1):
            i = np.nonzero(~ombra)[0]
            if not len(i): break
            ry, cx = at(xr[i] + k * 0.5 * dx, yr[i] + k * 0.5 * dy); ombra[i] |= arr[ry, cx] > z0[i] + k * 0.5 * tt + 0.3   # tolleranza 0,3 m sul rumore del DSM
        # confronto con il vettoriale "edifici + alberi tipico" e "edifici" sullo stesso insieme di celle
        f = {}
        for caso in ("base", "alberi_tipico", "alberi_max"):
            st, _, _, U = O.ombra_a_istante(O.scena_caso(caso), t, LAT, LON, finestra=win.buffer(rmax + 5)); f[caso] = round(float(shapely.contains_xy(U, xr, yr).mean()), 4)
        res.append({"data": data, "ora_locale": hhmm, "frazione_dsm": round(float(ombra.mean()), 4), "vettoriale_edifici": f["base"], "vettoriale_alberi_tipico": f["alberi_tipico"], "vettoriale_alberi_max": f["alberi_max"]})
        print("   DSM", res[-1], flush=True)
    return {"celle": int(len(xr)), "tolleranza_m": 0.3, "nota": "informativo: il DSM include alberi, veicoli, bias +0,47 m e terreno non piano; non è un riferimento per gli edifici", "risultati": res}


if __name__ == "__main__":
    o = verifica(); p = pathlib.Path(__file__).resolve().parent / "out" / "verifica_raster.json"; p.write_text(json.dumps(o, ensure_ascii=False, indent=1))
    print("scarto assoluto medio/max:", o["scarto_assoluto_medio"], o["scarto_assoluto_max"])
