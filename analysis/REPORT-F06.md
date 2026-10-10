# REPORT F06: accessibilità pedonale su Firenze Novoli

Consegna del 10 ottobre 2026. Il motore `analysis/` non dipende più da Pisa e gira su `aoi_firenze_novoli`.

## Cosa è cambiato

- `analysis/accessibilita.py`: tolte le costanti di Pisa.
  - L'area viene da `RL.AOI_ID` (variabile DT_AOI, default Firenze).
  - La baseline è l'ultima di `contracts/aree.json` per l'area (`bas_firenze_novoli_20261009`).
  - Il `graph_id` viene da `rete_manifest.json` dell'area.
  - File e GeoPackage vengono da `rete_lib` (`RL.RES`, `RL.OUT`, `RL.STEM`, `RL.OSM_GPKG`).
  - Snapshot dei manifest ricavati: OSM da `RL.OSM_SNAP`, civici e fonti della destinazione dalla baseline. Scuole: scuole statali e accessi della Città metropolitana. Tram: GTFS del gestore. Polo: solo OSM e civici.
  - Origini: famiglia `address_points` con `aoi_id` nei parametri del job. `civici_sit_z2` è tolta.
  - Testi generici o presi dall'area, per esempio "civici del Comune di Firenze (CC BY 4.0)".
  - Corretto `permissivo_m` per i civici "forbidden": ora include il raccordo dell'ingresso, come nel caso raggiungibile. A Pisa il raccordo era quasi nullo; a Firenze lo scarto era di 2,9 m sul campione V01 di F04.
- `analysis/run.py`: riscritto.
  - Destinazioni lette da `destinazioni.json` (5), 4 profili ciascuna.
  - Sensibilità sullo snapping (20, 40, 60 m) per ogni destinazione.
  - Sensibilità sugli ingressi per le destinazioni con più di un ingresso (il Polo): predefinito, tutti e 2, ciascun ingresso da solo.
  - Svuota e riscrive `analysis/firenze_novoli/manifest/` a ogni esecuzione.
- 10 ottobre, dopo F11, in `analysis/accessibilita.py`:
  - `compute_walk_access` accetta una lista di destinazioni. Usa tutti i loro ingressi insieme e per ogni civico vince il più vicino: è l'accessibilità verso almeno una. Il manifest ha il limite `almeno_una_destinazione`.
  - Nuove metriche `served_count_<soglia>min`: civici raggiunti per soglia, con l'intervallo di velocità 0,8-1,4 m/s.
  - `parametri_job` calcola inputs, parametri e `job_id` senza eseguire il calcolo. La usano il motore e il servizio.
  - Con una destinazione `job_id` e numeri restano uguali: i manifest di `analysis/firenze_novoli/manifest/` sono stati rigenerati con gli stessi nomi. L'hash del motore in `scenarios/firenze_novoli/baseline.json` è aggiornato.
- `analysis/run.sh`: lancia run.py e il test.
- `analysis/test_accessibilita.py`: riscritto per Firenze.
  - Conteggi: 3.296 origini, 3.112 raggiungibili, 168 insufficient_data, 16 forbidden o isolated.
  - Percorsi campione R01-R10 uguali a F04, V01 e V02 forbidden.
  - Agganci uguali a `origini_snap.gpkg`.
  - Determinismo del `job_id` e job diversi per input diversi.
  - 20 manifest e job validi per gli schemi, sha256 degli asset, nessuna stringa "pisa", "z2" o "sit di" nei file prodotti.
  - Monotonia dei profili, ingressi multipli, asset mappa e riepilogo.

## Comandi

- `bash analysis/run.sh` (analisi, poi test)
- `pipeline/.venv/bin/python analysis/test_accessibilita.py`

## Risultati principali

Civici raggiunti entro 5, 10 e 15 minuti a 1,2 m/s (quote su tutti i 3.296 civici) e tempo mediano dei raggiungibili:

- Polo delle Scienze Sociali: 12,2% / 24,4% / 45,9%, mediana 15,2 min.
- Scuola primaria Vamba: 15,5% / 39,0% / 54,0%, mediana 13,0 min.
- Scuola infanzia Vamba: uguale alla primaria (stesso accesso nei dati).
- Fermata T2 Novoli - Regione Toscana (`dst_tram_fm9056`): 7,3% / 29,7% / 60,0%, mediana 12,7 min.
- Fermata T2 Novoli - Torre Degli Agli (`dst_tram_fm9057`): 15,9% / 39,3% / 45,1%, mediana 15,5 min.

Stati, uguali per tutte le destinazioni: 3.112 reachable, 15 forbidden, 1 isolated, 168 insufficient_data, 0 outside_model. I 3.112 coincidono con F04.

Altri profili, quote entro 10 minuti:
- Lento 0,8 m/s: Polo 15,2%, Vamba 23,8%, fm9056 13,5%, fm9057 30,1%.
- Rapido 1,4 m/s: Polo 28,9%, Vamba 43,7%, fm9056 40,5%, fm9057 39,6%.
- Ridotta senza scale: Polo 14,6%, Vamba 21,5%, fm9056 12,9%, fm9057 29,0%.

Ingressi del Polo (profilo base, 5 / 10 / 15 minuti):
- Ingresso predefinito (n11152998932): 12,2% / 24,4% / 45,9%, mediana 15,2 min.
- Solo l'altro ingresso (n11152998933): 12,6% / 26,3% / 41,7%, mediana 15,7 min.
- Entrambi: 14,3% / 26,3% / 47,8%, mediana 14,9 min. 1.038 civici usano il predefinito, 2.074 l'altro.
- I 10 archi più usati coincidono solo per 1 su 10 fra predefinito ed entrambi: la scelta dell'ingresso sposta i percorsi più delle quote.

Snapping del Polo: a 20 m i raggiungibili scendono a 2.858 (10 minuti: 23,1%); a 60 m salgono a 3.141 (24,7%). Stesso andamento per le altre destinazioni.

## Output

- Versionati in `analysis/firenze_novoli/`: `manifest/` (20 manifest e 20 job), `riepilogo.json`, `accessibilita_<destination_id>.geojson` (5 file di circa 1 MB: civici, destinazione, archi usati, EPSG:4326).
- Dati grandi in `data/norm/firenze_novoli/analysis/<destination_id>/` (CSV per origine, archi usati, report), non versionati.

## Limiti

- Rete solo OSM, non verificata sul posto. Marciapiedi ignoti dove non taggati.
- I civici sono punti d'indirizzo, non residenti: le quote sono quote di civici.
- Ingressi, orari e accessi non verificati. Il Polo è un campus con cancelli e orari ignoti; i due ingressi OSM sono da verificare.
- Le due scuole Vamba hanno un solo accesso nei dati, quindi risultati identici.
- Velocità e penalità sono ipotesi, non misure. Mancano pendenze, larghezze e rampe: nessuna certificazione di accessibilità.
- 168 civici (5,1%) restano insufficient_data per lo snapping.
- Le fermate T2 sono punti GTFS, non banchine.
- Non validato sul posto (`validation_status` = `not_validated_locally`).
- Restano nomi storici interni (`in_z2` nei nodi di rete, variabili BAT e PEL nel test) per compatibilità con `rete_lib`.
- Il test vale solo per Firenze: si ferma se DT_AOI è diversa.
