"""F09: asset precotti della scena 3D di Firenze Novoli (sito statico, nessun server a runtime).

Uso: pipeline/.venv/bin/python scene/firenze_novoli/build.py [--out DIR] [--analysis DIR] [--shadow DIR]

Piano del motore (metri): x = est, y = alto, z = -nord; origine = centro del riquadro FP in EPSG:7791
(lon/lat degli open data trattati come RDN2008, come nel resto della pipeline).
Ogni asset è JSON compresso gzip (.json.gz); i vettori numerici grandi sono Float32 in base64.
L'indice assets/index.json riporta sha256 e dimensione di ogni asset, le fonti e i limiti.
"""
import argparse, base64, glob, gzip, hashlib, json, math, os, pathlib, re, shutil, sys, tempfile, datetime as dt
import numpy as np, geopandas as gpd, rasterio, rasterio.windows, shapely
from rasterio.enums import Resampling
from shapely.geometry import box, Point, Polygon
from shapely.geometry.polygon import orient
from pyproj import Transformer

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from lib import AOI, NORM  # area predefinita Firenze (D15)

STEP = 10.0          # passo del terreno, m
MARGINE = 110.0      # terreno oltre il riquadro, m: copre la fermata T2 San Donato - Università, circa 100 m a sud (D20)
ARR = 2              # decimali delle coordinate (cm)
BASSO = 1.5          # i volumi scendono 1,5 m sotto la quota di base (pendenze del terreno a 10 m)

E0, N0, E1, N1 = AOI["z2_en"]
CE, CN = (E0 + E1) / 2, (N0 + N1) / 2
to_en = Transformer.from_crs(6706, 7791, always_xy=True)
to_ll = Transformer.from_crs(7791, 6706, always_xy=True)
LON0, LAT0 = to_ll.transform(CE, CN)
FP = box(E0, N0, E1, N1)

# livelli della scena: etichetta e fonti (id di pipeline/sources) mostrate nella scheda
LIVELLI = {
    "terreno": {"etichetta": "Terreno", "fonti": ["src_fi_dtm2023", "src_osm_firenze"]},
    "etichette": {"etichetta": "Nomi dei luoghi", "fonti": ["src_osm_firenze"]},
    "edifici": {"etichetta": "Edifici", "fonti": ["src_rt_uv_firenze_novoli", "src_fi_dsm2023", "src_fi_dtm2023", "src_osm_firenze"]},
    "alberi": {"etichetta": "Alberi", "fonti": ["src_fi_alberi", "src_fi_dsm2023", "src_fi_dtm2023"]},
    "rete": {"etichetta": "Rete pedonale", "fonti": ["src_osm_firenze"]},
    "destinazioni": {"etichetta": "Destinazioni dei calcoli", "fonti": ["src_osm_firenze", "src_cm_edscol_firenze", "src_fi_scuole_statali", "src_gtfs_gest_firenze"]},
    "tram": {"etichetta": "Fermate tram", "fonti": ["src_fi_tram_fermate", "src_gtfs_gest_firenze"]},
    "scuole": {"etichetta": "Scuole statali", "fonti": ["src_fi_scuole_statali"]},
    "rifugi": {"etichetta": "Rifugi climatici", "fonti": ["src_fi_rifugi_aree", "src_fi_rifugi_biblioteche", "src_fi_civici"]},
    "percorsi_rifugi": {"etichetta": "Percorsi verso i rifugi (da verificare)", "fonti": ["src_osm_firenze", "src_fi_rifugi_aree", "src_fi_rifugi_biblioteche", "src_fi_civici"]},
    "attesa": {"etichetta": "Aree di attesa (protezione civile)", "fonti": ["src_fi_aree_attesa"]},
    "assistenza": {"etichetta": "Aree di assistenza (protezione civile)", "fonti": ["src_fi_aree_assistenza"]},
    "barriere": {"etichetta": "Barriere architettoniche", "fonti": ["src_fi_barriere"]},
    "farmacie": {"etichetta": "Farmacie", "fonti": ["src_fi_farmacie"]},
    "sosta_disabili": {"etichetta": "Stalli per disabili", "fonti": ["src_fi_sosta_disabili"]},
    "bike_sharing": {"etichetta": "Sosta del bike sharing", "fonti": ["src_fi_bike_sharing"]},
    "car_sharing": {"etichetta": "Posti del car sharing", "fonti": ["src_fi_car_sharing"]},
    "scudo_verde": {"etichetta": "Varchi dello Scudo Verde", "fonti": ["src_fi_scudo_verde"]},
    "zone30": {"etichetta": "Strade in zona 30", "fonti": ["src_fi_zone30"]},
    "verde": {"etichetta": "Aree verdi del Comune", "fonti": ["src_fi_aree_verdi"]},
    "giochi": {"etichetta": "Aree giochi", "fonti": ["src_fi_aree_giochi"]},
    "cani": {"etichetta": "Aree cani", "fonti": ["src_fi_aree_cani"]},
    "sport": {"etichetta": "Aree sportive", "fonti": ["src_fi_aree_sportive"]},
    "idraulica": {"etichetta": "Pericolosità idraulica (PGRA)", "fonti": ["src_fi_pericolosita_idraulica"]},
    "alluvione1966": {"etichetta": "Alluvione del 1966", "fonti": ["src_fi_allagate1966"]},
    "acustica": {"etichetta": "Classi acustiche (PCCA)", "fonti": ["src_fi_pcca"]},
    "residenti": {"etichetta": "Residenti per sezione (censimento 2011)", "fonti": ["src_fi_sezioni2011", "src_rt_censimento2011"]},
    "accessibilita": {"etichetta": "Accessibilità (minuti a piedi)", "fonti": ["src_fi_civici", "src_osm_firenze"]},
    "ombra": {"etichetta": "Ombra sui percorsi", "fonti": ["src_osm_firenze", "src_fi_dsm2023"]},
    "ombra_rifugi": {"etichetta": "Arrivo al rifugio all'ombra (14 del 15 luglio)", "fonti": ["src_fi_civici", "src_osm_firenze", "src_rt_uv_firenze_novoli", "src_fi_dsm2023", "src_fi_alberi",
                                                                              "src_fi_rifugi_aree", "src_fi_rifugi_biblioteche", "src_fi_sezioni2011", "src_rt_censimento2011"]},
    "scenari": {"etichetta": "Scenari (interventi ipotetici)", "fonti": []},
    "catasto": {"etichetta": "Particelle catastali", "fonti": ["src_fi_catasto"]},
    "temperature": {"etichetta": "Temperatura delle superfici", "fonti": ["src_fi_landsat_st"]},
    "meteo": {"etichetta": "Temperatura dell'aria (stazione SIR)", "fonti": ["src_sir_termo_firenze"]},
    "aria": {"etichetta": "Qualità dell'aria (stazioni ARPAT)", "fonti": ["src_arpat_aria"]},
}

LIMITI = [
    "Altezze degli edifici: quota LiDAR 2023 (DSM meno DTM) confrontata con le unità volumetriche regionali del 2011. Sono volumi, non modelli architettonici: nessun tetto a falde, nessun portico.",
    "Portici e volumi sospesi: nessuna fonte, restano \"ignoto\" e non sono disegnati. I volumi scendono di 1,5 m sotto la quota di base per seguire la pendenza del terreno a 10 m.",
    "Edifici non più presenti nel 2023 (probabili demolizioni) sono disegnati in grigio scuro e segnalati nella scheda.",
    "Alberi: il censimento comunale non riporta altezza né chioma. Altezza e chioma sono misurate dal LiDAR dove ci sono celle sufficienti, altrimenti stimate (classe indicata nella scheda). Il tronco è disegnato con almeno 25 cm di diametro per renderlo visibile.",
    "Terreno: DTM LiDAR 2023 ricampionato a passo 10 m. Verde, acqua e strade sono disegnati da OpenStreetMap: larghezze delle strade indicative per classe, non misurate.",
    "Nessuna ortofoto: le ortofoto regionali 2016, 2019 e 2022 sono concesse alla Regione Toscana per fini istituzionali e non se ne consente il download (verificato il 10 ottobre 2026). Non c'è un'ortofoto con licenza aperta per Firenze.",
    "Colori degli edifici: tetti in tono terracotta a scopo di lettura, non il colore reale. Tono più scuro per altezza misurata, più chiaro per altezza derivata.",
    "Ombre: sono quelle del motore grafico (sole calcolato per posizione e data), a scopo illustrativo. Non sono un calcolo analitico: gli alberi proiettano chiome piene.",
    "Destinazioni dei calcoli e loro ingressi: tutti da verificare sul campo. Condizioni di accesso, orari e cancelli non sono noti.",
    "Rifugi climatici: i 7 rifugi del Comune entro 700 m dal riquadro (biblioteche e aree fresche; il Parco delle Cascine è escluso perché i suoi ingressi non sono fra i civici). Ingresso = civico all'indirizzo dichiarato dal Comune, non verificato; orari ignoti. Percorsi verso i rifugi: asse della rete, stato da verificare sul posto.",
    "Rete pedonale da OpenStreetMap: stato del marciapiede \"ignoto\" dove non dichiarato, nessuna inferenza.",
    "Protezione civile: aree di attesa e di assistenza del piano comunale, file del 2024 (sopralluoghi delle aree di assistenza del 2021). Sono poche per tutta la città: la scena mostra tutte quelle entro 700 m dal riquadro: in scena quelle sul terreno disegnato, in elenco con la distanza quelle più lontane. Le classi di pericolosità sono i codici della fonte, senza legenda nel pacchetto. Non è il percorso di evacuazione e non indica quale area spetta a quale via.",
    "Servizi (farmacie, stalli per disabili, bike e car sharing, varchi dello Scudo Verde) e aree giochi, cani e sportive: dati del Comune di Firenze, solo quelli sul terreno disegnato. Gli stalli dicono dove sono, non se sono liberi; le farmacie non hanno orari né turni.",
    "Aree verdi: tutte quelle gestite dal Comune, comprese rotonde, spartitraffico e aiuole non fruibili; il verde privato non c'è.",
    "Strade in zona 30: porzioni di carreggiata dove vale il limite di 30 km/h, non perimetri di zona.",
    "Pericolosità idraulica: mappa del Piano di gestione del rischio alluvioni pubblicata dalla protezione civile comunale. Le classi sono i codici della fonte (PS_PERALL_1, 2, 3), senza legenda nel pacchetto. È pianificazione, non la previsione di un evento. Alluvione del 1966: profondità dell'acqua di un evento storico, non uno scenario attuale.",
    "Classi acustiche: limiti di legge del piano comunale di classificazione acustica, non rumore misurato.",
    "Residenti: censimento Istat 2011 per sezione (dati della Regione Toscana), quindici anni fa. Densità calcolata sulla superficie della sezione, strade e verde compresi. Non c'è un dato per sezione più recente sul catalogo regionale.",
    "Barriere architettoniche: rilievo del 2013, grado di accessibilità dell'edificio, non dell'ostacolo sul percorso.",
    "Livelli Accessibilità e Ombra sui percorsi: mostrano solo i dati prodotti dai moduli di analisi, se presenti. Non sono calcolati dalla scena.",
    "Particelle catastali: cartografia catastale dell'Agenzia delle Entrate, confini indicativi e non probatori. I fabbricati non ci sono nel servizio. La particella di un edificio è quella che ne contiene almeno metà della superficie: aggancio geometrico, non verificato sugli atti.",
    "Temperatura delle superfici (Landsat 8 e 9): è la temperatura dei tetti, delle strade e del verde, non dell'aria. Misura termica a 100 m ricampionata a 30 m: il dettaglio sotto i 100 m non è misurato. Solo giorni sereni sul riquadro (almeno l'80% di celle valide), passaggio del satellite verso le 10:00 UTC (12:00 ora legale), non l'ora più calda.",
    "Temperatura dell'aria: massima e minima giornaliera della stazione SIR Firenze Università, 1,3 km a est del riquadro, dati pre-validati. È un valore per tutta la zona, non per la singola strada, e non è misurata all'ora del passaggio del satellite.",
    "Qualità dell'aria: valori delle stazioni ARPAT, non una mappa e nessuna interpolazione. Nessuna stazione sta nel riquadro: la più vicina, FI-MOSSE (traffico), è a circa 750 m. Dati orari del 2025, validati da ARPAT (archivio pubblico, ora solare); il 2026 non è pubblicato come download. Superamenti contati sul solo 2025: per l'ozono la norma usa la media su 3 anni. Sotto il 90% di dati validi la media annua non vale ai fini di legge (FI-GRAMSCI è disattivata da marzo 2025 per i lavori della tramvia). ARPAT non specifica la licenza dei dati orari (note legali: CC BY-NC-SA 3.0 IT per i contenuti del sito, CC BY 4.0 per le banche dati): uso deciso il 10 ottobre 2026.",
]

USO = {
    "src_fi_dtm2023": "Terreno e quota di base degli alberi",
    "src_fi_dsm2023": "Altezza degli edifici e delle chiome",
    "src_rt_uv_firenze_novoli": "Impronte e volumi degli edifici",
    "src_osm_firenze": "Rete pedonale, impronte nuove, ingressi, mappa di base (verde, acqua, strade), nomi dei luoghi",
    "src_fi_alberi": "Alberi pubblici",
    "src_fi_tram_fermate": "Fermate tram",
    "src_fi_scuole_statali": "Scuole statali",
    "src_cm_edscol_firenze": "Accessi delle scuole",
    "src_gtfs_gest_firenze": "Punti delle fermate T2",
    "src_fi_rifugi_aree": "Rifugi climatici (aree)",
    "src_fi_rifugi_biblioteche": "Rifugi climatici (biblioteche)",
    "src_fi_aree_attesa": "Aree di attesa della protezione civile",
    "src_fi_aree_assistenza": "Aree di assistenza della protezione civile",
    "src_fi_barriere": "Barriere architettoniche",
    "src_fi_farmacie": "Farmacie",
    "src_fi_sosta_disabili": "Stalli di sosta per disabili",
    "src_fi_bike_sharing": "Aree di sosta del bike sharing",
    "src_fi_car_sharing": "Posti del car sharing",
    "src_fi_scudo_verde": "Varchi dello Scudo Verde",
    "src_fi_zone30": "Strade in zona 30",
    "src_fi_aree_verdi": "Aree verdi del Comune",
    "src_fi_aree_giochi": "Aree giochi",
    "src_fi_aree_cani": "Aree cani",
    "src_fi_aree_sportive": "Aree sportive",
    "src_fi_pericolosita_idraulica": "Pericolosità idraulica (PGRA)",
    "src_fi_allagate1966": "Aree allagate nel 1966",
    "src_fi_pcca": "Classi acustiche del piano comunale",
    "src_fi_sezioni2011": "Confini delle sezioni di censimento 2011",
    "src_rt_censimento2011": "Residenti 2011 per sezione (dati Istat)",
    "src_fi_civici": "Civici dei livelli analitici",
    "src_fi_catasto": "Particelle e fogli catastali, riferimento catastale degli edifici",
    "src_fi_landsat_st": "Temperatura delle superfici per data (Landsat 8 e 9, estati 2023-2026)",
    "src_sir_termo_firenze": "Temperatura dell'aria, massime e minime giornaliere (CC BY-SA 4.0)",
    "src_arpat_aria": "Stazioni e valori della qualità dell'aria 2025 (medie annue, superamenti, ultimo valore)",
}


# data del dato mostrata nella scena: solo quando la fonte la dichiara. Qui c'è solo la frase; le date vengono dal record di fonte
# (content_period start/end di pipeline/sources) o dai dati, così si aggiornano quando si riscarica. La data di aggiornamento della scheda
# del catalogo non è la data del dato (molte schede del Comune portano il 2026-02-11, un ricaricamento del catalogo) e non si mostra
ND = "data del rilievo non dichiarata"
DATA = {
    "src_fi_dtm2023": "volo del {start}", "src_fi_dsm2023": "volo del {start}", "src_rt_uv_firenze_novoli": "volo del {anno}",
    "src_osm_firenze": "stato di OpenStreetMap al {end}", "src_fi_alberi": "aggiornato ogni giorno dal Comune: stato al giorno dello scarico",
    "src_fi_tram_fermate": "dato del {start}", "src_fi_scuole_statali": "dato del {start}", "src_cm_edscol_firenze": "dato del {start}",
    "src_gtfs_gest_firenze": "orari dal {start} al {end}", "src_fi_rifugi_aree": "dato del {start}", "src_fi_rifugi_biblioteche": "dato del {start}",
    "src_fi_aree_attesa": "file del {start}", "src_fi_aree_assistenza": "file del {start}, sopralluoghi del 2021", "src_fi_barriere": "rilievo del {anno}",
    "src_fi_farmacie": ND, "src_fi_sosta_disabili": ND, "src_fi_bike_sharing": ND, "src_fi_car_sharing": ND,
    "src_fi_scudo_verde": "Scudo Verde attivo dal {start}", "src_fi_zone30": ND, "src_fi_aree_verdi": ND, "src_fi_aree_giochi": ND,
    "src_fi_aree_cani": ND, "src_fi_aree_sportive": ND, "src_fi_pericolosita_idraulica": "data della mappa non dichiarata",
    "src_fi_allagate1966": "alluvione del {start}", "src_fi_pcca": "data del piano non dichiarata", "src_fi_sezioni2011": "censimento {anno}",
    "src_rt_censimento2011": "censimento {anno}", "src_fi_civici": ND, "src_fi_catasto": "aggiornamento per foglio, il più recente del {foglio}",
    "src_fi_landsat_st": "estati dal {anno} al {anno_fine}", "src_sir_termo_firenze": "dal {start}, dati pre-validati", "src_arpat_aria": "anno {anno}, dati validati",
}
MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()


def _giorno(d):
    a, m, g = map(int, d[:10].split("-")); return f"{'1°' if g == 1 else g} {MESI[m - 1]} {a}"


def data_dato(sid, cp):
    """Frase di DATA con le date del record di fonte; il catasto prende la data più recente dei fogli."""
    v = {}
    if cp.get("start"): v.update(start=_giorno(cp["start"]), anno=cp["start"][:4])
    if cp.get("end"): v.update(end=_giorno(cp["end"]), anno_fine=cp["end"][:4])
    if "{foglio}" in DATA[sid]: v["foglio"] = _giorno(max(dt.datetime.strptime(x, "%d/%m/%Y") for x in gpd.read_file(NORM / "fi_catasto_fogli.gpkg").BEGINLIFESPANVERSION).strftime("%Y-%m-%d"))
    return re.sub(r"\b(al|dal|del) (8|11) ", r"\1l'\2 ", DATA[sid].format(**v))   # all'8, dell'11; KeyError se la frase chiede una data che il record non dichiara

def loc(e, n):
    """EPSG:7791 -> piano del motore (x, z)."""
    return round(e - CE, ARR), round(-(n - CN), ARR)


def loc_ll(lon, lat):
    return loc(*to_en.transform(lon, lat))


def f32b64(a):
    return base64.b64encode(np.asarray(a, dtype="<f4").tobytes()).decode()


def r(v, n=ARR):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), n)


def s(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)


# --- terreno -----------------------------------------------------------------
def terreno():
    x0, y0, x1, y1 = E0 - MARGINE, N0 - MARGINE, E1 + MARGINE, N1 + MARGINE
    nx, ny = math.ceil((x1 - x0) / STEP), math.ceil((y1 - y0) / STEP)
    x1, y1 = x0 + nx * STEP, y0 + ny * STEP
    with rasterio.open(NORM / "fi_dtm2023_0.5m.tif") as ds:
        win = rasterio.windows.from_bounds(x0, y0, x1, y1, ds.transform)
        z = ds.read(1, window=win, out_shape=(ny, nx), resampling=Resampling.average, boundless=True, fill_value=np.nan)
    z = np.where(np.isfinite(z) & (z > -100), z, np.nan)
    if np.isnan(z).any():
        z = np.where(np.isnan(z), np.nanmean(z), z)
    zref = round(float(z[ny // 2, nx // 2]), 1)
    # x = est, z = -nord: la riga 0 del raster è il nord, quindi z cresce con la riga
    return zref, {
        "nx": nx, "ny": ny, "passo": STEP, "x0": round(x0 + STEP / 2 - CE, 2), "z0": round(-(y1 - STEP / 2 - CN), 2),
        "quote_cm": np.round((z - zref) * 100).astype(int).ravel().tolist(),
        "min_m": round(float(z.min()), 1), "max_m": round(float(z.max()), 1),
    }


# --- edifici ------------------------------------------------------------------
def tris(poly):
    g = shapely.constrained_delaunay_triangles(poly)
    return [t for t in g.geoms] if hasattr(g, "geoms") else [g]


PICCOLE = {"di", "del", "della", "dello", "dei", "degli", "delle", "da", "dal", "e", "in", "a", "al", "alla"}


def via(nome):
    """VIA DELL'ARCOVATA -> Via dell'Arcovata."""
    def w(t, i):
        parti = t.split("'")
        return "'".join(q if (k < len(parti) - 1 and q in ("dell", "d", "l", "all", "nell", "sull")) else q if (i and q in PICCOLE) else q.capitalize()
                        for k, q in enumerate(parti))
    t = " ".join(w(t, i) for i, t in enumerate(nome.lower().split()))
    return re.sub(r"([aeiou])'(?=\s|$)", lambda m: "àèìòù"["aeiou".index(m[1])], t)   # BRAZZA' -> Brazzà


def _civici_e_nomi():
    """Civici comunali (neri prima dei rossi) e nomi OSM degli edifici, per le schede."""
    c = gpd.read_file(NORM / "fi_civici.gpkg")
    # grafia delle vie da OSM (maiuscole dei cognomi, es. Via Carlo Del Prete), altrimenti la regola di via()
    osm_vie = {str(n).upper(): n for n in gpd.read_file(NORM / "osm_firenze.gpkg", layer="highway", columns=["name"]).name.dropna()}
    c["testo"] = [f"{osm_vie.get(a.upper()) or via(a)} {str(n).replace(' R', 'r')}" for a, n in zip(c.STRADA, c.NUMEROCIVI)]
    c["rosso"] = c.NUMEROCIVI.astype(str).str.endswith("R")
    o = gpd.read_file(NORM / "osm_firenze.gpkg", layer="buildings").to_crs(7791)
    o = o[o["name"].notna()]
    return c, shapely.STRtree(c.geometry.values), o, shapely.STRtree(o.geometry.values)


def edifici(zref):
    g = json.load(open(ROOT / "geometry/firenze_novoli/edifici_fp.geojson"))
    civ, tciv, osm, tosm = _civici_e_nomi()
    cat_di = _aggancio_catasto()
    pos, meta = [], []
    for f in g["features"]:
        p = f["properties"]
        geom = shapely.transform(shapely.from_geojson(json.dumps(f["geometry"])), lambda c: np.array([to_en.transform(*q) for q in c]))
        zb, zt = p["z_base"] - zref - BASSO, p["z_base"] - zref + p["h"]
        v = []
        for poly in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
            poly = orient(poly.buffer(0), 1.0) if not poly.is_valid else orient(poly, 1.0)  # esterno antiorario
            if poly.is_empty or poly.area < 0.5:
                continue
            for t in tris(poly):  # tetto
                c = list(orient(t, 1.0).exterior.coords)[:3]
                for e, n in c:
                    x, z = loc(e, n); v += [x, zt, z]
            for ring in [poly.exterior, *poly.interiors]:
                c = list(ring.coords)
                for (e1_, n1_), (e2_, n2_) in zip(c[:-1], c[1:]):  # esterno antiorario, buchi orari: la normale esce sempre dal solido
                    a, b = loc(e1_, n1_), loc(e2_, n2_)
                    A, B = [a[0], zb, a[1]], [b[0], zb, b[1]]
                    At, Bt = [a[0], zt, a[1]], [b[0], zt, b[1]]
                    v += A + B + Bt + A + Bt + At
        if not v:
            continue
        vicini = tciv.query(geom, predicate="dwithin", distance=15)   # civico più vicino entro 15 m, i neri prima dei rossi
        ind = min(vicini, key=lambda i: (civ.rosso.iat[i], civ.geometry.iat[i].distance(geom))) if len(vicini) else None
        dentro = tosm.query(geom.representative_point(), predicate="within")
        pos += v
        meta.append({"id": p["id"], "n": len(v) // 3, "h": r(p["h"]), "h_min": r(p["h_min"]), "h_max": r(p["h_max"]),
                     "z_base": r(p["z_base"]), "classe_h": p["classe_h"], "tipo": p["tipo"], "fonte": p["fonte"],
                     "area_m2": r(p["area_m2"], 1), "presente_2023": bool(p["presente_2023"]), "flag": p.get("flag") or "",
                     "h_uv": r(p.get("h_uv")), "h_lidar": r(p.get("h_lidar")),
                     "ind": civ.testo.iat[ind] if ind is not None else None, "nome": osm["name"].iat[dentro[0]].replace("\n", " ") if len(dentro) else None,
                     "cat": cat_di(geom)})
    return {"n": len(meta), "edifici": meta, "posizioni": f32b64(pos)}


# --- catasto -------------------------------------------------------------------
def _particelle():
    p = gpd.read_file(NORM / "fi_catasto_particelle.gpkg")
    p["geometry"] = shapely.make_valid(p.geometry.values)
    p["rif"] = "foglio " + p.foglio_etichetta + " particella " + p.particella
    return p


def _aggancio_catasto():
    """Funzione edificio (EPSG:7791) -> riferimenti delle particelle che ne contengono almeno il 50% della superficie (di solito una)."""
    p = _particelle()
    t = shapely.STRtree(p.geometry.values)

    def cat_di(geom):
        g = shapely.make_valid(geom)
        if g.area <= 0:
            return []
        return [p.rif.iat[i] for i in t.query(g, predicate="intersects") if p.geometry.iat[i].intersection(g).area / g.area >= 0.5]
    return cat_di


def _contorni(geom):
    """Poligoni come [anello esterno, buchi...], ogni anello [x, z, x, z, ...]; nessuna semplificazione."""
    return [[[c for q in ring.coords for c in loc(*q)] for ring in [poly.exterior, *poly.interiors]]
            for poly in (geom.geoms if hasattr(geom, "geoms") else [geom]) if poly.geom_type == "Polygon"]


def catasto():
    p = _particelle()
    f = gpd.read_file(NORM / "fi_catasto_fogli.gpkg")
    part = [{"rif": row.rif, "f": row.foglio_etichetta, "p": row.particella, "t": row.tipo, "a": _contorni(row.geometry)} for row in p.itertuples()]
    fogli = []
    for row in f.itertuples():
        c = row.geometry.intersection(FP).representative_point() if row.geometry.intersects(FP) else row.geometry.representative_point()
        x, z = loc(c.x, c.y)
        fogli.append({"f": row.foglio_etichetta, "x": x, "z": z, "agg": dt.datetime.strptime(row.BEGINLIFESPANVERSION, "%d/%m/%Y").strftime("%Y-%m-%d"),
                      "a": _contorni(row.geometry)})
    return {"n": len(part), "particelle": part, "fogli": fogli}


# --- alberi --------------------------------------------------------------------
def alberi(zref):
    g = json.load(open(ROOT / "geometry/firenze_novoli/alberi_fp.geojson"))
    out = []
    for f in g["features"]:
        p = f["properties"]
        x, z = loc_ll(*f["geometry"]["coordinates"])
        out.append({"id": p["id"], "x": x, "z": z, "y": r(p["z_base"] - zref), "h": r(p["h"], 1), "h_min": r(p["h_min"], 1), "h_max": r(p["h_max"], 1),
                    "d": r(p["chioma_d"], 1), "d_min": r(p["chioma_d_min"], 1), "d_max": r(p["chioma_d_max"], 1),
                    "imp": r(p.get("imposta"), 1), "td": r(p.get("tronco_d"), 2), "specie": s(p.get("SPECIE")), "circ": r(p.get("CIRCONF_CM"), 1),
                    "h_cls": p["h_cls"], "ch_cls": p["chioma_cls"], "motivo": p.get("motivo_stima") or ""})
    return {"n": len(out), "alberi": out}


# --- rete e punti --------------------------------------------------------------
def rete():
    d = gpd.read_file(NORM / "network/rete_firenze_novoli.gpkg", layer="archi")
    d = d[d.intersects(FP)]
    out = []
    for _, row in d.iterrows():
        gs = row.geometry.geoms if row.geometry.geom_type == "MultiLineString" else [row.geometry]
        for ln in gs:
            pts = [loc(e, n) for e, n in ln.coords]
            out.append({"id": row.edge_id, "nome": s(row["name"]), "hw": s(row.highway), "tipo": s(row.tipo_arco), "marc": s(row.marciapiede_stato),
                        "m": r(row.length_m, 1), "p": [c for q in pts for c in q]})
    return {"n": len(out), "archi": out}


def in_fp(gdf):
    return gdf[gdf.intersects(FP)]


CATEGORIA = {"university": "università", "tram": "fermata del tram", "school": "scuola", "cooling_refuge": "rifugio climatico"}
INGRESSO = {"civico_edificio_ateneo": "civico di un edificio dell'ateneo", "ingresso_fermata": "accesso alla banchina della fermata",
            "accesso_citta_metropolitana": "accesso indicato dalla Città metropolitana", "civico_ingresso_rifugio": "civico all'indirizzo d'ingresso dichiarato dal Comune"}
AGGANCIO = {"agganciato": "collegato"}
VERIFICA = {"da_verificare": "da fare"}


def punti():
    out = []
    # destinazioni e ingressi
    dest = {d["destination_id"]: d for d in json.load(open(ROOT / "network/firenze_novoli/destinazioni.json"))["destinazioni"]}
    g = json.load(open(ROOT / "network/firenze_novoli/destinazioni_ingressi.geojson"))
    for f in g["features"]:
        p = f["properties"]
        if f["geometry"]["type"] != "Point":
            continue
        d = dest.get(p["destinazione"], {})
        x, z = loc_ll(*f["geometry"]["coordinates"])
        out.append({"livello": "destinazioni", "id": p["id"], "nome": p["nome"], "x": x, "z": z,
                    "attr": {"Destinazione": d.get("nome"), "Indirizzo": d.get("indirizzo"), "Categoria": CATEGORIA.get(d.get("categoria"), d.get("categoria")),
                             "Tipo di ingresso": INGRESSO.get(p["classe"], p["classe"]), "Rete pedonale": AGGANCIO.get(p["stato"], p["stato"]),
                             "Distanza dalla rete (m)": p["raccordo_m"], "Verifica sul posto": VERIFICA.get(p["verifica"], p["verifica"]),
                             "Condizioni di accesso": d.get("condizioni_accesso"), "Fonte dei dati": d.get("fonte")}})
    n = NORM
    tram = in_fp(gpd.read_file(n / "fi_tram_fermate.gpkg"))
    for _, row in tram.iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "tram", "id": row.id, "nome": "Fermata tram " + row.nome_ferma.title(), "x": x, "z": z,
                    "attr": {"Linea": row.linea, "Pensilina": "sì" if row.pensilina == 1 else "no"}})
    # fermate T2 fra le destinazioni ma assenti dal dato comunale (San Donato - Università, fuori dal riquadro FP: D20)
    for d in dest.values():
        if d["categoria"] != "tram":
            continue
        e = next(i for i in d["ingressi"] if i["entrance_id"] == d["ingresso_predefinito"])
        if any(Point(e["xy"]).distance(q) < 50 for q in tram.geometry):
            continue
        x, z = loc(*e["xy"])
        out.append({"livello": "tram", "id": e["entrance_id"], "nome": "Fermata tram " + d["nome"], "x": x, "z": z,
                    "attr": {"Linea": d["linee"], "Pensilina": "non nota (nessun dato nel feed)", "Fonte dei dati": d["fonte"]}})
    for _, row in in_fp(gpd.read_file(n / "fi_scuole_statali.gpkg")).iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "scuole", "id": row.id, "nome": row.nome.title(), "x": x, "z": z,
                    "attr": {"Codice": row.codicescuo, "Tipologia": row.tipologia.title(), "Indirizzo": row.indirizzo.title(), "Anno scolastico": "2026/27"}})
    for _, row in in_fp(gpd.read_file(n / "fi_barriere.gpkg")).iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "barriere", "id": row.id, "nome": "Scheda " + str(row.scheda), "x": x, "z": z,
                    "attr": {"Uso": row.destinaz_u, "Indirizzo": row.indirizzo, "Grado di accessibilità": row.grado_acce,
                             "Scheda PDF": f"http://datigis.comune.fi.it/barriere_architettoniche/scheda_{row.scheda}.pdf", "Rilievo": "2013"}})
    # rifugi climatici (D32): i 7 fra le destinazioni (entro 700 m dal riquadro), più le aree dentro il riquadro; quelli oltre il terreno disegnato vanno in elenco
    terra = box(E0 - MARGINE, N0 - MARGINE, E1 + MARGINE, N1 + MARGINE)
    rif = json.load(open(ROOT / "analysis/firenze_novoli/riepilogo.json"))["rifugi"]
    def attr_rifugio(d):
        return {"Tipo": "biblioteca" if d["tipo_rifugio"] == "biblioteca" else "area fresca all'aperto", "Ombreggiatura dichiarata": f"oltre il {d['ombreggiatura_dichiarata_pct']}%" if "ombreggiatura_dichiarata_pct" in d else None,
                "Ingressi usati nei calcoli": "; ".join(re.search(r"\(([^)]*)\)", e["fonte_ingresso"])[1] for e in d["ingressi"]) + " (civici del Comune agli indirizzi dichiarati)", "Condizioni di accesso": d.get("condizioni_accesso"),
                "Civici per cui è il rifugio più vicino": f"{rif['piu_vicino'][d['destination_id']]} su {rif['conteggi']['reachable']} che arrivano a un rifugio",
                "Verifica sul posto": "da verificare: ingresso, orari, cancelli", "Fonte dei dati": d["fonte"], "Dato del": "2026-06-18"}
    fatti = set()
    for _, row in in_fp(gpd.read_file(n / "fi_rifugi_aree.gpkg")).iterrows():
        c = row.geometry.centroid
        x, z = loc(c.x, c.y)
        poly = max(row.geometry.geoms, key=lambda q: q.area) if row.geometry.geom_type == "MultiPolygon" else row.geometry
        d = dest.get(f"dst_refuge_{row.id}"); fatti.add(f"dst_refuge_{row.id}")
        out.append({"livello": "rifugi", "id": row.id, "nome": row.nome_area, "x": x, "z": z, "metodo": "rifugi",
                    "contorno": [c_ for q in poly.exterior.coords for c_ in loc(*q)],
                    "attr": attr_rifugio(d) if d else {"Ombreggiatura": f"oltre il {row.percentuale_ombreggi}%", "Ingressi": row.ingresso, "Descrizione": row.descrizione, "Dato del": "2026-06-18"}})
    for d in dest.values():
        if d["categoria"] != "cooling_refuge" or d["destination_id"] in fatti: continue
        p = Point(d["ingressi"][0]["xy"]); x, z = loc(p.x, p.y)
        out.append({"livello": "rifugi", "id": d["destination_id"], "nome": d["nome"], "x": x, "z": z, "metodo": "rifugi",
                    **({"fuori": True, "distanza_m": round(FP.distance(p))} if not terra.intersects(p) else {}), "attr": attr_rifugio(d)})
    # percorsi campione verso i rifugi (RC1-RC5): linea sul terreno, stato da verificare; ombra se calcolata (shadow/run.py --rifugi RCn)
    om = {}
    for f in sorted((ROOT / "shadow/firenze_novoli").glob("sintesi_rifugi_RC*.json")):
        for r_ in json.load(open(f))["date"].get("2026-07-15", []):
            if r_["fascia"] == "punta_12_30_13_30": om[r_["receiver_id"].removeprefix("pth_fi_")] = r_["edifici_alberi_e_vegetazione_lidar"]["frazione"]["valore"]
    pc_ = {r_["id"]: r_ for r_ in json.load(open(ROOT / "network/firenze_novoli/percorsi_campione.json"))}
    nomi = {e["entrance_id"]: d["nome"] for d in dest.values() for e in d["ingressi"]}
    for f in json.load(open(ROOT / "network/firenze_novoli/percorsi_campione.geojson"))["features"]:
        pr = f["properties"]
        if not pr.get("id", "").startswith("RC") or "tipo" in pr: continue
        r_ = pc_[pr["id"]]; a_ = r_["destinazione"].split(" ")[0]; lin = [c_ for q in f["geometry"]["coordinates"] for c_ in loc_ll(*q[:2])]
        out.append({"livello": "percorsi_rifugi", "id": pr["id"], "nome": f"Percorso {pr['id']} verso {nomi.get(a_, a_)}", "x": lin[0], "z": lin[1], "linea": lin, "metodo": "rifugi",
                    "attr": {"Da": "Civico " + re.search(r"\((.*)\)", r_["origine"])[1].title() if r_.get("civico") else re.sub(r"\s*\(.*\)$", "", pr["descrizione"].split(" verso ")[0]), "A": nomi.get(a_, a_), "Lunghezza per la rete": f"{r_['lunghezza_totale_m']:.0f} m",
                             "In linea d'aria": f"{r_['diretta_m']:.0f} m", "Attraversamenti": r_["attraversamenti"], "Metri con marciapiede ignoto": f"{r_['m_marciapiede_ignoto']:.0f} m",
                             "Ombra il 15 luglio, 12:30-13:30": f"{om[pr['id']] * 100:.0f}% del percorso (con vegetazione LiDAR)".replace(".", ",") if pr["id"] in om else "non calcolata",
                             "Verifica sul posto": "da verificare: percorso, marciapiede e ingresso"}})
    # protezione civile: poche aree per tutta la città, quindi tutte quelle dell'area allargata (riquadro + 700 m).
    # Quelle oltre il terreno disegnato hanno fuori true e la distanza dal riquadro: la pagina le elenca, come le stazioni ARPAT
    fuori = lambda g: {"fuori": True, "distanza_m": round(FP.distance(g))} if not terra.intersects(g) else {}
    pc = lambda v: v.strip() if isinstance(v, str) and v.strip() not in ("", "None") else None   # vuoti e NaN della fonte
    for _, row in gpd.read_file(n / "fi_aree_attesa.gpkg").iterrows():
        c = row.geometry.centroid; x, z = loc(c.x, c.y)
        out.append({"livello": "attesa", "id": row.id, "nome": "Area di attesa " + row.nome, "x": x, "z": z, **fuori(row.geometry),
                    "attr": {"A cosa serve": "luogo sicuro dove radunarsi in caso di allerta o di evento calamitoso, per ricevere istruzioni dalla protezione civile",
                             "Indirizzo": row.indirizzo, "Associazione di riferimento": pc(row.associazio),
                             "Pericolosità indicata dalla fonte": ", ".join(v for v in (pc(row.pericolosi), pc(row.pericolos0)) if v) or None,
                             "Dato del": "2024-06-25"}})
    for _, row in gpd.read_file(n / "fi_aree_assistenza.gpkg").iterrows():
        x, z = loc(row.geometry.x, row.geometry.y)
        out.append({"livello": "assistenza", "id": row.id, "nome": f"Area di assistenza {row.cod_area} {row.denominazi}", "x": x, "z": z, **fuori(row.geometry),
                    "attr": {"A cosa serve": "area sicura dove la protezione civile allestisce i primi alloggi per la popolazione colpita",
                             "Indirizzo": row.indirizzo, "Struttura": pc(row.tipo_strut), "Dimensioni": pc(row.sup_mq), "Servizi igienici": pc(row.servizi_ig),
                             "Allacci": ", ".join(k for k, v in (("energia elettrica", row.energia_el), ("gas", row.gas), ("acqua", row.acqua), ("fognature", row.fognature)) if str(v).lower() == "si") or None,
                             "Accessi": re.sub(r"(\w)\?(\w)", r"\1'\2", pc(row.note)).replace("pu? ", "può ") if pc(row.note) else None,   # la fonte ha '?' al posto di apostrofo e accenti
                             "Associazione di riferimento": pc(row.associazio), "Pericolosità indicata dalla fonte": pc(row.pericolosi),
                             "Sopralluogo": pc(row.data_rilev), "Dato del": "2024-06-25"}})
    # servizi e aree attrezzate del Comune: solo quelli sul terreno disegnato
    # la fonte scrive l'accento finale con l'apostrofo ("Niccolo'"): ripristinato, tranne le elisioni come "De'"
    acc = lambda t: re.sub(r"\b(?![Dd]e')(\w+)([aeiouAEIOU])'(?=\s|$)", lambda m: m[1] + "àèìòùÀÈÌÒÙ"["aeiouAEIOU".index(m[2])], t)
    ti = lambda v: acc(pc(v).title()) if pc(v) else None
    sul = lambda f, l: (lambda g: g[g.intersects(terra)])(gpd.read_file(n / f, layer=l))
    def metti(livello, row, nome, attr, area=False):
        c = row.geometry.representative_point() if area else row.geometry.centroid; x, z = loc(c.x, c.y)
        d = {"livello": livello, "id": row.id, "nome": nome, "x": x, "z": z, "attr": {k: v for k, v in attr.items() if (pc(v) if isinstance(v, str) else v is not None)}}
        if area:
            poly = max(row.geometry.geoms, key=lambda q: q.area) if row.geometry.geom_type == "MultiPolygon" else row.geometry
            d["contorno"] = [c_ for q in poly.exterior.coords for c_ in loc(*q)]
        out.append(d)
    for _, r in sul("fi_farmacie.gpkg", "farmacie").iterrows():
        metti("farmacie", r, ti(r.DENOMINAZI), {"Indirizzo": " ".join(v for v in (ti(r.VIA), pc(r.NCIVICO)) if v) or None, "Orari e turni": "non nel dato (il Comune li pubblica in un altro dataset, giornaliero)"})
    for _, r in sul("fi_sosta_disabili.gpkg", "sosta_disabili").iterrows():
        metti("sosta_disabili", r, "Stallo per disabili", {"Strada": ti(r.strada), "Disposizione": {"LINEA": "in linea", "LISCA": "a spina", "PETTINE": "a pettine"}.get(r.stallo, r.stallo)})
    for _, r in sul("fi_bike_sharing.gpkg", "bike_sharing").iterrows():
        metti("bike_sharing", r, "Sosta del bike sharing", {"Indirizzo": ti(r.indirizzo), "Disponibilità dei mezzi": "non nel dato"})
    for _, r in sul("fi_car_sharing.gpkg", "car_sharing").iterrows():
        metti("car_sharing", r, "Posto del car sharing", {"Nel dato": "solo la posizione"})
    for _, r in sul("fi_scudo_verde.gpkg", "scudo_verde").iterrows():
        metti("scudo_verde", r, f"Varco {r.num_varco} {r.nome_varco}", {"Ubicazione": r.ubicazione, "Verso": {"IN": "in entrata", "OUT": "in uscita"}.get(r.tipo_varco, r.tipo_varco),
              "Attivo dal": r.data_ini.strftime("%Y-%m-%d") if r.data_ini is not None and str(r.data_ini) != "NaT" else None, "Atto": r.atto_ini})
    for _, r in sul("fi_aree_giochi.gpkg", "aree_giochi").iterrows():
        metti("giochi", r, r.NOME_AREA, {"Giardino": r.AREA_APPAR}, area=True)
    for _, r in sul("fi_aree_cani.gpkg", "aree_cani").iterrows():
        metti("cani", r, r.NOME_AREA, {"Giardino": r.AREA_APPAR}, area=True)
    for _, r in sul("fi_aree_sportive.gpkg", "aree_sportive").iterrows():
        metti("sport", r, r.NOMEAREA, {"Tipo": r.TIPOAREA, "Superficie": f"{r.SUPMQAREA:,.0f} m²".replace(",", ".") if r.SUPMQAREA == r.SUPMQAREA else None,
              "Proprietà": {"PU": "pubblica", "PR": "privata"}.get(r.PROPRIETA, r.PROPRIETA), "Gestione": r.ENTEGEST}, area=True)
    return out


# --- tematismi dipinti sul terreno: poligoni per classe, ritagliati sul terreno disegnato ---------------
VERDE_FRUIBILE = {"AREA  ATTREZZATA GIARDINO", "PARCO", "AREE ATTREZZATE COMPLEMENTARI", "GIARDINO SCOLASTICO COFI", "ORTI SOCIALI"}
ACUSTICA = {"1": "#4caf50", "2": "#c5e1a5", "3": "#ffee58", "4": "#ff9800", "5": "#e53935", "6": "#6a1b9a"}


def tematismi():
    terra = box(E0 - MARGINE, N0 - MARGINE, E1 + MARGINE, N1 + MARGINE)
    def tema(f, l, classi, cl, nota):
        g = gpd.read_file(NORM / f, layer=l); g = g[g.intersects(terra)]
        pol = []
        for row in g.itertuples():
            i = cl(row)
            if i is None: continue
            geom = row.geometry.intersection(terra)
            if not geom.is_empty: pol.append({"c": i, "a": _contorni(geom)})
        return {"nota": nota, "classi": [{"t": t, "c": c} for t, c in classi], "poligoni": pol}
    dens = lambda r: None if r.residenti_2011 != r.residenti_2011 else r.residenti_2011 / (r.geometry.area / 1e4)
    soglie = [50, 150, 300]
    out = {
        "verde": tema("fi_aree_verdi.gpkg", "aree_verdi", [("giardini, parchi, giardini scolastici, orti", "#4caf50"), ("verde sportivo", "#9ccc65"), ("rotonde, aiuole, aree accessorie e altro verde", "#c5e1a5")],
                      lambda r: 0 if r.USO_AREA in VERDE_FRUIBILE else 1 if str(r.USO_AREA).startswith("VERDE SPORTIVO") else 2,
                      "Aree verdi gestite dal Comune, per uso. Il verde privato non c'è."),
        "idraulica": tema("fi_pericolosita_idraulica.gpkg", "pericolosita_idraulica", [("codice PS_PERALL_1", "#bbdefb"), ("codice PS_PERALL_2", "#64b5f6"), ("codice PS_PERALL_3", "#1565c0")],
                          lambda r: {"PS_PERALL_1": 0, "PS_PERALL_2": 1, "PS_PERALL_3": 2}.get(r.pericolo),
                          "Classi di pericolosità da alluvione del piano di gestione del rischio. Il file dà solo i codici, senza legenda."),
        "alluvione1966": tema("fi_allagate1966.gpkg", "allagate1966", [("acqua fino a 2 m", "#90caf9"), ("da 2 a 4 m", "#1e88e5"), ("da 4 a 5 m", "#0d47a1")],
                              lambda r: {"0-2 (m)": 0, "2-4 (m)": 1, "4-5 (m)": 2}.get(r.AREE_ALLAG),
                              "Profondità dell'acqua nell'alluvione del 4 novembre 1966."),
        "acustica": tema("fi_pcca.gpkg", "pcca", [(f"classe {['I', 'II', 'III', 'IV', 'V', 'VI'][i]} ({t})", ACUSTICA[str(i + 1)]) for i, t in enumerate(["40-50 dBA", "45-55 dBA", "50-60 dBA", "55-65 dBA", "60-70 dBA", "70 dBA"])],
                         lambda r: int(r.CLASSE_ACU) - 1,
                         "Classe acustica del piano comunale: limiti di rumore ammessi di notte e di giorno, non rumore misurato."),
        "zone30": tema("fi_zone30.gpkg", "zone30", [("carreggiata in zona 30", "#f06292"), ("area pedonale in zona 30", "#f8bbd0")],
                       lambda r: {"area di circolazione veicolare": 0, "area di circolazione pedonale": 1}.get(r.tipologia, 0),
                       "Tratti di strada dove il limite è 30 km/h."),
        "residenti": tema("fi_sezioni2011.gpkg", "sezioni", [("meno di 50", "#fde0c5"), ("da 50 a 150", "#f59e4c"), ("da 150 a 300", "#d9480f"), ("300 e oltre", "#7f1d1d"), ("nessun dato", "#9e9e9e")],
                          lambda r: 4 if dens(r) is None else sum(dens(r) >= q for q in soglie),
                          "Residenti per ettaro in ogni sezione di censimento, censimento Istat 2011. Ogni area colorata è una sezione."),
    }
    return {"n": sum(len(v["poligoni"]) for v in out.values()), "livelli": out}


# --- mappa di base: verde, acqua e strade da OSM, dipinti sul terreno dalla pagina ---
VERDE = {"leisure": {"park", "garden", "pitch", "playground", "dog_park", "recreation_ground"},
         "landuse": {"grass", "recreation_ground", "allotments", "cemetery", "meadow", "village_green"}, "natural": {"scrub", "wood"}}
LARGHEZZA = {"primary": 14, "primary_link": 9, "secondary": 12, "secondary_link": 8, "tertiary": 10, "unclassified": 8,
             "residential": 7, "service": 4.5, "pedestrian": 6, "living_street": 6}   # m, carreggiata indicativa per il disegno
CAMMINO = {"footway", "cycleway", "path", "steps", "track"}


def _osm_aree():
    snap = json.load(open(ROOT / "pipeline/snapshots/snp_osm_firenze_20261009.json"))
    x0, y0, x1, y1 = E0 - MARGINE, N0 - MARGINE, E1 + MARGINE, N1 + MARGINE
    lo0, la0 = to_ll.transform(x0, y0); lo1, la1 = to_ll.transform(x1, y1)
    d = gpd.read_file(ROOT / snap["local_path"], layer="multipolygons", bbox=(lo0, la0, lo1, la1), engine="pyogrio")
    return d.set_crs(4326, allow_override=True).to_crs(7791), box(x0, y0, x1, y1)


def _anelli(geom):
    out = []
    for p in (geom.geoms if geom.geom_type in ("MultiPolygon", "GeometryCollection") else [geom]):
        if p.geom_type != "Polygon" or p.area < 20:
            continue
        p = p.simplify(0.5)
        out.append([[c for q in ring.coords for c in loc(*q)] for ring in [p.exterior, *p.interiors]])
    return out


def mappa(aree):
    d, quadro = aree
    d = d[d.geometry.notna()]
    verde = d[np.logical_or.reduce([d[k].isin(v) for k, v in VERDE.items() if k in d])]
    acqua = d[d["natural"] == "water"] if "natural" in d else d.iloc[:0]
    clip = lambda g: _anelli(g.buffer(0).intersection(quadro))
    h = gpd.read_file(NORM / "osm_firenze.gpkg", layer="highway").to_crs(7791)
    h = h[h.intersects(quadro)]
    strade = []
    for _, row in h.iterrows():
        tipo = row.highway
        w = LARGHEZZA.get(tipo) or (2 if tipo in CAMMINO else None)
        if not w:
            continue
        g = row.geometry.intersection(quadro)
        for ln in (g.geoms if g.geom_type.startswith("Multi") else [g]):
            if ln.geom_type == "LineString" and not ln.is_empty:
                strade.append({"w": w, "c": int(tipo in CAMMINO), "p": [c for q in ln.coords for c in loc(*q)]})
    poly = lambda df: [a for g in df.geometry for a in clip(g)]
    return {"n": len(strade), "verde": poly(verde), "acqua": poly(acqua), "strade": strade}


# nomi dei luoghi: scelti a mano fra le aree OSM con nome (priorità 1) e le vie principali (priorità 2)
LUOGHI = {"Palazzo di Giustizia di Firenze": "Palazzo di Giustizia", "Polo delle Scienze Sociali": "Polo delle Scienze Sociali",
          "Regione Toscana": "Regione Toscana", "Parco Piero Luigi Vigna": "Parco Piero Luigi Vigna",
          "Mercato Ortofrutticolo di Novoli": "Mercato Ortofrutticolo", "Scuola marescialli e brigadieri dei carabinieri": "Scuola marescialli dei Carabinieri",
          "PalaMattioli": "PalaMattioli", "Scuola Primaria \"Vamba\"": "Scuola primaria Vamba", "Cimitero di Rifredi": "Cimitero di Rifredi",
          "Piazza delle Medaglie D'Oro": "Piazza delle Medaglie d'Oro"}
VIE = ["Viale Alessandro Guidoni", "Via di Novoli", "Via Carlo Del Prete", "Viale della Toscana", "Via Enrico Forlanini",
       "Via Eugenio Barsanti", "Via Accademia del Cimento", "Via Panciatichi", "Via della Torre degli Agli", "Via Sandro Pertini"]


def etichette(aree):
    d, _ = aree
    out = []
    for nome_osm, testo in LUOGHI.items():
        g = d[d["name"] == nome_osm]
        if g.empty:
            continue
        geom = g.geometry.union_all()
        if not geom.intersects(FP):
            continue
        c = geom.intersection(FP).representative_point()
        x, z = loc(c.x, c.y)
        out.append({"t": testo, "x": x, "z": z, "k": 1})
    h = gpd.read_file(NORM / "osm_firenze.gpkg", layer="highway").to_crs(7791)
    h = h[h.intersects(FP.buffer(-60)) & h["name"].isin(VIE)]
    for nome, g in h.groupby("name"):
        ln = max((q for geom in g.geometry.intersection(FP.buffer(-60)) for q in (geom.geoms if geom.geom_type.startswith("Multi") else [geom])), key=lambda q: q.length)
        c = ln.interpolate(0.5, normalized=True)
        x, z = loc(c.x, c.y)
        out.append({"t": nome, "x": x, "z": z, "k": 2})
    return {"n": len(out), "etichette": out}


# --- livelli analitici (opzionali) ---------------------------------------------
def _feats(path):
    g = json.load(open(path))
    return g["features"] if g.get("type") == "FeatureCollection" else [g]


STATI = {"ok": "ok", "reachable": "ok", "non_raggiungibile": "non_raggiungibile", "isolated": "non_raggiungibile",
         "dati_insufficienti": "dati_insufficienti", "insufficient_data": "dati_insufficienti", "vietato": "vietato", "forbidden": "vietato"}


NOMI_ACC = {"rifugi": "Rifugio climatico più vicino (7 rifugi)"}


def accessibilita(dirpath):
    """Input: <dir>/accessibilita*.geojson, Point EPSG:4326, un file per destinazione.
    Proprietà: id, civico, minuti (null se non raggiungibile), stato (ok | non_raggiungibile | dati_insufficienti | vietato),
    destinazione (id), destinazione_nome, profilo. Alias accettati, per l'output del motore di analisi: t = minuti,
    ind = civico, stato reachable/isolated/insufficient_data/forbidden, layer = origine (gli altri layer sono ignorati)."""
    dnomi = {d["destination_id"]: d["nome"] for d in json.load(open(ROOT / "network/firenze_novoli/destinazioni.json"))["destinazioni"]}
    dst = {}
    for fn in sorted(glob.glob(str(pathlib.Path(dirpath) / "accessibilita*.geojson"))):
        stem = pathlib.Path(fn).stem
        for f in _feats(fn):
            p = f.get("properties", {})
            if f.get("geometry", {}).get("type") != "Point" or p.get("layer", "origine") != "origine":
                continue
            did = p.get("destinazione") or stem.removeprefix("accessibilita").lstrip("_") or "destinazione"
            e = dst.setdefault(did, {"id": did, "nome": p.get("destinazione_nome") or dnomi.get(did) or NOMI_ACC.get(did, did), "profilo": p.get("profilo"), "punti": []})
            m = p.get("minuti", p.get("t"))
            x, z = loc_ll(*f["geometry"]["coordinates"][:2])
            st = STATI.get(p.get("stato"), "ok" if m is not None else "non_raggiungibile")
            e["punti"].append({"id": p.get("id"), "civico": p.get("civico") or p.get("ind"), "x": x, "z": z,
                               "min": r(m, 1) if m is not None and st == "ok" else None, "stato": st})
    if not dst:
        return None
    return {"n": sum(len(d["punti"]) for d in dst.values()), "destinazioni": list(dst.values())}


def ombra(dirpath):
    """Input: <dir>/ombra_percorsi*.geojson, LineString o MultiLineString EPSG:4326. Proprietà: id, frazione_ombra (0 sole, 1 ombra),
    istante (testo, es. 2026-07-21T15:00), lunghezza_m. Un istante per file (o più istanti nello stesso file).
    Accetta anche l'uscita del motore F07, tratti_ombra_*.geojson: solo i tratti in ombra (frazione 1), caso veg_lidar_tipico."""
    d = pathlib.Path(dirpath)
    files = sorted(f for f in glob.glob(str(d / "ombra_percorsi*.geojson")) + glob.glob(str(d / "tratti_ombra_*.geojson")) if "_rifugi" not in f)   # i percorsi RC stanno nel livello dei rifugi
    ist, quota = {}, {}
    for fn in files:
        for f in _feats(fn):
            gt = f.get("geometry", {}).get("type")
            if gt not in ("LineString", "MultiLineString"):
                continue
            p = f["properties"]
            if "shade_fraction" in p:   # formato F07: un tratto in ombra per percorso, ora e caso
                if p["caso"] != "veg_lidar_tipico":
                    continue
                p = {"id": p["receiver_id"], "frazione_ombra": 1.0, "istante": f'{p["date"]}T{p["time_local"]}', "lunghezza_m": p["shaded_m"],
                     "quota": p["shade_fraction"]}
            if "quota" in p:
                quota.setdefault(p["istante"], {})[p["id"]] = r(p["quota"], 3)
            lines = [f["geometry"]["coordinates"]] if gt == "LineString" else f["geometry"]["coordinates"]
            for ln in lines:
                pts = [c for q in ln for c in loc_ll(*q[:2])]
                key = p.get("istante") or pathlib.Path(fn).stem
                ist.setdefault(key, []).append({"id": p.get("id"), "f": r(p["frazione_ombra"], 3), "m": r(p.get("lunghezza_m"), 1), "p": pts})
    if not ist:
        return None
    # percorsi interi, per disegnare al sole quello che non è in ombra
    ids = {t["id"] for v in ist.values() for t in v}
    g = json.load(open(ROOT / "network/firenze_novoli/percorsi_campione.geojson"))
    percorsi = [{"id": "pth_fi_" + f["properties"]["id"], "p": [c for q in f["geometry"]["coordinates"] for c in loc_ll(*q[:2])]}
                for f in g["features"] if "tipo" not in f["properties"] and "pth_fi_" + f["properties"]["id"] in ids]
    return {"n": sum(len(v) for v in ist.values()), "percorsi": percorsi,
            "istanti": [{"istante": k, "tratti": v, "quota": quota.get(k, {})} for k, v in sorted(ist.items())]}


# classi della quota di percorso in ombra (F6, compito 3): divergenti alla soglia del 50% (D49, D53), caldi sotto e freddi sopra
CLASSI_OMBRA = [(0.2, "#f2c230", "meno del 20%"), (0.4, "#e8913a", "dal 20 al 40%"), (0.5, "#c45a3c", "dal 40 al 50%"),
                (0.6, "#4f7fc2", "dal 50 al 60%"), (1.01, "#1b2a6b", "60% e oltre")]


def ombra_rifugi(dirpath):
    """Input: <dir>/ombra_rifugi_civici_<data>.geojson (un punto per civico entro 15 minuti dal rifugio più vicino, shadow/ombra_rifugi.py) e
    <dir>/ombra_rifugi_<data>.json (numeri, soglia e limiti). Classe = quota del percorso in ombra all'istante, caso con vegetazione."""
    fs = sorted(pathlib.Path(dirpath).glob("ombra_rifugi_civici_*.geojson"))
    if not fs:
        return None
    g = json.load(open(fs[-1])); R = json.load(open(fs[-1].with_name(fs[-1].name.replace("_civici", "").replace(".geojson", ".json"))))
    dnomi = {d["destination_id"]: d["nome"] for d in json.load(open(ROOT / "network/firenze_novoli/destinazioni.json"))["destinazioni"]}
    s = R["soglia_ombra"]
    punti = []
    for f in g["features"]:
        p = f["properties"]; x, z = loc_ll(*f["geometry"]["coordinates"][:2])
        punti.append({"x": x, "z": z, "c": next(i for i, (lim, _, _) in enumerate(CLASSI_OMBRA) if p["ombra"] < lim), "o": r(p["ombra"], 3), "i": [r(v, 3) for v in p["ombra_intervallo"]],
                      "e": r(p["ombra_solo_edifici"], 3), "m": r(p["minuti"], 1), "rif": dnomi.get(p["rifugio"], p["rifugio"]), "res": r(p["residenti_stimati"], 1)})
    classi = [{"c": col, "t": t + (" (soprattutto all'ombra)" if lim > s and (i == 0 or CLASSI_OMBRA[i - 1][0] >= s) else ""),
               "civici": sum(q["c"] == i for q in punti), "residenti": round(sum(q["res"] or 0 for q in punti if q["c"] == i))} for i, (lim, col, t) in enumerate(CLASSI_OMBRA)]
    soglie = [{"minuti": x["minuti"], "arrivano": x["arrivano"], "soprattutto_ombra": x["soprattutto_ombra"],
               "sensibilita": {k: v["residenti_stimati"] for k, v in x["sensibilita_soglia"].items()}, "riserva": x.get("riserva")} for x in R["soglie"]]
    return {"n": len(punti), "data": g["data"], "ora": g["ora_locale"], "soglia": s, "sensibilita": R["sensibilita_soglia"], "classi": classi, "soglie": soglie,
            "limiti": [x["text"] for x in R["limits"][:7]], "punti": punti}


# --- scenari: interventi ipotetici (opzionale) ---------------------------------
ETICHETTE_SCN = {
    "scn_fi_s1_filare_r01": "S1 filare di 7 alberi, chioma tipica (su R01)",
    "scn_fi_s1v_chioma_min": "S1, variante chioma minima",
    "scn_fi_s1v_chioma_max": "S1, variante chioma massima",
    "scn_fi_s2_pensilina_attesa_polo": "S2 pensilina alla fermata bus Guidoni Barsanti",
    "scn_fi_s5_pensilina_regione_toscana": "S5 pensilina alla fermata bus Regione Toscana",
    "scn_fi_s6_pensilina_di_novoli": "S6 pensilina alla fermata bus Di Novoli Sn",
}
FATTIBILITA = "ignota (sottoservizi, spazio radicale, permessi, proprietà del suolo, manutenzione). Intervento ipotetico, non un progetto."


def _pc(v):
    return f"{v * 100:.1f}".replace(".", ",") + "%"


def _mm(v):
    return f"{v:.2f}".replace(".", ",")


def costo_filare(sid):
    """Costo d'impianto e metri quadri d'ombra per mille euro (scenarios/firenze_novoli/costo_filare.json, D33 e D36), solo per lo scenario calcolato."""
    p = ROOT / "scenarios/firenze_novoli/costo_filare.json"
    if not p.exists() or (c := json.load(open(p)))["scenario_id"] != sid:
        return []
    eur = lambda v: f"{v:.0f} euro"   # senza separatore delle migliaia: la scena mette la virgola fra cifre separate da un punto
    r_, s_ = c["riferimento"], c["sensibilita_altre_specie"]
    return [["Costo d'impianto (prezzario Toscana 2026)", f"{eur(r_['costo_eur'])} per {c['alberi']} platani orientali 18/20, fornitura e piantagione, IVA esclusa; con altre specie da {eur(s_['minimo_eur'])} a {eur(s_['massimo_eur'])}"],
            ["Ombra per mille euro, 15 luglio, 12:30-13:30", f"{_mm(r_['m2_per_mille_euro'])} m² ({_mm(r_['m2'])} m² d'ombra in più); ombra di alberi adulti, prezzo di alberi da vivaio, manutenzione esclusa"]]


def numeri_scenari(conf):
    """Numeri chiave letti da confronto.json (F08): caso con vegetazione LiDAR, 15 luglio, punta 12:30-13:30.
    Filare (titolo "... su Rxx"): minuti al sole e ombra sul suo percorso, anche per le varianti. Pensilina: la sua area di attesa
    (titolo "... area di attesa sfc_fi_..." in aree_attesa; altrimenti area_attesa_polo, cioè S2)."""
    out = {}
    for sid, sc in conf["scenari"].items():
        if sc.get("stato") != "confrontato":
            continue
        rotta = re.search(r"\bsu (R\d\d)\b", sc["titolo"])
        if sc["interventi"]["alberi"] and rotta:
            R = rotta.group(1)
            for vid, v in {sid: sc, **sc.get("robustezza", {})}.items():
                if not isinstance(v, dict):
                    continue
                r = v["percorsi"]["2026-07-15"]["con_vegetazione_lidar"][R]["punta_12_30_13_30"]
                m, f = r["minuti_sole"], r["frazione_ombra"]
                out[vid] = [[f"Percorso {R}, 15 luglio, 12:30-13:30", f"minuti al sole da {_mm(m['baseline'])} a {_mm(m['scenario'])} ({_mm(m['delta'])})"],
                            [f"Ombra su {R}", f"da {_pc(f['baseline'])} a {_pc(f['scenario'])}"]]
                out[vid] += costo_filare(vid)
        elif sc["interventi"]["pensiline"]:
            rid = re.search(r"\b(sfc_fi_\w+)", sc["titolo"])
            a = (sc["aree_attesa"][rid.group(1)] if rid else sc["area_attesa_polo"])["2026-07-15"]
            for ctx, et in (("con_vegetazione_lidar", "Area di attesa, con vegetazione LiDAR"), ("solo_edifici", "Area di attesa, solo edifici")):
                p = a[ctx]["punta_12_30_13_30"]
                out.setdefault(sid, []).append([et + ", 15 luglio, 12:30-13:30", f"ombra da {_pc(p['baseline'])} a {_pc(p['scenario'])}"])
    return out


def interventi(sdir):
    """Input: <sdir>/interventi.geojson, EPSG:4326: Point = albero nuovo (id, scenario, h, chioma_d, imposta),
    Polygon = pensilina (id, scenario, z_lo, z_hi, quote sopra il suolo). I numeri chiave vengono da <sdir>/confronto.json."""
    sdir = pathlib.Path(sdir)
    if not (sdir / "interventi.geojson").exists():
        return None
    num = numeri_scenari(json.load(open(sdir / "confronto.json"))) if (sdir / "confronto.json").exists() else {}
    scn = {}
    for f in _feats(sdir / "interventi.geojson"):
        p, g = f["properties"], f["geometry"]
        e = scn.setdefault(p["scenario"], {"id": p["scenario"], "etichetta": ETICHETTE_SCN.get(p["scenario"], p["scenario"]), "alberi": [], "pensiline": [],
                                           "numeri": num.get(p["scenario"], []), "fattibilita": FATTIBILITA})
        if g["type"] == "Point":
            x, z = loc_ll(*g["coordinates"][:2])
            e["alberi"].append({"id": p["id"], "x": x, "z": z, "h": r(p["h"], 1), "d": r(p["chioma_d"], 1), "imp": r(p["imposta"], 1)})
        elif g["type"] == "Polygon":
            e["pensiline"].append({"id": p["id"], "z_lo": r(p["z_lo"], 2), "z_hi": r(p["z_hi"], 2), "p": [c for q in g["coordinates"][0][:-1] for c in loc_ll(*q[:2])]})
    ordine = list(ETICHETTE_SCN)
    lista = sorted(scn.values(), key=lambda s: ordine.index(s["id"]) if s["id"] in ordine else 99)
    return {"n": sum(len(s["alberi"]) + len(s["pensiline"]) for s in lista), "scenari": lista,
            "fonte_numeri": "scenarios/firenze_novoli/confronto.json (F08), caso con vegetazione LiDAR, stesse condizioni per scenario e base"}


# --- temperature -----------------------------------------------------------------
NODATA_T = -32768   # cella non valida (nube, ombra di nube, neve, acqua, fuori scena) nelle griglie in decimi di °C


def temperature():
    """Temperatura delle superfici Landsat (data/norm: fi_landsat_st_30m.tif e fi_landsat_st.json), griglia a 30 m nel piano del motore
    come il terreno (riga 0 = nord, x0/z0 centro della prima cella). Valori in decimi di °C, NODATA_T per le celle non valide."""
    if not (NORM / "fi_landsat_st.json").exists():
        return None
    m = json.load(open(NORM / "fi_landsat_st.json"))
    with rasterio.open(NORM / m["file"]) as ds:
        a = ds.read()
    p = m["passo_m"]
    dc = lambda g: np.where(np.isfinite(g), np.round(g * 10), NODATA_T).astype(int).ravel().tolist()
    validi = np.isfinite(a)
    nv = validi.sum(0)
    media = np.where(nv > 0, np.nansum(a, 0) / np.maximum(nv, 1), np.nan)   # media delle sole date valide nella cella
    return {"n": len(m["date_tenute"]), "nx": m["nx"], "ny": m["ny"], "passo": p,
            "x0": round(m["x0_ovest"] + p / 2 - CE, 2), "z0": round(-(m["y1_nord"] - p / 2 - CN), 2),
            "unita": "decimi di °C", "nodata": NODATA_T, "soglia_validi_pct": m["soglia_validi_pct"],
            "date": [{"data": v["data"], "ora_utc": v["ora_utc"], "satellite": v["satellite"], "validi_pct": v["validi_fp_pct"], "scena": v["scena"], "t": dc(a[i])}
                     for i, v in enumerate(m["date_tenute"])],
            "media": dc(media), "sopra_40": (np.nan_to_num(a, nan=-999) > 40).sum(0).ravel().astype(int).tolist(),
            "validi_per_cella": nv.ravel().astype(int).tolist()}


def meteo():
    """Temperatura dell'aria giornaliera della stazione SIR (data/norm: sir_termo_firenze.json): [data, Tmax, Tmin] in decimi di °C, null se mancante."""
    if not (NORM / "sir_termo_firenze.json").exists():
        return None
    m = json.load(open(NORM / "sir_termo_firenze.json"))
    st = m["stazione"]
    x, z = loc(st["e"], st["n"])
    dc = lambda v: None if v is None else int(round(v * 10))
    ls = json.load(open(NORM / "fi_landsat_st.json"))["date_tenute"] if (NORM / "fi_landsat_st.json").exists() else []
    return {"n": len(m["giorni"]), "stazione": {"id": st["id"], "nome": st["nome"], "x": x, "z": z, "quota_m": st["quota_m"], "distanza_fp_m": st["distanza_fp_m"]},
            "unita": "decimi di °C", "validazione": m["validazione"], "licenza": "CC BY-SA 4.0, Settore Idrologico e Geologico Regionale (SIR) - Regione Toscana",
            "giorni": [[g["data"], dc(g["tmax"]), dc(g["tmin"])] for g in m["giorni"]], "date_landsat": [v["data"] for v in ls]}


# --- qualità dell'aria -----------------------------------------------------------
def _limite_aria(p):
    """Testo del limite di legge di un inquinante, dai campi del riassunto (norm_firenze.LIMITI_ARIA)."""
    t = []
    if "soglia" in p:
        t.append(f'{p["soglia"]} {p["unita"]} come {p["soglia_su"]}, ' + (f'al massimo {p["ammessi"]} {p["conta"]} l\'anno' if p["ammessi"] else "nessun superamento ammesso"))
    if "limite_annuo" in p:
        t.append(f'media annua {p["limite_annuo"]} {p["unita"]}')
    return "; ".join(t) + " (D.Lgs. 155/2010)" + (f'. {p["nota"]}' if p.get("nota") else "")


def aria():
    """Stazioni ARPAT e riassunti annuali (data/norm: arpat_aria_riassunti.json, da norm_firenze.py arpat). Valori di stazione, nessuna interpolazione;
    le stazioni fuori dal riquadro hanno fuori_riquadro true e la distanza dal riquadro in metri."""
    if not (NORM / "arpat_aria_riassunti.json").exists():
        return None
    m = json.load(open(NORM / "arpat_aria_riassunti.json"))
    st = []
    for q in m["stazioni"]:
        x, z = loc(q["e"], q["n"])
        st.append({"id": "aqs_" + q["codice"].lower(), "codice": q["codice"], "nome": f'{q["codice"]} ({q["comune"]})', "x": x, "z": z,
                   "fuori_riquadro": not FP.contains(Point(q["e"], q["n"])), "distanza_m": q["distanza_fp_m"],
                   "tipo": q["tipo"] or "non dichiarato", "zona": q["zona"], "rete": ", ".join(q["reti"]), "avviso": q["avviso"], "misurati": q["misurati"],
                   "inquinanti": [{**p, "limite": _limite_aria(p)} for p in q["inquinanti"]]})
    return {"n": len(st), "anno": m["anno"], "periodo": f'{m["anno"]}-01-01 / {m["anno"]}-12-31', "validazione": m["validazione"], "ora": m["ora"],
            "norma": m["norma"], "limiti_url": m["limiti_url"], "selezione": m["selezione"], "stazioni": st}


# --- fonti ---------------------------------------------------------------------
def fonti():
    base = json.load(open(ROOT / "pipeline/baselines/bas_firenze_novoli_20261009.json"))
    snaps = {x["source_id"]: x for x in base["snapshot"]}
    out = []
    for sid, uso in USO.items():
        if sid not in snaps:   # fonte aggiunta dopo la baseline congelata (catasto): ultimo snapshot valido, segnalato
            ok = [json.load(open(q)) for q in sorted((ROOT / "pipeline/snapshots").glob(f"snp_{sid.removeprefix('src_')}_*.json"))]
            ok = [s_ for s_ in ok if s_["status"] == "ok"]
            snaps[sid] = {**ok[-1], "fuori_baseline": True}
        src = json.load(open(ROOT / f"pipeline/sources/{sid}.json"))
        sn = json.load(open(ROOT / f"pipeline/snapshots/{snaps[sid]['snapshot_id']}.json"))
        lic = src["license"]
        cp = src.get("content_period", {})
        out.append({"id": sid, "titolo": src["title"], "ente": src["publisher"], "url": src["dataset_url"],
                    "licenza": lic.get("identifier") or "non scritta sul layer (licenza regionale)", "stato_licenza": lic["state"],
                    "riserva": lic.get("reserve_note"), "scaricato": sn["retrieved_at"][:10],
                    "data": data_dato(sid, cp), "sha256_snapshot": snaps[sid]["sha256"], "uso": uso,
                    **({"fuori_baseline": True} if snaps[sid].get("fuori_baseline") else {})})
    return out


# --- scrittura -----------------------------------------------------------------
def scrivi(out, nome, obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    gz = gzip.compress(raw, 9, mtime=0)
    (out / nome).write_bytes(gz)
    return {"file": nome, "byte": len(gz), "byte_decompressi": len(raw), "sha256": hashlib.sha256(gz).hexdigest(), "n": obj.get("n")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "assets"))
    ap.add_argument("--analysis", default=str(ROOT / "analysis/firenze_novoli"))
    ap.add_argument("--shadow", default=str(ROOT / "shadow/firenze_novoli"))
    ap.add_argument("--scenarios", default=str(ROOT / "scenarios/firenze_novoli"))
    a = ap.parse_args()
    dest = pathlib.Path(a.out); dest.mkdir(parents=True, exist_ok=True)
    out = pathlib.Path(tempfile.mkdtemp(prefix=".build-", dir=dest.parent))   # stesso disco: os.replace atomico
    try:
        costruisci(out, a)
        for old in dest.glob("*.json.gz"):   # gli asset vecchi si toccano solo a costruzione riuscita
            if not (out / old.name).exists(): old.unlink()
        for f in sorted(out.iterdir(), key=lambda f: f.name == "index.json"):   # indice per ultimo
            os.replace(f, dest / f.name)
    finally:
        shutil.rmtree(out, ignore_errors=True)


def costruisci(out, a):
    zref, ter = terreno()
    assets = {"terreno": scrivi(out, "terreno.json.gz", {"n": ter["nx"] * ter["ny"], **ter}),
              "edifici": scrivi(out, "edifici.json.gz", edifici(zref)),
              "alberi": scrivi(out, "alberi.json.gz", alberi(zref)),
              "rete": scrivi(out, "rete.json.gz", rete())}
    pt = punti()
    assets["punti"] = scrivi(out, "punti.json.gz", {"n": len(pt), "punti": pt})
    aree = _osm_aree()
    assets["mappa"] = scrivi(out, "mappa.json.gz", mappa(aree))
    assets["etichette"] = scrivi(out, "etichette.json.gz", etichette(aree))
    assets["catasto"] = scrivi(out, "catasto.json.gz", catasto())
    assets["tematismi"] = scrivi(out, "tematismi.json.gz", tematismi())
    for nome, fn in (("temperature", temperature), ("meteo", meteo), ("aria", aria)):   # opzionali: servono i file normalizzati in data/norm
        if (obj := fn()) is not None:
            assets[nome] = scrivi(out, f"{nome}.json.gz", obj)
    analitici = {}
    for k, fn, d in (("accessibilita", accessibilita, a.analysis), ("ombra", ombra, a.shadow), ("ombra_rifugi", ombra_rifugi, a.shadow), ("scenari", interventi, a.scenarios)):
        obj = fn(d)
        analitici[k] = {"presente": obj is not None}
        if obj:
            nome = "interventi" if k == "scenari" else k
            assets[nome] = scrivi(out, f"{nome}.json.gz", obj)
    idx = {"versione": 1, "generato": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "aoi_id": AOI["aoi_id"],
           "area": {"nome": "Firenze, Novoli - Firenze Nova (riquadro FP, 2 km²)", "crs_origine": "EPSG:7791", "origine_e_n": [round(CE, 2), round(CN, 2)],
                    "lon_lat_centro": [round(LON0, 6), round(LAT0, 6)], "semiassi_m": [round((E1 - E0) / 2, 1), round((N1 - N0) / 2, 1)],
                    "quota_riferimento_m": zref, "piano": "x = est, y = alto, z = -nord, in metri dal centro"},
           "baseline": "bas_firenze_novoli_20261009", "assets": assets, "livelli_analitici": analitici,
           "livelli": LIVELLI, "fonti": fonti(), "limiti": LIMITI}
    (out / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    tot = sum(v["byte"] for v in assets.values())
    print({k: (v["byte"], v["n"]) for k, v in assets.items()}, "totale", tot, "byte")


if __name__ == "__main__":
    main()
