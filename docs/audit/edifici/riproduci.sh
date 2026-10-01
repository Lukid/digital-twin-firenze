#!/usr/bin/env bash
# Rigenera i campioni di docs/audit/edifici/campioni. Eseguire da docs/audit/edifici/.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p campioni
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip -q install shapely pyproj rasterio numpy; }
PY=.venv/bin/python
SIT=https://sit.comune.pisa.it/arcgis/rest/services
for u in Hosted/Base_DBTopografico/MapServer Hosted/FABBRICATI_PEG/FeatureServer Hosted/FABBRICATI_PEG/FeatureServer/0 Hosted/edifici_scolastici/FeatureServer/0 FABBRICATI_PEG/MapServer/0 periodizzazione_edificato_share/MapServer/1 periodizzazione_edificato_share/MapServer/0 Base_CTR_per_POC/MapServer/1 Base_CTR_2023/MapServer/1; do
  curl -s -m 40 "$SIT/$u?f=json" -o "campioni/sit_$(echo $u | tr / _).json"; done
$PY script/fetch_sit.py                 # edifici SIT comunale per zona (GeoJSON con Z)
W="https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato"
curl -sL "$W&SERVICE=WMS&REQUEST=GetCapabilities" -o campioni/rt_edificato_wms_caps.xml
curl -sL "$W&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities" -o campioni/rt_edificato_wfs_caps.xml
curl -sL "$W&SERVICE=WFS&VERSION=2.0.0&REQUEST=DescribeFeatureType&TYPENAMES=rt_edif.unitavolumetriche" -o campioni/rt_uv_describe.xml
$PY script/fetch_rt_uv.py               # Unità volumetriche Regione Toscana per zona
M="https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia"
curl -sL "$M&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities" -o campioni/rt_morfologia_wms_caps.xml
curl -sL "$M&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities" -o campioni/rt_morfologia_wcs_caps.xml
for z in Z1 Z2 Z3 Z4; do $PY script/fetch_raster.py $z 500; done   # DSM 2021, DTM 1 m (vuoto a Pisa), DTM 10 m
# DTM 1 m: tenere solo la prova di Z1 (nelle altre zone il contenuto è identico, tutto zero)
rm -f campioni/dtm_Z[234]_*.tif
curl -sL "https://www502.regione.toscana.it/geonetwork/srv/api/records/r_toscan:f3ff89ee-49fa-4487-89fe-c69ae58ecd0c/formatters/xml" -o campioni/geonetwork_lidar_1m.xml
curl -sL "https://www502.regione.toscana.it/geoscopio/geometa/html/r_toscan_261ec1b2-bf25-4973-b853-ac08e060ec62.htm" -o campioni/geometa_261ec.htm
curl -sL "https://www502.regione.toscana.it/geoscopio/geometa/html/r_toscan_c5c907bf-50cc-4a76-8787-abc547509c8d.htm" -o campioni/geometa_dsm2021.htm
for n in EDIFICATO MORFOLOGIA CTR; do curl -sL "http://www502.regione.toscana.it/geoscopio/servizi/wms/$n.htm" -o campioni/geoscopio_wms_$n.htm; done
for n in dbt2k database-topografico-1-2-000 dbt10k-li-pi-pt-po-si lidar dtm-2017; do curl -sL "https://dati.toscana.it/api/3/action/package_show?id=$n" -o campioni/ckan_$n.json; done
$PY script/fetch_osm.py                 # può richiedere vari tentativi: Overpass è spesso sovraccarico
$PY script/analizza_ndsm.py             # nDSM contro uv_av
$PY script/analizza_osm_uv.py           # statistiche per zona e confronto OSM/UV
$PY script/make_manifest.py
# Non rigenerati da questo script: ckan_ricerche_edifici.json (package_search ripetuti, query elencate nel file).
