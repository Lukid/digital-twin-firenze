# DTM LiDAR 2023 del Comune di Firenze (ASCII grid 0,5 m)

- Identificativo: `src_fi_dtm2023`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/dtm-lidar-2023
- Risorsa scaricata: https://datigis.comune.fi.it/grid/MDT_LIDAR_2023_ASCII.zip
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_fi_dtm2023_20261009`

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/dtm-lidar-2023
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: 2023-06-27
- Nota sul periodo: volo 2023-06-27
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_dtm2023_20261009` | 2026-10-09T15:13:29Z | 2023-06-27 | 3c8fdac2c02a | sì |

## Campi usati

Non elencati nel record di fonte (raster, rete o file con più tabelle).

Unità: `quota` m

Sistema di riferimento dichiarato: undeclared (i file ASCII 2023 non portano un CRS: EPSG:7791 assunto dal prefisso 32_ e confermato dalle quote (UV -0,14 m, siti alberi -0,07 m; audit edifici e verde); datum verticale non dichiarato)

## Controlli

- raster ritagliato su area allargata: superato. vedi report_firenze.json
- datum verticale: avviso. non dichiarato

## Limiti

- Datum verticale non confermato.
- datum verticale: non dichiarato

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
