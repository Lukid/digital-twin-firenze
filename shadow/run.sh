#!/usr/bin/env bash
# T09: test, verifica raster e analisi d'ombra (pochi minuti). Richiede pipeline/.venv, geometry/build.sh e network/build.sh già eseguiti.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
mkdir -p shadow/out shadow/manifest data/norm/shadow
$PY shadow/test_ombre.py
$PY shadow/verifica_raster.py
$PY shadow/run.py
