# Aree riservate alla sosta del bike sharing (Comune di Firenze)

- Identificativo: `src_fi_bike_sharing`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/be9ee992-0126-4b8d-afd7-16da15bfda71
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6558&type=99&format=url&file_format=shp&file_id=20337
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/be9ee992-0126-4b8d-afd7-16da15bfda71
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-09-19: stato alla data di scarico
- Ultima modifica della scheda del catalogo: 2026-09-19 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_bike_sharing_20261010` | 2026-10-10T18:03:48Z | non dichiarato (scheda aggiornata il 2026-09-19: stato alla data di scarico) | 7cf32cc6b0b0 | no |

## Campi usati

`id`, `nome`, `indirizzo`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- aree riservate alla sosta del bike sharing in area allargata: superato. 30 oggetti
- limite: avviso. aree di sosta, non disponibilità dei mezzi

## Limiti

- limite: aree di sosta, non disponibilità dei mezzi

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
