#!/usr/bin/env bash
# F03: acquisizione, normalizzazione, record di fonte, T17, baseline e validazione per aoi_firenze_novoli (circa 10 min con i download).
# Uso: pipeline/run_firenze.sh [fonte ...]   (fonti: alberi civici barriere aree_pedonali rifugi_aree rifugi_bibl aree_attesa aree_assistenza uv dtm dsm osm gtfs_tram gtfs_bus tram_fermate scuole cm_edscol catasto landsat_st sir_termo arpat)
# Variabili: DT_DAY=AAAAMMGG (giorno degli snapshot, default oggi UTC), OSM_URL (estratto OSM con la data nel nome).
# Con file già in data/raw i download vengono saltati. La baseline già congelata non si rifa (fonti_firenze.py baseline --force).
set -euo pipefail
cd "$(dirname "$0")/.."
export DT_DAY="${DT_DAY:-$(date -u +%Y%m%d)}"
PY=pipeline/.venv/bin/python
$PY pipeline/fonti_firenze.py acquire "$@"
$PY pipeline/norm_firenze.py
$PY pipeline/fonti_firenze.py sources
$PY pipeline/fonti_firenze.py baseline
$PY pipeline/validate_records.py | tail -1
$PY contracts/validate.py | tail -2
