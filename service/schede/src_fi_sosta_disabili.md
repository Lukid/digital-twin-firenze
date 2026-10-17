# Stalli di sosta riservati ai disabili (Comune di Firenze)

- Identificativo: `src_fi_sosta_disabili`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/c27abf04-33c0-44ba-ad74-ef8272af90d2
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=7411&type=99&format=url&file_format=shp&file_id=21966
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/c27abf04-33c0-44ba-ad74-ef8272af90d2
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-10-05, frequenza AS_NEEDED: stato alla data di scarico
- Ultima modifica della scheda del catalogo: 2026-10-05 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_sosta_disabili_20261010` | 2026-10-10T18:03:43Z | non dichiarato (scheda aggiornata il 2026-10-05, frequenza AS_NEEDED: stato alla data di scarico) | 7564f814550a | no |

## Campi usati

`id`, `quartiere`, `strada`, `stallo`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- stalli di sosta riservati ai disabili in area allargata: superato. 359 oggetti
- limite: avviso. stalli come punti: non dice se lo stallo è libero né la distanza dall'ingresso accessibile

## Limiti

- limite: stalli come punti: non dice se lo stallo è libero né la distanza dall'ingresso accessibile

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
