# GTFS Autolinee Toscane, copia di Firenze

- Identificativo: `src_gtfs_at_firenze`
- Editore: Regione Toscana / Autolinee Toscane
- Scheda del catalogo: https://dati.toscana.it/dataset/rt-oraritb
- Risorsa scaricata: https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_gtfs_at_firenze_20261009`

## Licenza

- Licenza: cc-by
- Verifica: verificata con riserva
- Uso consentito: solo prototipo interno: verificare prima di ridistribuire
- Evidenza: https://dati.toscana.it/dataset/rt-oraritb
- Nota: Scheda del catalogo regionale: 'cc-by'; risorsa Autolinee Toscane: CC BY 4.0.
- Riserva: Versione CC non indicata sulla scheda e condizioni specifiche del feed non trovate: vale il campo del catalogo.

## Date

- Data del dato: dal 2026-10-09 al 2026-10-29
- Nota sul periodo: finestra mobile di tre settimane: feed_start_date e feed_end_date da feed_info.txt
- Ultima modifica della scheda del catalogo: 2026-09-08 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_gtfs_at_firenze_20261009` | 2026-10-09T15:11:43Z | dal 2026-10-09 al 2026-10-29 | 6ca6c95f0556 | sì |
| `snp_gtfs_at_firenze_20261016` | 2026-10-16T19:35:14Z | dal 2026-10-16 al 2026-11-05 | 4b0a88dfac9b | no |

## Campi usati

`stop_id`, `stop_code`, `stop_name`, `wheelchair_boarding`

Unità: `stop_lat` deg, `stop_lon` deg, `trips_on_ref_date` count

Sistema di riferimento dichiarato: EPSG:4326 (lat/lon come da specifica GTFS)

## Controlli

- fermate in area allargata: superato. 189 fermate
- scadenza: avviso. il feed scade il 2026-10-29: rifare lo snapshot per ogni uso dopo quella data (la copia dell'audit scadeva il 2026-10-25)

## Limiti

- Finestra mobile di tre settimane: i calcoli usano solo le posizioni delle fermate, non gli orari.
- scadenza: il feed scade il 2026-10-29: rifare lo snapshot per ogni uso dopo quella data (la copia dell'audit scadeva il 2026-10-25)
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
