#!/usr/bin/env bash
# T10: baseline congelata, scenari dimostrativi, confronto e test (circa 8 minuti la prima volta, pochi secondi con la cache dei job).
# Richiede pipeline/.venv, geometry/build.sh, network/build.sh e shadow/run.sh già eseguiti (geometrie, grafo, asset di T06).
# Test del servizio (strumenti MCP): service/.venv/bin/python service/test_service.py
set -euo pipefail
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
mkdir -p scenarios/out data/norm/scenarios/jobs
$PY scenarios/costruisci.py        # baseline.json (se manca) e scenari S0, S1 (+ varianti), S2 in scenarios/
$PY scenarios/confronto.py         # ombre di baseline e scenari, confronto multicriterio, asset in scenarios/out
$PY scenarios/test_scenari.py
contracts/.venv/bin/python contracts/validate.py | tail -2
