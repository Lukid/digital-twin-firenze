#!/usr/bin/env python3
"""manifest.json: path, URL, timestamp UTC (mtime del file scaricato), byte, sha256. Segnala file a 0 byte."""
import json, os, hashlib, datetime, re
S = "https://sit.comune.pisa.it/arcgis/rest/services"
URL = {
 "ckan-nazionale-pisa-count.json": "https://www.dati.gov.it/opendata/api/3/action/package_search?q=Pisa&rows=0&facet.field=[\"organization\"]",
 "ckan-toscana-gtfs.json": "https://dati.toscana.it/api/3/action/package_show?id=rt-oraritb",
 "ckan-toscana-lidar.json": "https://dati.toscana.it/api/3/action/package_show?id=lidar",
 "ckan-toscana-pisa.json": "https://dati.toscana.it/api/3/action/package_search?q=Pisa&rows=100",
 "ckan-toscana-pisa-verde.json": "https://dati.toscana.it/api/3/action/package_search?q=Pisa+AND+verde",
 "ckan-toscana-pisa-alberi.json": "https://dati.toscana.it/api/3/action/package_search?q=Pisa+AND+alber*",
 "ckan-toscana-pisa-pilota.json": "https://dati.toscana.it/api/3/action/package_search?q=Pisa+AND+pilota (query ipotizzata)",
 "pisa-ciclabili-service.json": S + "/Piste_ciclabili/MapServer?f=json",
 "pisa-ciclabili-count.json": S + "/Piste_ciclabili/MapServer/0/query?where=1=1&returnCountOnly=true&f=json",
 "pisa-ciclabili-sample.geojson": S + "/Piste_ciclabili/MapServer/0/query?objectIds=1&outFields=*&outSR=4326&f=geojson",
 "pisa-hosted-services.json": S + "/Hosted?f=json",
 "pisa-dbtopografico-service.json": S + "/Hosted/Base_DBTopografico/MapServer?f=json",
 "pisa-scuole-service.json": S + "/Hosted/edifici_scolastici/FeatureServer?f=json",
 "pisa-scuole-layer.json": S + "/Hosted/edifici_scolastici/FeatureServer/4?f=json",
 "pisa-scuole-sample.json": S + "/Hosted/edifici_scolastici/FeatureServer/4/query?where=1=1&outFields=*&returnGeometry=false&resultRecordCount=1&f=json",
 "od-home.html": "https://opendata.comune.pisa.it/",
 "od-cosa-e.html": "https://opendata.comune.pisa.it/content/cos%C3%A8-lopendata",
 "od-api.html": "https://opendata.comune.pisa.it/content/api",
 "od-api-2_rest_licenses.json": "https://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/licenses",
 "od-api-2_rest_dataset.json": "https://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/dataset",
 "od-statportal-dataset.json": "https://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/dataset/{id} x663 (scarica_statportal.py)",
 "od-page-grafo.html": "https://opendata.comune.pisa.it/content/grafo-stradale",
 "od-grafo-dlpage.html": "https://opendata.comune.pisa.it/metadata_download_page/676/shp/477/650e32c2-94ad-495a-8635-cc9698152ce3%40pisa",
 "sit-root.json": S + "?f=json",
 "sit-folder-Hosted.json": S + "/Hosted?f=json", "sit-folder-SIT_2013.json": S + "/SIT_2013?f=json", "sit-folder-Utilities.json": S + "/Utilities?f=json",
 "sit-inventario.json": "inventario_sit.py su " + S,
 "sit-pagina-comune.html": "https://www.comune.pisa.it/Servizi/S.I.T",
 "sit-condizioni-servizio.pdf": "https://www.comune.pisa.it/ocmultibinary/download/16297/418809/2/bb7834eecf99f6426a937b5dc6f2f95a.pdf/file/Pisa%2Bcondizioni%2Bservizi.pdf",
 "arpat-licenza.html": "https://www.arpat.toscana.it/note-legali",
 "arpat-aria-orari.html": "https://www.arpat.toscana.it/datiemappe/qualita-dellaria-dati-orari/",
 "istat-basi-territoriali.html": "https://www.istat.it/notizia/basi-territoriali-e-variabili-censuarie/",
 "geoblog-open-geodata.html": "https://geoblog.regione.toscana.it/-/open-geodata",
 "geoscopio.html": "https://www.regione.toscana.it/-/geoscopio",
 "osm-copyright.html": "https://www.openstreetmap.org/copyright",
 "provincia-pisa-musei.zip": "https://maps.provincia.pisa.it/metarepo2/api/datasets/musei/download",
 "provincia-pisa-musei.geojson": "estratto da provincia-pisa-musei.zip (RISORSE/GeoJSON/musei_r1.geojson)",
 "provincia-pisa-musei-metadato.xml": "estratto da provincia-pisa-musei.zip (METADATO_E_LICENZA/musei_r1.xml)",
 "ckan-ricerche-tematiche.json": "ricerche_ckan.py su dati.toscana.it e dati.gov.it",
 "intestazioni-grandi-file.txt": "HEAD su DBT10K_050_PISA_2010_2010.7z e iternet.zip (regione.toscana.it/geoscopio)",
 "intestazioni-gtfs-dbtr.txt": "GET con Range su endpoint GTFS Autolinee Toscane e DBT10K Pisa; il GTFS ignora Range (sessione interrotta dopo 77 MB)",
}
files = []
for f in sorted(os.listdir("campioni")):
    p = os.path.join("campioni", f); b = open(p, "rb").read()
    ts = datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files.append({"path": "campioni/" + f, "url": URL.get(f, "?"), "timestamp_utc": ts, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
zero = [x["path"] for x in files if x["bytes"] == 0]
json.dump({"nota": "timestamp_utc = ora di scrittura del file (fine del download)", "files": files, "file_a_zero_byte": zero}, open("manifest.json", "w"), indent=1, ensure_ascii=False)
print(len(files), "file; a zero byte:", zero)
