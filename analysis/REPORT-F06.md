# REPORT F06: accessibilità pedonale su Firenze Novoli

Aggiornato dopo D19/D20 e la revisione del codice del 10 ottobre 2026. I risultati sotto sono stati ricalcolati in memoria e confrontati con il riepilogo versionato; manifest e asset non sono stati riscritti. Il motore `analysis/` non dipende più da Pisa e gira su `aoi_firenze_novoli`.

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
  - Destinazioni lette da `destinazioni.json` (6), 4 profili ciascuna.
  - Sensibilità sullo snapping (20, 40, 60 m) per ogni destinazione.
  - Sensibilità sugli ingressi per le destinazioni con più di un ingresso (il Polo): predefiniti (i 7 civici degli edifici del Polo, D19), ciascun ingresso da solo.
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
  - 24 manifest e job validi per gli schemi, sha256 degli asset, nessuna stringa "pisa", "z2" o "sit di" nei file prodotti.
  - Monotonia dei profili, ingressi multipli, asset mappa e riepilogo.

## Comandi

- `bash analysis/run.sh` (analisi, poi test)
- `pipeline/.venv/bin/python analysis/test_accessibilita.py`

## Risultati principali

Quote di tutti i 3.296 civici raggiunti entro 5, 10 e 15 minuti a 1,2 m/s, con mediana sui raggiungibili. Ricalcolo del 10 ottobre 2026, baseline `bas_firenze_novoli_20261009`.

- Polo delle Scienze Sociali (7 ingressi): 17,3% / 28,2% / 53,8%; mediana 14,2 minuti.
- Scuola primaria Vamba: 15,5% / 39,0% / 54,0%; mediana 13,0 minuti.
- Scuola infanzia Vamba: 15,5% / 39,0% / 54,0%; mediana 13,0 minuti.
- T2 San Donato - Università: 3,9% / 23,8% / 56,0%; mediana 13,5 minuti.
- T2 Novoli - Regione Toscana: 7,3% / 29,7% / 60,0%; mediana 12,7 minuti.
- T2 Novoli - Torre degli Agli: 15,9% / 39,3% / 45,1%; mediana 15,5 minuti.

Stati per ogni destinazione: 3.112 `reachable`, 15 `forbidden`, 1 `isolated`, 168 `insufficient_data`, 0 `outside_model`. Le due scuole hanno lo stesso accesso e gli stessi risultati.

Quote entro 10 minuti negli altri profili:

- Lento 0,8 m/s: Polo delle Scienze Sociali (7 ingressi): 21,8%; Scuola primaria Vamba: 23,8%; T2 San Donato - Università: 8,2%; T2 Novoli - Regione Toscana: 13,5%; T2 Novoli - Torre degli Agli: 30,1%.
- Rapido 1,4 m/s: Polo delle Scienze Sociali (7 ingressi): 34,0%; Scuola primaria Vamba: 43,7%; T2 San Donato - Università: 35,4%; T2 Novoli - Regione Toscana: 40,5%; T2 Novoli - Torre degli Agli: 39,6%.
- Ridotta 0,8 m/s senza scale, 10 s per attraversamento: Polo delle Scienze Sociali (7 ingressi): 21,6%; Scuola primaria Vamba: 21,5%; T2 San Donato - Università: 8,0%; T2 Novoli - Regione Toscana: 12,9%; T2 Novoli - Torre degli Agli: 29,0%.

Sensibilità agli ingressi del Polo (profilo base, quote a 5 / 10 / 15 minuti):

- Tutti i 7 ingressi, impostazione predefinita: 17,3% / 28,2% / 53,8%; mediana 14,2 minuti.
- Solo D1: 14,5% / 27,9% / 46,3%; mediana 15,1 minuti.
- Solo D4: 13,7% / 28,2% / 46,6%; mediana 15,1 minuti.
- Solo D5: 12,5% / 26,4% / 42,3%; mediana 15,6 minuti.
- Solo D6: 7,7% / 24,3% / 39,8%; mediana 16,2 minuti.
- Solo D10: 11,9% / 24,3% / 45,1%; mediana 15,3 minuti.
- Solo D14: 11,1% / 24,5% / 44,1%; mediana 15,4 minuti.
- Solo D15: 11,5% / 24,6% / 46,7%; mediana 15,1 minuti.

Scelte del cammino minimo con tutti gli ingressi: D1 53 civici, D10 10 civici, D14 2 civici, D15 955 civici, D4 2002 civici, D5 74 civici, D6 16 civici.

Snapping del Polo:

- 20 m: 2858 raggiungibili; 26,2% entro 10 minuti.
- 40 m: 3112 raggiungibili; 28,2% entro 10 minuti.
- 60 m: 3141 raggiungibili; 28,7% entro 10 minuti.

Gli intervalli con penalità di attraversamento hanno un difetto distinto dai valori centrali: vedi R3 della revisione del codice.

## Output

- Versionati in `analysis/firenze_novoli/`: `manifest/` (24 manifest e 24 job), `riepilogo.json`, `accessibilita_<destination_id>.geojson` (6 file di circa 1 MB: civici, destinazione, archi usati, EPSG:4326).
- Dati grandi in `data/norm/firenze_novoli/analysis/<destination_id>/` (CSV per origine, archi usati, report), non versionati.

## Limiti

- Rete solo OSM, non verificata sul posto. Marciapiedi ignoti dove non taggati.
- I civici sono punti d'indirizzo, non residenti: le quote sono quote di civici.
- Ingressi, porte e cancelli non verificati. Il Polo usa un civico del Comune per ciascuno dei 7 edifici dell'Ateneo (D19); il civico non è necessariamente la porta. Le condizioni di accesso riportano orari documentati, senza verifica sul posto.
- Le due scuole Vamba hanno un solo accesso nei dati, quindi risultati identici.
- Velocità e penalità sono ipotesi, non misure. Mancano pendenze, larghezze e rampe: nessuna certificazione di accessibilità.
- 168 civici (5,1%) restano insufficient_data per lo snapping.
- Le fermate T2 sono punti GTFS, non banchine.
- Non validato sul posto (`validation_status` = `not_validated_locally`).
- Restano nomi storici interni (`in_z2` nei nodi di rete, variabili BAT e PEL nel test) per compatibilità con `rete_lib`.
- Il test vale solo per Firenze: si ferma se DT_AOI è diversa.
