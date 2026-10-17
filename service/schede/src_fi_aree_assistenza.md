# Protezione civile, aree di assistenza della popolazione (Comune di Firenze)

- Identificativo: `src_fi_aree_assistenza`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/f3b1e6bb-6dc3-4de9-90bb-cedc1734b61b
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6505&type=99&format=url&file_format=shp&file_id=20230
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/f3b1e6bb-6dc3-4de9-90bb-cedc1734b61b
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: 2024-06-25
- Nota sul periodo: file dello zip del 2024-06-25; sopralluoghi 2021 (campo data_rilev); scheda del catalogo aggiornata il 2026-02-11 (non è la data del dato)
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_aree_assistenza_20261010` | 2026-10-10T17:00:27Z | non dichiarato (scheda aggiornata il 2026-02-11, file del 2024-06-25) | b7e5bb817cff | no |

## Campi usati

`cod_area`, `denominazi`, `data_rilev`, `indirizzo`, `sup_mq`, `posti_lett`, `associazio`

Sistema di riferimento dichiarato: EPSG:3003 (scheda: ROMA40/OVEST; CRS letto dal .prj dello shapefile e convertito in EPSG:7791)

## Controlli

- aree di assistenza in area allargata: superato. 3 oggetti (zero è un esito ammesso: sono poche per tutta la città)

## Limiti

- Nessun limite specifico registrato oltre ai limiti generali del progetto.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
