#!/usr/bin/env bash
# F07: poligoni della vegetazione LiDAR, analisi d'ombra su Firenze Novoli (circa 10 minuti) e test. Richiede pipeline/.venv e geometry/build_firenze.sh già eseguito.
# L'area viene da DT_AOI (default aoi_firenze_novoli). La verifica raster di Pisa (verifica_raster.py) è nel tag pilota-pisa-z2.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
mkdir -p shadow/firenze_novoli/manifest data/norm/firenze_novoli/shadow
$PY shadow/veg_lidar.py
$PY shadow/run.py
$PY shadow/test_ombre.py
