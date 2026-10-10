# Revisione del codice di Firenze Novoli

Data: 10 ottobre 2026. Codice esaminato: HEAD `2c13fd8`, senza modifiche iniziali ai file tracciati. Revisione mirata, test locali e aggiornamento della documentazione. Nessuna modifica ai motori, ai contratti, alla baseline o agli asset versionati.

Il progetto ha una base adatta al POC: calcoli separati dalla scena, contratti condivisi, risultati tracciati e test sui metodi. La suite esistente passa. Sei problemi restano aperti; i test attuali non coprono i casi che li mostrano. La validazione geometrica è la prima correzione da fare.

## Perimetro e valutazione

Lettura mirata di acquisizione e normalizzazione (`pipeline/lib.py`, `fonti_firenze.py`, `norm_firenze.py`), rete e ingressi, geometrie di Firenze, accessibilità, ombre, scenari, servizio, contratti, costruzione della scena e interfaccia. Esclusi motori di Pisa non mantenuti, librerie vendorizzate e contenuti scaricati da terzi. Non è una verifica riga per riga di tutto il repository.

| Dimensione | Valutazione | Evidenza |
|---|---|---|
| Sicurezza e robustezza degli ingressi | Da rafforzare | Input con proprietà aggiuntive respinti; geometrie formalmente valide possono però causare eccezioni non gestite (R1). API limitata a 127.0.0.1, senza autenticazione. |
| Correttezza | Buona sui casi coperti, incompleta ai margini | Determinismo, sole, geometrie sintetiche e replay verificati; sensibilità con penalità incoerente (R3), risultati incompleti per S5/S6 nel servizio (R5). |
| Prestazioni e concorrenza | Adeguate al POC locale, non qualificate per più utenti | Scena statica e alberi istanziati; calcoli sincroni, limiti per combinazioni, collisione nelle scritture concorrenti (R2). Nessuna prova di carico eseguita. |
| Manutenibilità | Accettabile | CLI, API e MCP condividono il nucleo; rete e geometrie sono riusate dai motori. Report aggiornati per eliminare riferimenti operativi superati. Cache e ricostruzione della scena richiedono maggiore robustezza (R4, R6). |

## Difetti aperti

P1 = da correggere prima di affidare il servizio a input liberi degli utenti. P2 = difetto da correggere nel consolidamento del POC. Stato al 10 ottobre 2026, dopo la revisione: tutti e sei i difetti corretti, con un test ciascuno.

- R1: `_validate` del motore ombre controlla tipo (LineString per `path`, Polygon o MultiPolygon per `surface`), validità e misura positiva di ogni ricevitore; il servizio risponde `invalid_params`. Vale anche per gli scenari, che passano dallo stesso motore. Cinque casi in `service/test_service.py`. Hash del motore aggiornato in `scenarios/firenze_novoli/baseline.json` con nota; confronto S1/S2/S5/S6 identico al versionato.
- R2: `_write` usa un temporaneo con nome univoco; test con otto scritture concorrenti in `service/test_service.py`.
- R3: ogni riga conserva `attesa_s`, cioè la penalità accumulata nel costo; quote e percentili per velocità ricalcolati riga per riga. Analisi rigenerata con `analysis/run.sh`: quote e geojson invariati; gli estremi bassi dei percentili del profilo ridotto salgono fino a 0,3 minuti (Polo `travel_time_p50`: da 12,39 a 12,47). Hash del motore aggiornato in `scenarios/firenze_novoli/baseline.json` con nota; confronto S1/S2/S5/S6 rieseguito identico al versionato.
- R4: il servizio calcola un'impronta della cache con gli hash del codice dei motori e del servizio, più dimensione e data di geometrie, vegetazione LiDAR, grafo e origini. Se l'impronta cambia, cancella job, manifest, confronti e alias in cache; gli scenari degli utenti restano. Gli job_id non cambiano. Vale anche per R3: dopo una correzione dei motori il servizio non restituisce più risultati vecchi. Test in `service/test_service.py`.
- R5: il servizio riporta `aree_attesa` nel riepilogo e i delta `scN_attesa_s5_…` e `scN_attesa_s6_…`; test su S5 in `service/test_service.py`.
- R6: la scena si costruisce in una cartella temporanea e sostituisce gli asset solo a costruzione riuscita; test di fallimento in `test_build.py`. Asset ricostruiti identici byte per byte.

### R1 · P1 · Geometrie ammesse dallo schema fanno fallire il calcolo

Riferimenti: [schema dei ricevitori](../contracts/schemas/mcp.schema.json), [geometrie comuni](../contracts/schemas/common.schema.json), `shadow/ombre.py:332`, `:367`, `service/core.py:338`, `:546`.

Lo schema ammette tutte le geometrie comuni per entrambi i valori di `kind`. Il motore controlla `kind`, ma non la corrispondenza con il tipo geometrico, la validità topologica o lunghezza e area positive. `run_tool` non intercetta tutte le eccezioni risultanti.

Prova: con punto `[679800, 4851600]`, data `2026-07-15`, ora `12:30` e metodo `geometric_ray`, tutti questi ricevitori superano `core.validate`:

- `kind=path`, LineString con due punti identici: `GEOSException`.
- `kind=path`, Point: `TypeError`.
- `kind=surface`, Polygon con quattro punti identici: `ZeroDivisionError`.

La prova chiama il vero nucleo, sostituendo solo la scena e la proiezione delle ombre con una scena vuota per isolare l'errore e ridurre il costo. Nessun dato reale viene modificato.

Effetto: il servizio non restituisce l'errore strutturato previsto; l'API può interrompere la risposta. Correzione minima: validare tipo, validità e misura positiva nel motore condiviso, prima di campionamento e divisioni. Restituire `invalid_params` dal servizio. Aggiungere questi casi a `service/test_service.py` e ai test del motore.

### R2 · P2 · Due scritture della stessa cache condividono il temporaneo

Riferimenti: `service/core.py:203`, `:260`, `:345`, `:480`, `:525`; `service/api.py` usa `ThreadingHTTPServer`, `service/mcp_server.py` esegue il nucleo tramite `asyncio.to_thread`.

`_write` usa sempre `p.with_suffix(".tmp")`. Due richieste contemporanee dello stesso job possono scrivere lo stesso temporaneo. Dopo la prima sostituzione, la seconda non trova più il file.

Prova: due thread chiamano `_write` sullo stesso percorso in una cartella temporanea; una barriera sincronizza l'ingresso in `Path.replace`. Una scrittura termina con `FileNotFoundError`. La sostituzione atomica protegge la singola lettura, ma il nome fisso non protegge le scritture concorrenti.

Effetto: una richiesta può fallire anche con input validi. Correzione minima: temporaneo univoco nella stessa cartella, poi sostituzione atomica, con pulizia in caso di errore. Verificare il helper e i suoi chiamanti; non serve introdurre una coda per correggere questa collisione.

### R3 · P2 · Sensibilità alla velocità incoerente con la penalità di attraversamento

Riferimenti: `analysis/accessibilita.py:80`, `:164`, `:284`.

Il costo del cammino ripartisce la penalità in proporzione alla frazione di arco attraversata. Le quote di sensibilità applicano invece una penalità intera per ogni arco contato. Gli intervalli dei percentili scalano inoltre tutto il tempo, comprese le attese, con la velocità.

Prove:

- Caso sintetico: attraversamento di 100 m, percorso sulla metà, velocità 1 m/s, penalità 10 s. `_costo` dà 55 s. A 1,4 m/s, sullo stesso percorso, sono circa 40,71 s. Alla soglia di 0,72 minuti l'estremo alto della quota vale 0, mentre dovrebbe valere 1: `_aggrega` usa 10 s invece di 5 s.
- Caso reale: Polo, profilo `ridotta_0_8_senza_scale`. L'estremo basso di `travel_time_p50` è 12,39 minuti; ricalcolando a 1,4 m/s sui medesimi percorsi e mantenendo le attese è 12,47 minuti, con gli arrotondamenti delle righe.

Effetto: intervalli di quote, conteggi e percentili non coerenti con il costo dichiarato. I valori centrali calcolati dal cammino minimo non sono oggetto di questo difetto. Correzione minima: conservare la penalità effettivamente accumulata e usarla in tutte le sensibilità; ricalcolare i percentili sulle righe, senza scalare un percentile già aggregato. Aggiungere una prova su un attraversamento parziale.

### R4 · P2 · L'alias della cache ombre non identifica tutti gli input

Riferimenti: `service/core.py:312`, `:327`; confronto con `scenarios/scenari.py:320` e con l'hash della vegetazione nel job di `shadow/ombre.py`.

La chiave veloce del servizio comprende richiesta, versione del motore ombre e dimensione/data di modifica del file delle geometrie. Non comprende il file separato della vegetazione LiDAR né la versione della logica di composizione degli scenari.

Prova statica e isolata: cambiando `O.VEG_GPKG`, `_alias_key` resta identica per una richiesta con vegetazione. La cache degli scenari considera invece anche l'impronta della vegetazione. La prova non altera i file reali e non simula una ricostruzione completa.

Effetto: dopo una ricostruzione che cambia la vegetazione ma lascia invariato il file degli edifici/alberi, il servizio può restituire il vecchio risultato prima di interrogare il motore, anche dopo un riavvio. Correzione minima: includere nell'alias tutte le dipendenze effettive, anche la composizione degli scenari. Verificare l'invalidazione su file temporanei; aggiungere poi una prova di integrazione con dati ricostruiti. A dati congelati invariati il difetto non modifica i risultati verificati oggi.

### R5 · P2 · Il servizio perde il beneficio delle pensiline S5 e S6

Riferimenti: `scenarios/confronto.py` produce `aree_attesa`; `service/core.py:416`, `:516` considerano solo `area_attesa_polo`.

Il confronto locale contiene i risultati delle aree di attesa di S5/S6. Il servizio li omette sia nel riepilogo `scenarios` sia nei `deltas`, riportando invece l'area storica di S2. Il limite era già segnalato in F08, ma mancava nello stato operativo del servizio.

Prova: `confronto.confronta([S1, S2, S5, S6], parallelo=False)` riproduce i risultati versionati usando i job di ombra in cache. Per S5, a luglio in punta, `sfc_fi_attesa_s5` passa da 0 a 0,3996; `_compatta` elimina `aree_attesa`.

Effetto: un client del servizio può ricevere soltanto delta nulli per una pensilina che ha un beneficio sulla propria area di attesa. Correzione minima: portare tutte le aree di attesa nel riepilogo e nelle metriche, mantenendo il campo storico di S2 per compatibilità. Verificare S5/S6 in `service/test_service.py` e aggiungere domande al prossimo giro NL.

### R6 · P2 · Una costruzione interrotta lascia la scena senza i vecchi asset

Riferimenti: `scene/firenze_novoli/build.py:820`, `:829`.

La costruzione cancella i file `*.json.gz` prima di caricare e preparare gli input. Se uno dei passaggi fallisce, l'indice precedente resta, ma gli asset cui fa riferimento sono stati eliminati o sostituiti solo in parte.

Prova: cartella temporanea con un asset e un indice precedenti, `build.main()` con `--out` su quella cartella e `terreno()` sostituito con un errore di input. Dopo l'errore l'asset è sparito e l'indice esiste ancora. Nessun asset del progetto è stato toccato.

Effetto: una ricostruzione fallita rende inutilizzabile la scena precedente. Correzione minima: costruire e verificare un pacchetto in una cartella temporanea, poi sostituire il pacchetto completo con possibilità di ripristino. Aggiungere la prova di fallimento a `test_build.py`.

## Verifiche eseguite

- `make lint`: passato.
- `make test`: passati rete, geometrie, scena, servizio, contratti, accessibilità, scenari, ombre e verifica NL. Contratti: 49 esempi validi accettati, 25 non validi respinti. Scenari: 16 controlli passati. NL: 28 domande archiviate, 14 job, 11 replay passati.
- `pipeline/.venv/bin/python pipeline/validate_records.py`: passato.
- Accessibilità: ricalcolati in memoria i quattro profili delle sei destinazioni, le prove sugli ingressi del Polo e i limiti di snapping 20/40/60 m. Quote e job dei profili coincidono con `analysis/firenze_novoli/riepilogo.json`.
- Percorsi: ricalcolati R01-R10 e V01-V02 con `accessibilita.calcola`.
- Scenari: rieseguita l'aggregazione del confronto S1/S2/S5/S6 e delle varianti, usando la cache di ombra esistente; risultati identici al confronto versionato. Non rifatto il calcolo completo delle ombre degli scenari senza cache.
- Casi limite R1/R2/R3/R5/R6 riprodotti; R4 verificato sulla composizione della chiave, senza modificare gli input reali.

Il test NL controlla e riproduce il registro già esistente: non è un nuovo giro di domande a un agente. Le modifiche successive a quel registro restano da verificare con un nuovo client.

## Documentazione allineata

- F04: default dell'area, ingressi, fermate e percorsi attuali.
- F06: risultati dopo D19/D20, sei destinazioni e 24 manifest, sensibilità del Polo e limiti.
- F08: S1 versione 3, effetti su entrambi i percorsi, varianti e test attuali.
- F09: decisione implementata, dimensione del pacchetto e comportamento degli asset opzionali.
- F10: sette ingressi del Polo, stato della verifica NL e difetti del servizio.
- STATO e README: collegamento alla revisione e priorità operative.

## Limiti della revisione

Nessun download, installazione, commit o pubblicazione. Nessun nuovo giro NL, verifica nel browser, prova su telefono o sopralluogo. Non ricostruita l'intera pipeline. Nessuna scansione completa dei segreti o audit delle dipendenze: la valutazione di sicurezza riguarda il codice e i confini osservati. Le licenze sono state controllate come metadati e contratti locali, senza nuova verifica sui siti delle fonti.

Per il POC i risultati centrali verificati restano riproducibili. Prima di un uso operativo servono le correzioni indicate e la validazione sul posto di ingressi, marciapiedi e ombra reale.

## Controllo dei numeri nei documenti

Dopo il commit `f836d95` ogni numero aggiunto dalla revisione a F04, F06, F08, F09 e F10 è stato confrontato in automatico con i file di risultato (`riepilogo.json` e manifest di F06, `confronto.json` e scenari di F08, `percorsi_campione.json` di F04, indice della scena). Tutti coincidono, tranne quattro lunghezze dei percorsi campione di F04 (R02, R03, R04, R06): erano prese dal ricalcolo di F06 e differivano di 0,1 m. Ora riportano i valori di `percorsi_campione.json`.
