#!/bin/bash
# Rigenera campioni e metriche F01 (rete pedonale e barriere) per FA e FB. Overpass può dare 429/504: lo script riprova.
# Richiede i dati grezzi in data/raw/fi_audit_20261001/ (barriere.zip, rifugi.geojson). Eseguire da qualunque cartella.
set -e
cd "$(dirname "$0")"
PY=../../../pipeline/.venv/bin/python
$PY scarica_osm.py           # campioni/osm_FA.json, osm_FB.json
$PY scarica_altri.py         # metadati CKAN e 7 KMZ Walking City in data/raw/.../walking/
$PY analizza_osm.py > /dev/null   # campioni/metriche_osm.json
$PY analizza_dati.py > /dev/null  # campioni/metriche_dati.json
$PY manifest.py              # manifest.json (sha256)
