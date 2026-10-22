# Gemello digitale di Firenze Novoli: come funziona

Aggiornato al 22 ottobre 2026. Documento tecnico sintetico: cosa fa il sistema, quali dati usa, quali calcoli fa e come. Il dettaglio completo, con la tabella delle 36 fonti e gli esempi di risposta, è in [DOCUMENTO-TECNICO.md](DOCUMENTO-TECNICO.md). Nessun risultato è validato sul posto.

## 1. Architettura in breve

Una catena di moduli, ognuno nella sua cartella con test e report:

1. `pipeline/`: scarica le fonti, registra ogni scarico, congela una baseline, normalizza.
2. `network/`: costruisce la rete pedonale e aggancia civici e ingressi.
3. `geometry/`: costruisce edifici, alberi e vegetazione in 3D.
4. `analysis/`: calcola l'accessibilità pedonale.
5. `shadow/`: calcola l'ombra sui percorsi.
6. `scenarios/`: aggiunge interventi e li confronta con la baseline.
7. `scene/firenze_novoli/`: genera la scena 3D statica per il browser.
8. `service/`: espone i calcoli agli assistenti tramite il protocollo MCP.

Tutto è in Python 3.12. I contratti fra i moduli (aree, fonti, baseline, job, manifest, scenari, strumenti MCP) sono JSON Schema in `contracts/schemas/`.

Area: riquadro di circa 2,1 km² su Novoli - Firenze Nova, sistema di riferimento EPSG:7791 (RDN2008 / UTM 32N). La rete pedonale si estende 700 m oltre il riquadro, perché un civico vicino al bordo può passare da fuori.

## 2. Dati

36 fonti aperte. Le 14 della baseline congelata del 9 ottobre 2026 alimentano i calcoli; le altre servono alla scena o a calcoli aggiuntivi dichiarati fuori baseline.

Dati che entrano nei calcoli:

| Cosa | Fonte | Licenza |
|---|---|---|
| Civici (origini dei percorsi, 3.296 nel riquadro) | Comune di Firenze | CC BY 4.0 |
| Rete pedonale (strade, marciapiedi, attraversamenti, scale) | OpenStreetMap | ODbL |
| Impronte degli edifici | Regione Toscana, unità volumetriche del DB topografico (2011) | politica regionale, con riserva |
| Altezze di edifici e chiome | Comune di Firenze, rilievo laser 2023 (DTM e DSM a 0,5 m) | CC BY 4.0 |
| Alberi pubblici (posizione, specie, circonferenza) | Comune di Firenze, censimento | CC BY 4.0 |
| Fermate tram e autobus | Comune di Firenze, feed GTFS di tram e autobus | CC BY (con riserva per i GTFS) |
| Scuole e loro accessi | Ministero dell'Istruzione (via Comune), Città metropolitana | IODL 2.0, CC BY |
| Rifugi climatici (aree fresche e biblioteche) | Comune di Firenze | CC BY 4.0 |
| Barriere architettoniche (2013) | Comune di Firenze | CC BY 4.0 |
| Residenti 2011 per sezione di censimento | Regione Toscana (dati Istat), confini del Comune | CC BY |
| Aree stradali e aree pedonali (poligoni) | Comune di Firenze | CC BY 4.0 |
| Prezzi di fornitura e piantagione degli alberi | Prezzario dei lavori della Regione Toscana 2026 | CC BY 4.0 |

Solo nella scena: catasto (Agenzia delle Entrate), temperatura delle superfici da satellite Landsat (2023-2026), temperatura dell'aria della stazione SIR Firenze Università, qualità dell'aria ARPAT 2025, servizi (farmacie, stalli per disabili, sharing, aree verdi e giochi), pericolosità idraulica, alluvione del 1966, classi acustiche, zone 30, aree di protezione civile.

Regole sui dati:

- Ogni scarico produce uno snapshot con data, URL, dimensione, impronta sha256, licenza e periodo del contenuto. Uno scarico fallito non sostituisce mai l'ultimo valido.
- La baseline è l'elenco congelato degli snapshot usati; ogni calcolo la dichiara. Se ne crea una nuova solo con una decisione esplicita.
- La data del dato è quella dichiarata dalla fonte; se manca, vale la data di scarico. Mai la data di modifica della scheda del catalogo.
- Ogni attributo ha una classe: misurato, derivato, stimato, ignoto.
- Ogni fonte ha una scheda leggibile da persone e da assistenti (`get_source_card`).

## 3. Calcoli

### 3.1 Rete pedonale e ingressi

- Archi da OpenStreetMap: tipo, lunghezza, stato del marciapiede ("ignoto" se non dichiarato, nessuna inferenza).
- Ogni civico si aggancia all'arco più vicino entro 40 m; 168 su 3.296 restano senza aggancio e sono contati a parte.
- Gli ingressi delle destinazioni sono punti espliciti: per il Polo delle Scienze Sociali un civico per edificio (7), per le scuole l'accesso della Città metropolitana, per le fermate la posizione del gestore, per i rifugi il civico all'indirizzo dichiarato dal Comune.

### 3.2 Accessibilità pedonale

- Per ogni civico: cammino minimo sulla rete fino all'ingresso più vicino della destinazione (algoritmo di Dijkstra).
- Tempo = lunghezza / velocità, più una penalità per attraversamento se prevista dal profilo.
- Profilo di riferimento: 1,2 m/s, nessuna penalità, scale ammesse. Sensibilità: 0,8 e 1,4 m/s; profilo ridotto a 0,8 m/s senza scale e con 10 s per attraversamento; aggancio a 20, 40 e 60 m.
- Con più destinazioni conta la più vicina.
- Risultati: civici raggiunti entro 5, 10 e 15 minuti e quota sul totale, con l'intervallo dovuto alla velocità; tempo mediano; tratti della rete più usati.

Residenti stimati: i residenti 2011 di ogni sezione di censimento divisi in parti uguali fra i civici della sezione (negozi compresi). Si riportano sempre accanto alla quota dei civici, mai al posto. Sensibilità: ripartizione sui soli civici neri.

### 3.3 Edifici, alberi e vegetazione

- Edifici: impronta 2011 della Regione; altezza = modello della superficie meno modello del terreno, dentro l'impronta, dal rilievo laser 2023. Edifici nuovi dopo il 2011 da OpenStreetMap; quelli assenti nel 2023 (183, probabili demolizioni) sono esclusi.
- Alberi del censimento: altezza e chioma misurate dal laser dove ci sono abbastanza celle, altrimenti stimate per specie e classe di circonferenza.
- Vegetazione senza albero censito: poligoni ricavati dal laser, trattati come volumi opachi pieni (limite superiore dell'ombra). Esclusi i poligoni lisci, probabili tetti non mappati.

### 3.4 Ombra

- Posizione del sole con l'algoritmo SPA del NREL, al centro del riquadro, in ora locale con cambio dell'ora gestito. Un orario inesistente o ambiguo è rifiutato.
- Il percorso è campionato ogni metro. Da ogni punto parte un raggio verso il sole: se incontra un edificio, una chioma o un volume di vegetazione, il punto è in ombra.
- Passo temporale di riferimento: 5 minuti. Sotto i 5 gradi di altezza del sole non si dà un numero.
- Tre casi calcolati insieme, così il risultato è un intervallo: soli edifici (altezza minima e massima), edifici e alberi censiti (chioma minima, tipica, massima), edifici, alberi e vegetazione laser.
- Risultati: quota del percorso in ombra e minuti passati al sole camminando a 1,2 m/s, per orario o per fascia (per esempio 12:30-13:30).

Su cosa si calcola:

- 15 percorsi campione: R01-R10 verso Polo, scuola e fermate; RC1-RC5 verso i rifugi climatici.
- Il percorso più breve di ogni civico entro 15 minuti dal rifugio più vicino, alle 14 del 15 luglio. "Soprattutto all'ombra" = almeno il 50% del percorso in ombra (soglia scelta da noi, con 40% e 60% accanto). Indicatore senza soglia accanto: quota media del percorso in ombra e minuti al sole.

### 3.5 Ombra sui due lati della strada (prototipo)

Il calcolo principale è sull'asse della strada, non dove si cammina. Accanto c'è un prototipo sui due lati:

- la linea di ogni lato è spostata dall'asse di una distanza presa, nell'ordine, dal marciapiede mappato in OpenStreetMap, dal bordo delle aree stradali del Comune meno un margine di 1,7 m, oppure da un valore dichiarato di 3 m;
- sotto 1 m dopo il margine si torna ai 3 m;
- il lato più in ombra entra nelle risposte solo come limite superiore (il massimo fra lato e asse), mai come valore principale.

Il margine di 1,7 m è la mediana dello scarto con il marciapiede mappato, tarata su pochi tratti: si ricontrolla con la verifica sul posto del 12 dicembre.

### 3.6 Scenari di intervento

- Uno scenario è un insieme versionato di interventi aggiunti alla baseline: alberi con dimensioni di classe, pensiline con quota d'imposta e copertura.
- Il sistema segnala interventi dentro un edificio o su una carreggiata senza marciapiede. La fattibilità resta sempre "ignota".
- Il confronto con la baseline è a parità di data, orari e ostacoli. Restituisce indicatori separati: ombra e minuti al sole sui percorsi, ombra sull'area di attesa, effetto sull'accessibilità. Nessun punteggio unico.
- Il filare S1 è posizionato con una regola sulle aree pedonali del Comune; la specie (platano orientale 18/20) è la specie da ombra più piantata dal Comune entro 400 m.

Costo: solo per i filari. Indicatore = m² d'ombra guadagnati fra 12:30 e 13:30 del 15 luglio diviso il costo in migliaia di euro, con voci del prezzario regionale (fornitura e piantagione in sede stradale, IVA esclusa). Esclusi scavo, pavimentazione, sottoservizi, manutenzione. Le pensiline non hanno un prezzo pubblico con licenza compatibile: non entrano nei calcoli.

### 3.7 Riproducibilità

- Identificativo del calcolo (job) = impronta della richiesta canonica (strumento, input, parametri). Stessa richiesta, stesso job.
- Ogni job ha un manifest: metodo e versione, snapshot usati con impronta e licenza, parametri, metriche con la loro classe, limiti.
- Un comando di replay riesegue un job dal manifest e confronta i numeri.
- La cache si invalida da sola se cambia il codice dei motori o un file di dati letto.
- Le coordinate sono arrotondate prima di scrivere i file, così macchine diverse producono gli stessi byte.

## 4. Servizio per assistenti (MCP)

L'assistente non accede a dati né codice: chiama solo strumenti con argomenti validati da JSON Schema. Nessun campo libero, nessuna interrogazione SQL.

Strumenti principali:

| Strumento | Cosa fa |
|---|---|
| `list_approved_sources`, `inspect_dataset`, `get_source_card` | fonti approvate, schema e qualità, scheda della fonte |
| `list_destinations`, `list_scenarios` | destinazioni con ingressi, scenari salvati |
| `compute_walk_access` | accessibilità dai civici verso una o più destinazioni |
| `estimate_residents` | residenti stimati raggiunti, accanto ai civici |
| `compute_shadow` | ombra su percorsi o geometrie per data e orari |
| `compare_scenarios` | confronto fra baseline e scenari |
| `get_route_exposure` | percorsi più esposti al sole, con il limite superiore sul lato più in ombra |
| `get_shaded_access` | civici e residenti che arrivano al rifugio soprattutto all'ombra |
| `get_street_side_shade` | ombra sui due lati della strada dei percorsi campione |
| `get_job_status`, `get_result_manifest` | stato e manifest di un job |

Regole:

- Un nome ambiguo ("la fermata del tram") produce un errore con i candidati: l'assistente deve chiedere.
- Errori con codici stabili: destinazione ambigua, identificativo sconosciuto, dati insufficienti, limite superato, calcolo non disponibile, parametri non validi, baseline incompatibile.
- Ogni risposta riporta job, dati, parametri, metriche e limiti.
- Un testo di istruzioni per l'assistente impone di elencare fonti e destinazioni prima di calcolare, riportare job e limiti, dire "non lo so" quando il calcolo non esiste, non chiamare persone i civici.

Versione remota (pronta, non installata): trasporto HTTP in sola lettura, limiti di chiamate per client, token facoltativo letto dall'ambiente, utente senza privilegi e file system in sola lettura tranne la cache.

Verifica: un giro di domande in linguaggio naturale con risposte registrate e rieseguibili (`nl/firenze_novoli/`), più le dieci domande del caso caldo.

## 5. Scena 3D

- Pagina statica generata da `scene/firenze_novoli/build.py`, con la libreria 3D inclusa nel progetto: funziona anche senza rete.
- Pannello a schede: Livelli, Sole, Analisi, Interventi, Legenda.
- Mostra edifici, alberi, terreno, rete, destinazioni, percorsi, ombre all'ora scelta, accessibilità per civico, scenari prima e dopo, e i livelli informativi aggiuntivi.
- Ogni livello ha un pulsante "i" con fonte, licenza e data del dato. Una pagina di metodo spiega da dove viene ogni numero.
- Si apre con `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/.

## 6. Limiti

- Ombra sull'asse della strada; il lato è solo un prototipo e un limite superiore.
- Ombra geometrica binaria: niente luce diffusa, niente trasparenza delle chiome, niente temperatura o comfort.
- Rete solo da OpenStreetMap: lato del marciapiede, larghezze e pendenze spesso ignoti.
- Civici come punti d'indirizzo; residenti 2011 ripartiti in modo uniforme.
- Edifici: impronte 2011 e altezze 2023, portici trattati come pieni, datum verticale del laser non confermato.
- Ingressi del Polo e dei rifugi non verificati; orari dei rifugi ignoti (si assumono aperti).
- Costo solo per il filare; fattibilità degli interventi non valutata.
- Nessuna validazione sul posto: la prima è prevista il 12 dicembre 2026 sul percorso R01.

## 7. Come si replica su un'altra area

Il codice non contiene costanti di Firenze: area, baseline e cartelle vengono da un registro delle aree validato da uno schema. Per una nuova area si registra il riquadro, si censiscono le fonti con licenza, si congela una baseline e si rieseguono i moduli. L'unico passo manuale è l'elenco delle destinazioni e dei loro ingressi, che va verificato sul posto.

Serve: censimento degli alberi, rilievo laser recente e civici georeferenziati, tutti con licenza aperta.

## 8. Comandi

```
make test-fast   # test rapidi, circa 50 s
make test        # tutti i test, circa 100 s
make lint        # controllo del codice
make validate    # contratti JSON Schema
```

Ricostruire i dati da zero: `pipeline/run_firenze.sh` (circa 10 minuti, scarica dalla rete).
