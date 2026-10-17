# Piano comunale di classificazione acustica, classi acustiche (Comune di Firenze)

- Identificativo: `src_fi_pcca`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/0dbc7df5-7172-4c1c-99e1-1acb017b5ad3
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6792&type=99&format=url&file_format=shp&file_id=20688
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/0dbc7df5-7172-4c1c-99e1-1acb017b5ad3
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-02-11, data di approvazione del piano non nel pacchetto
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_pcca_20261010` | 2026-10-10T18:03:54Z | non dichiarato (scheda aggiornata il 2026-02-11, data di approvazione del piano non nel pacchetto) | b60d84efdf0a | no |

## Campi usati

`PKID`, `CLASSE_ACU`, `DESC_CLASS`, `DESC_LUOGO`, `FASCIA`

Sistema di riferimento dichiarato: EPSG:4326 (CRS letto dal .prj dello shapefile (EPSG:4326) e convertito in EPSG:7791 (lon/lat trattati come RDN2008 geografico, ADR-T02))

## Controlli

- piano comunale di classificazione acustica, classi acustiche in area allargata: superato. 29 oggetti
- limite: avviso. classi di pianificazione con i limiti di legge in dBA, non rumore misurato

## Limiti

- Classi acustiche = limiti di legge, non rumore misurato.
- limite: classi di pianificazione con i limiti di legge in dBA, non rumore misurato

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
