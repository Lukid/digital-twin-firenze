#!/usr/bin/env bash
# T06: esegue le analisi (secondi) e i test. Richiede pipeline/.venv e l'output di network/build.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
mkdir -p analysis/out analysis/manifest data/norm/analysis
$PY analysis/run.py
$PY analysis/test_accessibilita.py
