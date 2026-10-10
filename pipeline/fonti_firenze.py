"""F03: fonti di aoi_firenze_novoli. Riusa lib (get/download/record/rawdir) e acquire (gtfs, wfs_uv); l'area viene da contracts/aree.json.
Uso: fonti_firenze.py acquire [fonte ...] | sources | baseline [--force]     (senza fonte: tutte)
Tabella S: una riga per fonte con scarico, licenza, periodo e controlli; T17 (rimando al catalogo o lacuna) in pipeline/t17_firenze.json."""
import io, json, os, sys, zipfile, struct, datetime as dt
os.environ["DT_AOI"] = "aoi_firenze_novoli"      # prima di importare lib: tutto il modulo lavora su questa area
import requests
import lib
from lib import AOI, ROOT, SNAP, SRCDIR, UA, DAY, NORM, download, record, rawdir, sha256
from acquire import gtfs, wfs_uv
from sources import chk, lic, n

BUF = AOI["buf_en"]
CKAN = "https://dati.toscana.it/dataset/"
DG = "https://datigis.comune.fi.it/"
OSM_URL = os.environ.get("OSM_URL", "https://download.geofabrik.de/europe/italy/centro-261008.osm.pbf")
LIDAR = {"fi_dtm2023": "https://datigis.comune.fi.it/grid/MDT_LIDAR_2023_ASCII.zip", "fi_dsm2023": "https://datigis.comune.fi.it/grid/MDS_LIDAR_2023_ASCII.zip"}
BY = lambda ckan, note="": lic("clear", "CC-BY-4.0", CKAN + ckan, "Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09)." + note, use="redistribution")

def dl(slug, url, name, media, note, **kw):
    """File unico (o più file: url e name liste) scaricato per intero."""
    def f():
        us, ns = (url, name) if isinstance(url, list) else ([url], [name])
        fs = [download(u, rawdir(slug) / nm) for u, nm in zip(us, ns)]
        return {"files": fs, "multi": len(fs) > 1, "url": us[0], "media_type": media, "content_period": {"note": note}, **kw}
    return f

class _Http(io.RawIOBase):
    """File remoto in sola lettura con richieste Range: lo zip della città non si scarica intero."""
    def __init__(s, url):
        s.url, s.pos, s.sess = url, 0, requests.Session(); s.sess.headers.update(UA, **{"Accept-Encoding": "identity"})
        s.size = int(s.sess.head(url, allow_redirects=True, timeout=60).headers["Content-Length"])
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, o, w=0): s.pos = {0: o, 1: s.pos + o, 2: s.size + o}[w]; return s.pos
    def readinto(s, b):
        k = min(len(b), s.size - s.pos)
        if k <= 0: return 0
        r = s.sess.get(s.url, headers={"Range": f"bytes={s.pos}-{s.pos + k - 1}"}, timeout=120); r.raise_for_status()
        b[:len(r.content)] = r.content; s.pos += len(r.content); return len(r.content)

def tessera(z, info):
    """Estrae una tessera; gli zip 2023 sono Deflate64 (metodo 9), che zipfile non legge: si usa inflate64 (installato con py7zr)."""
    if info.compress_type != 9: return z.read(info)
    import inflate64
    z.fp.seek(info.header_offset); h = z.fp.read(30); nl, el = struct.unpack("<HH", h[26:30]); z.fp.seek(info.header_offset + 30 + nl + el)
    out = inflate64.Inflater().inflate(z.fp.read(info.compress_size)); assert len(out) == info.file_size, info.filename; return out

def lidar(slug):
    """Tessere ASCII da 500 m (nome 32_<E>_<N>.ASC) che coprono riquadro + margine."""
    def f():
        z = zipfile.ZipFile(io.BufferedReader(_Http(LIDAR[slug]), buffer_size=1 << 20)); nomi = {i.filename: i for i in z.infolist()}
        need = [f"32_{x}_{y}.ASC" for x in range(int(BUF[0] // 500 * 500), int(BUF[2]) + 1, 500) for y in range(int(BUF[1] // 500 * 500), int(BUF[3]) + 1, 500)]
        d, fs, manca = rawdir(slug), [], []
        for t in need:
            if t not in nomi: manca.append(t); continue
            p = d / t
            if not p.exists() or p.stat().st_size != nomi[t].file_size:
                (d / (t + ".part")).write_bytes(tessera(z, nomi[t])); (d / (t + ".part")).rename(p)
            fs.append(p)
        nota = f"volo 2023-06-27 (foglie presenti), celle da 0,5 m; {len(fs)} tessere da 500 m estratte con richieste Range dallo zip cittadino"
        if manca: nota += f"; tessere assenti dallo zip (fuori dal territorio comunale): {len(manca)}"
        return {"files": fs, "multi": True, "url": LIDAR[slug], "media_type": "text/plain", "content_period": {"start": "2023-06-27", "end": "2023-06-27", "note": nota}}
    return f

def osm():
    d = rawdir("osm_firenze"); p = download(OSM_URL, d / OSM_URL.rsplit("/", 1)[1])
    return {"files": [p], "url": OSM_URL, "media_type": "application/x-osm+pbf",
            "content_period": {"note": "estratto regionale Centro Italia, timestamp nel nome del file (2026-10-08, ore 00 UTC circa); il ritaglio all'area allargata avviene in normalizzazione, il file originario resta intatto"}}

CATASTO = "https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php"
def catasto():
    """Particelle e fogli sul riquadro FP: solo GML in EPSG:6706 con assi lat,lon. Riquadri alti più di circa 0,017° rispondono numberMatched=0
    senza errore: FP (0,0124° x 0,0181°) sta in una richiesta. ponytail: niente tessere, servono (e dedup per gml:id) se si allarga al margine buf_en.
    Il server rifiuta i parametri codificati (%2C, %3A): URL scritta a mano."""
    import re
    s, w, n_, e = AOI["z2_ll_SWNE"]; d = rawdir("fi_catasto"); fs = []
    def chk_(r):
        m = re.search(r'numberMatched="(\d+)" numberReturned="(\d+)"', r.text[:3000])
        if not m or m[1] != m[2] or m[1] == "0": raise ValueError("risposta WFS incompleta o vuota: " + r.text[:300])
    for tipo, nome in (("CP:CadastralParcel", "particelle.gml"), ("CP:CadastralZoning", "fogli.gml")):
        url = f"{CATASTO}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES={tipo}&COUNT=15000&BBOX={s},{w},{n_},{e},urn:ogc:def:crs:EPSG::6706"
        (d / nome).write_bytes(lib.get(url, check=chk_).content); fs.append(d / nome)
    return {"files": fs, "multi": True, "url": url.replace("CP:CadastralZoning", "CP:CadastralParcel"), "media_type": "application/gml+xml",
            "content_period": {"note": "cartografia catastale aggiornata dall'Agenzia per foglio (BEGINLIFESPANVERSION dei fogli); stato alla data di scarico"}}

ARPAT, ARPAT_ANNO = "https://www.arpat.toscana.it/", 2025      # ultimo anno completo dell'archivio orario (il 2026 non è pubblicato come download)
ARPAT_IND = ["app/uploads/datiemappe/dati/pm10-medie-annuali/pm10-medie-annuali-2007-2024.csv", "app/uploads/datiemappe/dati/no2-medie-annuali/no2-medie-annuali-2007-2024.csv"]
def arpat():
    """Qualità dell'aria ARPAT, solo download pubblici del sito: archivio orario della rete di Firenze (zip di CSV), pagine delle stazioni fi-* (unica
    anagrafica pubblica con coordinate: il JSON della rete su dati.toscana.it rimanda alla home) e indicatori annuali PM10 e NO2 (tipo traffico/fondo).
    Niente API dell'app "Ambiente in Toscana": è un servizio per ARPAT. Le pagine HTML cambiano a ogni scarico: lo sha256 dello snapshot non si riproduce."""
    import re
    d = rawdir("arpat_aria")
    pag = lib.get(ARPAT + "datiemappe/qualita-dellaria-dati-orari/").text
    z = re.search(rf'https://[^"]+/FI_DATI_QA_{ARPAT_ANNO}_CSV\.zip', pag)[0]
    fs = [download(z, d / z.rsplit("/", 1)[1])] + [download(ARPAT + u, d / u.rsplit("/", 1)[1]) for u in ARPAT_IND]
    for s_ in sorted(set(re.findall(r"/stazione/(fi-[a-z0-9-]+)/", lib.get(ARPAT + "stazione-sitemap.xml").text))):   # filtro (rete regionale, comune, 3 km) in norm_firenze
        p = d / f"stazione_{s_}.html"; p.write_bytes(lib.get(f"{ARPAT}stazione/{s_}/").content); fs.append(p)
    return {"files": fs, "multi": True, "url": z, "media_type": "application/zip",
            "content_period": {"start": f"{ARPAT_ANNO}-01-01", "end": f"{ARPAT_ANNO}-12-31", "note": f"archivio {ARPAT_ANNO} dichiarato validato (intero ciclo di validazione); ore solari; anagrafica delle stazioni alla data di scarico"}}

STAC ="https://planetarycomputer.microsoft.com/api/stac/v1"
LANDSAT_ANNI, LANDSAT_PAD = (2023, 2024, 2025, 2026), 300.0   # ritaglio: riquadro FP + 300 m (copre il margine di 110 m della scena e il ricampionamento)
def landsat():
    """Landsat 8 e 9 Collection 2 Level-2, giugno-settembre: ritagli di ST_B10 e QA_PIXEL attorno al riquadro, letti con richieste Range dai COG
    del catalogo STAC di Planetary Computer. La firma SAS anonima resta in memoria: nei file e negli snapshot solo gli URL senza firma."""
    import re, rasterio, rasterio.windows
    from rasterio.warp import transform_bounds
    s, w, n_, e = AOI["buf_ll_SWNE"]; d = rawdir("fi_landsat_st"); fs, items = [], []
    for y in LANDSAT_ANNI:
        body = {"collections": ["landsat-c2-l2"], "bbox": [w, s, e, n_], "datetime": f"{y}-06-01T00:00:00Z/{y}-09-30T23:59:59Z",
                "query": {"platform": {"in": ["landsat-8", "landsat-9"]}}, "limit": 200}
        r = requests.post(STAC + "/search", json=body, headers=UA, timeout=120); r.raise_for_status(); r = r.json()
        assert not any(x["rel"] == "next" for x in r.get("links", [])), "risposta STAC su più pagine"
        items += r["features"]
    tok = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/landsateuwest/landsat-c2", headers=UA, timeout=60).json()["token"]
    x0, y0, x1, y1 = AOI["z2_en"]; box_ = (x0 - LANDSAT_PAD, y0 - LANDSAT_PAD, x1 + LANDSAT_PAD, y1 + LANDSAT_PAD)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3"):
        for it in items:
            for k, suf in (("lwir11", "ST_B10"), ("qa_pixel", "QA_PIXEL")):
                p = d / f"{it['id']}_{suf}.tif"
                if p.exists(): fs.append(p); continue
                href = it["assets"][k]["href"]
                try:
                    with rasterio.open(href + "?" + tok) as src:
                        win = rasterio.windows.from_bounds(*transform_bounds("EPSG:7791", src.crs, *box_), src.transform).round_offsets().round_lengths()
                        a = src.read(1, window=win, boundless=True, fill_value=0 if k == "lwir11" else 1)
                        prof = dict(driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype=a.dtype, crs=src.crs, transform=src.window_transform(win),
                                    nodata=0 if k == "lwir11" else 1, compress="deflate")
                except Exception as ex:   # il messaggio di GDAL contiene l'URL firmato: si toglie la firma prima che finisca in uno snapshot
                    raise RuntimeError(f"{href}: " + re.sub(r"\?\S*", "", str(ex))) from None
                with rasterio.open(p.with_suffix(".part"), "w", **prof) as o: o.write(a, 1)
                p.with_suffix(".part").rename(p); fs.append(p)
    meta = [{"id": it["id"], "datetime": it["properties"]["datetime"], "platform": it["properties"]["platform"], "eo:cloud_cover": it["properties"]["eo:cloud_cover"],
             "wrs": f"{it['properties']['landsat:wrs_path']}/{it['properties']['landsat:wrs_row']}", "categoria": it["properties"].get("landsat:collection_category"),
             "proj:epsg": it["properties"].get("proj:epsg"), "st_b10": it["assets"]["lwir11"]["href"], "qa_pixel": it["assets"]["qa_pixel"]["href"],
             "st_scala": it["assets"]["lwir11"]["raster:bands"][0]} for it in items]
    (d / "scene.json").write_text(json.dumps(sorted(meta, key=lambda m: m["id"]), indent=1)); fs.append(d / "scene.json")
    return {"files": fs, "multi": True, "url": STAC + "/search (collections=landsat-c2-l2, platform landsat-8/9, giugno-settembre 2023-2026, bbox riquadro + margine)",
            "media_type": "image/tiff; application=geotiff", "content_period": {"start": "2023-06-01", "end": "2026-09-30", "note": f"{len(items)} scene di giugno-settembre (path 192, righe 029 e 030), ritagli attorno al riquadro"}}

SIR = "https://www.sir.toscana.it/archivio/dati.php"
SIR_STAZIONE = "TOS01001096"   # Firenze Università, a 1,3 km a est del riquadro FP
def sir():
    """Temperature giornaliere massime e minime (Sez. A, Tab. 1) della stazione SIR, una pagina HTML per anno dall'archivio pubblico.
    Lo scarico CSV e i dati a 15 minuti chiedono e-mail e captcha: si usa la tabella pubblica."""
    d = rawdir("sir_termo_firenze"); fs = []
    def chk_(r):
        if "Anno" not in r.text or "text-danger" not in r.text: raise ValueError("tabella SIR vuota: " + r.text[:200])
    for y in LANDSAT_ANNI:
        p = d / f"{SIR_STAZIONE}_{y}.html"; p.write_bytes(lib.get(f"{SIR}?A={y}&IDS={SIR_STAZIONE}&IDST=termo", check=chk_).content); fs.append(p)
    p = d / f"{SIR_STAZIONE}_stazione.html"   # scheda della stazione: coordinate Gauss-Boaga e quota
    p.write_bytes(lib.get(SIR.replace("dati.php", f"stazione.php?IDST=termo&IDS={SIR_STAZIONE}")).content); fs.append(p)
    return {"files": fs, "multi": True, "url": f"{SIR}?A={LANDSAT_ANNI[0]}&IDS={SIR_STAZIONE}&IDST=termo", "media_type": "text/html",
            "content_period": {"start": f"{LANDSAT_ANNI[0]}-01-01", "note": "massime e minime giornaliere 2023-2026; dati dichiarati PRE-VALIDATO dal SIR (possono cambiare con la validazione)"}}

# ------------------------------------------------------------------------------ fonti
# ckan: id o nome del dataset su dati.toscana.it; None = lacuna del catalogo, motivata in "lacuna" (T17)
def S():
    tp = lambda k: lambda: [chk(f"{k[1]} in area allargata", (n(k[0], k[1]) or 0) > 0, f"{n(k[0], k[1])} oggetti")]
    return {
 "alberi": dict(slug="fi_alberi", title="Alberi pubblici, censimento del Comune di Firenze", publisher="Comune di Firenze", ckan="42cd1073-521f-4040-9491-e993d03663a4",
   res=DG + "json/alberi_pubblici.json", origin="official_download", lic=BY("42cd1073-521f-4040-9491-e993d03663a4"),
   period={"note": "dataset dichiarato aggiornato ogni giorno (frequenza DAILY): stato alla data di scarico, senza data di rilievo per albero"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lon/lat trattati come RDN2008 geografico (ADR-T02); il campo CRS della scheda (ROMA40/OVEST) è inaffidabile"},
   units={"circonf_cm": "cm"}, fields=["ID", "CODSITO_ALBERO", "QUARTIERE", "SPECIE", "NOME_COMUNE", "CIRCONF_CM"],
   fetch=dl("fi_alberi", DG + "json/alberi_pubblici.json", "alberi_pubblici.json", "application/geo+json", "dataset dichiarato aggiornato ogni giorno: stato alla data di scarico"),
   checks=lambda: [*tp(("fi_alberi.gpkg", "alberi"))(), chk("altezza e chioma", False, "assenti nel censimento (altezza da CHM in F05)", warn=True)]),
 "civici": dict(slug="fi_civici", title="Civici del Comune di Firenze", publisher="Comune di Firenze", ckan="11430710-56eb-4444-bd6f-c5433155afc5",
   res=DG + "shp/civici.zip", origin="official_download", lic=BY("11430710-56eb-4444-bd6f-c5433155afc5"),
   period={"note": "dataset dichiarato aggiornato al bisogno (AS_NEEDED), ultima modifica 2026-10-05; stato alla data di scarico"},
   crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791 come a Pisa (nessuno shift di datum), scarto non misurato su Firenze"},
   units={}, fields=["PK_ID", "ID", "CODICESTRA", "CODICECIVI", "STRADA", "NUMEROCIVI", "TIPO"],
   fetch=dl("fi_civici", DG + "shp/civici.zip", "civici.zip", "application/zip", "dataset aggiornato al bisogno (ultima modifica dichiarata 2026-10-05): stato alla data di scarico"),
   checks=lambda: [*tp(("fi_civici.gpkg", "civici"))(), chk("civici come punti d'indirizzo", True, "origins address_points (ADR-F02), non persone")]),
 "barriere": dict(slug="fi_barriere", title="Censimento delle barriere architettoniche e urbanistiche, Comune di Firenze", publisher="Comune di Firenze", ckan="92033b63-0598-4449-9007-22127abe505a",
   res=DG + "shp/mappa_accessibilita.zip", origin="official_download", lic=BY("92033b63-0598-4449-9007-22127abe505a"),
   period={"end": "2013-12-31", "note": "archivio dichiarato aggiornato al 2013; file dello zip del 2016-09-13; frequenza NOT_PLANNED"},
   crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791 come a Pisa"},
   units={}, fields=["pk_id", "quartiere", "utoe", "scheda", "destinaz_u", "indirizzo", "grado_acce", "url"],
   fetch=dl("fi_barriere", DG + "shp/mappa_accessibilita.zip", "mappa_accessibilita.zip", "application/zip", "archivio dichiarato aggiornato al 2013"),
   checks=lambda: [*tp(("fi_barriere.gpkg", "barriere"))(), chk("natura del dato", False, "schede di accessibilità di edifici (rilievo 2013), non ostacoli sul percorso", warn=True)]),
 "aree_pedonali": dict(slug="fi_aree_pedonali", title="Viabilità, aree di circolazione pedonale (poligoni), Comune di Firenze", publisher="Comune di Firenze", ckan="25703515-6bea-4148-8651-8c494a27bbf5",
   res="https://data.comune.fi.it/datastore/download.php?id=6527&type=99&format=url&file_format=shp&file_id=20272", origin="official_download", lic=BY("25703515-6bea-4148-8651-8c494a27bbf5"),
   period={"note": "scheda aggiornata il 2026-02-11; data di rilievo non dichiarata: stato alla data di scarico"},
   crs={"declared": "EPSG:32632", "vertical_datum": "not_declared", "note": "shapefile PolygonZ con .prj in WGS84 UTM 32N; convertito in EPSG:7791 e ridotto a 2D. Allineamento con i marciapiedi OSM controllato a vista su Via di Novoli (scarto sotto 1 m), non misurato"},
   units={"SHAPE_Area": "m2", "SHAPE_Leng": "m"}, fields=["acPedId", "acPedPos", "acPedZon", "acPedFon", "acPedLiv", "acPedSed"],
   fetch=dl("fi_aree_pedonali", "https://data.comune.fi.it/datastore/download.php?id=6527&type=99&format=url&file_format=shp&file_id=20272", "acPed_s.zip", "application/zip", "scheda aggiornata il 2026-02-11"),
   checks=lambda: [*tp(("fi_aree_pedonali.gpkg", "aree_pedonali"))(), chk("significato dei codici", False, "codici acPedPos, acPedZon, acPedFon, acPedSed senza legenda nel pacchetto: usati solo come geometria (dove si cammina)", warn=True)]),
 "rifugi_aree": dict(slug="fi_rifugi_aree", title="Rifugi climatici, aree fresche (Comune di Firenze)", publisher="Comune di Firenze", ckan="rifugi_climatici_aree_fresche",
   res=DG + "json/rifugi_climatici_aree_fresche.json", origin="official_download", lic=BY("rifugi_climatici_aree_fresche"),
   period={"note": "dato dichiarato del 2026-06-18, frequenza AS_NEEDED"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lon/lat trattati come RDN2008 geografico"},
   units={"percentuale_ombreggi": "percent"}, fields=["cod_area", "nome_area", "percentuale_ombreggi", "ingresso", "descrizione"],
   fetch=dl("fi_rifugi_aree", DG + "json/rifugi_climatici_aree_fresche.json", "rifugi_aree_fresche.json", "application/geo+json", "dato dichiarato del 2026-06-18"),
   checks=lambda: [chk("aree fresche in area allargata", n("fi_rifugi_aree.gpkg", "rifugi_aree") is not None, f"{n('fi_rifugi_aree.gpkg', 'rifugi_aree')} aree (zero è un esito ammesso)")]),
 "rifugi_bibl": dict(slug="fi_rifugi_biblioteche", title="Rifugi climatici, biblioteche (Comune di Firenze)", publisher="Comune di Firenze", ckan="rifugi_climatici_biblioteche",
   res=DG + "json/rifugi_climatici_biblioteche.json", origin="official_download", lic=BY("rifugi_climatici_biblioteche"),
   period={"note": "dato dichiarato del 2026-06-18, frequenza AS_NEEDED"},
   crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "il GeoJSON dichiara EPSG:3003 (audit cataloghi); letto con il CRS dichiarato e convertito"},
   units={}, fields=[],
   fetch=dl("fi_rifugi_biblioteche", DG + "json/rifugi_climatici_biblioteche.json", "rifugi_biblioteche.json", "application/geo+json", "dato dichiarato del 2026-06-18"),
   checks=lambda: [chk("biblioteche in area allargata", n("fi_rifugi_biblioteche.gpkg", "rifugi_biblioteche") is not None, f"{n('fi_rifugi_biblioteche.gpkg', 'rifugi_biblioteche')} punti (zero è un esito ammesso)")]),
 "uv": dict(slug="rt_uv_firenze_novoli", title="Unità volumetriche del DB topografico regionale (WFS), area di Firenze", publisher="Regione Toscana",
   ckan=None, lacuna="Le unità volumetriche di Firenze non sono su dati.toscana.it (il portale le ha per altri 40 comuni, non per Firenze): fonte il servizio WFS del Geoscopio. Da chiedere alla Regione: pubblicazione del layer per Firenze.",
   dataset_url="https://www502.regione.toscana.it/geoscopio/servizi/wms/EDIFICATO.htm", res="https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato", origin="ogc_service",
   lic=lic("clear_with_reserve", None, "https://www502.regione.toscana.it/geoscopio/servizi/wms/EDIFICATO.htm", "Nessuna licenza sul layer; vale la politica regionale sui dati geografici aperti (CC BY o CC BY-SA, atto 2013), come a Pisa.",
           "Licenza non scritta sul layer: dedotta dalla politica regionale. Verificare prima di ridistribuire."),
   period={"start": "2011-01-01", "end": "2011-12-31", "note": "volo 2011 (campo anno, audit edifici); data di aggiornamento del servizio non dichiarata"},
   crs={"declared": "EPSG:7791", "vertical_datum": "not_declared", "note": "richiesto direttamente in EPSG:7791; spiccato UV meno DTM 2023: mediana -0,14 m su 1.419 impronte (audit edifici), datum coerente ma non dichiarato dalla fonte"},
   units={"height_m": "m", "ground_elev_m": "m", "roof_elev_m": "m", "area_m2": "m2"}, fields=["uv_id", "edifc_id", "uv_av", "uv_qs", "uv_qe", "uv_dpor", "anno"],
   fetch=lambda: {**wfs_uv("rt_uv_firenze_novoli"), "content_period": {"start": "2011-01-01", "end": "2011-12-31", "note": "volo 2011 (campo anno nei dati); il servizio non dichiara la data di aggiornamento"}},
   checks=lambda: [*tp(("rt_uv_firenze_novoli.gpkg", "building_volume"))(), chk("portici (uv_dpor)", False, "un solo oggetto con loggia nell'audit: nessuna fonte per portici e volumi sospesi", warn=True)]),
 "dtm": dict(slug="fi_dtm2023", title="DTM LiDAR 2023 del Comune di Firenze (ASCII grid 0,5 m)", publisher="Comune di Firenze", ckan="dtm-lidar-2023", res=LIDAR["fi_dtm2023"], origin="official_download",
   lic=BY("dtm-lidar-2023"), period={"start": "2023-06-27", "note": "volo 2023-06-27"},
   crs={"declared": "undeclared", "vertical_datum": "not_declared", "note": "i file ASCII 2023 non portano un CRS: EPSG:7791 assunto dal prefisso 32_ e confermato dalle quote (UV -0,14 m, siti alberi -0,07 m; audit edifici e verde); datum verticale non dichiarato"},
   units={"quota": "m"}, fields=[], fetch=lidar("fi_dtm2023"), checks=lambda: [chk("raster ritagliato su area allargata", NORM.joinpath("fi_dtm2023_0.5m.tif").exists(), "vedi report_firenze.json"), chk("datum verticale", False, "non dichiarato", warn=True)]),
 "dsm": dict(slug="fi_dsm2023", title="DSM LiDAR 2023 del Comune di Firenze (ASCII grid 0,5 m)", publisher="Comune di Firenze", ckan="dsm-lidar-2023", res=LIDAR["fi_dsm2023"], origin="official_download",
   lic=BY("dsm-lidar-2023"), period={"start": "2023-06-27", "note": "volo 2023-06-27 (giugno: foglie presenti)"},
   crs={"declared": "undeclared", "vertical_datum": "not_declared", "note": "come il DTM 2023: EPSG:7791 assunto dal prefisso 32_; datum verticale non dichiarato"},
   units={"quota": "m"}, fields=[], fetch=lidar("fi_dsm2023"), checks=lambda: [chk("raster ritagliato su area allargata", NORM.joinpath("fi_dsm2023_0.5m.tif").exists(), "vedi report_firenze.json"), chk("foglie presenti", False, "volo di giugno: l'ombra invernale va trattata a parte", warn=True)]),
 "osm": dict(slug="osm_firenze", title="OpenStreetMap, estratto regionale Centro Italia (ritagliato su riquadro + 700 m)", publisher="OpenStreetMap contributors, estratto di un distributore di estratti OSM",
   ckan=None, lacuna="OSM non è su dati.toscana.it (fonte aperta esterna, ODbL): marciapiedi, attraversamenti e ingressi non hanno altra fonte nel catalogo.",
   dataset_url="https://download.geofabrik.de/europe/italy/centro.html", res=OSM_URL, origin="crowdsourced",
   lic=lic("clear", "ODbL-1.0", "https://www.openstreetmap.org/copyright", "Dati OpenStreetMap sotto ODbL.", use="redistribution"),
   period={"note": "stato di OpenStreetMap al 2026-10-08 (timestamp dell'estratto), senza data di rilievo per oggetto"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lon/lat trattati come RDN2008 geografico (scarto misurato a Pisa: mediana 0,08 m)"},
   units={"length_m": "m", "area_m2": "m2"}, fields=["id", "highway", "sidewalk", "crossing", "entrance", "building", "height"], fetch=osm,
   checks=lambda: [chk("strade in area allargata", (n("osm_firenze.gpkg", "highway") or 0) > 0, f"{n('osm_firenze.gpkg', 'highway')} tratti"),
                   chk("nodi con tag in area allargata", (n("osm_firenze.gpkg", "points") or 0) > 0, f"{n('osm_firenze.gpkg', 'points')} nodi"),
                   chk("edifici in area allargata", (n("osm_firenze.gpkg", "buildings") or 0) > 0, f"{n('osm_firenze.gpkg', 'buildings')} edifici"),
                   chk("marciapiedi e ingressi", False, "pochi (audit rete: 1,9 km di footway=sidewalk, 5 ingressi in FB)", warn=True)]),
 "gtfs_tram": dict(slug="gtfs_gest_firenze", title="GTFS tram (GEST), Firenze", publisher="Regione Toscana / GEST", ckan="rt-oraritb",
   res=CKAN + "8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/1f62d551-65f4-49f8-9a99-e19b02077be3/download/gest.gtfs", origin="official_download",
   lic=lic("clear_with_reserve", "cc-by", CKAN + "rt-oraritb", "Campo license_id della scheda del catalogo regionale: 'cc-by'.", "La risorsa GEST non porta licenza e la versione CC non è indicata: vale solo il campo della scheda."),
   period={"start": "2026-08-10", "end": "2026-12-30", "note": "minimo e massimo di calendar_dates.txt (nessun feed_info.txt); contiene solo T2 e T1.3, la T1 non compare"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lat/lon come da specifica GTFS"}, units={"stop_lat": "deg", "stop_lon": "deg", "trips_on_ref_date": "count"},
   fields=["stop_id", "stop_code", "stop_name", "wheelchair_boarding"], fetch=gtfs("gtfs_gest_firenze", CKAN + "8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/1f62d551-65f4-49f8-9a99-e19b02077be3/download/gest.gtfs", "gest.gtfs.zip"),
   checks=lambda: [chk("fermate in area allargata", (n("gtfs_gest_firenze.gpkg", "stops") or 0) > 0, f"{n('gtfs_gest_firenze.gpkg', 'stops')} fermate"), chk("linea T1", False, "assente dal feed (solo T2 e T1.3)", warn=True)]),
 "gtfs_bus": dict(slug="gtfs_at_firenze", title="GTFS Autolinee Toscane, copia di Firenze", publisher="Regione Toscana / Autolinee Toscane", ckan="rt-oraritb",
   res="https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs", origin="official_download",
   lic=lic("clear_with_reserve", "cc-by", CKAN + "rt-oraritb", "Scheda del catalogo regionale: 'cc-by'; risorsa Autolinee Toscane: CC BY 4.0.", "Versione CC non indicata sulla scheda e condizioni specifiche del feed non trovate: vale il campo del catalogo."),
   period={"start": "2026-10-09", "end": "2026-10-29", "note": "finestra mobile di tre settimane: feed_start_date e feed_end_date da feed_info.txt"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lat/lon come da specifica GTFS"}, units={"stop_lat": "deg", "stop_lon": "deg", "trips_on_ref_date": "count"},
   fields=["stop_id", "stop_code", "stop_name", "wheelchair_boarding"], fetch=gtfs("gtfs_at_firenze", "https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs", "gtfs.zip"),
   checks=lambda: [chk("fermate in area allargata", (n("gtfs_at_firenze.gpkg", "stops") or 0) > 0, f"{n('gtfs_at_firenze.gpkg', 'stops')} fermate"), chk("scadenza", False, "il feed scade il 2026-10-29: rifare lo snapshot per ogni uso dopo quella data (la copia dell'audit scadeva il 2026-10-25)", warn=True)]),
 "tram_fermate": dict(slug="fi_tram_fermate", title="Fermate tram, Comune di Firenze", publisher="Comune di Firenze", ckan="607b8031-252b-4442-950a-7b4452d9db8f",
   res=DG + "shp/tram_fermate.zip", origin="official_download", lic=BY("607b8031-252b-4442-950a-7b4452d9db8f"),
   period={"note": "dato dichiarato del 2025-03-11"}, crs={"declared": "undeclared", "vertical_datum": "not_declared", "note": "CRS letto dal .prj dello shapefile e convertito in EPSG:7791"},
   units={}, fields=[], fetch=dl("fi_tram_fermate", DG + "shp/tram_fermate.zip", "tram_fermate.zip", "application/zip", "dato dichiarato del 2025-03-11"),
   checks=lambda: [chk("fermate in area allargata", (n("fi_tram_fermate.gpkg", "tram_fermate") or 0) > 0, f"{n('fi_tram_fermate.gpkg', 'tram_fermate')} fermate")]),
 "scuole": dict(slug="fi_scuole_statali", title="Anagrafe scuole statali 2026/27 (MIM, ripubblicata dal Comune di Firenze)", publisher="Comune di Firenze (dati MIM)", ckan="anagrafica-scuole-statali-2026_27",
   res=DG + "json/miur_scuole_statali_2026_27.json", origin="official_download",
   lic=lic("clear_with_reserve", "IODL-2.0", CKAN + "anagrafica-scuole-statali-2026_27", "Scheda e risorse del catalogo regionale: IODL 2.0 (package_show del 2026-10-09).",
           "IODL 2.0 non è CC BY: richiede attribuzione; l'equivalenza con CC BY e la compatibilità con gli altri layer non sono state valutate giuridicamente. La fonte primaria MIM non ha licenza verificata.", use="internal_prototype"),
   period={"note": "anagrafe anno scolastico 2026/27, dato dichiarato del 2026-09-18"}, crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lon/lat trattati come RDN2008 geografico; due coordinate MIM sbagliate nel contesto (audit destinazioni)"},
   units={}, fields=["codicescuo", "nome", "indirizzo", "tipologia"], fetch=dl("fi_scuole_statali", DG + "json/miur_scuole_statali_2026_27.json", "miur_scuole_statali_2026_27.json", "application/geo+json", "anagrafe 2026/27, dato dichiarato del 2026-09-18"),
   checks=lambda: [chk("scuole in area allargata", (n("fi_scuole_statali.gpkg", "scuole") or 0) > 0, f"{n('fi_scuole_statali.gpkg', 'scuole')} punti"), chk("coordinate", False, "FIMM700011 cade sul punto di Vamba (errore di geocodifica noto)", warn=True)]),
 "cm_edscol": dict(slug="cm_edscol_firenze", title="Edifici scolastici della Città metropolitana di Firenze (poligoni e accessi)", publisher="Città metropolitana di Firenze", ckan="edifici-scolastici-citta-metropolitana-di-firenze",
   res="https://dati.cittametropolitana.fi.it/geonetwork/srv/api/records/cmfi:a507767e-63e2-4856-9711-5e9a9ea96a76/attachments/form_ed_scolastici.zip", origin="official_download",
   lic=lic("clear_with_reserve", "cc-by", CKAN + "edifici-scolastici-citta-metropolitana-di-firenze", "Campo license_id della scheda: 'cc-by'.", "Le risorse non portano licenza e la versione CC non è indicata: vale solo il campo della scheda.", use="internal_prototype"),
   period={"note": "dato dichiarato del 2014-02-13, scheda aggiornata il 2026-04-24, frequenza IRREG"}, crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791"},
   units={}, fields=["COD_MECCAN", "GRADO", "DENOM", "CODICE", "TIPOLOGIA", "DENOMINAZI"],
   fetch=dl("cm_edscol_firenze", ["https://dati.cittametropolitana.fi.it/geonetwork/srv/api/records/cmfi:a507767e-63e2-4856-9711-5e9a9ea96a76/attachments/form_ed_scolastici.zip",
                                  "https://dati.cittametropolitana.fi.it/geonetwork/srv/api/records/cmfi:a507767e-63e2-4856-9711-5e9a9ea96a76/attachments/form_ed_scolastici_accessi.zip"],
            ["form_ed_scolastici.zip", "form_ed_scolastici_accessi.zip"], "application/zip", "dato dichiarato del 2014-02-13, scheda del 2026-04-24"),
   checks=lambda: [chk("edifici in area allargata", (n("cm_edscol_firenze.gpkg", "edifici_scolastici") or 0) > 0, f"{n('cm_edscol_firenze.gpkg', 'edifici_scolastici')} poligoni"),
                   chk("accessi in area allargata", (n("cm_edscol_firenze.gpkg", "accessi") or 0) > 0, f"{n('cm_edscol_firenze.gpkg', 'accessi')} punti"),
                   chk("gradi coperti", True, "tutti i gradi, dai nidi alle superiori (chiude il dubbio di F01 sulle sole secondarie)")]),
 "catasto": dict(slug="fi_catasto", title="Cartografia catastale WFS (particelle e fogli), Agenzia delle Entrate, riquadro FP", publisher="Agenzia delle Entrate",
   ckan=None, lacuna="La cartografia catastale non è su dati.toscana.it: è un servizio nazionale dell'Agenzia delle Entrate (WFS INSPIRE).",
   dataset_url="https://www.agenziaentrate.gov.it/portale/cartografia-catastale-wfs", res=CATASTO, origin="ogc_service",
   lic=lic("clear", "CC-BY-4.0", "https://www.agenziaentrate.gov.it/portale/cartografia-catastale-wfs",
           "Pagina del servizio: dati sotto CC BY 4.0 con citazione obbligatoria della titolarità: \"Agenzia delle Entrate, cartografia catastale WFS, CC BY 4.0\".", use="redistribution"),
   period={"note": "aggiornamento dichiarato per foglio (BEGINLIFESPANVERSION dei fogli, il più recente 2026-10-06 nel riquadro); stato alla data di scarico"},
   crs={"declared": "EPSG:6706", "vertical_datum": "not_declared", "note": "GML in RDN2008 geografico con assi lat,lon (unica proiezione offerta); convertito in EPSG:7791. Scarico limitato al riquadro FP (particelle che lo intersecano)"},
   units={}, fields=["NATIONALCADASTRALREFERENCE", "LABEL", "NATIONALCADASTRALZONINGREFERENCE", "BEGINLIFESPANVERSION", "ORIGINALMAPSCALEDENOMINATOR"], fetch=catasto,
   checks=lambda: [*tp(("fi_catasto_particelle.gpkg", "particelle"))(), *tp(("fi_catasto_fogli.gpkg", "fogli"))(),
                   chk("fabbricati", False, "il servizio non pubblica i fabbricati: solo particelle (con strade e acque) e fogli", warn=True),
                   chk("valore dei confini", False, "cartografia catastale: confini indicativi, non probatori", warn=True)]),
 "landsat_st": dict(slug="fi_landsat_st", title="Landsat 8-9 Collection 2 Level-2, temperatura delle superfici (ST_B10) e QA_PIXEL, estati 2023-2026, riquadro FP", publisher="U.S. Geological Survey (copia di Microsoft Planetary Computer)",
   ckan=None, lacuna="Landsat non è su dati.toscana.it: prodotto dell'USGS, letto dalla copia pubblica del catalogo STAC di Microsoft Planetary Computer (accesso anonimo).",
   dataset_url="https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature", res=STAC + "/collections/landsat-c2-l2", origin="official_download",
   lic=lic("clear", "public-domain", "https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products",
           "Pagina USGS: \"There are no restrictions on the use of Landsat products.\" Politica dati USGS: \"All public domain imagery may be used, shared, transferred, or redistributed without restriction.\" "
           "Citazione chiesta: DOI 10.5066/P9OGBGM6 (Landsat 8-9 OLI/TIRS C2 L2); credito suggerito \"Landsat Collection 2 Level-2 image courtesy of the U.S. Geological Survey\".",
           "Il canale di accesso (Planetary Computer) dichiara license \"proprietary\" con collegamento alla politica USGS (Public Domain); il token SAS anonimo è personale e non cedibile (Supplemental Terms): non va scritto nei file.", use="redistribution"),
   period={"start": "2023-06-01", "end": "2026-09-30", "note": "passaggi estivi (giugno-settembre) 2023-2026 alle 09:58-09:59 UTC circa; tenute solo le date con almeno l'80% di celle valide sul riquadro FP"},
   crs={"declared": "EPSG:32632", "vertical_datum": "not_declared", "note": "COG in WGS84 UTM 32N a 30 m; ritagli ricampionati per vicinanza sul reticolo EPSG:7791 a 30 m della scena (scarto fra i due sistemi sotto il metro)"},
   units={"st_b10": "K = DN x 0,00341802 + 149,0 (nodata 0); convertito in °C", "qa_pixel": "bit"}, fields=["ST_B10", "QA_PIXEL"], fetch=landsat,
   checks=lambda: [chk("date valide sul riquadro", NORM.joinpath("fi_landsat_st.json").exists(), "vedi data/norm/firenze_novoli/fi_landsat_st.json"),
                   chk("risoluzione", False, "banda termica misurata a 100 m e distribuita a 30 m: il dettaglio fra 30 e 100 m non è misurato", warn=True),
                   chk("saturazione termica", False, "QA_RADSAT non ha un bit per la banda 10 su Landsat 8-9: la saturazione non si controlla", warn=True)]),
 "sir_termo": dict(slug="sir_termo_firenze", title="Temperatura dell'aria giornaliera (massima e minima), stazione SIR Firenze Università TOS01001096", publisher="Regione Toscana, Settore Idrologico e Geologico Regionale (SIR)",
   ckan="termometri", res=SIR, origin="official_download",
   lic=lic("clear_with_reserve", "CC-BY-SA-4.0", "https://www.sir.toscana.it/licenze",
           "Pagina Licenze del SIR: \"I dati pubblicati dal Settore Idrologico e Geologico Regionale (SIR) - Regione Toscana sono distribuiti con licenza Creative Commons Attribuzione-CondividiAlloStessoModo 4.0 Internazionale (CC BY-SA 4.0)\". "
           "Attribuzione: \"Settore Idrologico e Geologico Regionale (SIR) - Regione Toscana. Dati distribuiti con licenza Creative Commons CC BY-SA 4.0.\"",
           "Condividi allo stesso modo: i derivati di questo livello (meteo.json.gz) vanno distribuiti in CC BY-SA 4.0. La scheda del catalogo (anagrafica stazioni) dice cc-by-sa, le sue risorse A1_PublicDomain: vale la pagina del SIR. Dati dichiarati pre-validati.", use="redistribution"),
   period={"start": "2023-01-01", "note": "massime e minime giornaliere 2023-2026 della stazione, dati pre-validati; ora solare"},
   crs={"declared": "EPSG:3003", "vertical_datum": "declared", "note": "posizione della stazione dall'anagrafica WFS del SIR (Gauss-Boaga, quota 84 m s.l.m.), convertita in EPSG:7791"},
   units={"tmax": "°C", "tmin": "°C"}, fields=["Tmax", "Tmin"], fetch=sir,
   checks=lambda: [chk("serie normalizzata", NORM.joinpath("sir_termo_firenze.json").exists(), "vedi data/norm/firenze_novoli/sir_termo_firenze.json"),
                   chk("distanza dal riquadro", True, "1,3 km a est del riquadro FP, in città: rappresentativa della zona, non del singolo isolato"),
                   chk("validazione", False, "il SIR dichiara i dati pre-validati: possono cambiare", warn=True)]),
 "arpat": dict(slug="arpat_aria", title="Qualità dell'aria ARPAT, dati orari 2025 della rete regionale (stazioni del comune di Firenze)", publisher="ARPAT, Agenzia regionale per la protezione ambientale della Toscana",
   ckan=None, lacuna="I dati orari e l'anagrafica delle stazioni non sono su dati.toscana.it: sul catalogo ARPAT ha solo indicatori annuali fino al 2022-2024 e la risorsa \"Struttura della rete di monitoraggio della qualità dell'aria in Toscana\" (cc-by) punta a un JSON che oggi rimanda alla home del sito. Da segnalare: link morto e archivio orario da pubblicare sul catalogo.",
   dataset_url=ARPAT + "datiemappe/qualita-dellaria-dati-orari/", res=ARPAT + f"app/uploads/2026/05/FI_DATI_QA_{ARPAT_ANNO}_CSV.zip", origin="official_download",
   lic=lic("clear_with_reserve", "non specificata per i dati orari (note legali ARPAT)", ARPAT + "note-legali",
           "Note legali ARPAT: \"Salvo dove diversamente specificato, i contenuti del sito Web di ARPAT sono distribuiti con licenza Creative Commons Attribuzione – Non commerciale – Condividi allo stesso modo 3.0 Italia (CC BY-NC-SA 3.0)\"; "
           "\"Ai sensi delle Linee Guida Nazionali per la Valorizzazione del Patrimonio Informativo Pubblico, le banche banche dati distribuite in formato vettoriale sono rilasciate – dove non diversamente specificato – con licenza Creative Commons Attribution 4.0 International (CC-BY 4.0)\"; "
           "\"Salvo diversa indicazione le informazioni contenute nel sito Web ARPAT sono fornite a scopo informativo.\" La pagina dei dati orari non indica una licenza. Indicatori annuali PM10 e NO2 (solo per il tipo di stazione): schede del catalogo regionale cc-by.",
           "Non è scritto quale delle due licenze delle note legali vale per i CSV orari: se vale CC BY-NC-SA 3.0, niente uso commerciale e derivati nella stessa licenza. Uso deciso da Luca il 10/10/2026 (D21): pubblicato anche nella scena online, con entrambe le licenze dichiarate; per uso commerciale chiedere conferma ad ARPAT."),
   period={"start": f"{ARPAT_ANNO}-01-01", "end": f"{ARPAT_ANNO}-12-31", "note": "archivio orario 2025 (PM10 e PM2,5 giornalieri), dichiarato validato dall'intero ciclo di validazione; il 2026 non è pubblicato come download"},
   crs={"declared": "undeclared", "vertical_datum": "not_declared", "note": "coordinate delle pagine stazione \"N:... - E:...\" senza sistema dichiarato: Gauss-Boaga fuso Ovest (EPSG:3003) dedotto dai valori (FI-MOSSE cade in Via delle Mosse); convertite in EPSG:7791 come i civici"},
   units={"media_oraria": "µg/m³ a 20 °C (CO mg/m³)", "media_giornaliera": "µg/m³ a temperatura ambiente (PM10, PM2,5)"},
   fields=["STAZIONE", "PARAMETRO", "DATA (formato AAAAMMGG)", "ORA FINE MISURA (solare)", "MEDIA ORARIA", "VALIDITA'"], fetch=arpat,
   checks=lambda: [chk("stazioni selezionate", (n("arpat_aria.gpkg", "stazioni") or 0) > 0, f"{n('arpat_aria.gpkg', 'stazioni')} stazioni della rete regionale nel comune di Firenze (nessun'altra entro 3 km dal riquadro)"),
                   chk("stazioni nel riquadro FP", False, "nessuna: la più vicina (FI-MOSSE) è a circa 750 m; valori di stazione, non rappresentano il riquadro", warn=True),
                   chk("anno in corso", False, "il 2026 non è pubblicato come download: passa solo dall'API dell'app, esclusa", warn=True)]),
    }

def acquire(keys):
    s = S()
    for k in keys or s:
        d = s[k]; fn = d["fetch"]
        def run(fn=fn, d=d):
            r = fn(); r["license_state"] = d["lic"]["state"]; return r
        record("src_" + d["slug"], d["slug"], run)

def ckan_live(ids):
    """T17: package_show pubblico dei dataset; licenza di scheda e di risorse e data di modifica."""
    out = {}
    for i in sorted(set(ids)):
        r = requests.get("https://dati.toscana.it/api/3/action/package_show", params={"id": i}, headers=UA, timeout=60).json()["result"]
        out[i] = {"nome": r["name"], "titolo": r["title"], "license_id": r.get("license_id"), "licenza_risorse": sorted({x.get("license_type") or "assente" for x in r["resources"]}),
                  "metadata_modified": r["metadata_modified"][:10]}
    return out

def sources():
    SRCDIR.mkdir(exist_ok=True); s = S(); live = ckan_live([d["ckan"] for d in s.values() if d["ckan"]]); t17 = []
    for k, d in s.items():
        sid = "src_" + d["slug"]
        assert d["ckan"] or d.get("lacuna"), f"{sid}: T17 senza dataset del catalogo e senza lacuna motivata"
        assert d["lic"].get("evidence_url") and d["lic"]["state"] in ("clear", "clear_with_reserve"), f"{sid}: licenza non verificata"
        prov = {"origin": d["origin"], "note": "T17: dataset " + CKAN + d["ckan"] if d["ckan"] else "T17: lacuna del catalogo. " + d["lacuna"]}
        rec = {"source_id": sid, "title": d["title"], "publisher": d["publisher"], "dataset_url": (CKAN + d["ckan"]) if d["ckan"] else d["dataset_url"], "resource_url": d["res"],
               "provenance": prov, "license": d["lic"], "content_period": d["period"], "crs": d["crs"], "units": d["units"], "checks": d["checks"]()}
        if d["fields"]: rec["schema_fields"] = d["fields"]
        json.dump(rec, open(SRCDIR / f"{sid}.json", "w"), indent=1, ensure_ascii=False)
        t17.append({"source_id": sid, "dataset_catalogo": CKAN + d["ckan"] if d["ckan"] else None, "catalogo_live": live.get(d["ckan"]), "lacuna": d.get("lacuna"), "licenza_dichiarata": d["lic"]["state"]})
    json.dump({"verificato_il": DAY, "fonti": t17}, open(ROOT / "pipeline/t17_firenze.json", "w"), indent=1, ensure_ascii=False)
    print(len(s), "record di fonte;", sum(1 for t in t17 if t["lacuna"]), "lacune del catalogo")

def baseline(force=False):
    """Prima baseline di Firenze: ultimo snapshot valido di ogni fonte."""
    bid = f"bas_firenze_novoli_{DAY}"; p = ROOT / "pipeline/baselines" / f"{bid}.json"
    if p.exists() and not force:   # congelata: se uno snapshot è stato rifatto (es. il WFS si riscarica a ogni acquire) lo segnala
        diff = [x["snapshot_id"] for x in json.load(open(p))["snapshot"] if json.load(open(SNAP / f"{x['snapshot_id']}.json"))["sha256"] != x["sha256"]]
        return print(f"{p.name} esiste: baseline congelata, usare --force per rifarla" + (f". ATTENZIONE, snapshot diversi dalla baseline: {diff}" if diff else ""))
    snaps = []
    for k, d in S().items():
        s = json.load(open(SNAP / f"snp_{d['slug']}_{DAY}.json")); assert s["status"] == "ok", s["snapshot_id"]
        snaps.append({"snapshot_id": s["snapshot_id"], "source_id": s["source_id"], "sha256": s["sha256"], "license_state": s["license_state"]})
    p.parent.mkdir(exist_ok=True)
    json.dump({"baseline_id": bid, "version": 1, "frozen_at": lib.now(), "aoi_id": AOI["aoi_id"],
               "descrizione": "Prima baseline di Firenze Novoli - Firenze Nova (riquadro FP D13, rete con margine di 700 m): snapshot di F03.",
               "snapshot": snaps}, open(p, "w"), indent=1, ensure_ascii=False)
    print(p.name, len(snaps), "snapshot")

if __name__ == "__main__":
    a, rest = (sys.argv[1] if len(sys.argv) > 1 else "acquire"), sys.argv[2:]
    {"acquire": lambda: acquire(rest), "sources": sources, "baseline": lambda: baseline("--force" in rest)}[a]()
