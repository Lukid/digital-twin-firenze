# Civici del Comune di Firenze

- Identificativo: `src_fi_civici`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/11430710-56eb-4444-bd6f-c5433155afc5
- Risorsa scaricata: https://datigis.comune.fi.it/shp/civici.zip
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_fi_civici_20261009`

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/11430710-56eb-4444-bd6f-c5433155afc5
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: dataset dichiarato aggiornato al bisogno (AS_NEEDED), ultima modifica 2026-10-05; stato alla data di scarico
- Ultima modifica della scheda del catalogo: 2026-10-05 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_civici_20261009` | 2026-10-09T15:09:46Z | non dichiarato (dataset aggiornato al bisogno (ultima modifica dichiarata 2026-10-05): stato alla data di scarico) | 3c501a28c48a | sì |

## Campi usati

`PK_ID`, `ID`, `CODICESTRA`, `CODICECIVI`, `STRADA`, `NUMEROCIVI`, `TIPO`

Sistema di riferimento dichiarato: EPSG:3003 (shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791 come a Pisa (nessuno shift di datum), scarto non misurato su Firenze)

## Controlli

- civici in area allargata: superato. 13987 oggetti
- civici come punti d'indirizzo: superato. origins address_points (ADR-F02), non persone

## Limiti

- Civici come punti d'indirizzo, non persone: le quote di accessibilità sono quote di civici.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
