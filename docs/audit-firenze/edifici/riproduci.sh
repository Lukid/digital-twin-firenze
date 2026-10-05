#!/usr/bin/env bash
# Rigenera i campioni di docs/audit-firenze/edifici. Eseguire da qualunque cartella. Serve rete.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p campioni
PY=../../../pipeline/.venv/bin/python; RAW=../../../data/raw/fi_audit_20261001; mkdir -p $RAW
for n in dtm-lidar-2023 dsm-lidar-2023 dtm-2017 dsm-2017 dsm-2007 27e2c88c-620b-425e-b532-b15e176bc34e 6a0a42f0-3b1f-4498-8de1-a57b592cee59 fc7e03ee-9406-42ce-b176-0767b67ed299 life_escapos_mobile_measurements; do
  curl -s -m 60 "https://dati.toscana.it/api/3/action/package_show?id=$n" -o "campioni/ckan_pkg_$n.json"; done
$PY script/ckan_firenze_catalogo.py > /dev/null          # catalogo Comune di Firenze: titoli, licenze, risorse
[ -f $RAW/csEdi_s.zip ] || curl -sL -m 120 -o $RAW/csEdi_s.zip "https://data.comune.fi.it/datastore/download.php?id=6545&type=99&format=url&file_format=shp&file_id=20308"
mkdir -p $RAW/csEdi && unzip -oq $RAW/csEdi_s.zip -d $RAW/csEdi                     # cassone edilizio (Comune)
[ -f $RAW/sAlbero_p_shp.zip ] || curl -sL -m 120 -o $RAW/sAlbero_p_shp.zip "https://data.comune.fi.it/datastore/download.php?id=6489&type=99&format=url&file_format=shp&file_id=20212"
mkdir -p $RAW/sAlbero && unzip -oq $RAW/sAlbero_p_shp.zip -d $RAW/sAlbero          # siti alberi (usati dallo script del verde)
$PY script/fetch_rt_uv.py                                 # unità volumetriche Regione, FA e FB
$PY script/fetch_osm.py                                   # OSM (Overpass: può servire più di un tentativo)
$PY script/fetch_lidar.py                                 # DTM e DSM 2023, solo tessere dei riquadri (Range su zip remoto, Deflate64)
$PY script/fetch_lidar2017.py                             # DTM e DSM 2017, idem
cp $RAW/lidar/sha256.json campioni/lidar2023_sha256.json; cp $RAW/lidar/sha256_2017.json campioni/lidar2017_sha256.json
[ -f $RAW/acPed_s.zip ] || curl -sL -m 120 -o $RAW/acPed_s.zip "https://data.comune.fi.it/datastore/download.php?id=6527&type=99&format=url&file_format=shp&file_id=20272"
mkdir -p $RAW/acPed && unzip -oq $RAW/acPed_s.zip -d $RAW/acPed                    # aree di circolazione pedonale (portici inclusi)
$PY script/portici.py > /dev/null
$PY script/analizza_edifici.py > /dev/null                # conteggi, nDSM contro UV, sovrapposizioni
$PY script/make_manifest.py
