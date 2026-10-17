# Zone 30 (Comune di Firenze)

- Identificativo: `src_fi_zone30`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/88b6ca0a-61f7-42eb-9965-a9cd38df7f65
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=7483&type=99&format=url&file_format=shp&file_id=22111
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/88b6ca0a-61f7-42eb-9965-a9cd38df7f65
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-02-11, campi data_inizi e data_fine per oggetto
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_zone30_20261010` | 2026-10-10T18:03:52Z | non dichiarato (scheda aggiornata il 2026-02-11, campi data_inizi e data_fine per oggetto) | ac61bab929d3 | no |

## Campi usati

`id`, `tipologia`, `toponimo`, `data_inizi`, `data_fine`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- zone 30 in area allargata: superato. 416 oggetti
- limite: avviso. non sono perimetri di zona: sono le porzioni di strada (area veicolare o pedonale, campo tipologia) dove vale il limite di 30 km/h

## Limiti

- limite: non sono perimetri di zona: sono le porzioni di strada (area veicolare o pedonale, campo tipologia) dove vale il limite di 30 km/h

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
