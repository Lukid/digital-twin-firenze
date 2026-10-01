# Pisa Digital Twin — piano di fattibilità e realizzazione

Data: 1 ottobre 2026. Revisione 2, basata sulle risposte dell’utente. **Direzione definita; area pilota, interlocutore, budget e calendario ancora aperti.** Nessuna applicazione implementata o pubblicata.

## 1. Risultato proposto

Realizzare un prototipo di supporto alle decisioni per Comune di Pisa e potenziali partner tecnici o di ricerca. Integrare una città riconoscibile in 3D con dati aperti, analisi geografiche riproducibili e interrogazione in linguaggio naturale tramite MCP. L'utente accetta edifici semplificati; investire nel dettaglio dove incide sulla risposta analitica.

Domande prioritarie indicate dall'utente:

1. Dove valutare alberi o ombreggiamenti sui percorsi verso scuole, fermate e università?
2. Quali zone hanno accesso peggiore a servizi considerando i percorsi pedonali effettivi?
3. Come cambia l'ombra su una strada o piazza fra ipotesi di intervento?

La prima domanda unisce accessibilità e ombra; le altre due ne costituiscono moduli verificabili separatamente. **Proposta di sequenza tecnica: accessibilità pedonale → ombra su pochi percorsi → confronto di interventi.** Il primo caso da presentare a un partner sarà scelto dopo audit dei dati e individuazione di un interlocutore interessato.

Una vista pubblica più semplice è un'evoluzione successiva. Per il prototipo servono soprattutto un caso utile, dati controllabili e una restituzione comprensibile da un tecnico o decisore.

Padova resta un riferimento di esperienza visiva. La demo non è stata visitabile interattivamente in questa sessione: nessuna ipotesi di equivalenza del backend o dei modelli. Il fotorealismo integrale, l'analisi energetica dei tetti e le simulazioni specialistiche di traffico/allagamento sono fuori dallo scopo iniziale.

| Risultato | Fattibilità con il perimetro scelto | Limite principale |
|---|---|---|
| Scena 3D riconoscibile | Alta | Accuratezza dei volumi documentata per oggetto |
| Accessibilità pedonale | Buona su area verificata | Attraversamenti, accessi, barriere e qualità della rete |
| Ombra geometrica prima/dopo | Buona con altezze e ostacoli sufficienti | Chiome, pensiline e dettagli mancanti; incertezza delle quote |
| Priorità degli interventi | Utile come confronto multicriterio | Pesi, domanda pedonale e fattibilità di piantumazione da concordare |
| Raffrescamento in gradi e comfort termico | Da sviluppare con specialisti | Non deducibile dalla sola percentuale di ombra |

Un'animazione d'ombra non verifica il calcolo. Il prototipo deve usare un motore analitico separato dalla resa grafica, con input e risultati versionati.

## 2. Decisioni e questioni aperte

| ID | Stato | Decisione |
|---|---|---|
| D01 | Confermato dall'utente | Primo pubblico: Comune e partner tecnici/ricerca; utilizzo interno per demo e feedback |
| D02 | Confermato dall'utente | Casi prioritari: accessibilità pedonale e ombreggiamento; caso concreto scelto dopo audit e interlocutore |
| D03 | Parzialmente definito | Zona limitata di Pisa; selezione fra almeno tre candidate, senza assegnare ora un quartiere |
| D04 | Confermato dall'utente | Volumi semplificati; precisione adeguata alla domanda; dettaglio di altezze/chiome per le ombre |
| D05 | Aperto | Budget, calendario, tempo di revisione umana e capacità di rilievo locale |
| D06 | Confermato come impostazione | Sviluppo nostro + agenti AI; competenze GIS e di dominio per analisi specialistiche; nessun partner già confermato |
| D07 | Proposta tecnica | Snapshot riproducibili per il pilota; aggiornamenti periodici; tempo reale non richiesto |
| D08 | Aperto | Licenze del codice, diffusione del prototipo e successiva vista pubblica |
| D09 | Requisito confermato, modalità aperta | Interrogazione in linguaggio naturale di catalogo e analisi via MCP; MCP nel client AI come proposta iniziale, chat web da decidere |
| D10 | Confermato dall'utente | Fonti, aggiornamento e limiti visibili in ogni risultato |

### Selezione del pilota

Confrontare almeno tre zone candidate senza promettere copertura prima di averla verificata. Valutare: presenza delle destinazioni utili; rete e ostacoli rilevabili; dati edificio/verde sufficienti; possibilità di controlli sul campo; interesse di un possibile utilizzatore; dimensione gestibile. Ogni criterio ha evidenze, non un punteggio inventato dall'agente.

Dimensione di lavoro proposta: circa 0,5–2 km², 2–3 destinazioni, 5–10 percorsi rappresentativi e un corridoio o piazza per il primo confronto d'ombra. È un obiettivo di dimensionamento da adattare all'audit, non un'area già approvata. Acquisire anche il contesto necessario fuori dal perimetro: la rete non deve produrre falsi vicoli ciechi e gli edifici esterni possono proiettare ombre nell'area.

Un possibile interlocutore va identificato fra uffici comunali di mobilità/verde/SIT o referenti universitari e di ricerca. Preparare un brief con una decisione, un percorso reale e il risultato atteso. Nessun contatto esterno è stato avviato. L'esperimento tecnico può procedere anche prima di un incontro; l'utilità decisionale resta da validare.

## 3. Cosa sappiamo sui dati

Le verifiche e i collegamenti sono in [FONTI.md](FONTI.md). I metadati grezzi e un campione geografico sono in `research/`.

- Il portale comunale dichiara 663 dataset; la homepage mostra anche risorse riferite al 2010–2017. Il numero non misura attualità, unicità o utilità.
- Il catalogo comunale usa StatPortal e il SIT espone servizi ArcGIS: CKAN non copre direttamente tutte queste fonti.
- Le API CKAN di Regione Toscana e dati.gov.it hanno risposto. La ricerca testuale `Pisa` ha restituito rispettivamente 130 e 147 risultati, comprendendo provincia, riferimenti indiretti e dati fuori area: non sono conteggi dei dataset utili alla città.
- Il servizio comunale delle piste ciclabili ha restituito un conteggio di 144 feature e una geometria GeoJSON campione. La data del contenuto e le condizioni di riuso non sono ancora accertate.
- Il dataset regionale `rt-oraritb` include una risorsa GTFS per Autolinee Toscane. Non sono ancora verificati calendario attuale, copertura delle linee pisane, geometrie e integrità del feed.
- Lo ZIP ARPAT 2025 è scaricabile e contiene serie di Pisa-Borghetto e Pisa-Passi. Un CSV campione ha 8.760 righe orarie oltre all'intestazione, con indicatore di validità; ciò non implica 8.760 misure valide.
- Sono documentati DTM per la provincia e rilievi LiDAR regionali. Copertura, anno, precisione, quote verticali e download per Pisa richiedono un audit.

Priorità delle fonti: dato ufficiale locale/regionale con contenuto verificato; fonti nazionali pertinenti; OpenStreetMap per integrazioni dichiarate. In presenza di versioni discordanti conservarne la provenienza, evitando fusioni silenziose. Un endpoint pubblico non basta a dimostrare una licenza di redistribuzione.

## 4. Prima versione proposta

### Nucleo comune

1. Mappa 2D/3D di un'area pilota, edifici, rete pedonale, destinazioni e verde disponibile.
2. Schede con fonte, periodo, geometria disponibile e incertezza.
3. Percorsi/tempi di accesso calcolati sulla rete, con attraversamenti e barriere controllati.
4. Confronto fra baseline e uno/due scenari locali di ombreggiamento, se superato l'audit delle quote.
5. Interrogazione via strumenti MCP e restituzione di risultati geografici utilizzabili nella mappa.
6. Esportazione di una scheda di decisione con mappa, indicatori, ipotesi, risultati e punti ancora da verificare.

### Tre dimostrazioni da costruire

| Caso | Input | Output verificabile | Condizione |
|---|---|---|---|
| A — Raggiungibilità | Origini, ingressi reali, rete, profilo pedonale e soglie | Distanze/tempi, origini non raggiungibili e carenze di collegamento | Accessi e rete validati sul pilota |
| B — Ombra | Edifici/ostacoli, terreno, area o percorsi, data/ore | Quota ombreggiata e metri/minuti esposti, baseline e scenario | Quote, copertura degli ostacoli e metodo sufficienti |
| C — Candidati interventi | A + B, siti proposti, geometrie delle nuove chiome/pensiline | Beneficio marginale, sensibilità e fattibilità nota/ignota | Criteri espliciti; nessuna presunta domanda pedonale non misurata |

Il caso A valuta l'accesso spaziale: vicinanza a una fermata non significa qualità del servizio. Frequenze e tempi di trasporto richiedono un modulo GTFS successivo. Il caso C individua candidati da valutare con tecnici, senza certificare la possibilità di piantumare o il comfort termico.

Se mancano chiome o altezze adeguate, consegnare A e un confronto B su un sito rilevato localmente. Non rinviare tutto il progetto per ricostruire tutta Pisa. La vista pubblica e la chat web possono essere sviluppate dopo aver validato il percorso di analisi via MCP.

## 5. Architettura proposta

### Dati e analisi

Separare quattro componenti: acquisizione delle fonti, dataset approvati/versionati, motore di analisi deterministico, presentazione/MCP. Flusso: fonti → snapshot grezzo → controlli e normalizzazione → dati analitici → calcolo con parametri espliciti → risultato versionato → mappa e risposta in linguaggio naturale.

Proposta iniziale: Python per preparazione e analisi; GeoPackage/Parquet e grafo persistito per il piccolo pilota; una API locale con job/cache per i calcoli; un adattatore MCP sopra le stesse funzioni. PostGIS solo quando query multiutente e volumi lo giustificano. OSMnx/NetworkX sono candidati per la rete, da collaudare con i dati del pilota. Documentazione ufficiale in [FONTI.md](FONTI.md).

Per l'ombra confrontare un calcolo su volumi 3D con un riferimento GIS per il caso edifici. GRASS `r.sunmask` è un candidato di riferimento raster, con limiti da considerare per chiome sollevate e pensiline. Non ridurre chiome o pensiline a una colonna piena senza dichiarare l'approssimazione. I risultati analitici devono essere coerenti con gli oggetti mostrati.

### Interfaccia

TypeScript e un solo motore cartografico. MapLibre è il candidato iniziale per un atlante a scala locale con estrusioni; Cesium è il candidato se terreno, quote o modelli richiedono una scena geospaziale più articolata. Il confronto è breve, su un campione reale, e non blocca l'analisi indipendente. La decisione segue la qualità dei dati e i requisiti dell'ombra; un motore grafico non diventa il motore scientifico per il solo fatto di mostrare ombre.

### Linguaggio naturale e MCP

Il [MCP CKAN AgID](https://github.com/AgID/ckan-mcp-server) serve per scoprire e ispezionare fonti. In questa sessione non è esposto come tool; le ricerche sono state svolte via API CKAN. Il catalogo comunale e il SIT richiedono anche adattatori StatPortal/ArcGIS.

Il MCP geografico del progetto espone funzioni come elenco dati approvati, ispezione schema, percorsi, accessibilità, ombra, creazione di scenari locali, confronto e recupero manifest dei risultati. Il modello traduce la domanda in parametri e spiega l'output; il motore calcola numeri e geometrie. Non affidare al modello la ricostruzione di un dato mancante o l'esecuzione di SQL/codice libero sul sistema.

Ogni risposta analitica include ID del calcolo, dataset/versioni, parametri, metodo, metriche con unità, limiti e asset geografici. Domande ambigue su destinazione/data devono essere risolte prima del calcolo. La mappa e i controlli restano usabili senza chiamare un modello. Il costo AI appartiene alle interrogazioni e allo sviluppo, non al caricamento ordinario delle tile.

Modalità iniziale proposta: usare un client AI con MCP; aggiungere una chat nel prototipo se l'utente la considera necessaria già nella prima dimostrazione. Le due superfici devono usare lo stesso motore e gli stessi manifest.

### Contratti e aggiornamento

[SPEC_ANALISI.md](SPEC_ANALISI.md) definisce requisiti analitici, metriche, dati e strumenti. Fissare ID stabili, CRS metrico, datum verticale, timezone `Europe/Rome`, periodi del contenuto, checksum, schema/versione, unità e classificazione misurato/derivato/stimato/scenario.

Ogni analisi usa snapshot identificabili. Aggiornamento deterministico e report dei cambiamenti; conservare l'ultima versione valida quando la fonte fallisce. Baseline e scenario condividono snapshot, origini, date e metodo, cambiando solo gli interventi dichiarati.

## 6. Fasi, risultati e punti di decisione

Stime di pianificazione in giornate complessive di lavoro equivalente, inclusa revisione. Non sono scadenze, preventivi o tempo macchina degli agenti. Questa revisione include analisi pedonale e MCP: la precedente stima di un semplice atlante non copriva questi requisiti.

| Fase | Stima | Risultato | Condizione per procedere |
|---|---|---|---|
| 0 — Audit e scelta pilota | 4–6 giorni | Tre zone confrontate, dataset campione e lacune; brief per un interlocutore | Un'area adatta ad A; condizioni di B separate |
| 1 — Fondazioni | 5–8 giorni | Contratti, pipeline, grafo e campione 3D | Percorsi validi e geometrie allineate |
| 2 — Primo caso e MCP | 8–12 giorni | A, strumenti MCP, mappa dei risultati e scheda esportabile | Calcolo riproducibile e prove NL superate |
| 3 — Ombra e scenari locali | 10–18 giorni | B, prima versione C, confronto baseline/scenari e sensibilità | Quote/chiome adeguate o rilievo locale; nessun risultato quantitativo sul territorio non verificato |
| 4 — Collaudo e dimostrazione | 5–8 giorni | Controlli sul campo, report qualità, feedback e demo | Criteri analitici soddisfatti; scostamenti documentati |

Totale indicativo del pilota completo: **32–52 giorni equivalenti**, esclusi tempi di attesa per dati e disponibilità esterne. Prima dimostrazione di accessibilità con MCP: **17–26 giorni equivalenti** prima del collaudo finale. Se B non supera l'audit, limitarlo a un sito controllato. Una chat web immediata aumenta il lavoro: stimarla separatamente dopo la decisione D09.

Punti di decisione: G1 rete e accessi sufficienti; G2 quote/ostacoli adeguati all'ombra; G3 risultati riprodotti e verificati sul campo; G4 feedback di un utilizzatore. Senza interlocutore il risultato resta un prototipo tecnico e non una soluzione già validata nell'uso.

## 7. Budget e sostenibilità

Budget e scadenze sono aperti. L'audit locale e la stesura dei contratti possono partire senza acquisti; account a pagamento, installazioni esterne o pubblicazioni richiedono una scelta concreta quando necessaria.

Separare sviluppo/AI, revisione GIS e di dominio, rilievi locali, infrastruttura, aggiornamenti e possibile chat web. La precedente riserva di 20–100 euro/mese riguardava una demo leggera: non include la spesa dei modelli, le analisi asincrone o il lavoro specialistico e non è un tetto promesso.

Prima di acquistare servizi misurare su un campione: tempo e memoria per rete/ombre, volume degli asset, costo per aggiornamento e per domanda NL, cache dei risultati e traffico della demo. Stabilire un limite di spesa per fase e per job, con risultati precomputati per le demo ripetute. Il prototipo può essere dimostrato inizialmente in locale; la pubblicazione viene pianificata dopo il collaudo.

Gli agenti accelerano ricerca, connettori e implementazione. La revisione geografica, le verifiche sul campo e la validazione del significato decisionale hanno bisogno di una persona responsabile; il parallelismo non elimina questi passaggi.

## 8. Criticità e riduzioni di scopo

| Criticità | Effetto sulla decisione | Riduzione di scopo praticabile |
|---|---|---|
| Rete con accessi/attraversamenti sbagliati | Falsa raggiungibilità o falso isolamento | Verificare 5–10 percorsi e correggere il pilota con provenienza |
| Marciapiedi non rilevati | Ombra della strada diversa da quella del pedone | Rilevare il lato del percorso; dichiarare centerline come approssimazione |
| Altezze e chiome incomplete | Beneficio d'ombra incerto | A operativo; B su un sito rilevato; intervalli/sensibilità per stime |
| Censimento alberi esistente ma non disponibile | Baseline incompleta | Audit di accesso/licenza, rilievo locale o confronti limitati alle strutture documentate |
| Basemap disponibile solo come tile | Impossibilità di estrarre geometrie/quote | Individuare pacchetto vettoriale o altra fonte; non usare nomi dei layer come dati |
| Mancanza di domanda pedonale | Priorità non basata su flussi reali | Presentare pesi/utenze come ipotesi; mostrare beneficio per percorsi campione |
| Sottoservizi e spazio radicale ignoti | Un sito promettente può essere irrealizzabile | Stato fattibilità ignoto; valutazione con tecnico del verde prima di raccomandare l'intervento |
| Scenario di chioma senza modello di crescita | Beneficio futuro non temporizzabile | Confrontare geometrie a dimensione dichiarata, senza assegnare anni arbitrari |
| LLM confonde fonti, tempo o destinazione | Risposta plausibile ma non riproducibile | Strumenti con parametri/schema validati, manifest e chiarimento delle ambiguità |
| Campo non disponibile o interlocutore assente | Mancata validazione locale/decisionale | Etichettare il risultato come esperimento tecnico; registrare ciò che manca |

La priorità ambientale non è dimostrata dalla sola minore ombra. Confrontare indicatori separati e rendere visibili le preferenze del decisore.

## 9. Criteri di accettazione

Requisiti obbligatori:

- Ogni layer/risultato ha provenienza, periodo, licenza documentata e limiti; ogni stima è distinguibile da una misura.
- Destinazioni collegate a ingressi reali; nessuna connessione attraverso muri, cancelli chiusi o attraversamenti non verificati nei percorsi campione.
- Accessibilità calcolata sulla rete: origini isolate, dati mancanti e percorsi vietati hanno stati distinti.
- Baseline/scenario confrontati su stessi input, tempi, origini e metodo; delta riproducibili.
- Ombra verificata su geometrie semplici con risultato noto e con riscontri di campo; sensibilità a quote e chiome documentata. Non convertire automaticamente più ombra in gradi di raffrescamento.
- MCP: test di domande concrete, ambigue e non supportate; ogni risposta numerica rimanda a un job eseguito e a un manifest recuperabile.
- Mappa e report mostrano lo stesso risultato analitico. Rigenerazione documentata da snapshot e parametri.

Target proposti da confermare dopo il prototipo: 5–10 percorsi controllati, 20 punti/oggetti di allineamento e almeno 12 osservazioni d'ombra distribuite fra siti/orari. Prima vista utile entro 5 secondi e circa 30 fps su desktop di riferimento; su telefono modalità leggera. Le tolleranze geometriche e degli indicatori devono essere fissate prima del collaudo finale in rapporto alla decisione e alla precisione della fonte.

Il protocollo dettagliato è in [SPEC_ANALISI.md](SPEC_ANALISI.md). Se le tolleranze non sono raggiunte, restringere la validità spaziale o la precisione delle conclusioni invece di dichiarare comunque un risultato verificato.

## 10. Passaggio agli agenti

[BACKLOG.md](BACKLOG.md) contiene task, dipendenze, output e criteri per la futura esecuzione. [SPEC_ANALISI.md](SPEC_ANALISI.md) è il riferimento dei moduli e del MCP; [FONTI.md](FONTI.md) documenta le evidenze disponibili.

La direzione di prodotto è definita. Il primo incarico operativo è audit mirato + confronto delle zone candidate, senza attendere la definizione di un budget completo. Poi fissare contratti e baseline e iniziare in parallelo rete, geometrie e adattatore MCP quando gli input comuni sono stabili. Il motore delle ombre resta condizionato a G2.

Ogni agente consegna artefatti controllabili, istruzioni di riproduzione, verifiche e lacune. Un integratore mantiene i contratti comuni e le decisioni; un revisore diverso dall'autore verifica metodi e output. Nessun agente deve trasformare un requisito ancora aperto in una preferenza approvata dall'utente.
