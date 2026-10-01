#!/usr/bin/env bash
# Comando unico T03: acquisizione, normalizzazione, controlli, record di fonte, validazione, report.
# Uso: pipeline/run.sh [fonte ...]   (fonti: gtfs_at gtfs_tren osm uv dsm dtm10 civici scuole edscol dbt10k iternet)
# Variabili: DT_DAY=AAAAMMGG (giorno dello snapshot, default oggi UTC), OSM_URL (estratto OSM).
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x pipeline/.venv/bin/python ]; then
  python3 -m venv pipeline/.venv
  pipeline/.venv/bin/pip -q install pyogrio geopandas shapely pyproj rasterio numpy pandas osmium py7zr requests jsonschema referencing
fi
PY=pipeline/.venv/bin/python
$PY pipeline/acquire.py "$@"
$PY pipeline/normalize.py osm uv civici scuole edscol gtfs_at gtfs_tren dsm dtm10
$PY pipeline/inspect_big.py || echo "ispezione DBT10K/Iter.net non riuscita (non bloccante)"
$PY pipeline/checks.py > /dev/null
$PY pipeline/sources.py
$PY pipeline/validate_records.py
$PY contracts/validate.py | tail -3
$PY pipeline/report.py
