# Viabilità, aree di circolazione pedonale (poligoni), Comune di Firenze

- Identificativo: `src_fi_aree_pedonali`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/25703515-6bea-4148-8651-8c494a27bbf5
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6527&type=99&format=url&file_format=shp&file_id=20272
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/25703515-6bea-4148-8651-8c494a27bbf5
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-02-11; data di rilievo non dichiarata: stato alla data di scarico
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_aree_pedonali_20261010` | 2026-10-10T10:09:39Z | non dichiarato (scheda aggiornata il 2026-02-11) | 867ff3c0d7e0 | no |

## Campi usati

`acPedId`, `acPedPos`, `acPedZon`, `acPedFon`, `acPedLiv`, `acPedSed`

Unità: `SHAPE_Area` m2, `SHAPE_Leng` m

Sistema di riferimento dichiarato: EPSG:32632 (shapefile PolygonZ con .prj in WGS84 UTM 32N; convertito in EPSG:7791 e ridotto a 2D. Allineamento con i marciapiedi OSM controllato a vista su Via di Novoli (scarto sotto 1 m), non misurato)

## Controlli

- aree_pedonali in area allargata: superato. 1790 oggetti
- significato dei codici: avviso. codici acPedPos, acPedZon, acPedFon, acPedSed senza legenda nel pacchetto: usati solo come geometria (dove si cammina)

## Limiti

- significato dei codici: codici acPedPos, acPedZon, acPedFon, acPedSed senza legenda nel pacchetto: usati solo come geometria (dove si cammina)

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
