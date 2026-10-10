#!/usr/bin/env bash
# F08: baseline congelata, scenari dimostrativi su Firenze Novoli, confronto e test (circa 10-15 minuti la prima volta con i job in parallelo, pochi secondi con la cache).
# Richiede pipeline/.venv, geometry/build_firenze.sh, network/build_firenze.sh, analysis/run.sh e shadow/run.sh (vegetazione LiDAR) già eseguiti.
# L'area viene da DT_AOI (default aoi_firenze_novoli). Test del servizio (strumenti MCP): service/.venv/bin/python service/test_service.py
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
mkdir -p data/norm/firenze_novoli/scenarios/jobs
$PY scenarios/costruisci.py        # baseline.json (se manca), scenari S0, S1 (+ varianti), S2 e interventi.geojson in scenarios/firenze_novoli/
$PY scenarios/confronto.py         # ombre di baseline e scenari (job in parallelo), confronto in scenarios/firenze_novoli/confronto.json
$PY scenarios/test_scenari.py
