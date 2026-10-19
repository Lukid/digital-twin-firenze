# Gemello digitale pilota di Firenze Novoli: documento tecnico

Bozza del 17 ottobre 2026, con la sezione 7 sul caso caldo aggiunta il 18 ottobre, per un lettore tecnico della pubblica amministrazione. Descrive cosa calcola il prototipo, come, con quali dati e con quali limiti. Nessun risultato è validato sul posto.

## 1. Obiettivo

Il prototipo mostra cosa si ottiene combinando gli open data già pubblicati da Comune di Firenze, Regione Toscana e altri enti con motori di calcolo deterministici e riproducibili. Non è un modello della città completo: è un dimostratore su un'area piccola, costruito per rispondere a domande concrete di pianificazione con numeri tracciabili.

Domande a cui risponde oggi:

- quanti civici (punti d'indirizzo) raggiungono a piedi una destinazione entro 5, 10 o 15 minuti, a una velocità data;
- quanta parte di un percorso pedonale è in ombra a una data e a un'ora, e quanti minuti si passano al sole camminando;
- quanto cambia l'ombra su un percorso o su un'area di attesa con un intervento ipotetico (un filare di alberi, una pensilina).

Tre principi guidano il progetto:

1. Solo dati con licenza di riuso verificata. Ogni fonte ha una scheda con licenza, evidenza e uso consentito.
2. Ogni numero è riproducibile. Stessa richiesta e stessi dati danno lo stesso identificativo di calcolo (job) e gli stessi numeri.
3. Ogni risultato riporta fonti, parametri e limiti. Quando un calcolo non esiste, il sistema lo dice e non stima.

Il valore sta nel calcolo e nella sua tracciabilità, non nell'interfaccia. La scena 3D e il servizio di interrogazione per assistenti sono due modi di leggere gli stessi risultati.

## 2. Area di studio

- Area: Novoli - Firenze Nova, quartiere 5 di Firenze. Riquadro di circa 2,1 km² (1,5 km da ovest a est, 1,4 km da sud a nord), sistema di riferimento EPSG:7791 (RDN2008 / UTM 32N).
- Rete pedonale: riquadro più un margine di 700 m, perché un civico vicino al bordo può raggiungere la destinazione passando da fuori.
- Destinazioni dei calcoli: il Polo delle Scienze Sociali dell'Università (7 ingressi, uno per edificio), la scuola primaria e dell'infanzia Vamba, le tre fermate della tramvia T2 nell'area (San Donato - Università, Novoli - Regione Toscana, Torre degli Agli).
- Percorsi campione per l'ombra: dieci percorsi R01-R10, fra cui R01 (fermata San Donato - Università verso il Polo, 429 m) e R02 (fermata Novoli - Regione Toscana verso il Polo, 712 m).
- Origini: 3.296 civici del Comune nel riquadro.

La scelta dell'area segue tre criteri: dati comunali ricchi (censimento degli alberi, rilievo laser 2023, civici), una destinazione con molto traffico pedonale (il Polo universitario) e un tema concreto per l'estate (ombra sui percorsi dalle fermate).

## 3. Fonti e licenze

Le fonti sono 36. Le 14 della baseline congelata del 9 ottobre 2026 alimentano i calcoli; le altre servono alla scena 3D (servizi, rischio idraulico, temperatura delle superfici, qualità dell'aria). Per ogni fonte esiste una scheda leggibile da persone e da assistenti: editore, scheda del catalogo, licenza ed evidenza, data del dato, scarichi con impronta sha256, campi usati, controlli e limiti.

Regola di provenienza: la data del dato è quella dichiarata dalla fonte (per esempio la data del volo del rilievo laser). Quando la fonte non la dichiara, vale lo stato alla data di scarico. La data di modifica della scheda del catalogo non è mai usata come data del dato.

Tabella generata dalle schede delle fonti:

<!-- tabella-fonti -->
| Fonte | Editore | Licenza | Uso consentito | Data del dato | Nella baseline dei calcoli |
|---|---|---|---|---|---|
| Alberi pubblici, censimento del Comune di Firenze | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | sì |
| Civici del Comune di Firenze | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | sì |
| Censimento delle barriere architettoniche e urbanistiche, Comune di Firenze | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | dal 2013-01-01 al 2013-12-31 | sì |
| Viabilità, aree di circolazione pedonale (poligoni), Comune di Firenze | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Rifugi climatici, aree fresche (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2026-06-18 | sì |
| Rifugi climatici, biblioteche (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2026-06-18 | sì |
| Protezione civile, aree di attesa della popolazione (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2024-06-25 | no |
| Protezione civile, aree di assistenza della popolazione (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2024-06-25 | no |
| Stalli di sosta riservati ai disabili (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Aree verdi (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Aree giochi (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Aree cani (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Aree sportive (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Farmacie autorizzate (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Aree riservate alla sosta del bike sharing (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Posti auto riservati al car sharing (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Pericolosità idraulica del Piano di gestione del rischio alluvioni, a cura della protezione civile (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Aree allagate dall'alluvione del 1966 (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 1966-11-04 | no |
| Zone 30 (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Varchi dello Scudo Verde (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2025-04-01 | no |
| Piano comunale di classificazione acustica, classi acustiche (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Sezioni di censimento 2011 (Comune di Firenze) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2011-10-09 | no |
| XV Censimento della popolazione e delle abitazioni 2011, dati per sezione di censimento (Toscana) | Regione Toscana (dati Istat) | CC-BY, verificata con riserva | ridistribuzione | 2011-10-09 | no |
| Unità volumetriche del DB topografico regionale (WFS), area di Firenze | Regione Toscana | nessun identificativo dichiarato (vedere evidenza), verificata con riserva | solo prototipo interno | dal 2011-01-01 al 2011-12-31 | sì |
| DTM LiDAR 2023 del Comune di Firenze (ASCII grid 0,5 m) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2023-06-27 | sì |
| DSM LiDAR 2023 del Comune di Firenze (ASCII grid 0,5 m) | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2023-06-27 | sì |
| OpenStreetMap, estratto regionale Centro Italia (ritagliato su riquadro + 700 m) | OpenStreetMap contributors, estratto di un distributore di estratti OSM | ODbL-1.0, verificata | ridistribuzione | 2026-10-08 | sì |
| GTFS tram (GEST), Firenze | Regione Toscana / GEST | cc-by, verificata con riserva | solo prototipo interno | dal 2026-08-10 al 2026-12-30 | sì |
| GTFS Autolinee Toscane, copia di Firenze | Regione Toscana / Autolinee Toscane | cc-by, verificata con riserva | solo prototipo interno | dal 2026-10-09 al 2026-10-29 | sì |
| Fermate tram, Comune di Firenze | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2025-03-11 | sì |
| Anagrafe scuole statali 2026/27 (MIM, ripubblicata dal Comune di Firenze) | Comune di Firenze (dati MIM) | IODL-2.0, verificata con riserva | solo prototipo interno | 2026-09-18 | sì |
| Edifici scolastici della Città metropolitana di Firenze (poligoni e accessi) | Città metropolitana di Firenze | cc-by, verificata con riserva | solo prototipo interno | 2014-02-13 | sì |
| Cartografia catastale WFS (particelle e fogli), Agenzia delle Entrate, riquadro FP | Agenzia delle Entrate | CC-BY-4.0, verificata | ridistribuzione | non dichiarata: vale lo stato alla data di scarico | no |
| Landsat 8-9 Collection 2 Level-2, temperatura delle superfici (ST_B10) e QA_PIXEL, estati 2023-2026, riquadro FP | U.S. Geological Survey (copia pubblica su un catalogo di dati satellitari in cloud) | public-domain, verificata | ridistribuzione | dal 2023-06-01 al 2026-09-30 | no |
| Temperatura dell'aria giornaliera (massima e minima), stazione SIR Firenze Università TOS01001096 | Regione Toscana, Settore Idrologico e Geologico Regionale (SIR) | CC-BY-SA-4.0, verificata con riserva | ridistribuzione | 2023-01-01 | no |
| Qualità dell'aria ARPAT, dati orari 2025 della rete regionale (stazioni del comune di Firenze) | ARPAT, Agenzia regionale per la protezione ambientale della Toscana | non specificata per i dati orari (note legali ARPAT), verificata con riserva | solo prototipo interno | dal 2025-01-01 al 2025-12-31 | no |
| Aree stradali (poligoni per tronco e incrocio), Comune di Firenze | Comune di Firenze | CC-BY-4.0, verificata | ridistribuzione | 2025-05-26 | no |
<!-- /tabella-fonti -->

Note sulle licenze:

- "Verificata con riserva" indica una licenza dichiarata ma incompleta (versione CC non indicata, licenza dedotta dalla politica regionale, licenza del sito e non del dato). Queste fonti sono usate solo nel prototipo; prima di ridistribuire i dati derivati la riserva va sciolta.
- Le unità volumetriche regionali non hanno una licenza scritta sul servizio: vale la politica regionale sui dati geografici aperti. È il caso più delicato, perché le impronte degli edifici vengono da lì.
- I dati orari della qualità dell'aria non hanno una licenza specifica: le note legali dell'agenzia citano due licenze diverse. L'uso nella scena è stato deciso dichiarandole entrambe.
- Le ortofoto regionali non sono scaricabili con licenza aperta: la scena non le usa.

## 4. Motori di calcolo e metodo

Ogni motore è un modulo separato, con il suo report e i suoi test. I risultati dipendono solo dagli snapshot della baseline e dai parametri della richiesta.

### 4.1 Acquisizione e baseline

- Ogni scarico produce uno snapshot: data e ora, URL, dimensione, impronta sha256, stato della licenza e periodo del contenuto. Uno scarico fallito non sostituisce mai l'ultimo valido.
- La baseline è un elenco congelato di snapshot (uno per fonte) con le loro impronte. I calcoli dichiarano sempre la baseline usata. Una nuova baseline si crea solo con una decisione esplicita.
- Normalizzazione: tutti i dati vengono portati in EPSG:7791, con identificativi stabili e una classe per ogni attributo (misurato, derivato, stimato, ignoto).

### 4.2 Rete pedonale

- Costruita dai dati OpenStreetMap: strade percorribili a piedi, marciapiedi mappati come linee separate, attraversamenti, sentieri e scale.
- Ogni arco ha tipo, lunghezza e stato del marciapiede ("ignoto" quando non è dichiarato: nessuna inferenza).
- I civici sono agganciati all'arco più vicino entro 40 m, esclusi i tipi non percorribili; quelli senza aggancio sono contati a parte (168 su 3.296).
- Gli ingressi delle destinazioni sono punti espliciti: per il Polo un civico del Comune per edificio, per le scuole l'accesso della Città metropolitana, per le fermate la posizione del feed del gestore.

### 4.3 Accessibilità pedonale

- Per ogni civico: cammino minimo sulla rete fino all'ingresso più vicino della destinazione, tempo = lunghezza / velocità più l'eventuale penalità agli attraversamenti.
- Profilo di riferimento: 1,2 m/s, nessuna penalità, scale ammesse. Sensibilità: 0,8 e 1,4 m/s, profilo ridotto a 0,8 m/s senza scale e con 10 s per attraversamento, aggancio a 20, 40 e 60 m, ingressi presi uno alla volta.
- Con più destinazioni in una richiesta, per ogni civico conta la più vicina (accessibilità verso almeno una).
- Metriche: civici raggiunti e quota sul totale per soglia, con l'intervallo dovuto alla velocità; mediana del tempo; tratti della rete più usati, pesati per numero di civici.

### 4.4 Edifici e alberi

- Edifici: impronte delle unità volumetriche regionali (2011); altezza dal rilievo laser comunale del 2023 (modello della superficie meno modello del terreno) dentro ogni impronta. Gli edifici costruiti dopo il 2011 vengono da OpenStreetMap; quelli non più presenti nel 2023 (probabili demolizioni, 183) sono esclusi dalle ombre.
- Alberi: censimento comunale degli alberi pubblici; altezza e chioma misurate dal rilievo laser dove ci sono abbastanza celle, altrimenti stimate per specie e classe di circonferenza.
- Vegetazione senza albero censito (giardini privati, verde non censito): poligoni dal rilievo laser, trattati come volumi opachi pieni. Sono esclusi i poligoni lisci, probabili tetti non mappati.

### 4.5 Ombra sui percorsi

- Posizione del sole con l'algoritmo SPA del NREL, al centro del riquadro, in ora locale con cambio dell'ora gestito (un orario inesistente o ambiguo è rifiutato con un errore esplicito).
- Il percorso è campionato ogni metro; da ogni punto parte un raggio verso il sole e si controlla se incontra un ostacolo. Il passo temporale di riferimento è di 5 minuti.
- Casi calcolati insieme: soli edifici (con altezze minima e massima), edifici e alberi censiti (chioma minima, tipica, massima), edifici, alberi e vegetazione laser. Il risultato è un intervallo, non un solo numero.
- Con il sole sotto i 5 gradi il risultato ha uno stato esplicito e nessun numero.
- Metriche: frazione del percorso in ombra e minuti passati al sole camminando a 1,2 m/s, per orario e per fascia (per esempio 12:30-13:30).

### 4.6 Scenari di intervento

- Uno scenario è un insieme versionato di interventi aggiunti alla baseline: nuovi alberi con dimensioni di classe, pensiline con quota d'imposta e copertura.
- Il sistema segnala interventi dentro un edificio o su una carreggiata senza marciapiede. La fattibilità (sottoservizi, proprietà, codice della strada, manutenzione) non è valutata e resta sempre "ignota".
- Il confronto con la baseline avviene a parità di condizioni (stessa data, stessi orari, stessi ostacoli) e restituisce indicatori separati: ombra e minuti al sole sui percorsi, ombra sull'area di attesa, effetto sull'accessibilità. Non c'è un punteggio unico: con dei pesi il sistema risponde che il calcolo non è disponibile.

### 4.7 Riproducibilità

- Identificativo del job = impronta della richiesta canonica (strumento, input, parametri). Stessa richiesta, stesso job.
- Ogni job ha un manifest: metodo e versione, snapshot usati con impronta e licenza, parametri, metriche con classe (misurata, derivata, stimata), limiti.
- Un comando di replay riesegue un job dal suo manifest e confronta i numeri.
- I risultati in cache si invalidano da soli se cambia il codice dei motori o uno dei file di dati che leggono.

## 5. Servizio di interrogazione per assistenti

Il servizio espone i motori a un assistente basato su modelli linguistici attraverso il protocollo aperto MCP (Model Context Protocol). L'assistente non accede ai dati né al codice: può solo chiamare strumenti con argomenti validati.

Strumenti:

| Strumento | Cosa fa |
|---|---|
| `list_approved_sources`, `inspect_dataset`, `get_source_card` | fonti approvate per tema, schema e qualità di una fonte, schede delle fonti |
| `list_destinations`, `list_scenarios` | destinazioni con ingressi e stato di verifica; scenari salvati |
| `compute_walk_access` | accessibilità pedonale dai civici verso una o più destinazioni |
| `compute_shadow` | ombra su percorsi campione o geometrie, per data e orari |
| `compare_scenarios` | confronto fra baseline e scenari, o fra due calcoli d'ombra |
| `estimate_residents` | residenti stimati raggiunti entro le soglie di un calcolo di accessibilità, accanto ai civici |
| `get_route_exposure` | percorsi campione più esposti al sole in una data già calcolata; accanto all'asse, il lato della strada più in ombra come limite superiore |
| `get_shaded_access` | civici e residenti stimati che arrivano al rifugio più vicino camminando soprattutto all'ombra, già calcolati; accanto, il limite superiore camminando sul lato più in ombra |
| `get_street_side_shade` | ombra sui due lati della strada dei percorsi campione, accanto all'asse, già calcolata; prototipo da verificare sul posto |
| `get_job_status`, `get_result_manifest` | stato e manifest di un job |
| `create_local_scenario` | crea uno scenario; spento nel servizio remoto |

Regole del servizio:

- Ogni input è validato contro uno schema JSON pubblico prima del calcolo. Nessun campo libero: niente interrogazioni SQL né codice.
- Le destinazioni si indicano per identificativo. Un nome ambiguo (per esempio "la fermata del tram") produce un errore con i candidati: l'assistente deve chiedere all'utente.
- Gli errori hanno codici stabili: destinazione ambigua, identificativo sconosciuto, dati insufficienti, limite superato, calcolo non disponibile, parametri non validi, baseline incompatibile.
- Ogni risposta di calcolo riporta job, dataset, parametri, metriche e limiti.

Servizio remoto (pronto, non ancora installato):

- Trasporto HTTP del protocollo, in sola lettura: lo strumento che crea scenari risponde sempre "calcolo non disponibile".
- Limite di chiamate al minuto per client e di calcoli lunghi contemporanei, configurabili.
- Accesso con token facoltativo, letto dall'ambiente della macchina. Nessun segreto nel codice.
- Processo con utente dedicato senza privilegi e file system in sola lettura, tranne la cache.
- Un testo di istruzioni pronto da incollare nell'assistente fissa la procedura: elencare fonti e destinazioni prima di calcolare, usare solo gli identificativi restituiti, riportare job e limiti, dire "non lo so" quando il calcolo non esiste, non chiamare persone i civici.

## 6. Esempi di domande e risposte

Risposte reali di un assistente collegato al servizio, dal giro di verifica del 10 ottobre 2026 (28 domande). Ogni numero viene da un job; i job si possono rieseguire e danno gli stessi numeri.

| Domanda | Risposta (sintesi) | Job |
|---|---|---|
| Quanti civici arrivano a piedi al Polo delle Scienze Sociali in 10 minuti? | 28,2% dei 3.296 civici a 1,2 m/s (21,8-34,0% fra 0,8 e 1,4 m/s); 17,3% a 5 minuti, 53,8% a 15. Sono civici, non persone; 5,1% dei civici non calcolabile. | `job_9b2e74744a8d2865` |
| Quale fermata della T2 serve più civici entro 10 minuti? | Torre degli Agli 39,3%, Novoli - Regione Toscana 29,7%, San Donato - Università 23,8%; gli intervalli di velocità si sovrappongono. | `job_f5a4969062095f90`, `job_b83ab974753edcb9`, `job_22778e8ad5f27e8c` |
| Il percorso R01 dalla fermata al Polo è in ombra a mezzogiorno del 15 luglio? | In parte: 50,8% in ombra degli edifici (48,3-51,0% per l'incertezza sulle altezze); circa 3,0 minuti al sole su 5,95. | `job_ed5d4ccc6aab5503` |
| Quanta ombra c'è su R02 il 15 settembre alle 12:30, con la vegetazione? | 48,3% con alberi e vegetazione laser, 47,2% con i soli edifici. | `job_6c05deb15ab1344c` |
| Che effetto ha il filare di alberi previsto lungo R01? | 15 luglio, 12:30-13:30: ombra dal 29,5% al 35,4%, minuti al sole da 4,25 a 3,89 (-0,37); a settembre -0,41. Fattibilità ignota. | `job_50b4619ba9dda6d2` |
| La pensilina alla fermata dell'autobus fa ombra a chi aspetta, a luglio? | Sì: area di attesa in ombra dallo 0% al 40,1% alle 12:30-13:30 del 15 luglio. Dimensioni e posizione ipotetiche. | `job_1b99190fff812789` |
| Di quanti gradi si abbassa la temperatura lungo R01 con il filare? | Non si può dire: il servizio calcola ombra e minuti al sole, non temperature né comfort. Nessuna stima in gradi. | nessuno |
| Quanto ci si mette a piedi dall'ospedale di Careggi al Polo? | Non disponibile: Careggi è fuori dall'area e il servizio calcola tempi dai civici dell'area. | nessuno |

Esito del giro: nessun numero senza un job; l'assistente si è fermato a chiedere in tutti i casi ambigui; ha distinto civici e persone; 11 job su 11 rieseguiti con gli stessi numeri. Limite della prova: domande scritte da chi conosce il sistema, una sola esecuzione.

## 7. Il caso caldo

Domanda di partenza: dove si cammina al sole d'estate a Novoli, quanto è lontano un luogo fresco e quanto costa fare ombra. Le risposte sotto vengono dai motori della sezione 4; ogni numero rimanda al calcolo (job) o al file da cui viene. Nessuno è validato sul posto.

### 7.1 Rifugi climatici

Il Comune di Firenze pubblica un elenco di rifugi climatici: aree verdi e biblioteche aperte al pubblico. Entrano nei calcoli i 7 entro 700 m dall'area: Giardino di Piazza delle Medaglie d'Oro, Biblioteca Filippo Buonarroti, Giardino di piazza dei Cavalieri di Vittorio Veneto, Giardino di via Luigi Morandi, due giardini in via Arturo Toscanini, Giardino di piazza Giacomo Puccini. Gli ingressi sono i civici agli indirizzi dichiarati dal Comune, non verificati sul posto. Gli orari non sono nei dati: i calcoli assumono i rifugi aperti. File: `network/firenze_novoli/destinazioni.json`.

### 7.2 Accessibilità: civici e residenti

Dai 3.296 civici dell'area verso il rifugio più vicino, a 1,2 m/s (job `job_e1e75455f7511f7d`):

| Entro | Civici | Residenti stimati |
|---|---|---|
| 5 minuti | 14,2% | 15,2% (2.129) |
| 10 minuti | 39,1% | 43,6% (6.092) |
| 15 minuti | 56,4% | 59,9% (8.380) |

Tempo mediano 12,75 minuti per i civici che lo raggiungono. Fra 0,8 e 1,4 m/s la quota dei residenti a 10 minuti va dal 29,6% al 46,6%.

I residenti sono una stima, non un conteggio di persone: residenti del censimento Istat 2011 per sezione di censimento (tabella della Regione Toscana, licenza CC BY; confini del Comune, CC BY 4.0), divisi in parti uguali fra i civici di ogni sezione. Negozi e uffici contano come abitazioni; ripartendo solo sui civici neri la quota a 10 minuti è 44,0%. In tutto 13.982 residenti stimati; 70 civici stanno in sezioni senza dato. File: `analysis/firenze_novoli/residenti_rifugi.json`.

### 7.3 Ombra sui percorsi

Ombra degli edifici, degli alberi censiti e della vegetazione rilevata dal laser, sull'asse della strada.

Percorsi verso i rifugi, 15 luglio 2026, fra le 12:30 e le 13:30 (file `shadow/firenze_novoli/sintesi_rifugi_RC1.json` … `RC5.json`):

| Percorso | Lunghezza | In ombra | Minuti al sole |
|---|---|---|---|
| RC1 fermata Novoli - Regione Toscana → Giardino delle Medaglie d'Oro | 687 m | 18,9% | 7,7 |
| RC2 fermata Torre degli Agli → Biblioteca Buonarroti | 717 m | 10,2% | 9,0 |
| RC3 Polo, edificio D15 → Giardino di piazza Puccini | 996 m | 31,7% | 9,7 |
| RC4 civico di via De Pinedo 17 → Biblioteca Buonarroti | 1.071 m | 14,6% | 12,7 |
| RC5 scuola Vamba → Biblioteca Buonarroti | 630 m | 21,2% | 6,9 |

Percorsi più esposti alle 14:00 del 15 luglio, fra i 15 percorsi campione verso Polo, scuola, fermate e rifugi (un job per percorso, file `shadow/firenze_novoli/esposizione_2026-07-15.json`):

| Pos. | Percorso | Metri al sole | Minuti al sole | Job |
|---|---|---|---|---|
| 1 | RC4 civico di via De Pinedo 17 → Biblioteca Buonarroti | 942 su 1.071 | 13,1 su 14,9 | `job_125a412a3ee9f23f` |
| 2 | R10 stesso civico → fermata Novoli - Regione Toscana | 904 su 941 | 12,6 su 13,1 | `job_3eec2e73fce91b71` |
| 3 | R03 fermata Novoli - Regione Toscana → Polo, edificio D1 | 814 su 890 | 11,3 su 12,4 | `job_caf0a0f476d97f90` |

A quell'ora il sole è a 66 gradi e l'ombra è poca su tutti i percorsi: i metri al sole seguono soprattutto la lunghezza. I meno ombreggiati in proporzione portano alla scuola Vamba e alla fermata Regione Toscana: R09 0,8%, R08 3,7%, R10 3,9%. Il tratto al sole più lungo dei tre più esposti è in `shadow/firenze_novoli/tratti_sole_2026-07-15.geojson`.

### 7.4 Costo degli interventi

Filare S1 su R01 (7 alberi): unico intervento con un costo nei calcoli. Platano orientale di circonferenza 18/20 cm, scelto con una regola dichiarata (specie da ombra più piantata dal Comune vicino al tratto), voci del Prezzario dei Lavori della Regione Toscana 2026, Firenze (CC BY 4.0), IVA esclusa: fornitura 2.884,46 euro, piantagione in sede stradale 950,49 euro, totale 3.834,95 euro. Ombra guadagnata il 15 luglio fra le 12:30 e le 13:30: 146,0 m², cioè 38,07 m² d'ombra per mille euro (con altre specie da 21,35 a 65,78). File: `scenarios/firenze_novoli/costo_filare.json`; confronto con la baseline nel job `job_fddc0dab363245c4`. Esclusi scavo, pavimentazione, sottoservizi, progettazione e manutenzione; l'ombra è quella di un albero adulto, il prezzo quello di un albero da vivaio. La voce di piantagione è da confermare con l'ufficio del verde.

Pensiline S2, S5 e S6: l'ombra c'è (area di attesa da 0% a circa 40% a mezzogiorno di luglio per S2 e S5, job `job_8372d9e4c57a7983`), il costo no. Nessun prezzo pubblico con licenza compatibile entra nei calcoli. Solo come ordine di grandezza, non usato nei calcoli: dai contratti pubblici registrati presso ANAC fra il 2022 e il 2026, una pensilina per fermata d'autobus con fornitura e posa costa in mediana 4.940 euro, IVA esclusa (primo e terzo quartile 3.677 e 7.263 euro, 159 contratti, modelli e dimensioni molto diversi). Fonte: Autorità Nazionale Anticorruzione, open data sui contratti pubblici, licenza CC BY-SA 4.0; estratto in `docs/research/anac-pensiline/estratto_costi_unitari.csv`. Per il caso di Firenze serve il costo del piano comunale delle 72 pensiline, non pubblicato.

### 7.5 Limiti del caso caldo

- Residenti del 2011 ripartiti in modo uniforme: una stima, non persone contate.
- Ombra sull'asse della strada; alberi e vegetazione come volumi opachi; nessuna temperatura, nessun comfort.
- Ombra calcolata solo sui percorsi campione, non sul percorso di ogni civico: non si sa quanti residenti arrivano a un rifugio camminando soprattutto all'ombra.
- Ingressi e orari dei rifugi non verificati.
- Costi: solo il filare S1, con le esclusioni dette sopra.
- Le domande di prova sul caso caldo (registro `nl/firenze_novoli/caldo.json`) sono state scritte dal gruppo di lavoro, non dall'ufficio: vanno validate.

Per la verifica sul posto c'è una scheda stampabile per il percorso R01 in un giorno di dicembre: `docs/verifica-posto/`.

## 8. Limiti

Limiti dei dati:

- Rete pedonale solo da OpenStreetMap: lato del marciapiede, larghezze e pendenze non noti dove non mappati.
- Civici come punti d'indirizzo, non persone: le quote di accessibilità sono quote di civici. I residenti per sezione sono del 2011 ed entrano solo come stima per civico, accanto alla quota dei civici (sezione 7.2).
- Ingressi del Polo: un civico per edificio, non verificato sul posto; il civico non è per forza la porta.
- Edifici: impronte del 2011 con altezze del 2023; portici e volumi sospesi ignoti, trattati come pieni. Datum verticale del rilievo laser non confermato.
- Alberi pubblici censiti, chiome in parte stimate; vegetazione privata solo dal rilievo laser, come volume opaco pieno (limite superiore dell'ombra).
- Il censimento degli alberi è aggiornato ogni giorno e l'estratto OpenStreetMap ha una data: ricostruire i dati da zero dopo mesi dà numeri leggermente diversi. La baseline congelata con le impronte permette di accorgersene.

Limiti del metodo:

- Ombra misurata sull'asse della rete, non sulla linea dove si cammina. Ombra geometrica binaria (ombra o sole), senza luce diffusa né trasparenza delle chiome.
- Il lato della strada più in ombra è solo un limite superiore, accanto all'asse. La distanza del lato viene dal marciapiede OSM; altrimenti dal bordo delle aree stradali del Comune meno un margine di 1,7 m, tarato su pochi tratti con il marciapiede OSM; altrimenti è un valore dichiarato di 3 m. Da verificare sul posto.
- Nessun calcolo di temperatura, comfort termico o rischio da calore per le persone.
- Fattibilità degli interventi non valutata; costo solo per il filare S1 (sezione 7.4).
- Una fermata (San Donato - Università) è 100 m fuori dal riquadro: attorno ci sono il terreno e la rete, non gli edifici.

Limite generale: nessun risultato è validato sul posto. Il passo successivo proposto è la verifica di un percorso (ingressi, linea del marciapiede, ombra osservata a un'ora nota).

## 9. Come si replica su un'altra area

Il codice non contiene costanti di Firenze: area, baseline e cartelle vengono da un registro delle aree. Per una nuova area:

1. Registrare l'area: riquadro in coordinate geografiche, margine della rete, identificativo. Il registro è validato da uno schema.
2. Censire le fonti dell'area nel catalogo regionale e nei portali comunali: per ogni fonte licenza ed evidenza, data del dato, controlli minimi. Le fonti senza licenza di riuso restano fuori.
3. Scaricare e congelare una baseline. Le fonti regionali (unità volumetriche, censimento per sezione, orari del trasporto pubblico) valgono per tutta la Toscana; quelle comunali (alberi, civici, rilievo laser) dipendono dal Comune.
4. Ricostruire rete, geometrie e destinazioni con i moduli esistenti. Le destinazioni e i loro ingressi sono l'unico passo che richiede lavoro manuale e una verifica sul posto.
5. Rieseguire i test di ogni motore e il giro di domande per l'assistente.

Cosa serve perché funzioni bene:

- un censimento degli alberi con posizione e circonferenza, e un rilievo laser recente con licenza aperta;
- civici georeferenziati con licenza aperta;
- un elenco degli ingressi dei luoghi pubblici (scuole, uffici, sedi universitarie): oggi manca quasi ovunque ed è il dato che più cambia i risultati di accessibilità.

Il primo pilota, su un'area di Pisa, è stato accantonato quando il progetto si è spostato a Firenze; il passaggio ha richiesto di togliere dal codice ogni riferimento all'area precedente, e oggi il registro delle aree rende la replica un lavoro di dati più che di codice.
