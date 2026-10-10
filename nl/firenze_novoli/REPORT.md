# F11: verifica delle domande in linguaggio naturale su Firenze Novoli

Data: 10 ottobre 2026, secondo giro dopo D19 (7 ingressi del Polo) e D20 (fermata T2 San Donato - Università, R01 da lì). Controllo: `service/.venv/bin/python nl/firenze_novoli/test_nl.py` (circa 30 s, TUTTO OK, anche senza la cache del servizio). Non validato sul posto.

## Come è stata fatta

- Client: un agente nuovo, senza accesso al repository, che parla con il vero server MCP `dt-firenze` via stdio attraverso `mcp_client.py` (comandi `tools` e `call`). Il server non è attivo nella sessione principale, per questo serve il client.
- Contesto iniziale dato nel prompt: `aoi_firenze_novoli`, `bas_firenze_novoli_20261009`, EPSG:7791, Europe/Rome. Nessun id di destinazione o di scenario.
- 21 domande nel primo giro (`giro1.json`), 7 seguiti con le risposte di chiarimento dell'utente (`giro2.json`). Ogni voce riporta chiamate, argomenti, esito, job_id e risposta.
- Rispetto al primo giro cambia solo la domanda 8: "le due fermate" diventa "le fermate della T2" (ora sono tre). La domanda 9 resta uguale: cambia l'atteso, R01 parte da San Donato - Università (429 m).
- I seguiti sono rimasti quelli scritti nel primo giro. Due non combaciano del tutto con la domanda di chiarimento del client: 11b (il client chiedeva quale delle due 02:30, l'utente cambia orario) e 15b (il client aveva proposto il confronto con e senza alberi, l'utente lo accetta). Il client ha risposto lo stesso.
- Categorie: dati e licenze (1, 2), accessibilità (3, 4, 5, 6b, 7b, 8, 16b, 18b), ombra (9, 10, 11b, 15b), scenari (12, 13, 20, 20b), ambigue (6, 7, 11, 15, 18, 20), fuori capacità (14, 15, 16, 17), limiti (18b, 21), ripetibilità (19).
- Una sola esecuzione, domande scritte da chi conosce il sistema: misura la traduzione in chiamate, non la robustezza con utenti reali.
- I manifest dei job nuovi del client (ombra e scenari) sono versionati in `nl/firenze_novoli/manifest/`; quelli di accessibilità sono gli stessi di F06 in `analysis/firenze_novoli/manifest/`. I manifest del primo giro sono stati tolti prima di rifare il giro, così il server non poteva restituirli. Nessun job_id di ombra o di scenario coincide con quelli del primo giro.

## Esito rispetto ai criteri

- Nessun numero senza esecuzione: 28 risposte su 28 hanno un job per ogni percentuale e minuto. Unica eccezione dichiarata dal client: alla domanda 3 dà "circa 930 civici" come quota del job per 3.296, perché il job non dà conteggi. Il test lo ammette solo se la domanda ha un job.
- Ambiguità: il client si ferma e chiede in tutti i casi (origine e due scuole Vamba alla 6, tre fermate del tram alla 7, 02:30 del 25 ottobre alla 11, alberi "davanti al Polo" alla 15, destinazioni e forma del risultato alla 18, criterio alla 20). Con la risposta dell'utente completa il calcolo. Alla domanda 13 ha scelto la fermata Guidoni Barsanti dello scenario S2 e l'ha dichiarato.
- Persone e civici: alle domande 3, 7, 7b e 18b il client dice che i civici non sono persone e che manca un dato di popolazione.
- Fuori capacità: temperatura, rimozione di alberi, Careggi (fuori area), SQL, ordinamento con pesi. Nessuna stima inventata; il client propone cosa si può calcolare.
- Limiti: sei destinazioni in una chiamata danno `limit_exceeded`. Il client ripiega su un job per destinazione e dice che l'unione ("almeno una") non è disponibile.
- Replay: 11 job su 11 identici, anche senza la cache del servizio. Esclusi i 3 confronti di scenari, che non hanno replay.
- Confronto con la mappa:
  - Accessibilità: per Polo (7 ingressi), le tre fermate T2 e Vamba a 1,2 m/s il client ottiene gli stessi job di F06 che alimentano la mappa (stesso job_id).
  - Ombra: i metri in ombra del client (R01 il 15 luglio alle 12:00, R02 il 15 settembre alle 12:30, caso vegetazione LiDAR tipico) coincidono con i tratti in ombra della mappa allo stesso istante, entro 0,5 m.
  - Scenari: filare S1 -0,37 minuti al sole su R01 il 15 luglio 12:30-13:30 (F08: -0,36, differenza di arrotondamento), -0,41 a settembre; pensilina S2 da 0% a 40,1% d'ombra sull'area di attesa, come in F08.

## Risposte principali

- Polo entro 10 minuti a 1,2 m/s: 28,2% dei civici (17,3% a 5, 53,8% a 15), mediana 14,2 minuti.
- Fermate T2 entro 10 minuti: Torre degli Agli 39,3%, Regione Toscana 29,7%, San Donato - Università 23,8%. Gli intervalli di velocità (0,8-1,4 m/s) si sovrappongono.
- R01 il 15 luglio alle 12:00: 50,8% in ombra con i soli edifici, 51,3% con alberi e vegetazione LiDAR. R02 il 15 settembre alle 12:30: 48,3% con la vegetazione, 47,2% con i soli edifici.

## Benchmark

- Turni: circa 200 s in tutto (primo giro circa 150 s per 21 domande e 32 chiamate, secondo giro circa 50 s per 7 seguiti e 17 chiamate). Senza cache all'inizio; ogni chiamata fra 0,4 e 4,2 s.
- Correttezza al primo tentativo: 4 errori su 49 chiamate.
  - 1 non voluto per trovare gli scenari (`unknown_id` con un id inventato). Gli id veri arrivano dai candidati dell'errore.
  - 3 attesi: ora ambigua (11), più destinazioni (18b), pesi (20b).
  - Nessun errore di schema.
- Scelte non dichiarate dall'utente e prese dal client: anno 2026, velocità 1,2 m/s, soglie 5/10/15, soli edifici alla domanda 9, vegetazione LiDAR alla 10, scuola primaria Vamba. Il client le ha sempre dichiarate nella risposta.
- Il client registra anche chiamate ripetute solo per rileggere un risultato dalla cache (3, 12, 13, 18b).

## Difetti aperti

1. Nessun tool elenca gli scenari: il client li trova solo dagli errori (già aperto su Pisa). Chiuso il 10 ottobre dopo il giro: tool `list_scenarios`.
2. Lo schema accetta fino a 20 destinazioni, il motore una sola. Manca l'accessibilità verso "almeno una" di più destinazioni (già aperto su Pisa). Chiuso il 10 ottobre dopo il giro: più destinazioni in un job danno l'accessibilità verso almeno una.
3. L'accessibilità dà quote e totale, non il conteggio dei civici raggiunti: il client moltiplica per 3.296 (già aperto su Pisa). Chiuso il 10 ottobre dopo il giro: metriche `served_count_*`.
4. Lo schema di `compare_scenarios` ha ancora il campo `weights`, che il servizio respinge sempre: la descrizione ora lo dice, lo schema no.
5. Il risultato di `compute_shadow` è pesante (geometria completa e 9 casi) e non dice se l'orario è in ora legale o solare. Manca un campo per scegliere fra le due 02:30 del cambio d'ora (già aperto su Pisa).
6. Il replay è solo da riga di comando (`service/cli.py replay`), non via MCP: alla domanda 19 il client può solo confermare la cache (già aperto su Pisa).
7. Per alcune fonti il server dà lo stato della licenza (chiara, ridistribuibile) ma non il nome formale della licenza.
8. Il server non dice la linea del tram: il client non può confermare che le tre fermate siano della T2.
9. Intervalli di sensibilità a un solo lato: a 0,8 m/s il limite basso coincide con il valore (domanda 5); per Torre degli Agli il valore a 10 minuti è 39,3% e il limite alto 39,6%.
10. Mancano, e il client lo dice: tempo punto-punto, fermate bus fra le destinazioni, dati di popolazione, modelli di temperatura o comfort, rimozione di alberi.

Non riosservati in questo giro, perché il client non ha fatto le chiamate che li mostravano: `obstacles` registrato come `buildings_and_trees` con la vegetazione LiDAR, prefisso `sc1_`/`sc2_` delle metriche legato alla posizione, varianti di S1 con intervalli di larghezza zero.

Dei difetti di Pisa non si ripresenta lo scarto fra civici dell'area e civici usati: oggi i job dichiarano 3.296 civici, con il motivo degli esclusi (168 senza aggancio alla rete, 15 vietati, 1 isolato).

## Verifica durante la revisione del codice

Il 10 ottobre `make test` ha rieseguito `test_nl.py`: registro delle 28 domande e 11 replay passati. Non è un nuovo giro di domande a un agente; le valutazioni e il benchmark sopra restano riferiti al giro descritto. I difetti 1-3 sono coperti dai test del servizio ma non da un nuovo giro NL. Altri difetti riprodotti, tra cui la sensibilità con penalità e i risultati di S5/S6 omessi, sono nella [revisione del codice](../../docs/REVISIONE-CODICE-20261010.md).
