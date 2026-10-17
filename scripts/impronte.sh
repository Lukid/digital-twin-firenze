#!/usr/bin/env bash
# D39: sha256 dei file generati con geometrie (versionati e asset in data/norm citati dai manifest), uno per riga, in ordine.
# Uso: bash scripts/impronte.sh > impronte.txt sul Mac e sul worker, dopo aver rigenerato i file con gli stessi comandi; poi diff fra i due elenchi.
# Rigenerazione (ognuno riscrive i file del suo motore): network/destinazioni_firenze.py, network/percorsi_firenze.py, analysis/run.py, shadow/run.py,
# geometry/build_firenze.py; per interventi.geojson vedi docs/REPORT-AGENTE-F3.md (compito 1). I manifest non sono nell'elenco: contengono l'ora del calcolo.
set -euo pipefail
cd "$(dirname "$0")/.."
{
  ls network/firenze_novoli/*.geojson analysis/firenze_novoli/*.geojson shadow/firenze_novoli/*.geojson geometry/firenze_novoli/*.geojson scenarios/firenze_novoli/*.geojson
  ls data/norm/firenze_novoli/analysis/*/*_archi_usati.geojson 2>/dev/null || true
} | LC_ALL=C sort | while read -r f; do
  if command -v sha256sum >/dev/null; then sha256sum "$f"; else shasum -a 256 "$f"; fi
done
