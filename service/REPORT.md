# T07: servizio di analisi e MCP

Data: 1 ottobre 2026. Redatto dall'agente T07 e salvato dall'integratore. Test: `service/.venv/bin/python service/test_service.py` (circa 3 s, TUTTO OK, rieseguito dall'integratore).

## Contenuto

- `core.py`: nucleo unico `run_tool(nome, args)` usato da CLI, API e MCP. Valida l'input sullo schema, calcola il `job_id`, usa la cache se il manifest esiste, applica i limiti.
- `cli.py`, `api.py` (solo 127.0.0.1, porta predefinita 8792, `POST /tools/<nome>`), `mcp_server.py` (stdio), `replay.py`, `test_service.py`, `requirements.txt`.
- `service/.venv`: SDK MCP 1.30 (la 2.x ha un'API diversa) più un `.pth` verso le librerie geografiche di `pipeline/.venv`. L'API HTTP usa solo la libreria standard.
- Cache dei job in `service/cache/` (non versionata), modificabile con `DT_CACHE_DIR` dentro il progetto.

## Estensioni ai contratti

- `compute_walk_access.input`: `profile.crossing_penalty_s` (0-120), `profile.stairs` (allowed | excluded), `entrance_ids` (1-5), `origins.kind = civici_sit_z2`.
- `compute_walk_access.output`: campi opzionali `cached`, `datasets`, `params`, `limits`, `method`, perché ogni risposta numerica deve riportare dataset, parametri e limiti.
- Esempi nuovi validi e non validi; `contracts/validate.py`: 32 validi, 12 non validi respinti.

## Tool MCP (9)

- Con motore: `list_approved_sources`, `inspect_dataset`, `list_destinations`, `compute_walk_access`, `get_job_status`, `get_result_manifest`.
- Presenti ma `outside_capability` fino a T09/T10: `compute_shadow`, `create_local_scenario`, `compare_scenarios`.
- `additionalProperties: false` su tutti gli input: niente SQL né codice libero. Errori con `isError=true` e codice `tool_error`.
- `get_job_status` e `get_result_manifest` leggono anche i job di T06 in `analysis/manifest/`.

## Test coperti

Stesso input = stesso `job_id` e cache (anche con default espliciti e chiavi in ordine diverso); 8 input non validi respinti; destinazione ambigua o mancante; ombra e scenari `outside_capability`; CLI identica a MCP; replay uguale (job nuovo e job storico di T06); server MCP avviato con un client stdio reale. Il job base 1,2 m/s sulla Battisti riproduce il `job_id` di T06 (`job_4d23232eb780b0c1`).

## Collegamento al client AI (da eseguire a cura dell'utente)

```
claude mcp add dt-pisa --scope project -- /Users/lucabaroncini/progetti/digital-twin-pisa/service/.venv/bin/python /Users/lucabaroncini/progetti/digital-twin-pisa/service/mcp_server.py
```

## Domande di esempio

1. "Quali dati abbiamo per rete pedonale e alberi a Z2?" → `list_approved_sources`; per il verde restituisce la lacuna (nessun censimento).
2. "Che campi e che licenza ha il dataset dei civici?" → `inspect_dataset` (`src_sit_civici`: licenza non dimostrata, solo uso interno).
3. "Quanti civici arrivano a piedi alla Battisti in 10 minuti a passo lento?" → `list_destinations`, poi `compute_walk_access` (0,8 m/s, soglia 10). Il risultato è una quota di civici, non di persone.
4. "Calcola l'accessibilità alla stazione" → `ambiguous_destination` con i candidati (9 fermate "PISA stazione" e Gramsci stazione): il client chiede quale.
5. "Di quanti gradi si raffresca con due pensiline?" → `outside_capability`: il motore non produce questo risultato.
6. "Rifai il calcolo del job ..." → `get_result_manifest`, e `cli.py replay <job_id>` per confrontare i numeri.

## Lacune

- Una sola destinazione per job e solo origini `civici_sit_z2`. Griglia e punti sono validi per lo schema ma danno `outside_capability`; più destinazioni danno `limit_exceeded`.
- Senza `entrance_ids` si usa l'ingresso predefinito (per la Battisti, quello probabile, dichiarato nei parametri del manifest). È la scelta che pesa di più sui risultati.
- Limiti controllati: area (massimo 4 km²), origini (massimo 50.000), durata (massimo 600 s). La memoria è dichiarata ma non applicata. Il job gira nello stesso processo, senza coda.
- Il `job_id` viene previsto prima del calcolo replicando i parametri di `analysis/accessibilita.py`; un assert dopo l'esecuzione segnala divergenze. Se T06 cambia i parametri, va aggiornato `core._prevedi_job_id`.
- `inspect_dataset`: l'extent è quello del grafo Z2, non della fonte; unità non dichiarate = "1".
- Un nome di destinazione dà sempre `ambiguous_destination`, anche con un solo candidato. `destinazioni.json` non ha ancora categorie stazione, università o ospedale.
- Il `.pth` usa un percorso assoluto: se la cartella si sposta, va rigenerato il venv.
