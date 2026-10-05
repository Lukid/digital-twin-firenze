#!/usr/bin/env bash
# Rigenera i campioni di docs/audit-firenze/verde. Richiede prima edifici/riproduci.sh (DSM, DTM e UV). Serve rete.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p campioni
PY=../../../pipeline/.venv/bin/python; RAW=../../../data/raw/fi_audit_20261001; mkdir -p $RAW
[ -f $RAW/alberi.geojson ] || curl -sL -m 300 -o $RAW/alberi.geojson "https://data.comune.fi.it/datastore/download.php?id=6370&type=99&format=url&file_format=geojson&file_id=23066"
[ -f $RAW/escapos.geojson ] || curl -sL -m 120 -o $RAW/escapos.geojson "https://data.comune.fi.it/datastore/download.php?id=7840&type=99&format=url&file_format=geojson&file_id=22977"
[ -f $RAW/sAlbero_p_shp.zip ] || curl -sL -m 120 -o $RAW/sAlbero_p_shp.zip "https://data.comune.fi.it/datastore/download.php?id=6489&type=99&format=url&file_format=shp&file_id=20212"
mkdir -p $RAW/sAlbero && unzip -oq $RAW/sAlbero_p_shp.zip -d $RAW/sAlbero
for n in 42cd1073-521f-4040-9491-e993d03663a4 fc7e03ee-9406-42ce-b176-0767b67ed299 life_escapos_mobile_measurements; do
  curl -s -m 60 "https://dati.toscana.it/api/3/action/package_show?id=$n" -o "campioni/ckan_pkg_$n.json"; done
$PY script/analisi_verde.py > /dev/null     # conteggi per riquadro, attributi, abbinamenti censimento / siti / Escapos
$PY script/chm_escapos.py > /dev/null       # CHM da DSM-DTM 2023 contro altezza Escapos, Z dei siti contro DTM
$PY script/make_manifest.py
