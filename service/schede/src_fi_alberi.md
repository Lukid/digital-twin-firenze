# Alberi pubblici, censimento del Comune di Firenze

- Identificativo: `src_fi_alberi`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/42cd1073-521f-4040-9491-e993d03663a4
- Risorsa scaricata: https://datigis.comune.fi.it/json/alberi_pubblici.json
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_fi_alberi_20261009`

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/42cd1073-521f-4040-9491-e993d03663a4
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: dataset dichiarato aggiornato ogni giorno (frequenza DAILY): stato alla data di scarico, senza data di rilievo per albero
- Ultima modifica della scheda del catalogo: 2026-10-10 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_alberi_20261009` | 2026-10-09T15:09:45Z | non dichiarato (dataset dichiarato aggiornato ogni giorno: stato alla data di scarico) | 53b3e903dbbe | sì |

## Campi usati

`ID`, `CODSITO_ALBERO`, `QUARTIERE`, `SPECIE`, `NOME_COMUNE`, `CIRCONF_CM`

Unità: `circonf_cm` cm

Sistema di riferimento dichiarato: EPSG:4326 (lon/lat trattati come RDN2008 geografico (ADR-T02); il campo CRS della scheda (ROMA40/OVEST) è inaffidabile)

## Controlli

- alberi in area allargata: superato. 8491 oggetti
- altezza e chioma: avviso. assenti nel censimento (altezza da CHM in F05)

## Limiti

- Solo alberi pubblici: chiome in parte stimate e imposta della chioma sempre stimata.
- altezza e chioma: assenti nel censimento (altezza da CHM in F05)

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
