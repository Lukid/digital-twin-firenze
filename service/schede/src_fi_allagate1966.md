# Aree allagate dall'alluvione del 1966 (Comune di Firenze)

- Identificativo: `src_fi_allagate1966`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/7b27687e-1538-4bb8-a803-952f07560070
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6482&type=99&format=url&file_format=shp&file_id=20198
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/7b27687e-1538-4bb8-a803-952f07560070
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: 1966-11-04
- Nota sul periodo: evento del 4 novembre 1966; file dello zip del 2013-01-18
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_allagate1966_20261010` | 2026-10-10T18:03:51Z | non dichiarato (evento del 4 novembre 1966; file dello zip del 2013-01-18) | 5dc396ea3c16 | no |

## Campi usati

`AREE_ALLAG`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791: il .prj è Monte Mario con meridiano di Roma (Gauss-Boaga fuso Ovest scritto rispetto a Roma), equivalente a EPSG:3003; pyogrio non lo riconosce e il CRS è impostato a mano)

## Controlli

- aree allagate dall'alluvione del 1966 in area allargata: superato. 3 oggetti
- limite: avviso. classi di profondità dell'acqua (0-2, 2-4, 4-5 m) ricavate dalle curve di isoprofondità: evento storico, non scenario attuale

## Limiti

- Evento storico, non previsione.
- limite: classi di profondità dell'acqua (0-2, 2-4, 4-5 m) ricavate dalle curve di isoprofondità: evento storico, non scenario attuale

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
