# F11: verifica delle domande in linguaggio naturale su Firenze Novoli

Data: 10 ottobre 2026. Controllo: `service/.venv/bin/python nl/firenze_novoli/test_nl.py` (circa 30 s, TUTTO OK, anche senza la cache del servizio). Non validato sul posto.

## Come è stata fatta

- Client: un agente nuovo, senza accesso al repository, che parla con il vero server MCP `dt-firenze` via stdio attraverso `mcp_client.py` (comandi `tools` e `call`). Il server non è attivo nella sessione principale, per questo serve il client.
- Contesto iniziale dato nel prompt: `aoi_firenze_novoli`, `bas_firenze_novoli_20261009`, EPSG:7791, Europe/Rome. Nessun id di destinazione o di scenario.
- 21 domande nel primo giro (`giro1.json`), 7 seguiti con le risposte di chiarimento dell'utente (`giro2.json`). Ogni voce riporta chiamate, argomenti, esito, job_id e risposta.
- Categorie: dati e licenze (1, 2), accessibilità (3, 4, 5, 6b, 7b, 8, 16b, 18b), ombra (9, 10, 11b, 15b), scenari (12, 13, 20b), ambigue (6, 7, 11, 15, 16, 18, 20), fuori capacità (14, 15, 16, 17), limiti (18, 21), ripetibilità (19).
- Una sola esecuzione, domande scritte da chi conosce il sistema: misura la traduzione in chiamate, non la robustezza con utenti reali.
- I manifest dei job nuovi del client sono versionati in `nl/firenze_novoli/manifest/`. Il servizio ora li legge anche da lì (`core._read_job`).

## Esito rispetto ai criteri

- Nessun numero senza esecuzione: 28 risposte su 28. Il controllo automatico cerca percentuali e minuti nelle risposte e richiede un job.
- Ambiguità: il client si ferma e chiede in tutti i casi (due scuole Vamba, due fermate del tram, 02:30 del 25 ottobre, alberi non identificati, pesi assenti). Con la risposta dell'utente completa il calcolo. Alla domanda 13 ha scelto la fermata Guidoni Barsanti dello scenario S2 e l'ha dichiarato.
- Persone e civici: alle domande 7 e 7b il client dice che i civici non sono persone e che manca un dato di popolazione.
- Fuori capacità: temperatura, rimozione di alberi, Careggi (fuori area), SQL, ordinamento con pesi. Nessuna stima inventata; il client propone cosa si può calcolare.
- Limiti: cinque destinazioni in una chiamata danno `limit_exceeded`. Il client ripiega su un job per destinazione e dice che l'unione ("almeno una") non è disponibile.
- Replay: 9 job su 9 identici, anche senza la cache del servizio. Esclusi i 3 confronti di scenari, che non hanno replay.
- Confronto con la mappa:
  - Accessibilità: per Polo, fermate T2 e Vamba a 1,2 m/s il client ottiene gli stessi job di F06 che alimentano la mappa (stesso job_id).
  - Ombra: i metri in ombra del client (R01 il 15 luglio alle 12:00, R02 il 15 settembre alle 12:30, caso vegetazione LiDAR tipico) coincidono con i tratti in ombra della mappa allo stesso istante, entro 0,5 m.
  - Scenari: filare -0,55 minuti al sole su R01 e pensilina da 0% a 40% d'ombra, come in F08.

## Benchmark

- Turni: primo giro circa 265 s per 21 domande (28 chiamate), secondo giro circa 125 s per 7 seguiti (11 chiamate).
- Correttezza al primo tentativo: 5 errori su 39 chiamate.
  - 2 non voluti per trovare gli scenari (`invalid_params` senza `scenario_ids`, `unknown_id` con un id inventato). Gli id veri arrivano dai candidati dell'errore.
  - 3 attesi: ora ambigua (11), più destinazioni (18), pesi (20b).
  - Nessun errore di schema.
- Scelte non dichiarate dall'utente e prese dal client: velocità 1,2 m/s (3, 9, 10), soglie 5/10/15, passo d'ombra 1 m e 5 minuti, ostacoli con vegetazione LiDAR. Il client le ha sempre dichiarate nella risposta.

## Difetti corretti in questa fase

- La descrizione dello schema di `compare_scenarios` diceva "Indicare source_id oppure snapshot_id" (copiata da `inspect_dataset`). Ora descrive le due forme del confronto.
- La descrizione di `compare_scenarios` diceva "ordinamento solo se si danno i pesi", ma il servizio respinge sempre i pesi. Ora dice che non c'è ordinamento e che i pesi danno `outside_capability`.

## Difetti aperti

1. Nessun tool elenca gli scenari: il client li trova solo dagli errori (già aperto su Pisa).
2. Lo schema accetta fino a 20 destinazioni, il motore una sola. Manca l'accessibilità verso "almeno una" di più destinazioni (già aperto su Pisa).
3. L'accessibilità dà quote e totale, non il conteggio dei civici raggiunti: il client moltiplica per 3.296 (già aperto su Pisa).
4. Con `obstacles = buildings_trees_and_lidar_vegetation` il manifest registra `buildings_and_trees` più i casi `veg_lidar_*`. È voluto (così il motore chiede i casi), ma il client lo legge come un errore.
5. Il risultato di `compute_shadow` è pesante (geometria completa e 9 casi) e non dice se l'orario è in ora legale o solare. Manca un campo per scegliere fra le due 02:30 del cambio d'ora (già aperto su Pisa).
6. In `compare_scenarios` il prefisso delle metriche (`sc1_`, `sc2_`) dipende dalla posizione nella lista, non dall'id dello scenario.
7. In `compare_scenarios` le varianti di S1 danno intervalli di larghezza zero: da verificare se è un risultato vero o un difetto.
8. Il replay è solo da riga di comando (`service/cli.py replay`), non via MCP: alla domanda 19 il client può solo confermare la cache (già aperto su Pisa).
9. Per alcune fonti il server dà lo stato della licenza (chiara, ridistribuibile) ma non il nome formale della licenza.
10. Mancano, e il client lo dice: tempo punto-punto, fermate bus fra le destinazioni, dati di popolazione, modelli di temperatura o comfort.

Dei difetti di Pisa non si ripresenta lo scarto fra civici dell'area e civici usati: oggi i job dichiarano 3.296 civici, di cui 3.112 raggiungibili, con il motivo degli esclusi.
