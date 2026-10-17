# Unità volumetriche del DB topografico regionale (WFS), area di Firenze

- Identificativo: `src_rt_uv_firenze_novoli`
- Editore: Regione Toscana
- Scheda del catalogo: nessuna. Le unità volumetriche di Firenze non sono su dati.toscana.it (il portale le ha per altri 40 comuni, non per Firenze): fonte il servizio WFS del Geoscopio. Da chiedere alla Regione: pubblicazione del layer per Firenze.
- Pagina della fonte: https://www502.regione.toscana.it/geoscopio/servizi/wms/EDIFICATO.htm
- Risorsa scaricata: https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_rt_uv_firenze_novoli_20261009`

## Licenza

- Licenza: nessun identificativo dichiarato (vedere evidenza)
- Verifica: verificata con riserva
- Uso consentito: solo prototipo interno: verificare prima di ridistribuire
- Evidenza: https://www502.regione.toscana.it/geoscopio/servizi/wms/EDIFICATO.htm
- Nota: Nessuna licenza sul layer; vale la politica regionale sui dati geografici aperti (CC BY o CC BY-SA, atto 2013), come a Pisa.
- Riserva: Licenza non scritta sul layer: dedotta dalla politica regionale. Verificare prima di ridistribuire.

## Date

- Data del dato: dal 2011-01-01 al 2011-12-31
- Nota sul periodo: volo 2011 (campo anno, audit edifici); data di aggiornamento del servizio non dichiarata

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_rt_uv_firenze_novoli_20261009` | 2026-10-09T15:16:16Z | dal 2011-01-01 al 2011-12-31 | 2197d5f11058 | sì |

## Campi usati

`uv_id`, `edifc_id`, `uv_av`, `uv_qs`, `uv_qe`, `uv_dpor`, `anno`

Unità: `height_m` m, `ground_elev_m` m, `roof_elev_m` m, `area_m2` m2

Sistema di riferimento dichiarato: EPSG:7791 (richiesto direttamente in EPSG:7791; spiccato UV meno DTM 2023: mediana -0,14 m su 1.419 impronte (audit edifici), datum coerente ma non dichiarato dalla fonte)

## Controlli

- building_volume in area allargata: superato. 7987 oggetti
- portici (uv_dpor): avviso. un solo oggetto con loggia nell'audit: nessuna fonte per portici e volumi sospesi

## Limiti

- Unità volumetriche del 2011 con altezze dal LiDAR 2023: edifici nuovi solo dove li ha OSM; portici ignoti trattati come pieni.
- portici (uv_dpor): un solo oggetto con loggia nell'audit: nessuna fonte per portici e volumi sospesi
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
