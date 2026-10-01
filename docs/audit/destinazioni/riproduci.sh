#!/bin/bash
# Rigenera i campioni di docs/audit/destinazioni/campioni. Data di riferimento dell'audit: 2026-10-01.
# Richiede curl e python3. Il feed GTFS (circa 177 MB) e i CSV MIM vengono scaricati in una cartella temporanea, non nel repository.
set -u
cd "$(dirname "$0")"
mkdir -p campioni; T=${TMPDIR:-/tmp}/dest_audit; mkdir -p $T
SIT=https://sit.comune.pisa.it/arcgis/rest/services/Hosted
UA="digital-twin-pisa-audit/0.1"

# 1. SIT Pisa: scuole (punti), edifici scolastici (poligoni), plessi e istituti comprensivi (bacini), civici
q() { curl -sS -m 90 -G "$SIT/$1/FeatureServer/$2/query" --data-urlencode "where=1=1" --data-urlencode "outFields=*" --data-urlencode "outSR=4326" --data-urlencode "f=geojson" -o campioni/sit_$3.geojson; }
q Plessi_scolastici 6 plessi
q Scuole_infanzia_materne_primarie_e_secondarie 0 scuole
q Istituti_Comprensivi 7 istituti
q edifici_scolastici 4 edifici
for s in Plessi_scolastici Scuole_infanzia_materne_primarie_e_secondarie Istituti_Comprensivi edifici_scolastici Civici_puntuali_View; do curl -sS -m 60 "$SIT/$s/FeatureServer?f=json" -o campioni/sit_$s.service.json; done
curl -sS -m 60 "$SIT/Scuole_infanzia_materne_primarie_e_secondarie/FeatureServer/0?f=json" -o campioni/sit_layer_scuole.json
curl -sS -m 60 "$SIT/Plessi_scolastici/FeatureServer/6?f=json" -o campioni/sit_layer_plessi.json
curl -sS -m 60 "$SIT/Civici_puntuali_View/FeatureServer/0?f=json" -o campioni/sit_layer_civici.json
# civici entro il raggio di ciascuna zona (zone.json)
python3 - <<'PY'
import json,subprocess
z=json.load(open('zone.json'))
for k in ['Z1','Z2','Z3','Z4']:
    c=z[k]; out=[]; off=0
    while True:
        a=['curl','-sS','-m','90','-G','https://sit.comune.pisa.it/arcgis/rest/services/Hosted/Civici_puntuali_View/FeatureServer/0/query',
           '--data-urlencode',f"geometry={c['lon']},{c['lat']}",'--data-urlencode','geometryType=esriGeometryPoint','--data-urlencode','inSR=4326',
           '--data-urlencode',f"distance={c['raggio_m']}",'--data-urlencode','units=esriSRUnit_Meter','--data-urlencode','spatialRel=esriSpatialRelIntersects',
           '--data-urlencode','where=1=1','--data-urlencode','outFields=objectid_1,indirizzo,num_civico,esp_civico,sezione_censuaria_istat,quartiere,plesso_scolastico,ambito,dt_agg',
           '--data-urlencode','outSR=4326','--data-urlencode','f=geojson','--data-urlencode',f'resultOffset={off}','--data-urlencode','resultRecordCount=1000']
        d=json.loads(subprocess.check_output(a)); f=d.get('features',[]); out+=f
        if len(f)<1000 and not d.get('exceededTransferLimit'): break
        off+=1000
    json.dump({'type':'FeatureCollection','features':out},open(f'campioni/sit_civici_{k}.geojson','w'))
PY

# 2. MIM anagrafe scuole 2026/27 (statali e paritarie), senza coordinate
MIM=http://dati.istruzione.it/opendata/opendata/catalogo/elements1
curl -sS -m 180 -L -o $T/mim_stat.csv $MIM/SCUANAGRAFESTAT20262720260901.csv
curl -sS -m 180 -L -o $T/mim_par.csv  $MIM/SCUANAGRAFEPAR20262720260901.csv
curl -sS -m 60 "https://www.dati.gov.it/opendata/api/3/action/package_show?id=informazioni-anagrafiche-scuole-statali" -o campioni/ckan_dati_gov_mim_scuole_statali.json

# 3. Provincia di Pisa, edifici scolastici (scuole superiori, 2017)
curl -sS -m 60 "https://dati.toscana.it/api/3/action/package_show?id=edifici-scolastici" -o campioni/ckan_edifici_scolastici_provpisa.json
curl -sS -m 90 -L -o $T/edprov.zip https://maps.provincia.pisa.it/metarepo2/api/datasets/edifici_scolastici/download
(cd $T && unzip -oq edprov.zip -d edprov)
cp $T/edprov/edifici_scolastici_r1/RISORSE/*.csv campioni/provincia_edifici_scolastici_raw.csv
cp $T/edprov/edifici_scolastici_r1/METADATO_E_LICENZA/edifici_scolastici_r1.rdf campioni/provincia_edifici_scolastici_metadato.rdf

# 4. GTFS Autolinee Toscane (bus, tutta la regione)
curl -sS -m 600 -L -o $T/gtfs_at.zip https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs
shasum -a 256 $T/gtfs_at.zip
(cd $T && rm -rf g && mkdir g && cd g && unzip -oq ../gtfs_at.zip)
G=$T/g
cp $G/feed_info.txt campioni/gtfs_feed_info.txt; cp $G/agency.txt campioni/gtfs_agency.txt
for f in stops routes trips calendar calendar_dates stop_times; do head -1 $G/$f.txt > campioni/gtfs_${f}_intestazione.txt; done
head -6 $G/stop_times.txt > campioni/gtfs_stop_times_prime5righe.txt
python3 - <<PY
import csv
r=list(csv.reader(open('$G/routes.txt')))
w=csv.writer(open('campioni/gtfs_routes_pisa_UPI_EXPI.csv','w',newline='')); w.writerow(r[0]); w.writerows(x for x in r[1:] if x[1] in('UPI','EXPI'))
PY

# 4b. GTFS Trenitalia (solo per le stazioni di Pisa)
curl -sS -m 200 -L -o $T/tren.zip https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/4f85393b-357d-443d-8378-65de4198505f/download/trenitalia.gtfs
shasum -a 256 $T/tren.zip
(cd $T && rm -rf tren && mkdir tren && cd tren && unzip -oq ../tren.zip)
python3 treni_pisa.py $T/tren campioni/trenitalia_stazioni_pisa.csv

# 5. OpenStreetMap via Overpass (ritentativi: il servizio risponde spesso 504/429)
./osm_tutte.sh

# 6. Analisi: fermate per zona, concordanza fonti, riepilogo
python3 analizza.py $G $T/mim_stat.csv $T/mim_par.csv campioni/provincia_edifici_scolastici_raw.csv
python3 verifica_gtfs.py $G > campioni/gtfs_verifica_integrita.txt
# 6b. Ricalcolo sui riquadri canonici di ../ZONE.json
./ricalcolo_osm.sh
python3 ricalcolo.py $G $T/mim_stat.csv $T/mim_par.csv

# 7. Conteggio civici attorno ai candidati (dipende da candidati_caso_A.json prodotto da analizza.py)
python3 - <<'PY'
import json,subprocess
d=json.load(open('campioni/candidati_caso_A.json'));out={}
for k,v in d.items():
    la,lo=v['centro_osm']; r=[]
    for dist in (500,1000):
        a=subprocess.check_output(['curl','-sS','-m','60','-G','https://sit.comune.pisa.it/arcgis/rest/services/Hosted/Civici_puntuali_View/FeatureServer/0/query','--data-urlencode',f'geometry={lo},{la}','--data-urlencode','geometryType=esriGeometryPoint','--data-urlencode','inSR=4326','--data-urlencode',f'distance={dist}','--data-urlencode','units=esriSRUnit_Meter','--data-urlencode','where=1=1','--data-urlencode','returnCountOnly=true','--data-urlencode','f=json'])
        r.append(json.loads(a)['count'])
    out[k]={'civici_entro_500m':r[0],'civici_entro_1000m':r[1]}
json.dump(out,open('campioni/civici_attorno_ai_candidati.json','w'),indent=1)
PY
python3 manifest.py
