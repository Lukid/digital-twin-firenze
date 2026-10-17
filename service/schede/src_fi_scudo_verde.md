# Varchi dello Scudo Verde (Comune di Firenze)

- Identificativo: `src_fi_scudo_verde`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/varchi-scudo-verde
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=7826&type=99&format=url&file_format=shp&file_id=22904
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/varchi-scudo-verde
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: 2025-04-01
- Nota sul periodo: ZTL ambientale attiva dal 2025-04-01 (data_ini per varco); scheda del catalogo aggiornata il 2026-02-11
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_scudo_verde_20261010` | 2026-10-10T18:03:53Z | non dichiarato (scheda aggiornata il 2026-02-11; ZTL ambientale attiva dal 2025-04-01) | 2b553d015e65 | no |

## Campi usati

`id`, `num_varco`, `nome_varco`, `ubicazione`, `atto_ini`, `tipo_varco`, `tipol_cost`, `data_ini`, `data_fine`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- varchi dello scudo verde in area allargata: superato. 11 oggetti

## Limiti

- Nessun limite specifico registrato oltre ai limiti generali del progetto.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
