#!/usr/bin/env bash
# F06: esegue le analisi (secondi) e i test sull'area DT_AOI (default aoi_firenze_novoli). Richiede pipeline/.venv e l'output di network/build_firenze.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
$PY analysis/run.py
$PY analysis/test_accessibilita.py
