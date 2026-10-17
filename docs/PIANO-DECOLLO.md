# Piano di decollo

Scritto il 16 ottobre 2026. Orizzonte: fine gennaio 2027. Tempo di Luca: una giornata a settimana (D26).

## Obiettivo

Entro fine gennaio un ufficio del Comune di Firenze chiede una proposta sul caso caldo estivo (D25). La vetrina regionale e il riuso su dati.gov.it vengono di conseguenza.

Da dove nasce:
- Romeo Zitarosa (Genius Loci, 16/10): senza un caso d'uso che risolva un problema vero del cliente resta un esercizio di stile; negli scenari manca la valutazione economica.
- Referente regionale (call del 16/10): il valore non è l'interfaccia ma il calcolo; serve un documento tecnico; i casi d'uso di oggi servono più al Comune che alla Regione; integrarsi con l'esistente, non rifarlo.
- DVNS (dovevannoinostrisoldi.com): MCP pubblico in sola lettura, una scheda per fonte leggibile dagli agenti, pagina di metodo, stato delle fonti.

Il gemello non è un prodotto da vendere da solo: è il dimostratore di cosa si ottiene dai dati che Net7 già pubblica (portale regionale, nuovo portale del Comune) e di cosa si può ordinare con l'accordo quadro regionale sui dati.

## Fasi

### F0 - Decidere (settimana del 19 ottobre)

- Incontro con Romeo (martedì 20, giovedì 22 o venerdì 23): caso caldo, costi, i due MCP sullo stesso agente.
- RUP del portale open data del Comune: sistemi informativi del Comune (noto il 16/10). Da lui si passa per arrivare all'ufficio che segue caldo e rifugi climatici.
- GTFS: fatto il 16/10. Il feed dei bus è una finestra mobile di tre settimane (quello di oggi va dal 16/10 al 5/11); le fermate nella zona sono identiche a quelle del 9/10 più una nuova, il tram è invariato e valido fino al 30/12. I calcoli usano solo le posizioni delle fermate: baseline e risultati restano validi, nessun ricalcolo. Snapshot del 16/10 registrati fuori baseline.

Fatto quando: data dell'incontro fissata, GTFS verificato (fatto), un nome di riferimento in Comune (fatto: il RUP).

### F1 - Provabile da altri (26 ottobre - 13 novembre, 3 giornate)

- MCP raggiungibile da remoto, in sola lettura, con un prompt pronto da copiare nell'agente (regole: fonti e limiti in ogni risposta, "non lo so" se il calcolo non c'è).
- Una scheda per fonte leggibile dagli agenti: fonte, licenza, data del dato, filtri, limiti.
- Pagina di metodo nella scena: da dove viene ogni numero, cosa non sappiamo.
- Documento tecnico per la Regione: cosa calcola, come, con quali dati, con quali limiti. Senza nomi di prodotto.

Fatto quando: un collega collega l'MCP dal suo assistente e ottiene una risposta giusta senza Luca accanto.

MCP sulla macchina di staging AI di Net7 (D28). Prima di installarlo, rileggere la minuta del 13/10 sul piano di remediation delle macchine: l'installazione deve rispettarlo.

### F2 - Il caso caldo (16 novembre - 18 dicembre, 5 giornate)

- Dieci domande scritte con l'ufficio del Comune, o in sua assenza con il referente regionale. Esempi: quanti residenti raggiungono un rifugio climatico in 10 minuti camminando all'ombra; quali percorsi verso scuole e fermate sono più esposti alle 14 di luglio; dove un intervento dà più ombra per euro speso.
- Accessibilità verso i rifugi climatici (il dataset c'è già nella baseline) e ombra sui percorsi verso di essi.
- Costi degli interventi da un prezzario pubblico con licenza di riuso: pensilina, filare, tenda. Indicatore "metri quadri d'ombra per mille euro".
- Esperimento con l'MCP di Genius Loci: isole di calore e rischio ondate accanto a ombre e percorsi.
- Verifica sul posto di un percorso: geometria dell'ombra a un'ora nota, anche d'inverno.

Fatto quando: l'agente risponde alle dieci domande con numeri, fonti e limiti, e la scena mostra il caso.

### F3 - Presentare (gennaio, 3 giornate)

- Demo e documento all'ufficio del Comune.
- Proposta di adesione all'accordo quadro regionale sui dati, quando è aggiudicato.
- Candidatura come storia di riuso su dati.gov.it e nel nuovo portale del Comune.

Fatto quando: l'ufficio chiede una proposta.

## Cosa resta fuori fino a febbraio

- Allagamenti: interessanti, ma un risultato sbagliato lì ha conseguenze vere. Secondo giro, con il modello di Genius Loci.
- Seconda area e confronto tra quartieri.
- Rilievi da drone per portici e marciapiedi.

## Rischi

- Il Comune ha già un suo gemello (rilievi 3D e LiDAR per gli uffici): presentarsi come integrazione, non come alternativa (decisione aperta 1 di STATO).
- Senza un ufficio del Comune entro F2 le dieci domande le scriviamo noi: il caso perde forza. Ripiego: farle validare al referente regionale.
- Il nuovo portale del Comune va in esercizio a giugno 2027: fino ad allora il gemello legge dal portale regionale e dai servizi del Comune già esistenti.
- Una giornata a settimana non regge imprevisti: se una fase slitta, si taglia la F2 (meno domande), non la F1.

## Registro

| Settimana | Fatto | Prossimo |
|---|---|---|
| 12-16 ottobre | Mail a Romeo, sua risposta; demo al referente regionale; piano scritto; RUP noto; GTFS verificato; ospitalità dell'MCP decisa | Incontro con Romeo, poi F1 |
| 17 ottobre (agente, ramo `agente/f1`) | F1 preparata: MCP HTTP in sola lettura, schede delle fonti, prompt, pagina di metodo, bozza del documento tecnico; analisi F2 su rifugi e prezzario ([REPORT-AGENTE-F1.md](REPORT-AGENTE-F1.md)) | Luca: revisione del ramo, dati del worker (domanda 1), installazione su staging |
