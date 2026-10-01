# T12: verifica delle domande in linguaggio naturale

Data: 1 ottobre 2026. Controllo: `service/.venv/bin/python nl/test_nl.py` (circa 25 s, TUTTO OK).

## Come è stata fatta

- Client: un agente nuovo, senza accesso al repository, con i soli tool MCP del server `dt-pisa`. Contesto iniziale: `aoi_z2`, `bas_z2_20261001`, EPSG:7791, Europe/Rome. Questi due ID non si possono scoprire via tool e vanno nel prompt del client.
- 18 domande in un primo giro (`giro1.json`), 7 seguiti con le risposte di chiarimento dell'utente (`giro2.json`). Ogni voce riporta chiamate, argomenti, esito, job_id e risposta.
- Categorie: dati e licenze (1, 2), accessibilità (3, 4, 5b, 7, 3b), ombra (9, 11, 17), scenari (13b), ambigue (5, 6, 8, 10, 14), fuori capacità (12, 14, 15, 16), limiti (6b, 8b, 19), ripetibilità (18, 19).
- Una sola esecuzione, domande scritte da chi conosce il sistema: misura la traduzione in chiamate, non la robustezza su utenti reali.

## Esito rispetto ai criteri

- Nessun numero senza esecuzione: 25 risposte su 25. Il controllo automatico cerca percentuali e minuti nelle risposte e richiede un job.
- Ambiguità: il client si ferma e chiede in tutti i casi (stazione con 9 fermate, ora del 25 ottobre, albero non identificato, Pellico). Con la risposta dell'utente completa il calcolo.
- Fuori capacità: gradi di raffrescamento, rimozione di un albero, SQL, ospedale assente. Nessuna stima inventata; il client propone cosa si può calcolare.
- Limiti: più destinazioni in una chiamata danno `limit_exceeded`; il client ripiega su un job per destinazione e dice che l'unione non è disponibile.
- Replay: 18 job su 18 identici, anche senza la cache del servizio (manifest versionati in `nl/manifest/`, letti anche da `get_result_manifest`) (job_id, metriche, parametri). Escluso il job della domanda 19, che oggi viene respinto, e il confronto scenari, che non ha replay.
- Confronto con la mappa: a parità di destinazione, velocità e soglia, i 4 valori del client coincidono con i manifest della scena (Battisti 1,2 e 0,8 m/s, fermata Pellico 10 e 15 minuti). L'ombra non si confronta valore per valore: la mappa usa passo 1 m e 5 minuti, il client 2 m e 10 minuti; il massimo del client (90,9%, mattina) è coerente con il 91,3% della mappa nella fascia d'ingresso.

## Benchmark

- Turni: primo giro circa 120 s per 18 domande (18 chiamate), secondo giro circa 75 s per 7 seguiti (17 chiamate).
- Durata dei calcoli (dal manifest): accessibilità 0,25-0,46 s; ombra con 3 orari 2,8 s; ombra con 79 orari 16,9 s; confronto scenari 0,7 s con le ombre già in cache.
- Correttezza al primo tentativo: 2 rifiuti non voluti su 34 chiamate, entrambi per il limite di una destinazione per job, più 1 prova volontaria dell'ora ambigua (10b). Nessun errore di schema.
- Scelte non dichiarate dall'utente e prese dal client: velocità 1,33 m/s (domande 3, 7), anno 2026, passo d'ombra 2 m e 10 minuti. Il client le ha sempre dichiarate nella risposta.

## Difetti corretti in questa fase

- Soglie duplicate (`[10, 10.0]`) accettate: job nuovo e metrica ripetuta. Ora `thresholds_min` ha `uniqueItems` e la richiesta dà `invalid_params` (test in `service/test_service.py`).
- Descrizioni dello schema: velocità di riferimento 1,2 m/s, soglie della mappa `[5, 10, 15]`, passo d'ombra della mappa 1 m e 5 minuti. Con questi valori il client riusa i job della mappa invece di crearne di nuovi. Il server MCP va riavviato per vederle.

## Difetti aperti

1. Nessun tool elenca gli scenari: nel primo giro il client non ha trovato filare e pensilina (domande 12 e 13) e ha chiesto all'utente di definirli.
2. `compute_shadow` restituisce medie e minimo/massimo, non il valore per orario. La mappa ha gli asset per orario; il client no.
3. L'ora ambigua del cambio d'ora viene respinta correttamente, ma non c'è un campo per dire quale delle due si intende.
4. Lo schema accetta fino a 20 destinazioni, il motore una sola. Manca l'accessibilità verso "almeno una" di più destinazioni (caso stazione).
5. L'accessibilità dà quote e totale, non il conteggio dei civici raggiunti.
6. `inspect_dataset` dichiara 7.606 civici nell'area, i job ne usano 2.224. Il server non spiega la differenza.
7. Il replay è solo da riga di comando (`service/cli.py replay`), non via MCP: alla domanda 18 il client può solo confermare la cache.
8. Le domande dicevano "scuola Pellico": Pellico è la fermata `dst_stop_pi4390`, punto di partenza di R01. Il client l'ha segnalato correttamente.
