#!/bin/bash
# F01 destinazioni Firenze. Rigenera campioni/ e manifest.json. Richiede curl, unzip e pipeline/.venv (geopandas, shapely, pyproj).
# Il GTFS di Autolinee Toscane (circa 170 MB) e gli altri dati grandi vanno in data/raw/fi_audit_20261001/ (non versionato).
# fi_scuole2627.csv (MIM 2026/27) deve già esistere in quella cartella.
set -eu
cd "$(dirname "$0")"
ROOT=$(cd ../../.. && pwd); R=$ROOT/data/raw/fi_audit_20261001; PY=$ROOT/pipeline/.venv/bin/python
mkdir -p campioni "$R"
DB='https://data.comune.fi.it/datastore/download.php?id='
CM=https://dati.cittametropolitana.fi.it/geonetwork/srv/api/records/cmfi:a507767e-63e2-4856-9711-5e9a9ea96a76/attachments
# 1. scuole: Comune di Firenze (CKAN dati.toscana.it), Città Metropolitana (edifici e accessi)
for p in anagrafica-scuole-statali-2026_27 anagrafica-scuole-paritarie-2026_27 edifici-scolastici-citta-metropolitana-di-firenze; do
  curl -sS -m 60 "https://dati.toscana.it/api/3/action/package_show?id=$p" -o campioni/ckan_$p.json; done
curl -sS -m 90 -L -o $R/cf_statali.geojson "${DB}7857&type=99&format=url&file_format=geojson&file_id=23125"
curl -sS -m 90 -L -o $R/cf_paritarie.geojson "${DB}7856&type=99&format=url&file_format=geojson&file_id=23121"
for n in form_ed_scolastici_accessi form_ed_scolastici; do
  curl -sS -m 120 -L -o $R/cm_$n.zip $CM/$n.zip; rm -rf $R/cm_$n; mkdir $R/cm_$n; unzip -oq $R/cm_$n.zip -d $R/cm_$n; done
# 2. GTFS: tram GEST (T1.3 e T2) e bus Autolinee Toscane
curl -sS -m 60 "https://dati.toscana.it/api/3/action/package_show?id=rt-oraritb" -o campioni/ckan_rt-oraritb.json
curl -sS -m 200 -L -o $R/gest.zip https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/1f62d551-65f4-49f8-9a99-e19b02077be3/download/gest.gtfs
rm -rf $R/gest; mkdir $R/gest; unzip -oq $R/gest.zip -d $R/gest
curl -sS -m 900 -L -o $R/gtfs_at.zip https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs
rm -rf $R/gtfs_at; mkdir $R/gtfs_at; unzip -oq $R/gtfs_at.zip -d $R/gtfs_at
# 3. OSM (Overpass, con ritentativi)
./osm_firenze.sh
# 4. analisi e manifest
$PY analizza_fi.py > /dev/null
$PY manifest.py
