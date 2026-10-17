# DSM LiDAR 2023 del Comune di Firenze (ASCII grid 0,5 m)

- Identificativo: `src_fi_dsm2023`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/dsm-lidar-2023
- Risorsa scaricata: https://datigis.comune.fi.it/grid/MDS_LIDAR_2023_ASCII.zip
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_fi_dsm2023_20261009`

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/dsm-lidar-2023
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09).

## Date

- Data del dato: 2023-06-27
- Nota sul periodo: volo 2023-06-27 (giugno: foglie presenti)
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_dsm2023_20261009` | 2026-10-09T15:13:51Z | 2023-06-27 | 1c6c250f2b91 | sì |

## Campi usati

Non elencati nel record di fonte (raster, rete o file con più tabelle).

Unità: `quota` m

Sistema di riferimento dichiarato: undeclared (come il DTM 2023: EPSG:7791 assunto dal prefisso 32_; datum verticale non dichiarato)

## Controlli

- raster ritagliato su area allargata: superato. vedi report_firenze.json
- foglie presenti: avviso. volo di giugno: l'ombra invernale va trattata a parte

## Limiti

- Datum verticale non confermato.
- Vegetazione LiDAR trattata come prisma opaco pieno: limite superiore dell'ombra.
- foglie presenti: volo di giugno: l'ombra invernale va trattata a parte

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
