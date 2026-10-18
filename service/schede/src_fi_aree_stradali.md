# Aree stradali (poligoni per tronco e incrocio), Comune di Firenze

- Identificativo: `src_fi_aree_stradali`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/a44ea551-7b09-4d0d-af64-7c08159e9316
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6379&type=99&format=url&file_format=shp&file_id=19953
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata solo per la distanza del lato della strada nell'ombra sui due lati, accanto all'asse; non nei calcoli di accessibilità e ombra sull'asse)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/a44ea551-7b09-4d0d-af64-7c08159e9316
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-18).

## Date

- Data del dato: 2025-05-26
- Nota sul periodo: file dello zip del 2025-05-26 (campo modified della scheda: 26-05-2025); frequenza dichiarata WEEKLY, scheda del catalogo aggiornata il 2026-02-11
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_aree_stradali_20261018` | 2026-10-18T16:00:11Z | non dichiarato (file del 2025-05-26) | 772f43cad021 | no |

## Campi usati

`ID`, `CODICESTRA`, `TOPONIMO`

Sistema di riferimento dichiarato: EPSG:3003 (shapefile con .prj in Monte Mario Italia zona 1; convertito in EPSG:7791 come le altre fonti del Comune)

## Controlli

- aree_stradali in area allargata: superato. 1341 oggetti
- larghezza: avviso. nessun campo di larghezza: la distanza del lato è ricavata dalla forma del poligono con una regola nostra (shadow/lati_strada.py), una stima

## Limiti

- Fuori dalla baseline congelata (D59): serve solo alla distanza del lato della strada dove il marciapiede non è mappato in OSM (shadow/lati_strada.py).
- Nessun campo di larghezza: la distanza è dal bordo del poligono lungo la normale, una stima nostra. Il bordo a volte comprende il marciapiede, a volte no: sui tratti con il marciapiede OSM sta in mediana circa 1,7 m più lontano.
- Incroci (poligoni senza toponimo) esclusi.
- larghezza: nessun campo di larghezza: la distanza del lato è ricavata dalla forma del poligono con una regola nostra (shadow/lati_strada.py), una stima

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
