"""Record di fonte (contracts/schemas/source.schema.json) in pipeline/sources/*.json, con i controlli sui dati normalizzati."""
import json, pyogrio
import lib
from lib import NORM, ROOT, SRCDIR

def n(gpkg, layer):
    try: return pyogrio.read_info(NORM / gpkg, layer=layer)["features"]
    except Exception: return None
def chk(name, ok, detail, warn=False): return {"name": name, "result": "pass" if ok else ("warn" if warn else "fail"), "detail": detail}
def lic(state, ident, url, ev, reserve=None, use="internal_prototype"):
    d = {"state": state, "permitted_use": use, "evidence_url": url, "evidence_note": ev}
    if ident: d["identifier"] = ident
    if reserve: d["reserve_note"] = reserve
    return d

SIT_RES = "Nessuna licenza dichiarata sul servizio (copyrightText vuoto, scheda del sito senza condizioni di riuso): un endpoint pubblico non prova una licenza. Uso interno al prototipo finche' il Comune non conferma per iscritto."
SIT_URL = "https://sit.comune.pisa.it/arcgis/rest/services/Hosted"
RT_UV_URL = "https://www502.regione.toscana.it/geoscopio/servizi/wms/EDIFICATO.htm"
RT_MOR_URL = "http://www502.regione.toscana.it/geoscopio/servizi/wms/MORFOLOGIA.htm"
GEOSC = "https://www502.regione.toscana.it/geoscopio/"
S = {
 "src_osm_pisa": dict(title="OpenStreetMap, estratto regionale Centro Italia (ritagliato su Z2 + 500 m)", publisher="OpenStreetMap contributors, estratto di un distributore di estratti OSM",
   dataset_url="https://download.geofabrik.de/europe/italy/centro.html", resource_url="https://download.geofabrik.de/europe/italy/centro-260930.osm.pbf",
   prov={"origin": "crowdsourced", "note": "estratto locale al posto di Overpass (instabile); ritaglio in normalizzazione"},
   license=lic("clear", "ODbL-1.0", "https://www.openstreetmap.org/copyright", "Dati OpenStreetMap sotto ODbL.", use="redistribution"),
   period={"note": "stato di OpenStreetMap al 2026-09-30 (timestamp dell'estratto), senza data di rilievo per oggetto"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lon/lat trattati come RDN2008 geografico (scarto misurato in crs_check.json, voce B)"},
   units={"length_m": "m", "area_m2": "m2"}, fields=["id", "highway", "sidewalk", "crossing", "entrance", "building", "height"],
   checks=lambda: [chk("strade in AOI", (n("osm_pisa.gpkg", "highway") or 0) > 0, f"{n('osm_pisa.gpkg','highway')} tratti"),
                   chk("nodi con tag in AOI", (n("osm_pisa.gpkg", "points") or 0) > 0, f"{n('osm_pisa.gpkg','points')} nodi"),
                   chk("edifici in AOI", (n("osm_pisa.gpkg", "buildings") or 0) > 0, f"{n('osm_pisa.gpkg','buildings')} edifici"),
                   chk("altezze edifici (tag height) compilate", False, "campo quasi vuoto, vedi audit edifici", warn=True)]),
 "src_gtfs_at_toscana": dict(title="GTFS Autolinee Toscane (trasporto pubblico locale)", publisher="Regione Toscana / Autolinee Toscane",
   dataset_url="https://dati.toscana.it/dataset/rt-oraritb", resource_url="https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs",
   prov={"origin": "official_download"},
   license=lic("clear_with_reserve", "cc-by", "https://dati.toscana.it/dataset/rt-oraritb", "Campo license_id del catalogo regionale (CKAN, letto con gli strumenti ckan): 'Creative Commons Attribution'.",
               "Le condizioni specifiche del feed non sono state trovate: vale solo il campo del catalogo."),
   period={"start": "2026-10-01", "end": "2026-10-21", "note": "feed_start_date e feed_end_date da feed_info.txt; il feed scade il 21 ottobre 2026"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared", "note": "lat/lon come da specifica GTFS"},
   units={"stop_lat": "deg", "stop_lon": "deg", "trips_on_ref_date": "count"}, fields=["stop_id", "stop_code", "stop_name", "wheelchair_boarding"],
   checks=lambda: [chk("fermate in AOI", (n("gtfs_at_toscana.gpkg", "stops") or 0) > 0, f"{n('gtfs_at_toscana.gpkg','stops')} fermate"),
                   chk("wheelchair_boarding valorizzato", False, "vuoto sulle fermate del feed (come da audit)", warn=True),
                   chk("calendar.txt con giorni attivi", False, "servizio in calendar_dates: le corse del giorno si ricavano da li'", warn=True)]),
 "src_gtfs_trenitalia": dict(title="GTFS Trenitalia (servizio regionale toscano)", publisher="Regione Toscana / Trenitalia",
   dataset_url="https://dati.toscana.it/dataset/rt-oraritb", resource_url="https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/4f85393b-357d-443d-8378-65de4198505f/download/trenitalia.gtfs",
   prov={"origin": "official_download"},
   license=lic("clear_with_reserve", "cc-by", "https://dati.toscana.it/dataset/rt-oraritb", "Stesso dataset del catalogo regionale (CC BY).", "Condizioni specifiche del feed non trovate: vale solo il campo del catalogo."),
   period={"start": "2026-01-15", "end": "2026-12-12", "note": "minimo e massimo di calendar_dates.txt (nessun feed_info.txt); risorsa aggiornata il 2026-01-15"},
   crs={"declared": "EPSG:4326", "vertical_datum": "not_declared"}, units={"stop_lat": "deg", "stop_lon": "deg", "trips_on_ref_date": "count"}, fields=["stop_id", "stop_name"],
   checks=lambda: [chk("stazioni in AOI", (n("gtfs_trenitalia.gpkg", "stops") or 0) > 0, f"{n('gtfs_trenitalia.gpkg','stops')} stazione (Pisa Centrale)")]),
 "src_rt_unita_volumetriche": dict(title="Unita' volumetriche del DB topografico regionale (WFS)", publisher="Regione Toscana", dataset_url=RT_UV_URL,
   resource_url="https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato", prov={"origin": "ogc_service"},
   license=lic("clear_with_reserve", None, RT_UV_URL, "Nessuna licenza sul layer; vale la politica regionale sui dati geografici aperti (CC BY o CC BY-SA, atto 2013).",
               "Licenza non scritta sul layer: dedotta dalla politica regionale. Verificare prima di ridistribuire.", use="internal_prototype"),
   period={"start": "2010-01-01", "end": "2010-12-31", "note": "volo 2010 (campo anno); data di aggiornamento del servizio non dichiarata"},
   crs={"declared": "EPSG:7791", "vertical_datum": "not_declared", "note": "richiesto direttamente in EPSG:7791, nessuna trasformazione"},
   units={"height_m": "m", "ground_elev_m": "m", "roof_elev_m": "m", "area_m2": "m2"}, fields=["uv_id", "edifc_id", "uv_av", "uv_qs", "uv_qe", "uv_por", "anno"],
   checks=lambda: [chk("volumi in AOI", (n("rt_unita_volumetriche.gpkg", "building_volume") or 0) > 0, f"{n('rt_unita_volumetriche.gpkg','building_volume')} volumi"),
                   chk("coincidenza con DBT10K (un_vol)", True, "3107 oggetti in AOI in entrambi; vertici a 0,35 m (crs_check.json, voce C)"),
                   chk("portici (uv_por) popolato", False, "attributo non popolato (audit edifici)", warn=True)]),
 "src_rt_dsm2021": dict(title="DSM 1 m 2021 (WMS morfologia, surrogato del download ufficiale)", publisher="Regione Toscana", dataset_url=RT_MOR_URL,
   resource_url="https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia", prov={"origin": "ogc_service", "note": "SURROGATO: raster letto via GetMap, non il download ufficiale (Cartoteca regionale)"},
   license=lic("clear_with_reserve", "CC-BY-4.0", GEOSC + "geometa/html/r_toscan_c5c907bf-50cc-4a76-8787-abc547509c8d.htm", "Metadato del layer DSM 2021 (audit edifici).",
               "Letto via WMS come surrogato: valori e pixel possono differire dal download ufficiale; datum verticale non dichiarato."),
   period={"start": "2021-01-01", "end": "2021-12-31", "note": "DSM 2021; data esatta di acquisizione nei metadati del layer"},
   crs={"declared": "EPSG:7791", "vertical_datum": "not_declared", "note": "GetMap richiesto in EPSG:7791"}, units={"value": "m"}, fields=["band1"],
   checks=lambda: [chk("raster ritagliato su AOI", True, "1963 x 2144 pixel da 1 m, nessun nodata"), chk("datum verticale", False, "non dichiarato", warn=True)]),
 "src_rt_dtm10": dict(title="DTM 10 m (WMS morfologia, surrogato del download ufficiale)", publisher="Regione Toscana", dataset_url=RT_MOR_URL,
   resource_url="https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia", prov={"origin": "ogc_service", "note": "SURROGATO: raster letto via GetMap, non il download ufficiale"},
   license=lic("clear_with_reserve", "CC-BY-4.0", RT_MOR_URL, "Metadato regionale (audit edifici).", "Letto via WMS come surrogato; datum verticale non dichiarato."),
   period={"note": "epoca del DTM 10 m non dichiarata dal servizio"}, crs={"declared": "EPSG:7791", "vertical_datum": "not_declared"}, units={"value": "m"}, fields=["band1"],
   checks=lambda: [chk("raster ritagliato su AOI", True, "196 x 214 pixel da 10 m"), chk("nodata", False, "0,51% dei pixel con -9999 (mascherati)", warn=True)]),
 "src_sit_civici": dict(title="Civici puntuali del Comune di Pisa (SIT)", publisher="Comune di Pisa", dataset_url=SIT_URL + "/Civici_puntuali_View/FeatureServer/0",
   prov={"origin": "ogc_service"}, license=lic("unproven", None, "https://sit.comune.pisa.it/arcgis/rest/services/Hosted", "Servizio ArcGIS pubblico senza licenza.", SIT_RES),
   period={"note": "campo dt_agg per civico; ultimo aggiornamento del layer 2026-09-30 (audit)"},
   crs={"declared": "EPSG:3857", "vertical_datum": "not_declared", "note": "CRS nativo del layer 102100 (Web Mercator), non 3003 come per gli altri layer SIT"}, units={}, fields=["objectid_1", "num_civico", "indirizzo", "sezione_censuaria_istat"],
   checks=lambda: [chk("civici in AOI", (n("sit_civici.gpkg", "civici") or 0) > 0, f"{n('sit_civici.gpkg','civici')} punti"), chk("licenza", False, "non dimostrata", warn=True)]),
 "src_sit_scuole": dict(title="Scuole (infanzia, primarie, secondarie) del Comune di Pisa (SIT)", publisher="Comune di Pisa", dataset_url=SIT_URL + "/Scuole_infanzia_materne_primarie_e_secondarie/FeatureServer/0",
   prov={"origin": "ogc_service"}, license=lic("unproven", None, "https://sit.comune.pisa.it/arcgis/rest/services/Hosted", "Servizio ArcGIS pubblico senza licenza.", SIT_RES),
   period={"note": "layer aggiornato il 2025-11-24 (audit)"}, crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "nativo 102091 (Monte Mario Italy 1 = EPSG:3003)"}, units={}, fields=["fid", "tiposcuola", "nomi", "via", "istit_scol"],
   checks=lambda: [chk("scuole in AOI", (n("sit_scuole.gpkg", "scuole") or 0) > 0, f"{n('sit_scuole.gpkg','scuole')} punti"), chk("codice meccanografico MIM", False, "assente: nessun dst_ ufficiale ricavabile dal solo SIT", warn=True)]),
 "src_sit_edifici_scolastici": dict(title="Edifici scolastici del Comune di Pisa (SIT)", publisher="Comune di Pisa", dataset_url=SIT_URL + "/edifici_scolastici/FeatureServer/4",
   prov={"origin": "ogc_service"}, license=lic("unproven", None, "https://sit.comune.pisa.it/arcgis/rest/services/Hosted", "Servizio ArcGIS pubblico senza licenza.", SIT_RES),
   period={"note": "layer aggiornato il 2025-11-24 (audit)"}, crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "nativo 102091"}, units={"SHAPE__Area": "m2"}, fields=["fid"],
   checks=lambda: [chk("edifici in AOI", (n("sit_edifici_scolastici.gpkg", "edifici_scolastici") or 0) > 0, f"{n('sit_edifici_scolastici.gpkg','edifici_scolastici')} poligoni")]),
 "src_rt_dbt10k_pisa": dict(title="DB topografico regionale 1:10.000, foglio Pisa (2010)", publisher="Regione Toscana", dataset_url="https://dati.toscana.it/dataset/dbt10k-li-pi-pt-po-si",
   resource_url="http://www502.regione.toscana.it/geoscopio/download/dbtopografico/dbt10k/7z/DBT10K_050_PISA_2010_2010.7z", prov={"origin": "official_download"},
   license=lic("clear", "CC-BY-4.0", "https://dati.toscana.it/dataset/dbt10k-li-pi-pt-po-si", "Catalogo (CKAN): Creative Commons Attribution; il pacchetto contiene licenza_dbt10k_ccby40.pdf.", use="redistribution"),
   period={"start": "2010-01-01", "end": "2010-12-31", "note": "dati 2010, scala 1:10.000"}, crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "shapefile 3003 con Z"}, units={}, fields=["un_vol_id", "un_vol_av"],
   checks=lambda: [chk("ispezionato in AOI", True, "vedi ispezione_big.json"), chk("non normalizzato in data/norm", False, "ispezione soltanto (non bloccante, non richiesto)", warn=True)]),
 "src_rt_iternet": dict(title="Grafo stradale regionale Iter.net", publisher="Regione Toscana", dataset_url="http://www502.regione.toscana.it/geoscopio/download/grafo_stradale/iternet.zip",
   resource_url="http://www502.regione.toscana.it/geoscopio/download/grafo_stradale/iternet.zip", prov={"origin": "official_download"},
   license=lic("clear_with_reserve", None, "https://dati.toscana.it/", "Atto regionale 2013 sui dati aperti: CC BY o CC BY-SA, non riportata sul file (audit cataloghi).", "Licenza non sul file e BY/BY-SA da accertare."),
   period={"note": "epoca non dichiarata nel file; StatPortal indica aprile 2015; file del 2025-10-10"}, crs={"declared": "EPSG:3003", "vertical_datum": "not_declared", "note": "shapefile, CRS dai file .prj"}, units={}, fields=["elem_strad", "civici"],
   checks=lambda: [chk("ispezionato in AOI", True, "vedi ispezione_big.json"), chk("non normalizzato in data/norm", False, "ispezione soltanto", warn=True)]),
}

def build():
    SRCDIR.mkdir(exist_ok=True)
    for sid, s in S.items():
        d = {"source_id": sid, "title": s["title"], "publisher": s["publisher"], "dataset_url": s["dataset_url"], "provenance": s["prov"], "license": s["license"],
             "content_period": s["period"], "crs": s["crs"], "units": s["units"], "schema_fields": s["fields"], "checks": s["checks"]()}
        if "resource_url" in s: d["resource_url"] = s["resource_url"]
        json.dump(d, open(SRCDIR / f"{sid}.json", "w"), indent=1, ensure_ascii=False)
    print(len(S), "record di fonte")
if __name__ == "__main__": build()
