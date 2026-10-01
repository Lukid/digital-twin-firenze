#!/bin/bash
# Rigenera i campioni del tema verde/alberi. Richiede curl e python3. Eseguire da questa cartella.
set -e; cd "$(dirname "$0")"; mkdir -p campioni
python3 scan_catalogo_pisa.py campioni/catalogo_pisa_titoli.json   # 663 titoli del catalogo comunale
./ckan_queries.sh                                                    # query CKAN Toscana e dati.gov.it (inclusi zeri)
for id in dtm-lidar-2023 dsm-lidar-2023 dtm-2017 dsm-2017 dsm-2007; do curl -s "https://dati.toscana.it/api/3/action/package_show?id=$id" -o campioni/ckan_pkg_$id.json; done
python3 sit_verde.py                                                 # conteggi layer verde SIT per zona
for l in 104 105 218 237 243; do curl -s "https://sit.comune.pisa.it/arcgis/rest/services/PSI/MapServer/$l?f=json" -o campioni/sit_psi_layer_$l.json; done
curl -s "https://sit.comune.pisa.it/arcgis/rest/services/PSI/MapServer?f=json" -o campioni/sit_psi_service.json
python3 osm_alberi.py && python3 analisi_osm.py                      # Overpass (~1 min per zona)
B=https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_StreetTreeLayer_2018/MapServer
curl -s "$B?f=pjson" -o campioni/cop_stl_mapserver.json; curl -s "$B/0?f=pjson" -o campioni/cop_stl_layer0.json; curl -s "$B/2?f=pjson" -o campioni/cop_stl_layer2.json
curl -s -G "$B/0/query" --data-urlencode "geometry=10.3920,43.7115,10.4060,43.7215" --data "geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&resultRecordCount=5&f=geojson" -o campioni/cop_stl_sample_Z1.geojson
curl -sL "https://www.comune.pisa.it/Novita/Comunicati/Rinnovo-arboreo-il-Comune-di-Pisa-prosegue-gli-incontri-con-le-associazioni-ambientaliste" -o campioni/comunicato_rinnovo_arboreo.html
curl -sL "https://www.comune.pisa.it/it/ufficio-scheda/20099/Censimento-e-Mappa-degli-alberi.html" -o campioni/censimento_mappa_alberi_old_url_410.html
curl -sL "https://www.comune.pisa.it/Argomenti/Ambiente/Spazio-verde" -o campioni/spazio_verde.html
curl -sL "https://www.comune.pisa.it/Amministrazione/Documenti-e-dati/Dataset" -o campioni/dataset_page.html
curl -sL "https://arpi.unipi.it/handle/11568/885149" -o campioni/arpi_885149.html
B2=http://opendata.comune.pisa.it/SpodCkanApi/api
curl -sL $B2/1/rest/licenses -o campioni/spod_1_rest_licenses.json; curl -sL $B2/2/rest/package -o campioni/spod_2_rest_package.json
# NON scaricare http://www502.regione.toscana.it/geoscopio/download/tematici/aree_protette/alberi_monumentali.zip: risponde con 1,68 GB (verificato con HEAD).
for p in catalogo-opendata categoria/ambiente content/api; do curl -sL "https://opendata.comune.pisa.it/$p" -o "campioni/od_$(echo $p|tr / _).html"; done
python3 make_manifest.py
find campioni -size 0 -print   # deve stampare nulla
python3 sit_verde.py; python3 osm_alberi.py && python3 analisi_osm.py   # zone.json = riquadri canonici ZONE.json; i primi riquadri sono in campioni/riquadri_iniziali/
