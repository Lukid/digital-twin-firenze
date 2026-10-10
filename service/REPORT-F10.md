# F10: servizio di analisi e MCP su Firenze Novoli

Aggiornato nella revisione del codice del 10 ottobre 2026. Test: `service/.venv/bin/python service/test_service.py` (circa 16 s con la cache degli scenari, TUTTO OK). Non validato sul posto.

## Cosa è cambiato

- `core.py` non ha più costanti di Pisa. Area, baseline e cartelle vengono dal registro `contracts/aree.json` (variabile `DT_AOI`, default `aoi_firenze_novoli`, come i motori).
  - Baseline: `bas_firenze_novoli_20261009`.
  - Origini: `address_points` con `aoi_id`. La forma storica `civici_sit_z2` dà `outside_capability` e non compare nello schema mostrato al client.
  - Destinazioni da `network/firenze_novoli/destinazioni.json`.
  - Percorsi campione da `network/firenze_novoli/percorsi_campione.geojson`, solo quelli raggiungibili (R01-R10), con id `pth_fi_R01` e seguenti come in `shadow/run.py`.
  - Job storici letti da `analysis/firenze_novoli/manifest/` e `shadow/firenze_novoli/manifest/`.
- Fonti approvate: solo le 14 della baseline, con lo snapshot del 9 ottobre. Fonte o snapshot fuori baseline: `unknown_id` con l'elenco di quelle ammesse.
- Cache dei job: `service/cache/firenze_novoli/` (modificabile con `DT_CACHE_DIR` dentro il progetto).
- Server MCP rinominato `dt-firenze`. Tool di calcolo invariati; aggiunto `list_scenarios` dopo il giro F11.
- Ombra: nuova opzione `obstacles = buildings_trees_and_lidar_vegetation` (edifici, alberi censiti e vegetazione LiDAR, D14), con 9 casi. Estensione additiva di `contracts/schemas/mcp.schema.json`.
- Replay: porta `aoi_id` nelle origini e i casi dell'ombra dal manifest.
- Scenari: `create_local_scenario` e `compare_scenarios` usano `scenarios/` di F08 (id `scn_fi_*`, file in `scenarios/firenze_novoli/`). Le alternative negli errori sono solo `scn_fi_*`.
- `compute_shadow` con `scenario_id` (`obstacles = buildings_and_scenario`) calcola sempre i 9 casi (edifici, alberi censiti, vegetazione LiDAR, ognuno con centrale e due estremi).
- 10 ottobre, dopo F11: nuovo tool `list_scenarios`; `compute_walk_access` accetta più destinazioni (accessibilità verso almeno una: tutti gli ingressi insieme, per ogni civico vince il più vicino, limite `almeno_una_destinazione` nel manifest); nuove metriche `served_count_*` (civici raggiunti per soglia, con intervallo di velocità). Con una sola destinazione `job_id` e numeri non cambiano.

## Tool MCP (10)

- `list_approved_sources`, `inspect_dataset`, `list_destinations`, `list_scenarios`, `compute_walk_access`, `compute_shadow`, `get_job_status`, `get_result_manifest`, `create_local_scenario`, `compare_scenarios`.
- `additionalProperties: false` su tutti gli input. Errori con `isError=true` e codice (`invalid_params`, `unknown_id`, `ambiguous_destination`, `outside_capability`, `limit_exceeded`, `incompatible_baseline`).

## Confronto di scenari

- Con `manifest_ids` e `metric_ids`: delta fra manifest di `compute_shadow` con condizioni comuni.
- Con `baseline_id` e `scenario_ids`: confronto con la baseline S0 per data (15 luglio e 15 settembre) e per contesto.
  - `context`: `con_vegetazione_lidar` (default, base principale, D14), `solo_edifici`, `con_alberi_esistenti`, `entrambi` (tutti e tre).
  - `deltas`: minuti al sole e frazione d'ombra su R01 e R02, per fascia, più l'area di attesa di S2 (fermata Guidoni Barsanti dal 10 ottobre), con intervallo dai casi estremi del contesto. Il `metric_id` finisce con `_edifici`, `_alb` o `_lidar`.
  - `scenarios`: segnalazioni, fattibilità ignota, archi più usati pesati per civici, accessibilità (delta zero per costruzione), fasce utili su R01, robustezza alle varianti di S1, sovrapposizioni con gli alberi esistenti.
  - Nessun punteggio unico e nessun ordinamento: con `weights` risponde `outside_capability`.
  - Usa i job in cache di F08 (`data/norm/firenze_novoli/scenarios/jobs`). Senza cache ogni job richiede alcuni minuti; il servizio non li lancia in parallelo (il pool di processi si rompe su macOS quando è chiamato dal servizio).
- Esempio: `service/.venv/bin/python service/cli.py compare_scenarios '{"baseline_id":"bas_firenze_novoli_20261009","scenario_ids":["scn_fi_s1_filare_r01","scn_fi_s2_pensilina_attesa_polo"]}'`

## Destinazioni e alias

- `dst_university_w83537185`, Polo delle Scienze Sociali (7 ingressi, uno per edificio: senza `entrance_ids` vince il più vicino): polo, università, ateneo, pandette, scienze sociali, polo scienze sociali.
- `dst_school_fiee86002g`, scuola primaria Vamba: primaria vamba, scuola primaria.
- `dst_school_fiaa86002a`, scuola infanzia Vamba: infanzia vamba, scuola infanzia.
- `vamba`, `scuola vamba` e `scuola` danno entrambe le scuole.
- `dst_tram_fm9056`, fermata T2 Novoli - Regione Toscana: fermata regione, regione toscana, regione.
- `dst_tram_fm9057`, fermata T2 Novoli - Torre Degli Agli: torre degli agli, fermata torre degli agli, agli.
- `dst_tram_fm9055`, fermata T2 San Donato - Università (indicata dall'Ateneo per il Polo, D20): san donato, fermata san donato, san donato università, fermata università, fermata del polo.
- `tram`, `t2`, `fermata` e `fermata tram` danno le tre fermate.
- Il confronto ignora maiuscole e accenti; cerca anche in nome, id, indirizzo e codice MIM.
- `compute_walk_access` non sceglie mai per nome: con un nome o senza destinazione risponde `ambiguous_destination` con i candidati.
- Le fermate del tram hanno categoria `stop`: il contratto non ha `tram`.

## Comandi

- Test: `service/.venv/bin/python service/test_service.py`.
- CLI: `service/.venv/bin/python service/cli.py <strumento> '<json>'`, oppure `list`, oppure `replay <job_id>`.
- API HTTP: `service/.venv/bin/python service/api.py` (solo 127.0.0.1, porta 8792, `POST /tools/<nome>`).
- MCP: `service/.venv/bin/python service/mcp_server.py` (stdio). Nel client il server va registrato come `dt-firenze` (`.mcp.json` nella radice del progetto).

## Esempi di chiamata

Accessibilità al Polo a 1,2 m/s, con i 7 ingressi degli edifici (stesso `job_id` di F06, `job_9b2e74744a8d2865`, dal 10 ottobre, D19):

```
service/.venv/bin/python service/cli.py compute_walk_access '{"baseline_id":"bas_firenze_novoli_20261009","origins":{"kind":"address_points","aoi_id":"aoi_firenze_novoli"},"destination_ids":["dst_university_w83537185"],"profile":{"speed_m_s":1.2},"thresholds_min":[5,10,15]}'
```

Trovare la fermata dal nome:

```
service/.venv/bin/python service/cli.py list_destinations '{"aoi_id":"aoi_firenze_novoli","category":"stop","name_query":"torre degli agli"}'
```

Ombra su R02 il 15 settembre alle 12:30, con alberi e vegetazione LiDAR:

```
service/.venv/bin/python service/cli.py compute_shadow '{"baseline_id":"bas_firenze_novoli_20261009","receivers":[{"route_id":"R02"}],"when":{"date":"2026-09-15","timezone":"Europe/Rome","times":["12:30"]},"method":{"name":"geometric_ray","space_step_m":1,"time_step_min":5,"obstacles":"buildings_trees_and_lidar_vegetation"}}'
```

## Test coperti

- Stesso input = stesso `job_id` e cache. Il job sul Polo riproduce quello di F06.
- Validazione dello schema in ingresso (8 input non validi, origini di altre aree, baseline di Pisa) e in uscita per ogni tool.
- Alias delle destinazioni ed errore chiaro su destinazione ambigua o mancante.
- Fonti: solo quelle della baseline.
- Ombra con parametri ridotti: cache, vegetazione LiDAR, ora ambigua e inesistente, sole sotto l'orizzonte, limite di costo.
- Replay di job nuovi e storici.
- Nessuna stringa "Pisa", "Z2", "Pellico" o "Battisti" nelle risposte, nei manifest e negli schemi mostrati al client.
- Server MCP avviato con un client stdio reale (`dt-firenze`, 10 tool).
- Scenari provati con i file di F08: creazione, ombra con scenario (9 casi), confronto per manifest e per scenari, contesti, pesi non ammessi, errori.

## Limiti

- Più destinazioni in un job danno solo l'accessibilità verso almeno una, non un risultato per destinazione. Griglia e punti: `outside_capability`.
- Senza `entrance_ids` si usano gli ingressi predefiniti della destinazione: per il Polo tutti i 7 civici degli edifici (D19), scegliendo il più vicino per ogni origine. Porte e cancelli restano da verificare.
- Limiti: area massima 4 km², 50.000 origini, 600 s per l'accessibilità; ombra fino a 1.500 combinazioni (ricevitori per orari per casi). Calcolo sincrono, senza coda.
- Il `job_id` dell'accessibilità è previsto prima del calcolo con `accessibilita.parametri_job`, la stessa funzione che usa il motore.
- Ricevitori dell'ombra solo da percorso campione o geometria esplicita, sull'asse della rete.
- Il `.pth` del venv usa un percorso assoluto.
- Risultati degli scenari `not_validated_locally`: interventi ipotetici, fattibilità ignota.
- Il confronto per scenari non produce `indicators` né `ranking` (F08 ha tolto `indicatori()`, `ordina()` e `sensibilita_pesi()`). Nel riepilogo solo R01 e R02; l'andamento per ora è in `scenarios/firenze_novoli/confronto.json`.
- La verifica NL di Firenze è in `nl/firenze_novoli/`: registro dopo D19/D20 e test con replay rieseguito. Non è stato eseguito un nuovo giro di domande dopo `list_scenarios`, accessibilità verso almeno una destinazione e conteggi `served_count_*`.

## Difetti confermati nella revisione del codice

- Geometrie degeneri o incoerenti con `kind` possono causare eccezioni non strutturate (R1).
- Scritture concorrenti della stessa cache possono collidere sul temporaneo (R2).
- Gli intervalli di accessibilità con penalità di attraversamento non seguono il costo del cammino (R3).
- L'alias di cache delle ombre non identifica tutte le dipendenze (R4).
- `compare_scenarios` omette le aree di attesa di S5 e S6, sia nei delta sia nel riepilogo. Per queste pensiline non basta leggere i delta dell'area storica di S2 (R5).

Priorità, prove e correzioni proposte nella [revisione del codice](../docs/REVISIONE-CODICE-20261010.md). I difetti sono aperti; il passaggio dei test esistenti non li chiude.
