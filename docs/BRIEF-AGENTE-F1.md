# Brief per l'agente autonomo: fase F1 del piano di decollo

Scritto il 17 ottobre 2026 per una sessione lunga senza supervisione sul worker VPS. Contesto: [PIANO-DECOLLO.md](PIANO-DECOLLO.md), fase F1 "Provabile da altri". Prima di iniziare leggere `CLAUDE.md` e `docs/STATO.md`: valgono tutte le loro regole.

## Obiettivo

Un collega che non conosce il progetto collega l'MCP `dt-firenze` dal suo assistente e ottiene risposte giuste, con fonti e limiti, senza Luca accanto. Tutto deve essere pronto per l'installazione, ma l'installazione la decide Luca.

## Regole di questa sessione

Permesso senza chiedere:
- ricreare `data/` con `pipeline/run_firenze.sh` (scarica dalla rete: autorizzato da Luca per questa sessione);
- creare il ramo `agente/f1` da `main`, fare commit piccoli (uno per compito), fare push del ramo;
- installare pacchetti solo dentro `pipeline/.venv` e `service/.venv`, aggiornando il relativo `requirements.txt`.

Vietato:
- merge o push su `main`, tag, force push;
- installare o avviare qualcosa su altre macchine (staging AI compresa), rilasciare su Vercel;
- `fonti_firenze.py baseline --force`, cambiare a mano i numeri dei REPORT, toccare la baseline congelata;
- contattare persone o servizi esterni oltre ai download delle fonti già in `docs/FONTI.md`;
- nomi di prodotti software nel documento tecnico (compito 5): si descrive la funzione.

Quando fermarsi: se un compito richiede una decisione di Luca, scriverla in fondo al report finale come domanda con le opzioni e passare al compito successivo. Non inventare dati, licenze o date: se mancano, scriverlo.

## Compito 0 - Ambiente riproducibile

- Creare i due venv, ricreare `data/`, eseguire `make lint`, `make validate`, `make test`.
- I numeri devono uscire uguali a quelli dei REPORT: se cambiano, fermarsi su questo compito e documentare la differenza (fonte, sha256, file).

Fatto quando: `make test` passa sul worker, con l'esito nel report.

## Compito 1 - MCP raggiungibile da remoto, in sola lettura

- Aggiungere a `service/mcp_server.py` il trasporto HTTP (streamable HTTP del protocollo MCP) accanto a stdio, scelto da argomento o variabile d'ambiente. Stdio resta il default: `.mcp.json` non cambia.
- Sola lettura per chi arriva da remoto: `create_local_scenario` disattivato in modalità remota (risponde con un errore esplicito), gli altri strumenti invariati. Limite di richieste e di job lunghi concorrenti, con valori in variabili d'ambiente.
- Nessun segreto nel codice. Se serve un token d'accesso, si legge da variabile d'ambiente e il nome va in un `.env.example` senza valore.
- File pronti per l'installazione, non usati: unità di servizio o container, istruzioni in `service/INSTALLA-REMOTO.md` (porta, utente dedicato senza privilegi, aggiornamento dei dati, cache).
- Test: un test eseguibile come script che avvia il server HTTP in locale, elenca gli strumenti, esegue `list_destinations` e `compute_walk_access` sul Polo e confronta il risultato con quello di stdio; verifica che `create_local_scenario` sia rifiutato da remoto.

Fatto quando: il test passa ed è aggiunto a `make test-fast` se dura meno di 30 secondi.

## Compito 2 - Schede delle fonti leggibili dagli agenti

- Uno script genera una scheda Markdown per ogni fonte, da `pipeline/sources/*.json`, dagli snapshot e da `pipeline/t17_firenze.json`: titolo, editore, link alla scheda del catalogo, licenza e uso consentito, data del dato solo se certa (regola di provenienza: mai la data della scheda del catalogo), periodo, campi usati, controlli, limiti.
- Un indice `service/schede/INDEX.md` con una riga per fonte, e uno strumento o una risorsa MCP che restituisce indice e schede.
- Test: tutte le fonti della baseline hanno una scheda; nessuna scheda ha campi licenza vuoti; le date coincidono con gli snapshot.

## Compito 3 - Prompt pronto per l'agente

- `service/PROMPT-AGENTE.md`: il testo da incollare in un assistente per usare l'MCP. Procedura: elencare fonti e destinazioni prima di calcolare, usare solo gli id restituiti, riportare job_id, dataset, parametri e limiti, dire "non lo so" quando il calcolo non esiste (esempio: temperatura percepita), non chiamare "persone" i civici.
- Verifica: rieseguire le domande di `nl/firenze_novoli/` con il prompt e l'MCP via HTTP; registrare risposte e scostamenti in `nl/firenze_novoli/REPORT-REMOTO.md`.

## Compito 4 - Pagina di metodo nella scena

- Una pagina o un pannello in `scene/firenze_novoli/` raggiungibile dalla scena: da dove viene ogni numero, cosa calcola ogni livello, cosa non sappiamo (limiti di `docs/STATO.md`), con rimando alle schede del compito 2.
- Stile e tono come il resto della scena, WCAG 2.2 AA. Solo build e prova in locale (`scene/firenze_novoli/build.py`, `python3 -m http.server`), con uno screenshot nel report. Niente rilascio.

## Compito 5 - Documento tecnico per la Regione (bozza)

- `docs/DOCUMENTO-TECNICO.md`, 6-10 pagine, per un lettore tecnico della pubblica amministrazione: obiettivo, area, fonti e licenze (tabella generata dalle schede), motori di calcolo e metodo, servizio di interrogazione per assistenti, esempi di domande con risposte reali e job_id, limiti, come si replica su un'altra area.
- Nessun nome di prodotto software, nessun importo, nessun nome di persona. Accenti veri, virgolette dritte.

## Se resta tempo - preparazione della fase F2 (caso caldo)

Solo analisi e proposte, nessuna decisione:
- elenco dei rifugi climatici nel riquadro e fuori, con accessibilità a piedi dai civici verso il più vicino (strumento esistente con più destinazioni);
- proposta di 3-5 percorsi campione verso i rifugi, con le stesse regole dei percorsi R01-R10, senza calcolarne l'ombra;
- ricerca di un prezzario pubblico per pensiline, filari e tende con licenza di riuso verificata: fonte, licenza, voci utili. Se la licenza non è chiara, scriverlo.

## Report finale

`docs/REPORT-AGENTE-F1.md`, aggiornato alla fine di ogni compito (così resta utile anche se la sessione si interrompe):
- per compito: fatto o no, commit, comando di verifica ed esito;
- cosa è cambiato rispetto a `main`;
- domande per Luca, ognuna con le opzioni e una raccomandazione;
- tempo e costo stimati della sessione, se disponibili.
