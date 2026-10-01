#!/usr/bin/env bash
# T05: rigenera geometrie Z2 (volumi, alberi) e verifica. Richiede data/norm (pipeline/run.sh) e data/work (DBT10K estratto da pipeline/inspect_big.py).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
$PY -c "import scipy" 2>/dev/null || pipeline/.venv/bin/pip install -q scipy
$PY geometry/build_geometrie.py
$PY geometry/test_geometrie.py
