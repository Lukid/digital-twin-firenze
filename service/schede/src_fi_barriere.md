# Censimento delle barriere architettoniche e urbanistiche, Comune di Firenze

- Identificativo: `src_fi_barriere`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/92033b63-0598-4449-9007-22127abe505a
- Risorsa scaricata: https://datigis.comune.fi.it/shp/mappa_accessibilita.zip
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_fi_barriere_20261009`

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/92033b63-0598-4449-9007-22127abe505a
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: dal 2013-01-01 al 2013-12-31
- Nota sul periodo: archivio dichiarato aggiornato al 2013; file dello zip del 2016-09-13; frequenza NOT_PLANNED
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_barriere_20261009` | 2026-10-09T15:09:47Z | non dichiarato (archivio dichiarato aggiornato al 2013) | 0f687cebb744 | sì |

## Campi usati

`pk_id`, `quartiere`, `utoe`, `scheda`, `destinaz_u`, `indirizzo`, `grado_acce`, `url`

Sistema di riferimento dichiarato: EPSG:3003 (shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791 come a Pisa)

## Controlli

- barriere in area allargata: superato. 222 oggetti
- natura del dato: avviso. schede di accessibilità di edifici (rilievo 2013), non ostacoli sul percorso

## Limiti

- natura del dato: schede di accessibilità di edifici (rilievo 2013), non ostacoli sul percorso

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
