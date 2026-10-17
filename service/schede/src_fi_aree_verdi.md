# Aree verdi (Comune di Firenze)

- Identificativo: `src_fi_aree_verdi`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/d0ffa579-e002-4dc3-94b4-d69207cae114
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6855&type=99&format=url&file_format=shp&file_id=21081
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/d0ffa579-e002-4dc3-94b4-d69207cae114
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: scheda aggiornata il 2026-10-05: stato alla data di scarico
- Ultima modifica della scheda del catalogo: 2026-10-05 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_aree_verdi_20261010` | 2026-10-10T18:03:44Z | non dichiarato (scheda aggiornata il 2026-10-05: stato alla data di scarico) | e8036d81d5e0 | no |

## Campi usati

`ID`, `CODICE_ARE`, `NOME_AREA`, `SUPERF_MQ`, `USO_AREA`, `QUARTIERE`

Unità: `SUPERF_MQ` m2

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile (EPSG:3003) e convertito in EPSG:7791)

## Controlli

- aree verdi in area allargata: superato. 242 oggetti
- limite: avviso. aree verdi gestite dal Comune, comprese rotonde, spartitraffico e aree non fruibili (campo USO_AREA)

## Limiti

- limite: aree verdi gestite dal Comune, comprese rotonde, spartitraffico e aree non fruibili (campo USO_AREA)

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
