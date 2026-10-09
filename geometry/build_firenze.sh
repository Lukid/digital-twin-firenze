#!/usr/bin/env bash
# F05: rigenera le geometrie di Firenze Novoli (edifici, alberi, chiome) e verifica. Richiede data/norm/firenze_novoli (pipeline/run_firenze.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
export DT_AOI=aoi_firenze_novoli
PY=pipeline/.venv/bin/python
$PY geometry/build_firenze.py > /dev/null
$PY geometry/test_geometrie_firenze.py
