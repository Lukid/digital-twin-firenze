# Verifica del prompt con l'MCP via HTTP

Data: 17 ottobre 2026, sul worker VPS. Prova del compito 3 di [BRIEF-AGENTE-F1.md](../../docs/BRIEF-AGENTE-F1.md): le domande di F11 rifatte da un agente nuovo con il testo di [PROMPT-AGENTE.md](../../service/PROMPT-AGENTE.md) e il server `dt-firenze` raggiungibile solo via HTTP. Non validato sul posto.

## Come è stata fatta

- Server: `service/mcp_server.py --http` su `127.0.0.1:8793`, in sola lettura, limiti di default (30 chiamate al minuto, un calcolo lungo alla volta), cache vuota all'inizio.
- Client: un agente nuovo, istruito solo con il prompt (la parte fra le due righe di `PROMPT-AGENTE.md`) e con il divieto di leggere il repository. Chiamava gli strumenti con `nl/firenze_novoli/mcp_client.py` e `DT_MCP_URL`.
- Domande: le 21 del primo giro di F11 (`giro1.json`) e i 7 seguiti del secondo (`giro2.json`), dati come messaggi successivi dell'utente. 28 voci in tutto.
- Registro: [giro_remoto.json](giro_remoto.json), con chiamate, argomenti, esito, job_id e risposta per ogni voce. I manifest non sono versionati: i job_id dipendono dai dati del worker (sotto).
- Dati: quelli ricostruiti sul worker il 17 ottobre ([REPORT-AGENTE-F1.md](../../docs/REPORT-AGENTE-F1.md), compito 0). Stesse metriche della baseline per accessibilità e ombre, job_id diversi, confronto fra scenari rifiutato con `incompatible_baseline`.

## Esito

- 64 chiamate in circa 10 minuti: 56 riuscite, 8 errori.
  - 3 attesi: ora ambigua del 25 ottobre (11, `invalid_params`), pesi nel confronto (20b, `outside_capability`), un `limit_exceeded` alla 9 perché l'agente ha lanciato due `compute_shadow` insieme; riprovato, riuscito.
  - 5 `incompatible_baseline` su `compare_scenarios` con la baseline (12, 13, 20): effetto dei dati del worker, non del trasporto. Il codice mancava nel prompt: aggiunto dopo la prova.
  - Nessun errore di schema, nessun id inventato.
- Nessun numero senza un job riuscito della stessa conversazione.
- Ambiguità: l'agente si è fermato a chiedere in tutti i casi del primo giro (6, 7, 11, 15, 16, 18, 20) e ha completato con il seguito.
- Civici e persone: alle domande 3, 7, 7b, 8 e 18b dice che sono civici, non persone, e che manca un dato di popolazione. La parola "persone" compare solo in negazioni.
- Fuori capacità: temperatura (14), rimozione di alberi (15), Careggi (16), SQL (17), classifica con pesi (20, 20b). Risponde "non lo so" e propone cosa si può calcolare.
- Schede delle fonti: alle domande 1 e 2 usa `get_source_card` (indice e schede) oltre a `list_approved_sources`, e riporta data del dato e licenza dalle schede.

## Confronto con il giro del 10 ottobre (stdio)

Numeri uguali:

| Voce | 10 ottobre | 17 ottobre via HTTP |
|---|---|---|
| 3 Polo entro 10 minuti | 28,2% (21,8-34,0%) | 28,2% (21,8-34,0%), 930 civici |
| 4 Torre degli Agli entro 10 minuti | 39,3% (30,1-39,6%) | 39,3% (30,1-39,6%) |
| 5 Vamba primaria, 0,8 m/s, 15 minuti | 39,0% | 39,0% |
| 6b Vamba primaria 5/10/15 minuti | 15,5% / 39,0% / 54,0% | 15,5% / 39,0% / 54,0% |
| 7b Regione Toscana entro 10 minuti | 29,7% (13,5-40,5%) | 29,7% (13,5-40,5%) |
| 8 tre fermate T2 | 39,3% / 29,7% / 23,8% | 39,3% / 29,7% / 23,8% |
| 9 R01 15 luglio 12:00 | 50,8% edifici; 51,3% con vegetazione | 50,8% edifici; 51,3% con vegetazione |
| 10 R02 15 settembre 12:30 | 48,3% con vegetazione, 47,2% edifici | 48,3% con vegetazione, 47,2% edifici |
| 11b R01 25 ottobre 14:30 | 45,7% edifici (40,1-49,6%) | 45,7% edifici (40,1-49,6%) |
| 15b peso degli alberi su R01 | 50,8% → 51,3% | 50,8% → 51,3% |
| 16b Polo, mediana e 90° percentile | 14,2 e 18,9 minuti | 14,2 e 18,9 minuti |
| 19 ripetibilità | stesso job dalla cache | stesso job dalla cache; un secondo calcolo con la sola soglia di 10 minuti (job nuovo) dà lo stesso 39,3% |

Differenze:

- job_id: tutti diversi da quelli versionati, per i dati del worker (impronta del grafo e degli alberi nell'hash). Esempio: Polo `job_8c9ce69401b3ae91` invece di `job_9b2e74744a8d2865`.
- 12 e 20 (filare S1): senza `compare_scenarios` con la baseline, l'agente ha ricostruito l'effetto con quattro `compute_shadow` (baseline, S1 e varianti di chioma, 12:00 e 13:00) e `compare_scenarios` per manifest, e l'ha dichiarato. Risultato: ombra su R01 dal 39,9% al 45,0%, -0,34 minuti al sole (da -0,14 a -0,51 con le varianti). Il 10 ottobre, fascia 12:30-13:30 dal confronto fra scenari: dal 29,5% al 35,4%, -0,37 minuti. Ordini di grandezza coerenti, orari diversi: non è un confronto alla pari. Il prompt ora chiede di non ricostruire il confronto senza dichiararlo.
- 13 (pensilina S2) e parte della 20: "non lo so, per ora", perché l'ombra sull'area di attesa passa solo dal confronto fra scenari. Il 10 ottobre: dallo 0% al 40,1%.
- 18b: oggi esiste l'accessibilità verso almeno una destinazione (chiusa dopo F11): 67,8% dei civici entro 10 minuti da almeno una delle sei (60,1-72,4%). Il 10 ottobre il client aveva ricevuto `limit_exceeded` e risposto con le sole quote separate.

## Difetti visti

1. `compare_scenarios` con la baseline non funziona su una macchina con dati ricostruiti: corretto che rifiuti, ma per il servizio remoto servono gli stessi dati della baseline (domanda 1 del report dell'agente).
2. `compute_shadow` registra `obstacles: buildings_and_trees` nei parametri anche quando la richiesta è `buildings_trees_and_lidar_vegetation` o `buildings_and_scenario`; le metriche con vegetazione e scenario ci sono. È il difetto già segnalato in REPORT.md e non riosservato il 10 ottobre.
3. Il limite di un calcolo lungo alla volta si vede quando l'assistente lancia chiamate in parallelo: il prompt ora lo dice.

## Benchmark

- 28 voci, 64 chiamate, circa 10 minuti con la cache vuota all'inizio (il 10 ottobre: 49 chiamate in circa 200 s, senza i calcoli d'ombra aggiuntivi delle domande 12 e 20).
- Errori non voluti al primo tentativo: 1 (`limit_exceeded` per chiamate parallele), più i 5 dovuti ai dati.
