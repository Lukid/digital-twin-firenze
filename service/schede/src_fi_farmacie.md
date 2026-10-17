# Farmacie autorizzate (Comune di Firenze)

- Identificativo: `src_fi_farmacie`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/87aaabce-41a5-43d1-b9fe-1282fd882e69
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6413&type=99&format=url&file_format=shp&file_id=20036
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/87aaabce-41a5-43d1-b9fe-1282fd882e69
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-02-11, data di rilievo non dichiarata
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_farmacie_20261010` | 2026-10-10T18:03:47Z | non dichiarato (scheda aggiornata il 2026-02-11, data di rilievo non dichiarata) | 362409973414 | no |

## Campi usati

`ID`, `DENOMINAZI`, `VIA`, `NCIVICO`, `ESPONENTEC`, `TIPOCIV`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- farmacie autorizzate in area allargata: superato. 10 oggetti
- limite: avviso. orari e turni non inclusi (sono un altro dataset, giornaliero)

## Limiti

- limite: orari e turni non inclusi (sono un altro dataset, giornaliero)

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
