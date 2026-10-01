#!/usr/bin/env bash
# T04: ricostruisce rete, destinazioni, confronto, percorsi campione e lancia il test. Richiede pipeline/.venv (T03) e i dati in data/norm.
# Uso: network/build.sh        (circa 90 s: 66 s sono la lettura del file OSM da 384 MB)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
[ -x "$PY" ] || { echo "manca pipeline/.venv: lanciare pipeline/run.sh"; exit 1; }
$PY -c "import networkx" 2>/dev/null || $PY -m pip install -q networkx
mkdir -p data/norm/network
[ -f data/norm/network/osm_estratto.pkl ] && [ -z "${DT_REEXTRACT:-}" ] || $PY network/estrai_osm.py    # DT_REEXTRACT=1 per rifare l'estrazione
cd network
../$PY build_rete.py > /dev/null
../$PY destinazioni.py > /dev/null
../$PY confronto_iternet.py > /dev/null
../$PY percorsi.py > /dev/null
../$PY test_rete.py
