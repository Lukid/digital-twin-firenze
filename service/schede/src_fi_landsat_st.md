# Landsat 8-9 Collection 2 Level-2, temperatura delle superfici (ST_B10) e QA_PIXEL, estati 2023-2026, riquadro FP

- Identificativo: `src_fi_landsat_st`
- Editore: U.S. Geological Survey (copia di Microsoft Planetary Computer)
- Scheda del catalogo: nessuna. Landsat non è su dati.toscana.it: prodotto dell'USGS, letto dalla copia pubblica del catalogo STAC di Microsoft Planetary Computer (accesso anonimo).
- Pagina della fonte: https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature
- Risorsa scaricata: https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: public-domain
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
- Nota: Pagina USGS: "There are no restrictions on the use of Landsat products." Politica dati USGS: "All public domain imagery may be used, shared, transferred, or redistributed without restriction." Citazione chiesta: DOI 10.5066/P9OGBGM6 (Landsat 8-9 OLI/TIRS C2 L2); credito suggerito "Landsat Collection 2 Level-2 image courtesy of the U.S. Geological Survey".
- Riserva: Dati USGS di pubblico dominio, scaricati tramite Microsoft Planetary Computer.

## Date

- Data del dato: dal 2023-06-01 al 2026-09-30
- Nota sul periodo: passaggi estivi (giugno-settembre) 2023-2026 alle 09:58-09:59 UTC circa; tenute solo le date con almeno l'80% di celle valide sul riquadro FP

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_landsat_st_20261010` | 2026-10-10T16:22:29Z | dal 2023-06-01 al 2026-09-30 | 1401627a99aa | no |

## Campi usati

`ST_B10`, `QA_PIXEL`

Unità: `st_b10` K = DN x 0,00341802 + 149,0 (nodata 0); convertito in °C, `qa_pixel` bit

Sistema di riferimento dichiarato: EPSG:32632 (COG in WGS84 UTM 32N a 30 m; ritagli ricampionati per vicinanza sul reticolo EPSG:7791 a 30 m della scena (scarto fra i due sistemi sotto il metro))

## Controlli

- date valide sul riquadro: superato. vedi data/norm/firenze_novoli/fi_landsat_st.json
- risoluzione: avviso. banda termica misurata a 100 m e distribuita a 30 m: il dettaglio fra 30 e 100 m non è misurato
- saturazione termica: avviso. QA_RADSAT non ha un bit per la banda 10 su Landsat 8-9: la saturazione non si controlla

## Limiti

- Temperatura delle superfici, non dell'aria; misura a 100 m distribuita a 30 m; solo passaggi di metà mattina.
- risoluzione: banda termica misurata a 100 m e distribuita a 30 m: il dettaglio fra 30 e 100 m non è misurato
- saturazione termica: QA_RADSAT non ha un bit per la banda 10 su Landsat 8-9: la saturazione non si controlla
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
