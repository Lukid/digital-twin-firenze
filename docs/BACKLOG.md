# Backlog per gli agenti — pilota accessibilità e ombra

Revisione 3, 1 ottobre 2026. Leggere [PIANO.md](PIANO.md), [SPEC_ANALISI.md](SPEC_ANALISI.md) e [FONTI.md](FONTI.md). Stato dei task: [STATO.md](STATO.md) (T01-T10 e T12 consegnati, T11 preparato). Aggiunti T15-T17 dopo l'indicazione dell'utente su Padova (D11, [RIFERIMENTO-PADOVA.md](RIFERIMENTO-PADOVA.md)). **Revisione 4: nuovo pilota Firenze Novoli - Firenze Nova (D12)**, con il ciclo F qui sotto; i task T01-T12 restano come consegne del primo pilota su Pisa.

## Regole di esecuzione

Ogni task consegna artefatti controllabili, comandi di riproduzione, esito dei controlli e lacune. Non trasformare stime in misure o decisioni aperte in preferenze dell'utente. Snapshot originari conservati; correzioni locali e scenari separati. Fonte pubblica o visualizzabile non significa automaticamente fonte redistribuibile.

Un integratore mantiene contratti e decisioni, assegna percorsi/branch e riesamina le consegne. I ruoli possono essere eseguiti in sequenza; la futura delega dipende dalle istruzioni e dai limiti dell'ambiente esecutore. Non avviare contatti con enti, acquisti o pubblicazioni senza l'autorizzazione relativa. Ricerca pubblica, audit e lavoro locale non dipendono dalla definizione di un budget completo.

## Task e dipendenze

| ID | Stato/ruolo | Dipendenze | Output concreto | Criterio di chiusura |
|---|---|---|---|---|
| T00 | Indirizzo prodotto: definito | Risposte utente | Decisioni D01–D10 nel piano | Scopo accessibilità/ombra/MCP e questioni aperte registrati |
| T01 | Audit mirato: primo incarico | T00 | `docs/audit-pilota.md`, catalogo strutturato con campioni, confronto di almeno tre zone | Rete/ingressi e geometrie disponibili identificati; altezze/chiome/accesso/licenze controllati separatamente; nessuna promessa dal solo metadato |
| T01-I | Brief utilizzatore | T00 + primi risultati T01 | Brief di una pagina con decisione, area candidata, input richiesti e feedback atteso | Ruoli di possibili interlocutori e domande concrete; nessun contatto avviato automaticamente |
| T02 | Contratti e progetto | T00 + primi risultati T01 | Schemi JSON fonti/job/scenari/tool, convenzioni ID/CRS/tempo e ADR | Campione letto da GIS, API e client senza interpretazioni discordanti |
| T03 | Acquisizione e normalizzazione | T01 + T02 | Script ripetibili, manifest/checksum, dati GIS, report di copertura/licenze | Snapshot utilizzabile; errori non sostituiscono l'ultima versione valida |
| T04 | Rete e ingressi | T02 + T03 | Grafo, destinazioni verificate, raccordi e correzioni locali | Componenti/barriere/livelli gestiti; ingressi reali e percorsi campione controllabili |
| T05 | Edifici e verde | T02 + T03 | Geometrie/quote, parametri delle chiome e copertura/incertezza per oggetto | Base e altezze coerenti; dati e stime separati; esito G2 documentato |
| T06 | Analisi A | T04 | Accessibilità, percorsi/indicatori, manifest e asset | Raggiungibile, isolato e dati insufficienti distinti; sensibilità a profilo/snapping; verifiche semantiche |
| T07 | Servizio analisi e MCP | T02 + primi output T06 | API/CLI e adattatore MCP, cache/job, strumenti e replay | Stessi calcoli fuori dal client AI; tool con input validati; numeri associati a job e dataset |
| T08 | Scena e mappa risultati | T02 + campioni T04/T05 | ADR motore grafico, scena 2D/3D, layer risultato, schede e versione leggera | Un solo motore scelto; geometrie coerenti col modello; dati non validati riconoscibili |
| T09 | Analisi B | T05 + G2 favorevole + T02 | Motore ombre, test geometrie note, metriche per percorso/superficie e sensibilità | Volumi sollevati gestiti; unione delle ombre; timezone/passaggi temporali corretti; calcolo indipendente dal renderer |
| T10 | Scenari e analisi C | T06 + T09 + T07 | Baseline congelata, scenari versionati e confronto multicriterio | Delta su condizioni comuni; beneficio per rotte campione senza flussi inventati; fattibilità ignota dichiarata |
| T11 | Validazione locale | T04/T05 + T06; T09 per ombre | Protocollo, osservazioni e report con tolleranze predefinite | Campioni rete/ombra verificati; correzioni separate dai dati di verifica; ambito di validità esplicito |
| T12 | Verifica NL e integrazione | T07 + T08 + T06, poi T09/T10 | Almeno 12 domande, replay, confronto mappa/manifest e benchmark | Ambiguità/mancanze/fuori capacità gestiti; niente risultati numerici senza esecuzione |
| T13 | Demo e handoff | T11 + T12 | Installazione/build, scheda decisione, demo, registro difetti/costi/manutenzione | Un tecnico può riprodurre e discutere una decisione; stato del feedback utente/partner registrato |
| T14 | Chat web, condizionale | Decisione D09 + T07/T12 | UI conversazionale collegata agli stessi tool/job | Stesso risultato della via MCP; costi e gestione sessioni verificati |
| T15 | Scena di presentazione, condizionale | Decisione D11 + T08; revisione ADR-T08 | Approccio di Padova: pipeline offline che precuoce la scena in riquadri con due livelli di dettaglio e hash, sito statico, motore 3D scelto dopo nuovo confronto. Estensione decisa, tetti, verde 3D con altezza chioma da CHM, nomi dei luoghi, ricerca per via, civico e particella, mobilità, temperatura delle superfici per data; risultati di T06/T09/T10 sopra la stessa scena | Prima vista e fluidità entro i target del piano anche fuori da Z2; ogni livello con fonte, data, licenza e limiti nei dati; nessun livello descrittivo presentato come risultato analitico; risultati di Z2 identici ai manifest |
| T16 | Dati ambientali ARPAT, condizionale | Decisione D11 + consenso ARPAT | Stazioni PI-BORGHETTO e PI-PASSI (e litorale) nella scena con ultimo valore, livello e data; serie storica dall'archivio orario; snapshot versionati; tool MCP `get_environment_observations` | Valori con stazione, data, unità e validazione; mancanti distinti da zero; nessuna interpolazione spaziale; licenza e consenso registrati |
| T17 | Fonti dal portale regionale via MCP CKAN, condizionale | Decisione D11 + T03 | Inventario dei livelli di T15/T16 cercati su dati.toscana.it con il server MCP CKAN; adattatori per scaricare e versionare; elenco delle lacune del catalogo (fonte fuori da CKAN o assente) con proposta di pubblicazione | Ogni livello rimanda a un dataset del catalogo o a una lacuna motivata; nessuna fonte usata senza licenza verificata |

T15 può partire prima di T11 per la parte di scena, ma la demo T13 non mostra risultati di Z2 come validati finché T11 non è chiuso. T04 e T05 possono procedere insieme dopo T02/T03. T07 e T08 possono usare campioni contrattualizzati mentre l'analisi A si completa. T09 entra solo dopo G2; in caso negativo, limitare B a un sito con rilievo locale o consegnare A con le lacune delle ombre. La preparazione del protocollo T11 inizia presto, prima di vedere i risultati finali.

G1 chiude la fattibilità di A. G2 chiude la fattibilità geometrica di B. G3 è la verifica tecnica/di campo. G4 è il riscontro di un utilizzatore reale: T13 può consegnare una demo tecnica senza partner, ma non dichiarare già dimostrato il valore nella decisione.

## Ciclo Firenze (D12)

| ID | Riuso da Pisa | Output | Criterio di chiusura |
|---|---|---|---|
| F01 Audit e riquadro (consegnato il 5/10/2026, [audit-firenze.md](audit-firenze.md); riquadro approvato il 9/10, D13) | metodo T01 | Riquadro di 1,5-2 km² fra Novoli e Firenze Nova; destinazioni (scuole, università, fermate del tram, Careggi se nel raggio); inventario delle fonti dal portale regionale con il server MCP CKAN e lacune; confronto con i gemelli esistenti | Riquadro e destinazioni motivati; licenza di ogni fonte verificata (Life Escapos è CC BY-NC 4.0) |
| F02 Contratti (consegnato il 9/10/2026, [ADR-F02](../contracts/ADR-F02.md)) | T02 | Estensione di `contracts/` a più aree (`aoi_id`, baseline per area) | Pisa e Firenze validano con gli stessi schemi |
| F03 Acquisizione (consegnato il 9/10/2026, [REPORT-F03](../pipeline/REPORT-F03.md)) | T03 | Snapshot di alberi, civici, barriere, rifugi climatici, edifici, DTM e DSM LiDAR 2023, OSM, GTFS tram e bus | Manifest con sha256; T17 applicato |
| F04 Rete e ingressi | T04 | Grafo pedonale; barriere architettoniche censite come attributi | Percorsi campione e casi vietati controllabili |
| F05 Edifici e verde | T05 | Altezze edifici da DSM 2023; alberi censiti con altezza e chioma da LiDAR, verificate sui 50 alberi Life Escapos | Chiome misurate e stimate separate; scarto sul campione dichiarato |
| F06-F10 Analisi | motori T06, T09, T10 | Accessibilità, ombre, scenari sul nuovo riquadro | Stessi test dei motori, nuovi casi |
| F07 Servizio MCP | T07, T12 | Server con più aree; domande di T12 ripetute su Firenze | Replay e confronto con la mappa |
| F11 Campo | T11 | Protocollo e punti per Firenze | Come T11 |
| F15-F17 | T15-T17 | Scena sul modello di Padova, dati ARPAT di Firenze, fonti dal portale | Come T15-T17 |

Ordine: F01, poi F02 e F03, poi F04 e F05 in parallelo, poi analisi e servizio. T15 può partire dopo F03.

## Primo incarico pronto da assegnare

> Leggi piano, specifiche e fonti. Esegui T01 su Pisa. Confronta almeno tre zone candidate rispetto a destinazioni, rete pedonale, accessi, dati edifici/quote/verde, licenze e possibilità di verifica sul posto. Usa il MCP CKAN se disponibile e API dirette/adattatori per le altre fonti. Non installare servizi globali o avviare contatti esterni senza necessità/autorizzazione. Per ogni fonte distinguine esistenza, accessibilità tecnica, contenuto valido e riuso. Salva metadati/campioni con timestamp e checksum. Consegna una proposta motivata del pilota, un caso A riproducibile come obiettivo, condizioni minime per B e lacune con alternative concrete. Non scrivere l'intera applicazione durante l'audit.

Output minimo di T01:

- Tre aree confrontate con evidenze e una raccomandazione, senza attribuire interesse a enti non consultati.
- Una scuola/sede/fermata candidata con ingresso da verificare e una famiglia di origini esplicita.
- Fonte candidata per rete e sua completezza; eventuale necessità di rilievo attraversamenti/marciapiedi.
- Percentuale di edifici con altezze documentate o piano per determinarla sul campione; disponibilità di chiome separata dalla sola posizione degli alberi.
- Condizioni di riuso, download e campione per ciascuna fonte ammessa; query con zero risultati registrate come tali, non come prova di assenza.
- Dimensione degli input e stima del lavoro successivo aggiornata con i risultati dell'audit.

## Brief degli altri ruoli

**GIS rete:** costruisci T04 preservando accessi, attraversamenti, livelli e componenti; documenta snapping e correzioni. Controlla percorsi consentiti e almeno un caso vietato; non certificare accessibilità universale quando mancano attributi.

**GIS geometrie/ombre:** costruisci T05/T09 dalla specifica; separa quote misurate e stimate, chiome e tronchi, volumi pieni e sospesi. Consegna casi semplici verificabili, convergenza e sensibilità. Se G2 fallisce, proponi un sito controllabile e una riduzione di scopo.

**Backend/MCP:** implementa funzioni deterministiche condivise fra CLI/API/MCP, strumenti tipizzati, job e manifest. Il modello risolve la domanda e spiega risultati eseguiti. Limita area e costo dei job e restituisci la mancanza degli input invece di inventarli.

**Client:** implementa la scena scelta, i risultati e il confronto A/B sullo stesso modello, con date/fonti/ipotesi e stato di validazione. La resa non produce autonomamente le metriche delle ombre. Verifica schede, URL condivisibili, modalità leggera e coerenza con i manifest.

**Revisore:** riproduci le consegne e verifica contenuto e metodi contro fonti e campo, oltre alla build. Esegui domande ambigue/non supportate; confronta delta degli scenari, risultato mappa e output numerico. Registra scostamenti e ambito di validità; non approvare un dato soltanto perché appare plausibile.
