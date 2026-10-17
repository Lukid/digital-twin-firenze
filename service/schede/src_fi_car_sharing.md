# Posti auto riservati al car sharing (Comune di Firenze)

- Identificativo: `src_fi_car_sharing`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/66de7a99-a435-45d7-8ad0-6a1caf88c943
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6563&type=99&format=url&file_format=shp&file_id=20352
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/66de7a99-a435-45d7-8ad0-6a1caf88c943
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-02-11, data di rilievo non dichiarata
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_car_sharing_20261010` | 2026-10-10T18:03:49Z | non dichiarato (scheda aggiornata il 2026-02-11, data di rilievo non dichiarata) | 65789283a73d | no |

## Campi usati

`id`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- posti auto riservati al car sharing in area allargata: superato. 9 oggetti
- limite: avviso. solo la posizione, nessun attributo

## Limiti

- limite: solo la posizione, nessun attributo

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
