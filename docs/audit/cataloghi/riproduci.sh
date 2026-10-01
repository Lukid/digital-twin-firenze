#!/usr/bin/env bash
# Rigenera i campioni in campioni/. Eseguire dalla cartella docs/audit/cataloghi.
set -u
cd "$(dirname "$0")"; mkdir -p campioni; cd campioni
UA="Mozilla/5.0 (audit)"; S=https://sit.comune.pisa.it/arcgis/rest/services
dl(){ curl -sSL -m 90 -A "$UA" -o "$1" -w "$1 %{http_code} %{size_download}\n" "$2"; }
# 1. ricostruzione dei campioni di docs/research (stessi nomi file)
dl ckan-nazionale-pisa-count.json 'https://www.dati.gov.it/opendata/api/3/action/package_search?q=Pisa&rows=0&facet.field=%5B%22organization%22%5D'
dl ckan-toscana-gtfs.json 'https://dati.toscana.it/api/3/action/package_show?id=rt-oraritb'
dl ckan-toscana-lidar.json 'https://dati.toscana.it/api/3/action/package_show?id=lidar'
dl ckan-toscana-pisa.json 'https://dati.toscana.it/api/3/action/package_search?q=Pisa&rows=100'
dl ckan-toscana-pisa-verde.json 'https://dati.toscana.it/api/3/action/package_search?q=Pisa+AND+verde'
dl ckan-toscana-pisa-alberi.json 'https://dati.toscana.it/api/3/action/package_search?q=Pisa+AND+alber*'
dl ckan-toscana-pisa-pilota.json 'https://dati.toscana.it/api/3/action/package_search?q=Pisa+AND+pilota'   # query ipotizzata: il manifest non la riporta
dl pisa-ciclabili-service.json "$S/Piste_ciclabili/MapServer?f=json"
dl pisa-ciclabili-count.json "$S/Piste_ciclabili/MapServer/0/query?where=1%3D1&returnCountOnly=true&f=json"
dl pisa-ciclabili-sample.geojson "$S/Piste_ciclabili/MapServer/0/query?objectIds=1&outFields=*&outSR=4326&f=geojson"
dl pisa-hosted-services.json "$S/Hosted?f=json"
dl pisa-dbtopografico-service.json "$S/Hosted/Base_DBTopografico/MapServer?f=json"
dl pisa-scuole-service.json "$S/Hosted/edifici_scolastici/FeatureServer?f=json"
dl pisa-scuole-layer.json "$S/Hosted/edifici_scolastici/FeatureServer/4?f=json"
dl pisa-scuole-sample.json "$S/Hosted/edifici_scolastici/FeatureServer/4/query?where=1%3D1&outFields=*&returnGeometry=false&resultRecordCount=1&f=json"
# 2. StatPortal
dl od-home.html https://opendata.comune.pisa.it/
dl od-cosa-e.html 'https://opendata.comune.pisa.it/content/cos%C3%A8-lopendata'
dl od-api.html https://opendata.comune.pisa.it/content/api
dl od-api-2_rest_licenses.json https://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/licenses
dl od-api-2_rest_dataset.json https://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/dataset
dl od-page-grafo.html https://opendata.comune.pisa.it/content/grafo-stradale
dl od-grafo-dlpage.html "https://opendata.comune.pisa.it/metadata_download_page/676/shp/477/650e32c2-94ad-495a-8635-cc9698152ce3%40pisa"
# 3. SIT
dl sit-root.json "$S?f=json"
dl sit-pagina-comune.html https://www.comune.pisa.it/Servizi/S.I.T
dl sit-condizioni-servizio.pdf "https://www.comune.pisa.it/ocmultibinary/download/16297/418809/2/bb7834eecf99f6426a937b5dc6f2f95a.pdf/file/Pisa%2Bcondizioni%2Bservizi.pdf"
# 4. licenze di fonti trasversali
dl arpat-licenza.html https://www.arpat.toscana.it/note-legali
dl arpat-aria-orari.html https://www.arpat.toscana.it/datiemappe/qualita-dellaria-dati-orari/
dl geoscopio.html https://www.regione.toscana.it/-/geoscopio
dl istat-basi-territoriali.html https://www.istat.it/notizia/basi-territoriali-e-variabili-censuarie/
dl geoblog-open-geodata.html https://geoblog.regione.toscana.it/-/open-geodata
dl osm-copyright.html https://www.openstreetmap.org/copyright
dl provincia-pisa-musei.zip https://maps.provincia.pisa.it/metarepo2/api/datasets/musei/download
# intestazioni (nessun download completo: GTFS >77 MB, DBT10K Pisa ~411 MB)
{ for u in http://www502.regione.toscana.it/geoscopio/download/dbtopografico/dbt10k/7z/DBT10K_050_PISA_2010_2010.7z http://www502.regione.toscana.it/geoscopio/download/grafo_stradale/iternet.zip; do echo "### HEAD $u"; curl -sSI -m 40 -A "$UA" "$u" | head -12; done; } > intestazioni-grandi-file.txt
cd ..
python3 scarica_statportal.py
python3 inventario_sit.py
python3 ricerche_ckan.py
python3 genera_manifest.py
