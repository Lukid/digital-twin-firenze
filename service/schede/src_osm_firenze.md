# OpenStreetMap, estratto regionale Centro Italia (ritagliato su riquadro + 700 m)

- Identificativo: `src_osm_firenze`
- Editore: OpenStreetMap contributors, estratto di un distributore di estratti OSM
- Scheda del catalogo: nessuna. OSM non è su dati.toscana.it (fonte aperta esterna, ODbL): marciapiedi, attraversamenti e ingressi non hanno altra fonte nel catalogo.
- Pagina della fonte: https://download.geofabrik.de/europe/italy/centro.html
- Risorsa scaricata: https://download.geofabrik.de/europe/italy/centro-261008.osm.pbf
- Nella baseline congelata `bas_firenze_novoli_20261009`: sì, snapshot `snp_osm_firenze_20261009`

## Licenza

- Licenza: ODbL-1.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://www.openstreetmap.org/copyright
- Nota: Dati OpenStreetMap sotto ODbL.

## Date

- Data del dato: 2026-10-08
- Nota sul periodo: stato di OpenStreetMap al 2026-10-08 (data nel nome dell'estratto), senza data di rilievo per oggetto

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_osm_firenze_20261009` | 2026-10-09T15:07:52Z | non dichiarato (estratto regionale Centro Italia, timestamp nel nome del file (2026-10-08, ore 00 UTC circa); il ritaglio all'area allargata avviene in normalizzazione, il file originario resta intatto) | 9fcfe51bab23 | sì |

## Campi usati

`id`, `highway`, `sidewalk`, `crossing`, `entrance`, `building`, `height`

Unità: `length_m` m, `area_m2` m2

Sistema di riferimento dichiarato: EPSG:4326 (lon/lat trattati come RDN2008 geografico (scarto misurato a Pisa: mediana 0,08 m))

## Controlli

- strade in area allargata: superato. 4596 tratti
- nodi con tag in area allargata: superato. 20281 nodi
- edifici in area allargata: superato. 3885 edifici
- marciapiedi e ingressi: avviso. pochi (audit rete: 1,9 km di footway=sidewalk, 5 ingressi in FB)

## Limiti

- Rete pedonale solo OSM: lato del marciapiede, larghezze e pendenze ignoti.
- Estratto regionale del 2026-10-08, non più scaricabile da Geofabrik: la baseline non si ricostruisce identica da zero.
- marciapiedi e ingressi: pochi (audit rete: 1,9 km di footway=sidewalk, 5 ingressi in FB)

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
