# Edifici scolastici della Città metropolitana di Firenze (poligoni e accessi)

- Identificativo: `src_cm_edscol_firenze`
- Editore: Città metropolitana di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/edifici-scolastici-citta-metropolitana-di-firenze
- Risorsa scaricata: https://dati.cittametropolitana.fi.it/geonetwork/srv/api/records/cmfi:a507767e-63e2-4856-9711-5e9a9ea96a76/attachments/form_ed_scolastici.zip
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_cm_edscol_firenze_20261009`

## Licenza

- Licenza: cc-by
- Verifica: verificata con riserva
- Uso consentito: solo prototipo interno: verificare prima di ridistribuire
- Evidenza: https://dati.toscana.it/dataset/edifici-scolastici-citta-metropolitana-di-firenze
- Nota: Campo license_id della scheda: 'cc-by'.
- Riserva: Le risorse non portano licenza e la versione CC non è indicata: vale solo il campo della scheda.

## Date

- Data del dato: 2014-02-13
- Nota sul periodo: dato dichiarato del 2014-02-13, scheda aggiornata il 2026-04-24, frequenza IRREG
- Ultima modifica della scheda del catalogo: 2026-04-24 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_cm_edscol_firenze_20261009` | 2026-10-09T15:12:35Z | non dichiarato (dato dichiarato del 2014-02-13, scheda del 2026-04-24) | 791cc1192fa5 | sì |

## Campi usati

`COD_MECCAN`, `GRADO`, `DENOM`, `CODICE`, `TIPOLOGIA`, `DENOMINAZI`

Sistema di riferimento dichiarato: EPSG:3003 (shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791)

## Controlli

- edifici in area allargata: superato. 229 poligoni
- accessi in area allargata: superato. 36 punti
- gradi coperti: superato. tutti i gradi, dai nidi alle superiori (chiude il dubbio di F01 sulle sole secondarie)

## Limiti

- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
