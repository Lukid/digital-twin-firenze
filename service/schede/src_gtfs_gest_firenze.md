# GTFS tram (GEST), Firenze

- Identificativo: `src_gtfs_gest_firenze`
- Editore: Regione Toscana / GEST
- Scheda del catalogo: https://dati.toscana.it/dataset/rt-oraritb
- Risorsa scaricata: https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/1f62d551-65f4-49f8-9a99-e19b02077be3/download/gest.gtfs
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_gtfs_gest_firenze_20261009`

## Licenza

- Licenza: cc-by
- Verifica: verificata con riserva
- Uso consentito: solo prototipo interno: verificare prima di ridistribuire
- Evidenza: https://dati.toscana.it/dataset/rt-oraritb
- Nota: Campo license_id della scheda del catalogo regionale: 'cc-by'.
- Riserva: La risorsa GEST non porta licenza e la versione CC non è indicata: vale solo il campo della scheda.

## Date

- Data del dato: dal 2026-08-10 al 2026-12-30
- Nota sul periodo: minimo e massimo di calendar_dates.txt (nessun feed_info.txt); contiene solo T2 e T1.3, la T1 non compare
- Ultima modifica della scheda del catalogo: 2026-09-08 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_gtfs_gest_firenze_20261009` | 2026-10-09T15:09:58Z | dal 2026-08-10 al 2026-12-30 | 97d18a9d9eae | sì |
| `snp_gtfs_gest_firenze_20261016` | 2026-10-16T19:35:15Z | dal 2026-08-10 al 2026-12-30 | 97d18a9d9eae | no |

## Campi usati

`stop_id`, `stop_code`, `stop_name`, `wheelchair_boarding`

Unità: `stop_lat` deg, `stop_lon` deg, `trips_on_ref_date` count

Sistema di riferimento dichiarato: EPSG:4326 (lat/lon come da specifica GTFS)

## Controlli

- fermate in area allargata: superato. 12 fermate
- linea T1: avviso. assente dal feed (solo T2 e T1.3)

## Limiti

- I calcoli usano solo le posizioni delle fermate, non gli orari.
- linea T1: assente dal feed (solo T2 e T1.3)
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
