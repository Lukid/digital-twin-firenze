# T10: scenari e confronto (analisi C)

Data: 1 ottobre 2026. Redatto dall'agente T10 e salvato dall'integratore. `bash scenarios/run.sh` (circa 6 min la prima volta, 23 s con la cache): test scenari 10/10; `service/test_service.py` TUTTO OK; contratti 39 validi e 19 non validi respinti (rieseguiti dall'integratore). Risultati `not_validated_locally`.

## Baseline (`baseline.json`, `bas_z2_20261001`)

- Fissa 14 snapshot con sha256, grafo (pkl e regole), GeoPackage delle geometrie, parametri delle chiome, 2.224 civici, percorsi campione, motori (ombre 0.2.0, accessibilità 0.1.0, con sha del file), job di riferimento di T06 e condizioni.
- Condizioni: 15 settembre, 42 orari, 4 fasce, passo 1 m e 5 min, 1,2 m/s.
- Ricevitori: 7 percorsi (R01, R03-R08), R01 spostata di ±3 m, area di attesa della fermata Pellico (8x4 m), 37 archi più usati (primi 20 verso Battisti e verso Pellico).
- `verifica_baseline()` ricalcola tutti gli hash; un test controlla che resti invariata dopo scenari e confronto.

## Scenari (`scn_*.json`, schema valido)

- Tipi ammessi: nuovo albero (dimensioni di classe, classe `scenario`) e pensilina. Il resto è `outside_capability`. Fattibilità sempre "ignota" (`feasibility_checked` rifiutato).
- Interventi dentro edifici o sulla carreggiata senza marciapiede (semilarghezza 3 m, ipotesi), o entro 1 m da un arco molto usato: segnalati, non bloccati.
- **S0**: nessun intervento.
- **S1**: filare di 7 alberi di classe "medio" tipica (11 m, chioma 6 m, imposta 2,5 m), interasse 8 m, a 3 m dall'asse, su R01 fra 236 e 296 m. Regola: massima esposizione media 12:30-13:30, poi media 8-18, poi primo tratto lungo il percorso. Metà di R01 è al sole pieno a mezzogiorno: 162 finestre a pari merito, la scelta del tratto è arbitraria entro quel gruppo. Lato scelto col sole delle 13:00 (ipotesi). Varianti: chioma minima, massima, lato opposto.
- **S2**: pensilina 6x2 m (intradosso 2,5 m, tetto 3,0 m) centrata sulla piattaforma della fermata Pellico (PI4390), parallela al marciapiede.

## Risultati (delta rispetto a S0; intervallo = altezze edifici e, su R01, lato ±3 m)

- Baseline R01 a mezzogiorno (12:30-13:30): ombra 0,458, minuti al sole 5,715.
- S1 su R01 a mezzogiorno: ombra +0,056 [+0,012; +0,056], minuti al sole -0,58 [-0,58; -0,12]: discrimina.
- S1 su R01 8-18: ombra +0,033, minuti -0,35 [-0,38; -0,19]. Al mattino non discrimina; al pomeriggio incerto [-0,57; 0].
- S1, sensibilità a mezzogiorno: chioma minima -0,35 min, massima -0,84, lato opposto -0,03. Il lato è l'incertezza dominante.
- S1 sui tratti più usati verso Pellico a mezzogiorno: 4 archi toccati, 434 civici-minuti evitati (somma per arco, non civici distinti). Verso la Battisti nessun beneficio.
- S2 su R01: -0,008 min [-0,008; 0], non discrimina.
- S2 sull'area di attesa a mezzogiorno: ombra 0 → 0,31; mattina invariata; 8-18 da 0,21 a 0,33.
- S2 sui tratti: effetto solo nella fascia 8-18 (30 civici-minuti su un arco usato da 2.148 civici).
- Accessibilità: delta 0, nullo per costruzione; verificato con hash di grafo, regole e origini invariati e ricalcolo dei job (stesso `job_id` e metriche di T06).
- Nessun punteggio unico: `ordina()` richiede pesi espliciti. Con un indicatore alla volta l'ordine cambia (area di attesa → S2, gli altri → S1).
- La pensilina cade sul marciapiede più usato (2.148 civici): il passaggio libero non è modellato.

## Test (`test_scenari.py`)

Baseline invariata dopo gli scenari; S0 contro S0 = delta 0; un albero aggiunto non riduce mai l'ombra né aumenta i minuti al sole; stesso input = stesso `scenario_id` e `job_id`; condizioni non comuni respinte (data, ricevitori, velocità, geometrie, baseline, passo); fattibilità sempre ignota; segnalazioni; accessibilità invariata; asset di scena.

## Tool MCP

- `create_local_scenario`: id = hash del contenuto, scenari salvati e immutabili, risposta con `warnings` e `feasibility`.
- `compute_shadow` con `scenario_id` (`obstacles = buildings_and_scenario`): cache con sha dello scenario, replay funzionante.
- `compare_scenarios`: per manifest (delta con intervallo e `discriminates`, respinto se le condizioni non sono comuni) o per scenari (multicriterio, ordinamento solo con `weights`). Job e manifest validi. Il confronto per scenari usa la cache di `scenarios/`, altrimenti richiede minuti.
- `mcp.schema.json` esteso, 9 esempi nuovi. `DT_SCENARIOS_DIR` sposta gli scenari creati dal servizio (usato nei test).

## Asset (`scenarios/out/`)

Ombre di S0, S1, S2 alle 8:00, 13:00 e 16:30 (EPSG:4326); interventi di S1 e S2 (punto, chioma, poligono); `confronto_riepilogo.json`.

## Limiti

- La baseline esclude gli alberi esistenti: un albero nuovo non è confrontato con le chiome già presenti nello stesso punto.
- Percorsi sull'asse della rete, lato del marciapiede ignoto.
- Gli alberi di scenario entrano nel motore d'ombra sostituendo temporaneamente una funzione di `shadow/ombre.py` (non thread-safe): da sostituire con un parametro esplicito del motore.
- S0 differisce da `shadow/out` di circa 0,01-0,04% sull'area d'ombra (riferimento solare dal baricentro dei ricevitori).
- Pesi dei tratti = civici SIT, non persone; nessun flusso misurato. Dimensioni e posizioni degli interventi sono ipotesi, senza crescita né anni.
- Job di confronto sincrono, senza avanzamento.
