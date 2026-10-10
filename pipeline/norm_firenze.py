"""F03: normalizzazione di aoi_firenze_novoli in data/norm/firenze_novoli/ (EPSG:7791 E,N, 0,01 m, classi per attributo in 'cls') e report di copertura.
Riusa le funzioni di Pisa (normalize.norm_osm, norm_uv, norm_gtfs, finish). Uso: norm_firenze.py [lavoro ...] | report   (senza argomenti: tutti i lavori, poi il report)"""
import os, re, sys, json, math, pathlib
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare lib
import numpy as np, geopandas as gpd, pyogrio, rasterio, shapely
from rasterio.merge import merge
import lib
from lib import AOI, ROOT, NORM, SNAP
from normalize import finish, raw, sha, norm_osm, norm_uv, norm_gtfs, M, D
BUF, FP = AOI["buf_en"], shapely.box(*AOI["z2_en"])

def leggi(slug, pat, crs, enc=None):
    """Vettoriale (zip o file) nel CRS dichiarato dalla fonte, convertito in EPSG:7791 (come a Pisa: nessuno shift di datum)."""
    f = raw(slug, pat)[0]; p = f"/vsizip/{f}" if f.suffix == ".zip" else str(f)
    g = pyogrio.read_dataframe(p, **({"encoding": enc} if enc else {}))
    g = g.rename(columns={"id": "fid_src", "ID": "id_orig"})      # 'id' e 'ID' collidono in GeoPackage e 'id' è nostro
    for c in [c for c in g.columns if str(g[c].dtype) in ("object", "str", "string")]: g[c] = g[c].astype(str).str.strip().replace({"None": None, "nan": None})
    return g.set_crs(crs, allow_override=True).to_crs(7791)

def scrivi(g, slug, source_id, layer, idcol, prefix, rango=None, out=None, cls_extra=None, low=False):
    """ID = prefisso + chiave originaria (con rango spaziale se la fonte non ha una chiave unica); attributi misurati, derivati dichiarati in cls_extra."""
    if rango:   # chiave di contenuto: codice + ordine spaziale nel codice (la fonte non ha ID univoco)
        o = g.assign(x=g.geometry.centroid.x, y=g.geometry.centroid.y).sort_values(["x", "y"]); g["_n"] = o.groupby(rango).cumcount().reindex(g.index)
        g["id"] = prefix + g[idcol].astype(str) + "_" + g["_n"].astype(str); g = g.drop(columns="_n")
    else: g["id"] = prefix + g[idcol].astype(str)
    g["id"] = g["id"].map(lambda s: re.sub(r"[^A-Za-z0-9_.-]", "_", s.lower() if low else s))   # ID ammessi dallo schema
    attrs = [c for c in g.columns if c not in ("id", "geometry")]
    finish(g[["id"] + attrs + ["geometry"]], source_id, sha(slug), {**{c: M for c in attrs}, **(cls_extra or {})}, out or f"{slug}.gpkg", layer)

def lidar(slug, out):
    """Mosaico delle tessere ASCII ritagliato su riquadro + margine, sul reticolo da 0,5 m delle tessere, GeoTIFF float32 EPSG:7791."""
    srcs = [rasterio.open(f) for f in raw(slug, "*.ASC")]
    b = (math.floor(BUF[0] * 2) / 2, math.floor(BUF[1] * 2) / 2, math.ceil(BUF[2] * 2) / 2, math.ceil(BUF[3] * 2) / 2)
    a, tr = merge(srcs, bounds=b, res=0.5, nodata=-9999.0); a = a[0].astype("float32")
    ok = a != -9999.0
    with rasterio.open(NORM / out, "w", driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype="float32", crs="EPSG:7791", transform=tr,
                       nodata=-9999.0, compress="deflate", predictor=3, tiled=True) as o: o.write(a, 1)
    st = {"file": out, "tessere": len(srcs), "shape": list(a.shape), "res_m": 0.5, "nodata_pct": round(float((~ok).mean() * 100), 3),
          "min": round(float(a[ok].min()), 2), "max": round(float(a[ok].max()), 2), "mean": round(float(a[ok].mean()), 2), "bounds": list(b)}
    print("  ", st); json.dump(st, open(NORM / (out[:-4] + ".stats.json"), "w"))

def cm():
    (NORM / "cm_edscol_firenze.gpkg").unlink(missing_ok=True)
    ed = leggi("cm_edscol_firenze", "form_ed_scolastici.zip", 3003); ac = leggi("cm_edscol_firenze", "form_ed_scolastici_accessi.zip", 3003)
    scrivi(ed, "cm_edscol_firenze", "src_cm_edscol_firenze", "edifici_scolastici", "COD_MECCAN", "bld_cm_", rango="COD_MECCAN", out="cm_edscol_firenze.gpkg")
    # secondo layer nello stesso GeoPackage: finish riscrive il file, quindi si accoda con pyogrio
    p = NORM / "cm_edscol_firenze.gpkg"; ac["id"] = "acc_cm_" + ac["CODICE"].astype(str)
    o = ac.assign(x=ac.geometry.x, y=ac.geometry.y).sort_values(["x", "y"]); ac["id"] += "_" + o.groupby("CODICE").cumcount().reindex(ac.index).astype(str)
    attrs = [c for c in ac.columns if c not in ("id", "geometry")]; ac = ac[["id"] + attrs + ["geometry"]].copy()
    ac["source_id"], ac["snapshot_id"] = "src_cm_edscol_firenze", sha("cm_edscol_firenze"); ac["cls"] = json.dumps({**{c: M for c in attrs}, "geometry": M}, sort_keys=True)
    ac["geometry"] = shapely.set_precision(ac.geometry.values, 0.01); ac = ac[ac.geometry.intersects(shapely.box(*BUF))]
    assert ac["id"].is_unique; ac.set_crs(7791, allow_override=True).to_file(p, layer="accessi", driver="GPKG", engine="pyogrio", mode="a"); print(f"  {p.name}:accessi {len(ac)} oggetti")

def catasto():
    """Particelle e fogli dell'Agenzia delle Entrate. Dal riferimento D612_0042B0.123: comune, foglio (4 cifre), allegato e sviluppo (0 = nessuno), particella dopo il punto."""
    def parti(g, ref):
        r = g[ref]
        g["foglio"] = r.str.slice(5, 9).astype(int)
        g["allegato"] = r.str.slice(9, 10).replace("0", None)
        g["sviluppo"] = r.str.slice(10, 11).replace("0", None)
        g["foglio_etichetta"] = g.foglio.astype(str) + g.allegato.fillna("") + g.sviluppo.fillna("")   # come il LABEL del foglio: 42B, 43
        return g
    f = parti(leggi("fi_catasto", "fogli.gml", 6706), "NATIONALCADASTRALZONINGREFERENCE")
    assert (f.foglio_etichetta == f.LABEL).all(), f[f.foglio_etichetta != f.LABEL][["LABEL", "NATIONALCADASTRALZONINGREFERENCE"]]
    D_ = {c: D for c in ("foglio", "allegato", "sviluppo", "foglio_etichetta")}
    scrivi(f.drop(columns=["gml_id"]), "fi_catasto", "src_fi_catasto", "fogli", "NATIONALCADASTRALZONINGREFERENCE", "fgl_fi_", out="fi_catasto_fogli.gpkg", cls_extra=D_)
    p = parti(leggi("fi_catasto", "particelle.gml", 6706), "NATIONALCADASTRALREFERENCE")
    p["particella"] = p.NATIONALCADASTRALREFERENCE.str.split(".").str[1]
    p["tipo"] = np.select([p.LABEL.str.startswith("STRADA"), p.LABEL.str.startswith("ACQUA")], ["strada", "acqua"], "particella")
    assert (p.particella == p.LABEL).all() and p.foglio_etichetta.isin(f.foglio_etichetta).all()
    scrivi(p.drop(columns=["gml_id"]), "fi_catasto", "src_fi_catasto", "particelle", "NATIONALCADASTRALREFERENCE", "cat_fi_", out="fi_catasto_particelle.gpkg",
           cls_extra={**D_, "particella": D, "tipo": D})

MARGINE_SCENA, PASSO_ST = 110.0, 30.0   # come MARGINE di scene/firenze_novoli/build.py: il reticolo copre il terreno della scena
QA_SCARTO = 0b10111111   # QA_PIXEL bit 0 fill, 1 nube dilatata, 2 cirro, 3 nube, 4 ombra di nube, 5 neve, 7 acqua (bit 6 = sereno, non scarta)
def landsat_st(soglia=80.0):
    """Temperatura delle superfici in °C su reticolo EPSG:7791 a 30 m (riquadro FP + 110 m, riga 0 = nord), una banda per data tenuta.
    Per ogni data la scena (riga WRS 029 o 030) con più celle valide sul riquadro FP; tenuta se le valide sono almeno il 'soglia'% delle celle di FP."""
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_origin
    d = raw("fi_landsat_st", "scene.json")[0].parent; scene = json.load(open(d / "scene.json"))
    E0, N0, E1, N1 = AOI["z2_en"]; x0, y0 = E0 - MARGINE_SCENA, N0 - MARGINE_SCENA
    nx, ny = math.ceil((E1 + MARGINE_SCENA - x0) / PASSO_ST), math.ceil((N1 + MARGINE_SCENA - y0) / PASSO_ST)
    tr = from_origin(x0, y0 + ny * PASSO_ST, PASSO_ST, PASSO_ST)
    xc, yc = x0 + (np.arange(nx) + 0.5) * PASSO_ST, y0 + ny * PASSO_ST - (np.arange(ny) + 0.5) * PASSO_ST
    in_fp = (xc[None, :] >= E0) & (xc[None, :] <= E1) & (yc[:, None] >= N0) & (yc[:, None] <= N1)
    def leggi_(p, fill):
        out = np.full((ny, nx), fill, dtype="uint16")
        with rasterio.open(p) as src: reproject(rasterio.band(src, 1), out, dst_transform=tr, dst_crs="EPSG:7791", resampling=Resampling.nearest, dst_nodata=fill)
        return out
    per_data = {}
    for s in scene:
        st, qa = leggi_(d / f"{s['id']}_ST_B10.tif", 0), leggi_(d / f"{s['id']}_QA_PIXEL.tif", 1)
        sc = s["st_scala"]; ok = (st != 0) & ((qa & QA_SCARTO) == 0)
        c = np.where(ok, st * sc["scale"] + sc["offset"] - 273.15, np.nan).astype("float32")
        v = {"scena": s["id"], "data": s["datetime"][:10], "ora_utc": s["datetime"][11:16], "satellite": s["platform"], "wrs": s["wrs"], "nubi_scena_pct": s["eo:cloud_cover"],
             "validi_fp_pct": round(float(ok[in_fp].mean() * 100), 1), "acqua_fp": int(((qa & 0b10000000) > 0)[in_fp & (qa != 1)].sum()), "_c": c}
        if v["validi_fp_pct"] > per_data.get(v["data"], {"validi_fp_pct": -1})["validi_fp_pct"]: per_data[v["data"]] = v
    tenute = [per_data[k] for k in sorted(per_data) if per_data[k]["validi_fp_pct"] >= soglia]
    a = np.stack([v.pop("_c") for v in tenute])
    with rasterio.open(NORM / "fi_landsat_st_30m.tif", "w", driver="GTiff", height=ny, width=nx, count=len(tenute), dtype="float32", crs="EPSG:7791", transform=tr,
                       nodata=float("nan"), compress="deflate", predictor=3) as o:
        o.write(a)
        for i, v in enumerate(tenute, 1): o.set_band_description(i, v["data"])
    for v in per_data.values(): v.pop("_c", None)
    st = {"file": "fi_landsat_st_30m.tif", "crs": "EPSG:7791", "passo_m": PASSO_ST, "nx": nx, "ny": ny, "x0_ovest": x0, "y1_nord": y0 + ny * PASSO_ST, "celle_fp": int(in_fp.sum()),
          "soglia_validi_pct": soglia, "unita": "°C", "maschera_qa_pixel": "bit 0-5 e 7 (fill, nube dilatata, cirro, nube, ombra di nube, neve, acqua)", "source_id": "src_fi_landsat_st",
          "snapshot_sha256": sha("fi_landsat_st"), "date_tenute": tenute, "date_scartate": [per_data[k] for k in sorted(per_data) if per_data[k]["validi_fp_pct"] < soglia]}
    json.dump(st, open(NORM / "fi_landsat_st.json", "w"), indent=1, ensure_ascii=False)
    print(f"  {len(tenute)} date tenute su {len(per_data)}, celle {nx}x{ny}")

def sir_termo():
    """Massime e minime giornaliere dalla tabella annuale del SIR (Tmax in text-danger, Tmin in text-primary; cella vuota o '-' = mancante)."""
    fs = raw("sir_termo_firenze", "*_20??.html"); giorni = []
    for f in sorted(fs):
        y, t = int(f.stem[-4:]), f.read_text(errors="ignore")
        for g, riga in re.findall(r'<tr><td class="bg-secondary[^>]*>&nbsp;(\d+)&nbsp;</td>(.*?)</tr>', t, re.S):
            for m, cella in enumerate(re.findall(r"<td[^>]*>(.*?)</td>", riga, re.S)[:12], 1):
                tx, tn = [re.sub(r"<[^>]+>", "", q).strip() for q in cella.split("<br />")]
                num = lambda q: float(q) if re.fullmatch(r"-?\d+(\.\d+)?", q) else None
                if num(tx) is None and num(tn) is None: continue
                giorni.append({"data": f"{y}-{m:02d}-{int(g):02d}", "tmax": num(tx), "tmin": num(tn)})
    giorni.sort(key=lambda q: q["data"]); assert len({q["data"] for q in giorni}) == len(giorni)
    sz = raw("sir_termo_firenze", "*_stazione.html")[0].read_text(errors="ignore")
    e, n = (float(v) for v in re.search(r"<b>E</b>&nbsp;(\d+)\s*<b>N</b>&nbsp;(\d+)", sz).groups())
    q = float(re.search(r"Quota slm \[m\]</b></div>\s*<div[^>]*>\s*([\d.]+)", sz)[1])
    from pyproj import Transformer
    E, N = Transformer.from_crs(3003, 7791, always_xy=True).transform(e, n)
    out = {"stazione": {"id": "TOS01001096", "nome": "Firenze Università", "e": round(E, 1), "n": round(N, 1), "quota_m": q, "distanza_fp_m": round(FP.distance(shapely.Point(E, N)))},
           "validazione": "pre-validato (dichiarato dal SIR per tutti gli anni scaricati)", "ora": "solare", "unita": "°C",
           "source_id": "src_sir_termo_firenze", "snapshot_sha256": sha("sir_termo_firenze"), "giorni": giorni}
    json.dump(out, open(NORM / "sir_termo_firenze.json", "w"), indent=1, ensure_ascii=False)
    print(f"  {len(giorni)} giorni, dal {giorni[0]['data']} al {giorni[-1]['data']}, stazione a {out['stazione']['distanza_fp_m']} m dal riquadro")


# Limiti del D.Lgs. 155/2010 come nella tabella ARPAT (https://www.arpat.toscana.it/limiti-di-riferimento-d-lgs-155-2010/).
# breve: (soglia, base del confronto, superamenti ammessi in un anno, unità contata). Gli altri parametri dell'archivio (NO, NOX, toluene, xileni...) restano solo in "misurati".
LIMITI_ARIA = {
    "PM10": {"annuo": 40, "breve": (50, "media giornaliera", 35, "giorni")},
    "PM2.5": {"annuo": 25},
    "NO2": {"annuo": 40, "breve": (200, "media oraria", 18, "ore")},
    "O3": {"breve": (120, "massima giornaliera della media mobile su 8 ore", 25, "giorni"),
           "nota": "valore obiettivo: 25 giorni l'anno come media su 3 anni; qui i giorni del solo 2025"},
    "CO": {"breve": (10, "massima giornaliera della media mobile su 8 ore", 0, "giorni")},
    "SO2": {"breve": (350, "media oraria", 24, "ore")},
    "BENZENE": {"annuo": 5},
}

def serie_aria(f):
    """Un CSV dell'archivio ARPAT -> (unità, DataFrame data, ora, v). v = NaN se non valido; ora None per i dati giornalieri (PM).
    Serie completa sull'anno (reindex), così le medie mobili non saltano i buchi."""
    import pandas as pd
    t = pd.read_csv(f, sep=";", encoding="latin-1", decimal=",", na_values=["nan", "NaN"])
    c = list(t.columns); u = re.search(r"IN (\S+/m³)", c[-2])[1]     # colonne: stazione, parametro, data, [ora], media, validità
    t["v"] = t[c[-2]].where(t[c[-1]] == 1)
    anno = str(t[c[2]].iat[0])[:4]; giorni = pd.date_range(f"{anno}-01-01", f"{anno}-12-31").strftime("%Y%m%d").astype(int)
    if "ORA" in c[3]:
        t = t.rename(columns={c[2]: "data", c[3]: "ora"}).set_index(["data", "ora"])[["v"]]
        t = t.reindex(pd.MultiIndex.from_product([giorni, range(1, 25)], names=["data", "ora"])).reset_index()
    else:
        t = t.rename(columns={c[2]: "data"}).set_index("data")[["v"]].reindex(pd.Index(giorni, name="data")).reset_index(); t["ora"] = None
    return u, t

def riassunto_aria(par, u, t):
    """Media annua, % validi, superamenti nel senso del D.Lgs. 155/2010, ultimo valore valido. Valori di stazione, nessuna interpolazione."""
    L = LIMITI_ARIA[par]; v = t.v; base = "giornaliera" if t.ora.isna().all() else "oraria"
    out = {"parametro": par, "unita": u, "base": base, "media_annua": None if v.isna().all() else round(float(v.mean()), 1),
           "validi_pct": round(float(v.notna().mean() * 100), 1), "superamenti": None}
    out["copertura_ok"] = out["validi_pct"] >= 90      # ARPAT: sotto il 90% "efficienza inferiore al 90%", la media annua non vale per la legge
    if "annuo" in L: out["limite_annuo"] = L["annuo"]
    if "breve" in L:
        s, su, k, cosa = L["breve"]
        if "8 ore" in su:   # media mobile su 8 ore valida con almeno 6 ore; massimo del giorno di fine periodo con almeno 18 medie valide
            m8 = v.rolling(8, min_periods=6).mean()
            g = m8.groupby(t.data).agg(["max", "count"]); x = g["max"].where(g["count"] >= 18)
        else: x = v
        out["superamenti"] = int((x > s).sum())
        out.update(soglia=s, soglia_su=su, ammessi=k, conta=cosa)
    if L.get("nota"): out["nota"] = L["nota"]
    ok = t[v.notna()]
    if len(ok):
        z = ok.iloc[-1]; d = str(int(z.data))
        out["ultimo"] = {"valore": round(float(z.v), 1), "data": f"{d[:4]}-{d[4:6]}-{d[6:]}", "ora_fine_solare": None if z.ora is None else int(z.ora)}
    else: out["ultimo"] = None
    return out

def arpat_aria(raggio=3000.0):
    """Stazioni ARPAT della rete regionale nel comune di Firenze o entro 3 km dal riquadro FP (gpkg EPSG:7791, anche fuori dall'area allargata)
    e riassunti 2025 per stazione e inquinante (arpat_aria_riassunti.json)."""
    import csv, html, io, zipfile
    from pyproj import Transformer
    gb = Transformer.from_crs(3003, 7791, always_xy=True)
    st = {}
    for f in raw("arpat_aria", "stazione_fi-*.html"):
        t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", f.read_text(errors="ignore"), flags=re.S))))
        m = re.search(r"(FI-[A-Z0-9-]+) Rete: (.+?) (?:Zona: (\S+) )?Comune: (.+?) Provincia: \S+ Coordinate: N:(\d+) - E:(\d+)", t)
        if not m or not m[2].startswith("Regionale"): continue     # autolaboratori: campagne temporanee, fuori dalla rete regionale
        cod, rete, zona, comune, n, e = m.groups()
        avv = re.search(r"Avvisi \d+ di \d+ (.+?) Dati in tempo reale", t)
        E, N = gb.transform(float(e), float(n))
        s = st.setdefault(cod, {"codice": cod, "reti": [], "zona": zona.lower() if zona else None, "comune": comune.title(), "e": E, "n": N, "avviso": avv[1] if avv else None})
        s["reti"].append(rete)
    tipo = {}
    for f in raw("arpat_aria", "*-medie-annuali-2007-2024.csv"):
        righe = list(csv.reader(io.StringIO(f.read_bytes().decode("latin-1"))))[2:]
        h = [q.lower() for q in righe[0]]
        for r_ in righe[1:]:
            if len(r_) > h.index("stazione") and r_[h.index("stazione")].upper() in st: tipo[r_[h.index("stazione")].upper()] = r_[h.index("tipo")].strip().lower()
    sel = {k: v for k, v in st.items() if v["comune"] == "Firenze" or FP.distance(shapely.Point(v["e"], v["n"])) <= raggio}
    z = zipfile.ZipFile(raw("arpat_aria", "FI_DATI_QA_*_CSV.zip")[0])
    for k, v in sel.items():
        v["tipo"] = tipo.get(k)      # None: tipo non dichiarato negli indicatori annuali (FI-LAVAGNINI, attiva dal 2025)
        v["distanza_fp_m"] = round(FP.distance(shapely.Point(v["e"], v["n"])))
        nomi = sorted(q for q in z.namelist() if q.startswith(k + "_"))
        v["misurati"] = [q[len(k) + 1:].rsplit("_", 1)[0] for q in nomi]
        v["inquinanti"] = [riassunto_aria(p, *serie_aria(z.open(q))) for q, p in zip(nomi, v["misurati"]) if p in LIMITI_ARIA]
    ord_ = sorted(sel.values(), key=lambda q: q["distanza_fp_m"])
    g = gpd.GeoDataFrame([{"id": "aqs_" + q["codice"].lower(), "codice": q["codice"], "rete": ", ".join(q["reti"]), "zona": q["zona"], "tipo": q["tipo"], "comune": q["comune"],
                           "avviso": q["avviso"], "distanza_fp_m": q["distanza_fp_m"], "misurati": ", ".join(q["misurati"])} for q in ord_],
                         geometry=[shapely.Point(round(q["e"], 2), round(q["n"], 2)) for q in ord_], crs=7791)
    g["source_id"], g["snapshot_id"] = "src_arpat_aria", sha("arpat_aria")
    g["cls"] = json.dumps({**{c: M for c in ("codice", "rete", "zona", "tipo", "comune", "avviso", "misurati")}, "distanza_fp_m": D, "geometry": M}, sort_keys=True)
    assert g["id"].is_unique
    (NORM / "arpat_aria.gpkg").unlink(missing_ok=True); g.to_file(NORM / "arpat_aria.gpkg", layer="stazioni", driver="GPKG", engine="pyogrio")   # niente finish(): ritaglierebbe sull'area allargata
    out = {"source_id": "src_arpat_aria", "snapshot_id": sha("arpat_aria"), "anno": int(re.search(r"_(\d{4})_CSV", z.filename)[1]),
           "validazione": "dati validati (ARPAT: intero ciclo di validazione, usati per gli indicatori ufficiali)", "ora": "solare, ora di fine misura (24 = mezzanotte)",
           "norma": "D.Lgs. 155/2010", "limiti_url": "https://www.arpat.toscana.it/limiti-di-riferimento-d-lgs-155-2010/",
           "selezione": f"rete regionale ARPAT, comune di Firenze o entro {raggio:.0f} m dal riquadro FP", "stazioni": [{**q, "e": round(q["e"], 2), "n": round(q["n"], 2)} for q in ord_]}
    json.dump(out, open(NORM / "arpat_aria_riassunti.json", "w"), indent=1, ensure_ascii=False)
    for q in ord_: print(f"  {q['codice']:14} {q['tipo'] or '-':9} {q['distanza_fp_m']:6} m  {' '.join(p['parametro'] for p in q['inquinanti'])}")

def sezioni2011():
    """Sezioni di censimento 2011 del Comune con i residenti 2011 (P1) del CSV regionale: SEZ2011 = 48017 x 10^7 + CODSEZ2011."""
    import pandas as pd
    g = leggi("fi_sezioni2011", "sezioni2011.zip", 3003); g["CODSEZ2011"] = g["CODSEZ2011"].astype("int64")
    c = pd.read_csv(raw("rt_censimento2011", "censimento2011.csv")[0], sep=";", usecols=["PROCOM", "SEZ2011", "P1"], encoding="latin-1")
    c = c[c.PROCOM == 48017].assign(CODSEZ2011=lambda d: d.SEZ2011 - 48017 * 10**7)
    g = g.merge(c[["CODSEZ2011", "P1"]].rename(columns={"P1": "residenti_2011"}), on="CODSEZ2011", how="left")   # 118 sezioni senza riga: residenti nullo, non zero
    scrivi(g, "fi_sezioni2011", "src_fi_sezioni2011", "sezioni", "CODSEZ2011", "sez_fi_", cls_extra={"residenti_2011": M})


JOBS = {
    "osm": lambda: norm_osm("osm_firenze", "src_osm_firenze"),
    "uv": lambda: norm_uv("rt_uv_firenze_novoli", "src_rt_uv_firenze_novoli"),
    "gtfs_tram": lambda: norm_gtfs("gtfs_gest_firenze", "src_gtfs_gest_firenze", "gest.gtfs.zip", "tram"),
    "gtfs_bus": lambda: norm_gtfs("gtfs_at_firenze", "src_gtfs_at_firenze", "gtfs.zip", "stop"),
    "alberi": lambda: scrivi(leggi("fi_alberi", "alberi_pubblici.json", 6706), "fi_alberi", "src_fi_alberi", "alberi", "id_orig", "tre_fi_"),
    "civici": lambda: scrivi(leggi("fi_civici", "civici.zip", 3003, "ISO-8859-1"), "fi_civici", "src_fi_civici", "civici", "id_orig", "adr_fi_"),
    "barriere": lambda: scrivi(leggi("fi_barriere", "mappa_accessibilita.zip", 3003, "cp850"), "fi_barriere", "src_fi_barriere", "barriere", "pk_id", "bar_fi_"),   # dbf in cp850 (audit rete)
    "aree_pedonali": lambda: scrivi(leggi("fi_aree_pedonali", "acPed_s.zip", 32632).pipe(lambda g: g.set_geometry(shapely.force_2d(g.geometry.values), crs=7791)), "fi_aree_pedonali", "src_fi_aree_pedonali", "aree_pedonali", "acPedId", "ped_fi_"),   # PolygonZ ridotti a 2D
    "rifugi_aree": lambda: scrivi(leggi("fi_rifugi_aree", "rifugi_aree_fresche.json", 6706), "fi_rifugi_aree", "src_fi_rifugi_aree", "rifugi_aree", "cod_area", "rif_fi_"),
    "rifugi_bibl": lambda: scrivi(leggi("fi_rifugi_biblioteche", "rifugi_biblioteche.json", 3003), "fi_rifugi_biblioteche", "src_fi_rifugi_biblioteche", "rifugi_biblioteche", "fid_src", "rib_fi_"),
    "aree_attesa": lambda: scrivi(leggi("fi_aree_attesa", "aree_attesa.zip", 3003, "ISO-8859-1").astype({"gid": int}), "fi_aree_attesa", "src_fi_aree_attesa", "aree_attesa", "gid", "pcv_att_fi_"),   # 'codice' ha doppioni (AT04, AT14): chiave gid
    "aree_assistenza": lambda: scrivi(leggi("fi_aree_assistenza", "aree_assistenza.zip", 3003, "ISO-8859-1"), "fi_aree_assistenza", "src_fi_aree_assistenza", "aree_assistenza", "cod_area", "pcv_ass_fi_"),
    "sosta_disabili": lambda: scrivi(leggi("fi_sosta_disabili", "sosta_disabili.zip", 3003), "fi_sosta_disabili", "src_fi_sosta_disabili", "sosta_disabili", "fid_src", "sdi_fi_"),
    "aree_verdi": lambda: scrivi(leggi("fi_aree_verdi", "aree_verdi.zip", 3003), "fi_aree_verdi", "src_fi_aree_verdi", "aree_verdi", "CODICE_ARE", "grn_fi_"),
    "aree_giochi": lambda: scrivi(leggi("fi_aree_giochi", "aree_giochi.zip", 3003), "fi_aree_giochi", "src_fi_aree_giochi", "aree_giochi", "CODAREAAPP", "gio_fi_"),
    "aree_cani": lambda: scrivi(leggi("fi_aree_cani", "aree_cani.zip", 3003), "fi_aree_cani", "src_fi_aree_cani", "aree_cani", "id_orig", "can_fi_"),   # CODAREAAPP ha doppioni: chiave ID
    "aree_sportive": lambda: scrivi(leggi("fi_aree_sportive", "aree_sportive.zip", 3003), "fi_aree_sportive", "src_fi_aree_sportive", "aree_sportive", "CODAREA", "spo_fi_"),
    "farmacie": lambda: scrivi(leggi("fi_farmacie", "farmacie.zip", 3003), "fi_farmacie", "src_fi_farmacie", "farmacie", "id_orig", "far_fi_"),
    "bike_sharing": lambda: scrivi(leggi("fi_bike_sharing", "bike_sharing.zip", 3003), "fi_bike_sharing", "src_fi_bike_sharing", "bike_sharing", "fid_src", "bks_fi_"),
    "car_sharing": lambda: scrivi(leggi("fi_car_sharing", "car_sharing.zip", 3003), "fi_car_sharing", "src_fi_car_sharing", "car_sharing", "fid_src", "cks_fi_"),
    "pericolosita_idraulica": lambda: scrivi(leggi("fi_pericolosita_idraulica", "pericolosita_idraulica.zip", 3003), "fi_pericolosita_idraulica", "src_fi_pericolosita_idraulica", "pericolosita_idraulica", "fid_src", "idr_fi_"),
    "allagate1966": lambda: scrivi(leggi("fi_allagate1966", "allagate1966.zip", 3003), "fi_allagate1966", "src_fi_allagate1966", "allagate1966", "AREE_ALLAG", "all66_fi_", rango="AREE_ALLAG"),   # .prj Monte Mario/Roma = EPSG:3003; nessuna chiave
    "zone30": lambda: scrivi(leggi("fi_zone30", "zone30.zip", 3003), "fi_zone30", "src_fi_zone30", "zone30", "fid_src", "z30_fi_"),
    "scudo_verde": lambda: scrivi(leggi("fi_scudo_verde", "scudo_verde.zip", 3003), "fi_scudo_verde", "src_fi_scudo_verde", "scudo_verde", "fid_src", "ssv_fi_"),
    "pcca": lambda: scrivi(leggi("fi_pcca", "pcca.zip", 6706), "fi_pcca", "src_fi_pcca", "pcca", "PKID", "acu_fi_"),
    "sezioni2011": sezioni2011,
    "tram_fermate": lambda: scrivi(leggi("fi_tram_fermate", "tram_fermate.zip", 3003), "fi_tram_fermate", "src_fi_tram_fermate", "tram_fermate", "nome_ferma", "stp_fi_", rango="nome_ferma"),
    "scuole": lambda: scrivi(leggi("fi_scuole_statali", "miur_scuole_statali_2026_27.json", 6706), "fi_scuole_statali", "src_fi_scuole_statali", "scuole", "codicescuo", "dst_school_", low=True),
    "cm": cm, "catasto": catasto, "landsat_st": landsat_st, "sir_termo": sir_termo, "arpat": arpat_aria,
    "dtm": lambda: lidar("fi_dtm2023", "fi_dtm2023_0.5m.tif"), "dsm": lambda: lidar("fi_dsm2023", "fi_dsm2023_0.5m.tif"),
}

def report():
    """Conteggi per layer: area allargata (riquadro + margine) e riquadro (FP); snapshot e raster. Scrive pipeline/report_firenze.json."""
    out = {"aoi": AOI, "giorno": lib.DAY, "layer": {}, "raster": {}, "snapshot": {}}
    for p in sorted(NORM.glob("*.gpkg")):
        for name, _ in pyogrio.list_layers(p):
            g = gpd.read_file(p, layer=name)
            out["layer"][f"{p.name}:{name}"] = {"in_area_allargata": len(g), "in_riquadro": int(g.intersects(FP).sum())}
    for p in sorted(NORM.glob("*.stats.json")): out["raster"][p.name[:-11]] = json.load(open(p))
    for p in sorted(SNAP.glob(f"snp_*_{lib.DAY}.json")):
        s = json.load(open(p))
        if s["source_id"] in {f"src_{d}" for d in FIRENZE}: out["snapshot"][s["snapshot_id"]] = {k: s.get(k) for k in ("status", "bytes", "sha256", "license_state", "expires_at")}
    json.dump(out, open(ROOT / "pipeline/report_firenze.json", "w"), indent=1, ensure_ascii=False)
    for k, v in out["layer"].items(): print(f"{k:58} allargata {v['in_area_allargata']:7}  riquadro {v['in_riquadro']:7}")

if __name__ == "__main__":
    from fonti_firenze import S
    FIRENZE = [d["slug"] for d in S().values()]
    a = sys.argv[1:]
    if a != ["report"]:
        for k in a or JOBS: print(k); JOBS[k]()
    if not a or a == ["report"]: report()
