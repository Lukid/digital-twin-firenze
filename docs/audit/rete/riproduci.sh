#!/bin/bash
# Rigenera i campioni. Overpass è spesso lento (429/504): lo script riprova da solo. Eseguire da docs/audit/rete/.
set -e
cd "$(dirname "$0")"; mkdir -p campioni
python3 scarica_osm.py            # osm_Z1..Z4.json
python3 scarica_poi.py            # osm_poi.json
python3 analizza_osm.py > /dev/null   # campioni/metriche_osm.json
python3 analizza_poi.py           # stampa destinazioni e ingressi
S=https://sit.comune.pisa.it/arcgis/rest/services
curl -s "$S?f=json" -o campioni/sit_root.json
curl -s "$S/STRADE/MapServer/0?f=json" -o campioni/sit_STRADE_layer0.json
curl -s "$S/Base_CTR_2023/MapServer/1?f=json" -o campioni/sit_CTR_layer1.json
curl -s -G "$S/Base_CTR_2023/MapServer/1/query" --data-urlencode "geometry=10.3990,43.7190,10.4010,43.7200" --data-urlencode geometryType=esriGeometryEnvelope --data-urlencode inSR=4326 --data-urlencode "where=1=1" --data-urlencode "outFields=layer,v_lin_cl,v_lin_lt,other_ty" --data-urlencode returnGeometry=false --data-urlencode f=json -o campioni/sit_ctr_campione_cavalieri.json
T=https://dati.toscana.it/api/3/action
curl -s "$T/package_show?id=grafo-civici" -o campioni/ckan_toscana_grafo-civici.json
curl -s -G "$T/package_search" --data-urlencode "q=database topografico regionale" --data-urlencode rows=8 -o campioni/ckan_toscana_dbtopo.json
curl -sIL http://www502.regione.toscana.it/geoscopio/download/grafo_stradale/iternet.zip | head -12 > campioni/head_iternet.txt
curl -sIL http://www502.regione.toscana.it/geoscopio/download/dbtopografico/dbt10k/7z/DBT10K_050_PISA_2010_2010.7z | egrep -i "HTTP|content-length|last-mod" > campioni/head_dbt10k_pisa.txt
# altre ricerche CKAN eseguite: vedere campioni/ckan_*.json (q= grafo stradale, marciapiedi, rete pedonale, attraversamenti pedonali, ...)
