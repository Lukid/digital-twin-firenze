#!/usr/bin/env bash
# F04: ricostruisce rete, destinazioni, percorsi campione e scarto 3003 -> 7791 di Firenze Novoli e lancia il test. Richiede pipeline/.venv e i dati di F03 in data/norm/firenze_novoli.
# Uso: network/build_firenze.sh        (circa 90 s: 70 s sono la lettura del file OSM da 384 MB; DT_REEXTRACT=1 per rifare l'estrazione)
set -euo pipefail
cd "$(dirname "$0")/.."
export DT_AOI=aoi_firenze_novoli
PY=pipeline/.venv/bin/python
mkdir -p data/norm/firenze_novoli/network network/firenze_novoli
[ -f data/norm/firenze_novoli/network/osm_estratto.pkl ] && [ -z "${DT_REEXTRACT:-}" ] || $PY network/estrai_osm.py
cd network
../$PY build_rete.py > /dev/null
../$PY destinazioni_firenze.py > /dev/null
../$PY percorsi_firenze.py > /dev/null
../$PY scarto_crs_firenze.py > /dev/null
../$PY test_rete_firenze.py
