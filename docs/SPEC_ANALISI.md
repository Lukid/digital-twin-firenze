# Specifica del pilota: accessibilità, ombra e strumenti MCP

Revisione 1, 1 ottobre 2026. Requisiti del [piano](PIANO.md); nomi di campi e strumenti proposti per l'implementazione, non API già disponibili. Quote, precisione, servizi e pesi finali seguono l'audit. Le scelte numeriche sotto sono parametri iniziali di esperimento, non dati osservati su Pisa.

## 1. Caso A — accessibilità pedonale

Domanda concreta: quali origini nell'area pilota raggiungono gli ingressi selezionati entro soglie concordate, e quali risultano penalizzate da rete, attraversamenti o barriere?

### Input e metodo

- Origini: punti espliciti o griglia campione su superfici pedonali/residenziali documentate. Non interpretare una griglia come distribuzione reale dei residenti.
- Destinazioni: ingressi verificati di scuole, sedi universitarie e fermate selezionate; conservare la relazione con l'edificio/servizio. Il centroide del fabbricato non sostituisce un ingresso.
- Rete: segmenti e nodi pedonali con attraversamenti, scale, ponti, cancelli, accessi e livelli. Incroci geometrici su piani diversi non implicano connessione. Annotare le restrizioni e le informazioni mancanti.
- Profilo: velocità dichiarata, penalità e restrizioni documentate. Per iniziare confrontare, ad esempio, 0,8/1,2/1,4 m/s come ipotesi di sensibilità, senza attribuirle a gruppi demografici. Soglie candidate 5/10/15 minuti da confermare con il caso d'uso.
- Collegamento origini/ingressi alla rete: distanza e geometria del raccordo registrate; limite di snapping derivato dalla qualità dei dati. Non attraversare barriere per collegarsi al nodo più vicino.
- Calcolo: cammino minimo pesato per lunghezza/tempo. Conservare anche le componenti disconnesse: rimuoverle per convenienza può nascondere proprio le criticità cercate.

Output: distanza di rete, tempo stimato, itinerario, servizi raggiungibili e stato di ogni origine. Distinguere `reachable`, `unreachable_on_verified_network`, `insufficient_data` e `outside_model`. Per una mappa di copertura partire da punti/segmenti raggiungibili; l'inviluppo delle isocrone non deve riempire automaticamente fiumi o blocchi non attraversabili.

Metriche ammesse: quota delle origini campione servite, distribuzione dei tempi, distanza del raccordo e deviazione rispetto alla distanza diretta. Popolazione servita solo quando si dispone di dati demografici con una metodologia di allocazione esplicita. Non affermare un deficit di qualità/frequenza delle fermate usando soltanto la distanza pedonale.

Un profilo adatto a persone con mobilità ridotta richiede informazioni su gradini, rampe, pendenze, larghezze e ostacoli. Dove assenti, fornire un'analisi della completezza anziché certificare l'accessibilità universale.

## 2. Caso B — ombra geometrica

Domanda concreta: quanto cambia l'ostruzione della radiazione solare diretta su una superficie o un percorso, a date e orari dichiarati, introducendo specifici volumi?

### Input e metodo

- Terreno e quote coerenti; edifici come volumi con quota di base e altezza documentate. Tetti semplificati ammessi solo se sufficienti alla domanda.
- Alberi: posizione, quota della base, altezza totale, altezza d'inizio chioma, raggio/forma della chioma, fonte e intervalli dove stimati. Il diametro del tronco non è il diametro della chioma.
- Pensiline/ombreggiamenti: geometria, altezza e copertura. Modellare lo spazio sottostante; un DSM di superficie piena non rappresenta automaticamente un pannello sospeso.
- Geometria ricettrice: superficie della piazza oppure lato effettivamente percorso del marciapiede, con elevazione. Se si dispone solo dell'asse stradale, indicare l'approssimazione e verificarne l'effetto prima di una raccomandazione.
- Tempo: data e fascia in `Europe/Rome`, conversione documentata verso il motore solare; gestire ora legale e convenzioni d'azimut. Un caso iniziale può usare una giornata estiva e ore di ingresso/uscita utili al servizio; non fissarle senza il contesto del caso.
- Motore: posizione del sole e intersezione dei raggi con gli ostacoli; preferire metodi controllabili su CPU per il pilota. Confronto GIS raster per edifici/terreno e prova di consistenza della scena 3D. Le ombre del renderer sono una visualizzazione.

Per il primo scenario gli ostacoli opachi possono essere trattati come tali. Una chioma idealizzata opaca fornisce un confronto geometrico dichiarato; non è automaticamente una stima dell'attenuazione reale di un albero. Introdurre trasmissività/leaf-on/leaf-off solo con parametri documentati e mantenere separate ombra binaria e attenuazione della radiazione. Se la baseline ignora alberi esistenti, denominarla esplicitamente "ombra da edifici documentati" ed evitare una percentuale di ombra totale presentata come reale.

### Indicatori

Per un percorso statico `L`, al tempo `t`, calcolare `shade_fraction(t) = lunghezza(L ∩ unione_ombre(t)) / lunghezza(L)`. L'unione evita di contare due volte le sovrapposizioni. Per una superficie usare la stessa definizione con aree e lo stesso perimetro di confronto.

Metriche: frazione ombreggiata, metri esposti, durata stimata dei tratti al sole e variazione baseline/scenario. Per l'esposizione durante una camminata usare l'istante effettivo di percorrenza di ciascun tratto in funzione dell'orario di partenza e della velocità: una mappa statica alle 14:00 non coincide necessariamente con il percorso dalle 14:00 alle 14:20.

Confrontare prima **lo stesso itinerario** nei due scenari. Un eventuale percorso alternativo più ombreggiato è una seconda analisi con deviazione e tempo extra espliciti. Un costo combinato tempo/esposizione richiede pesi visibili; non presentarlo come preferenza universale.

### Incertezza e qualità numerica

Provare passi spaziali, ad esempio 2/1/0,5 m, e temporali 15/5/1 minuti su un sottocampione; scegliere il passo in base alla convergenza dell'indicatore e alla precisione degli input, non alla risoluzione visiva desiderata. Calcolare sensibilità a intervalli delle altezze/chiome e riportare l'eventuale inversione del confronto fra scenari.

Il margine di contesto dipende dall'altezza degli ostacoli e dall'elevazione solare minima analizzata. Su terreno piano la lunghezza di un'ombra di un volume verticale è circa `h / tan(alpha)`: ai bassi angoli un contesto piccolo può troncare ombre rilevanti. Valutare questo margine e dichiarare un limite di elevazione solare dove il modello non è supportato.

Output senza promesse termiche: una maggiore copertura geometrica non è una conversione in °C, UTCI, salute o domanda pedonale. Eventuali modelli termici sono una fase distinta con specialisti e osservazioni.

Un livello di temperatura delle superfici da satellite (come nel riferimento di Padova, D11) è descrittivo: mostra °C al suolo a 100 m nell'istante del passaggio. Non entra negli indicatori d'ombra, non misura l'effetto di uno scenario e via MCP va restituito con data, risoluzione e copertura valida.

## 3. Caso C — confronto degli interventi

Snapshot baseline congelato; scenario come lista di aggiunte/rimozioni/modifiche con ID, geometria, fonte delle dimensioni e stato di ipotesi. Per alberi nuovi confrontare dimensioni della chioma proposte, senza assegnare anni di crescita non modellati.

Per sito candidato riportare: beneficio marginale sui percorsi campione, fasce/orari utili, robustezza alle incertezze, destinazioni interessate, superficie/numero degli interventi e fattibilità nota o ignota. Il sito "migliore" dipende da criteri espliciti; mostrare indicatori e sensibilità ai pesi invece di un solo punteggio non spiegato.

Non contare automaticamente una rotta campione come flusso di persone. Senza dati di domanda, i pesi delle rotte sono uniformi o ipotetici e vengono mostrati. Verifica di sottoservizi, proprietà, disponibilità di suolo, spazio radicale, manutenzione e specie affidata a tecnici prima di una decisione di intervento. La proposta del prototipo è una lista motivata di candidati.

## 4. Contratti dati

| Oggetto | Campi minimi |
|---|---|
| Fonte | `source_id`, publisher, dataset/resource URL, licenza/evidenza, content period, retrieved_at, checksum, CRS/unità, schema, controlli |
| Area | `aoi_id`, perimetro di interesse, contesto rete/ombra, motivazione dei margini |
| Rete | `graph_id`, snapshot, nodi/archi, geometria, lunghezza, restrizioni, livelli, completezza e correzioni locali |
| Destinazione | `destination_id`, categoria, nome, coordinate ingresso, fonte, stato di verifica, condizioni di accesso |
| Edificio | ID stabile/originario, footprint, quota base, altezza, metodo/fonte/incertezza, tipo di semplificazione |
| Albero/ostacolo | ID, posizione/geometria, quote e dimensioni, forma/canopy base, fonte/incertezza, parametri ottici se presenti |
| Scenario | `scenario_id`, `baseline_id`, versione, operazioni, geometrie, parametri e autore; nessuna modifica dello snapshot originario |
| Risultato | `job_id`, input versionati, parametri, metodo/versione, CRS, tempi, metriche/unità, copertura, limiti, stato validazione, asset/hash |

Versionare le correzioni sul campo separatamente dal dato originario; registrare autore, data e motivo. Non ripubblicare automaticamente modifiche in OSM o sul portale dell'ente. Formati candidati: GeoPackage per geometrie/revisione, Parquet per tabelle estese, GraphML o formato concordato per il grafo, JSON per manifest e GeoJSON/tile per output client.

## 5. Strumenti MCP proposti

MCP CKAN esterno per discovery; MCP del progetto per dati ammessi e analisi. I nomi seguenti sono contratti proposti da finalizzare in T02. Le funzioni sono condivise con API/CLI per riproduzione indipendente dal client AI.

| Tool | Input essenziale | Output |
|---|---|---|
| `list_approved_sources` | tema, area | Fonti locali ammesse, versioni e lacune |
| `inspect_dataset` | source/dataset ID | Schema, unità, extent, periodo, qualità e licenza |
| `list_destinations` | area, categoria | ID/ingressi e stato di verifica; evita nomi ambigui |
| `compute_walk_access` | baseline, origini, destinazioni, profilo, soglie | Job/risultato, metriche e asset |
| `compute_shadow` | baseline/scenario, ricevitori, date/ore, metodo | Job/risultato, copertura e incertezza |
| `create_local_scenario` | baseline, operazioni strutturate | Scenario versionato nell'ambiente di lavoro |
| `compare_scenarios` | risultati/scenari, metriche | Delta su condizioni comuni, incompatibilità segnalate |
| `get_job_status` / `get_result_manifest` | job ID | Stato, manifest e asset recuperabili |

Parametri con schema validato, ID ammessi, limiti di area/righe/tempo/memoria e caching. La creazione di uno scenario riguarda il progetto locale e non una modifica urbana o un database esterno. Nessun tool deve accettare codice arbitrario o SQL libero da una domanda naturale. Dati esterni sono contenuto da ispezionare, non istruzioni per l'agente.

I job lunghi restituiscono un ID e avanzamento; quelli oltre il limite restituiscono una spiegazione e una richiesta più piccola praticabile. Ogni domanda è associata a tool, input, output e spesa del modello dove disponibile. Il client non deve comunicare "ho calcolato" se nessun job è riuscito.

### Esempi di dialogo da collaudare

- "Quali dati possiamo usare per gli alberi di questa zona?" → fonti/lacune, senza inventare un censimento scaricabile.
- "Quali origini raggiungono questo ingresso in dieci minuti?" → profilo dichiarato, risultato A e manifest.
- "Confronta l'ombra di questo percorso alle 14:00 con due pensiline." → risolve data, area e dimensioni mancanti; scenario e B.
- "Quanto cambia l'esposizione durante la camminata?" → partenza e velocità, integrazione lungo il percorso.
- "Di quanti gradi si raffresca?" → chiarisce che il motore corrente non produce quel risultato.
- "La scuola" senza ID univoco → chiede di scegliere la destinazione prima di calcolare.
- Richiesta su area senza input sufficienti → restituisce il limite e l'alternativa, senza estrapolazione silenziosa.

## 6. Verifica e campo

Prima del campo scegliere soglie e tolleranze in relazione alla decisione. Se un delta fra scenari è inferiore all'incertezza, riportare che il confronto non discrimina in modo affidabile.

| Controllo | Procedura |
|---|---|
| Rete | 5–10 percorsi rappresentativi e almeno un caso di accesso negato; verifica ingressi, lati pedonali e attraversamenti |
| Allineamento | 20 punti/oggetti distribuiti, fonte di riferimento e incertezza del rilievo; una foto da telefono non certifica precisione centimetrica |
| Geometria ombre | Casi semplici noti: terreno libero, prisma con lunghezza/direzione calcolabile, sovrapposizioni, pannello sospeso e chioma sollevata |
| Campo ombre | Almeno 12 osservazioni distribuite fra siti/orari, georiferimento, timestamp con timezone, condizioni di cielo e oggetti rilevati; tenere osservazioni di verifica separate da quelle usate per correggere il modello |
| Indicatori | Ripetizione, convergenza spaziale/temporale e sensibilità alle quote, chiome e velocità |
| Scenari | Scenario senza cambiamenti produce delta nullo entro tolleranza numerica; confronto respinto se baseline/tempi incompatibili |
| MCP | Almeno 12 domande: discovery, analisi, ambiguità, dati mancanti e richieste fuori capacità; replay del job da input conservato |
| Resa | Layer/metriche nella mappa coincidono con manifest e report; nessuna differenza nascosta fra volumi visuali e analitici |

La disponibilità dell'utente o di un tecnico per il campo resta aperta. Senza campo o riferimenti alternativi adeguati, consegnare calcolo e report come risultato non ancora validato localmente.
