# Anagrafe scuole statali 2026/27 (MIM, ripubblicata dal Comune di Firenze)

- Identificativo: `src_fi_scuole_statali`
- Editore: Comune di Firenze (dati MIM)
- Scheda del catalogo: https://dati.toscana.it/dataset/anagrafica-scuole-statali-2026_27
- Risorsa scaricata: https://datigis.comune.fi.it/json/miur_scuole_statali_2026_27.json
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_fi_scuole_statali_20261009`

## Licenza

- Licenza: IODL-2.0
- Verifica: verificata con riserva
- Uso consentito: solo prototipo interno: verificare prima di ridistribuire
- Evidenza: https://dati.toscana.it/dataset/anagrafica-scuole-statali-2026_27
- Nota: Scheda e risorse del catalogo regionale: IODL 2.0 (package_show del 2026-10-09).
- Riserva: IODL 2.0 non è CC BY: richiede attribuzione; l'equivalenza con CC BY e la compatibilità con gli altri layer non sono state valutate giuridicamente. La fonte primaria MIM non ha licenza verificata.

## Date

- Data del dato: 2026-09-18
- Nota sul periodo: anagrafe anno scolastico 2026/27, dato dichiarato del 2026-09-18
- Ultima modifica della scheda del catalogo: 2026-09-19 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_scuole_statali_20261009` | 2026-10-09T15:12:34Z | non dichiarato (anagrafe 2026/27, dato dichiarato del 2026-09-18) | 5a9ab7914290 | sì |

## Campi usati

`codicescuo`, `nome`, `indirizzo`, `tipologia`

Sistema di riferimento dichiarato: EPSG:4326 (lon/lat trattati come RDN2008 geografico; due coordinate MIM sbagliate nel contesto (audit destinazioni))

## Controlli

- scuole in area allargata: superato. 37 punti
- coordinate: avviso. FIMM700011 cade sul punto di Vamba (errore di geocodifica noto)

## Limiti

- coordinate: FIMM700011 cade sul punto di Vamba (errore di geocodifica noto)
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
