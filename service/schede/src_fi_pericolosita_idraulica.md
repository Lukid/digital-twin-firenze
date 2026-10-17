# Pericolosità idraulica del Piano di gestione del rischio alluvioni, a cura della protezione civile (Comune di Firenze)

- Identificativo: `src_fi_pericolosita_idraulica`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/3511ed47-4797-450b-a583-3163774f246b
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=7470&type=99&format=url&file_format=shp&file_id=22071
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/3511ed47-4797-450b-a583-3163774f246b
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-02-11, data della mappa non dichiarata
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_pericolosita_idraulica_20261010` | 2026-10-10T18:03:50Z | non dichiarato (scheda aggiornata il 2026-02-11, data della mappa non dichiarata) | bf2c46e91098 | no |

## Campi usati

`id`, `decreto`, `nome`, `data`, `pericolo`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- pericolosità idraulica del piano di gestione del rischio alluvioni, a cura della protezione civile in area allargata: superato. 58 oggetti
- limite: avviso. classi nel campo pericolo come codici della fonte (PS_PERALL_1, _2, _3) senza legenda nel pacchetto; mappa di pianificazione, non previsione di un evento

## Limiti

- Mappa di pianificazione, non previsione; classi senza legenda nel pacchetto.
- limite: classi nel campo pericolo come codici della fonte (PS_PERALL_1, _2, _3) senza legenda nel pacchetto; mappa di pianificazione, non previsione di un evento

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
