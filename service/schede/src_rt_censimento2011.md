# XV Censimento della popolazione e delle abitazioni 2011, dati per sezione di censimento (Toscana)

- Identificativo: `src_rt_censimento2011`
- Editore: Regione Toscana (dati Istat)
- Scheda del catalogo: https://dati.toscana.it/dataset/xv-censpop-2011-datisez
- Risorsa scaricata: https://dati.toscana.it/dataset/46c34b90-92dd-4bd8-ab19-398da5dc933c/resource/1a338a93-65be-45a2-86a0-e13578ce953c/download/r09indicatori2011sezioni.csv
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY
- Verifica: verificata con riserva
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/xv-censpop-2011-datisez
- Nota: Scheda del catalogo regionale: licenza cc-by (package_show del 2026-10-10).
- Riserva: La scheda non indica la versione della licenza CC BY: attribuzione a Regione Toscana e Istat in ogni caso.

## Date

- Data del dato: 2011-10-09
- Nota sul periodo: data di riferimento del censimento 2011; scheda aggiornata il 2023-09-05
- Ultima modifica della scheda del catalogo: 2023-09-05 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_rt_censimento2011_20261010` | 2026-10-10T18:03:58Z | non dichiarato (censimento 2011) | 4893b902480f | no |

## Campi usati

`PROCOM`, `SEZ2011`, `P1`

Unità: `P1` persone

Sistema di riferimento dichiarato: undeclared (tabella senza geometria: agganciata ai poligoni di src_fi_sezioni2011 con SEZ2011 = 48017 x 10^7 + CODSEZ2011)

## Controlli

- aggancio alle sezioni: superato. solo P1 (residenti); aggancio sull'intero comune: 2.067 sezioni su 2.185 (le altre senza riga nel CSV)
- anno: avviso. censimento 2011: Novoli è cambiato da allora (nuove residenze e studentati)

## Limiti

- Dato di quindici anni fa; densità sulla superficie lorda della sezione.
- anno: censimento 2011: Novoli è cambiato da allora (nuove residenze e studentati)
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
