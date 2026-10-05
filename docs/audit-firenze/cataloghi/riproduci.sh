#!/usr/bin/env bash
# Rigenera dump, verifiche, inventario e manifest. Eseguire da qualunque cartella. Circa 5 minuti (feed GTFS autolinee 176 MB).
# GTFS_DIR: dove tenere il feed autolinee (default: cartella temporanea di sistema; se il file c'è già non lo riscarica).
set -eu
cd "$(dirname "$0")"
PY="${PY:-../../../pipeline/.venv/bin/python}"
mkdir -p campioni
"$PY" ricerche_ckan_fi.py
"$PY" verifica_url.py
"$PY" controlli_contenuto.py
"$PY" inventario.py
"$PY" genera_manifest.py
