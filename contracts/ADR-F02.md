# ADR-F02: contratti a più aree

Stato: consegnato il 9 ottobre 2026. Estende ADR-T02 al pilota di Firenze (D12, riquadro D13). Controllo: `contracts/.venv/bin/python contracts/validate.py` (45 validi passano, 23 non validi respinti); `service/test_service.py` e `nl/test_nl.py` ripassano senza modifiche.

## Decisioni

1. **Registro delle aree** in `contracts/aree.json` (schema `aoi.schema.json`): `aoi_z2` (Pisa, D03, margine 500 m, baseline `bas_z2_20261001`) e `aoi_firenze_novoli` (riquadro FP, D13, margine 700 m, nessuna baseline ancora). Il riquadro resta in lon/lat, come nelle fonti di decisione: `validate.py` controlla che coincida con `docs/audit/ZONE.json` e `docs/audit-firenze/RIQUADRO.json`. La versione in EPSG:7791 si deriva in acquisizione, non si duplica qui.
2. **Schema della baseline** (`baseline.schema.json`): nucleo obbligatorio comune a ogni area (`baseline_id`, `version`, `frozen_at`, `aoi_id`, `snapshot`); le parti dei motori restano libere. `scenarios/baseline.json` di Pisa ora è validato, e la sua area e il suo id devono comparire nel registro.
3. **`dataset_ref`** in `common.schema.json`: stesso riferimento a snapshot per manifest e baseline.
4. **Origini generiche**: `{kind: address_points, aoi_id}`. La forma `civici_sit_z2` non si tocca: il `job_id` è l'hash dell'input, rinominarla invaliderebbe la cache del servizio, i manifest di T12 e la scena.
5. CRS, unità, classi, stati e tempo non cambiano: Firenze sta nello stesso fuso UTM 32N (E circa 680.000), dentro i limiti degli schemi.
6. `aoi_id` resta facoltativo nei manifest: il legame obbligatorio passa per la baseline. Tutti i manifest esistenti lo riportano già.

## Rinviato

- Baseline di Firenze: nasce in F03 con gli snapshot veri. Gli esempi MCP su Firenze usano `baseline_id` e `destination_id` illustrativi, non codici ufficiali.
- `service/core.py` ha area e baseline di Pisa scritte nel codice: si legge il registro in F07.
- `pipeline/lib.py` legge il riquadro da `ZONE.json`: passato al registro in F03 (variabile `DT_AOI`).
- Campione geografico di Firenze in EPSG:7791 con `cls`: in F03 (gli estratti F01 sono in CRS84 e senza classi).
