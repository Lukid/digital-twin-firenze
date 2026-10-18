# Stato del progetto

Aggiornato al 10 ottobre 2026 (sessioni del 17 ottobre sotto): POC di Firenze Novoli completo nei quattro punti chiesti (accessibilità, ombre, scenari, scena alla Padova), con servizio MCP. Il 10 ottobre Polo e fermata T2 sono stati rifatti (D19, D20) e ricalcolati da F04 a F11. Revisione del codice completata e i sei difetti trovati (R1-R6) corretti il 10 ottobre, ognuno con un test (commit `f836d95` e `df0481b`): `make lint` e `make test` passano. I numeri dei report sono confrontati con i file di risultato. Dettagli in [REVISIONE-CODICE-20261010.md](REVISIONE-CODICE-20261010.md). Punto di ripartenza per la prossima sessione.

17 ottobre 2026: sessione autonoma sulla fase F1 del [piano di decollo](PIANO-DECOLLO.md), ramo `agente/f1` (non ancora in `main`): MCP via HTTP in sola lettura (pronto, non installato), schede delle fonti e strumento `get_source_card`, prompt per l'assistente, pagina di metodo nella scena, bozza del documento tecnico. Esiti, differenze dei dati ricostruiti sul worker e domande aperte in [REPORT-AGENTE-F1.md](REPORT-AGENTE-F1.md).

17 ottobre 2026, seconda sessione autonoma, fase F2, ramo `agente/f2` (non ancora in `main`): civici dei percorsi campione e dei test ritrovati per `CODICECIVI` (D30); 7 rifugi climatici fra le destinazioni, 39,1% dei civici entro 10 minuti dal più vicino (job versionato); indicatore "metri quadri d'ombra per mille euro" del filare S1 con il prezzario regionale 2026; ricerca di prezzi pubblici per pensiline e tende; percorsi RC1-RC5 verso i rifugi. Esiti e domande in [REPORT-AGENTE-F2.md](REPORT-AGENTE-F2.md).

17 ottobre 2026, terza sessione autonoma, fase F3, ramo `agente/f3` (non ancora in `main`): coordinate arrotondate prima di scrivere i GeoJSON (D39, funzione `arrotonda` in `pipeline/coordinate.py`, 8 decimali in gradi), file rigenerati e baseline degli scenari aggiornata senza cambiare job né metriche, `scripts/impronte.sh` per il confronto col Mac; costo del filare S1 con il platano orientale 18/20 (D36): 3.834,95 euro, 38,07 m² d'ombra per mille euro; RC3 verso il rifugio più vicino (Giardino Puccini, 996 m) e ombra dei 5 percorsi RC, uno alla volta; costi unitari di pensiline e strutture ombreggianti dagli open data ANAC (licenza CC BY-SA 4.0, non CC BY); scena con rifugi, percorsi RC, accessibilità verso il rifugio più vicino e costo di S1. Esiti e domande in [REPORT-AGENTE-F3.md](REPORT-AGENTE-F3.md).

18 ottobre 2026, sessione autonoma F4, ramo `agente/f4` (non ancora in `main`): dieci domande sul caso caldo (bozza nostra, da validare con l'ufficio) con risposte solo dall'MCP e replay in `test_nl.py`; residenti 2011 stimati per civico (D45): 43,6% dei residenti stimati entro 10 minuti dal rifugio più vicino, 39,1% dei civici; percorsi più esposti alle 14 del 15 luglio (RC4, R10, R03); due strumenti MCP in sola lettura (`estimate_residents`, `get_route_exposure`); sezione 7 del documento tecnico sul caso caldo; kit stampabile per verificare R01 sul posto sabato 12 dicembre 2026. Esiti e domande in [REPORT-AGENTE-F4.md](REPORT-AGENTE-F4.md).

## In una riga

Gemello digitale pilota di Firenze, area Novoli - Firenze Nova (riquadro FP di 2 km²), costruito solo da open data con licenza che ne permette il riuso, per mostrarne le potenzialità. Pisa è accantonata nel tag git `pilota-pisa-z2` (D15); il 10 ottobre i suoi file sono stati tolti dal ramo principale, tranne gli script di rete e geometria di Pisa (`network/build.sh`, `geometry/build.sh` e i loro test), non più mantenuti.

## Fatto su Firenze (ogni consegna ha un REPORT e un test rieseguito dall'integratore)

| Task | Dove | Controllo |
|---|---|---|
| F01 audit e riquadro | `docs/audit-firenze.md`, `docs/audit-firenze/` | approvato (D13) |
| F02 contratti a più aree | `contracts/` (ADR-F02.md) | `pipeline/.venv/bin/python contracts/validate.py` |
| F03 acquisizione, 14 fonti nella baseline; fonti aggiunte alla scena fuori baseline | `pipeline/` (REPORT-F03.md) | `pipeline/.venv/bin/python pipeline/validate_records.py` |
| F04 rete e ingressi | `network/` (REPORT-F04.md) | `pipeline/.venv/bin/python network/test_rete_firenze.py` |
| F05 edifici e verde | `geometry/` (REPORT-F05.md) | `pipeline/.venv/bin/python geometry/test_geometrie_firenze.py` |
| F06 accessibilità | `analysis/` (REPORT-F06.md) | `bash analysis/run.sh` |
| F07 ombre | `shadow/` (REPORT-F07.md) | `pipeline/.venv/bin/python shadow/test_ombre.py` (90 s) |
| F08 scenari | `scenarios/` (REPORT-F08.md) | `bash scenarios/run.sh` (15 min senza cache) |
| F09 scena 3D, con livelli accessibilità, ombra e scenari | `scene/firenze_novoli/` (ADR-F09.md) | `pipeline/.venv/bin/python scene/firenze_novoli/test_build.py` e verifica nel browser |
| F10 servizio e MCP `dt-firenze` | `service/` (REPORT-F10.md) | `service/.venv/bin/python service/test_service.py` |
| F11 verifica in linguaggio naturale | `nl/firenze_novoli/` (REPORT.md) | `service/.venv/bin/python nl/firenze_novoli/test_nl.py` (30 s); giro rifatto dopo D19-D20 |

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/ (funziona anche senza rete: three.js è in `vendor/`)

Ricerca sui gemelli già esistenti a Firenze: `docs/research/gemelli-firenze.md`.

## Risultati principali (non validati sul posto)

- Accessibilità a 1,2 m/s, quote sui 3.296 civici entro 10 minuti: Polo delle Scienze Sociali 28% (54% entro 15, mediana 14 min; 7 ingressi, il più vicino vince), scuola Vamba 39%, fermate T2 San Donato - Università 24%, Regione Toscana 30%, Torre degli Agli 39%. Con un solo ingresso del Polo la quota a 10 minuti scende al 24-28%.
- Ombra sui percorsi fermata T2 → Polo, 12:30-13:30: R01 (San Donato - Università → D15, 429 m) in ombra al 30% a luglio e al 72% a settembre; R02 (Regione Toscana → D15) al 15% e al 42%. Alberi e vegetazione LiDAR pesano meno di 2 punti.
- Scenari: filare su R01 (versione 3, stessa regola sul nuovo R01, tratto 198-258 m) -0,36 minuti di sole a mezzogiorno di luglio, da -0,11 a -0,63 con la chioma; a settembre -0,41. Pensilina alla fermata bus Guidoni Barsanti: a mezzogiorno di luglio l'area di attesa passa da 0% a 40% d'ombra.

- Scenari aggiunti (10 ottobre): pensiline S5 (fermata bus Regione Toscana, area di attesa da 0% a 40% d'ombra a mezzogiorno di luglio) e S6 (Di Novoli Sn, già all'ombra a mezzogiorno). Filari nuovi su R02 e verso Vamba non possibili con la regola di S1 (su R02 ricade su S1).
- Nuovi livelli nella scena (10 ottobre): particelle catastali con ricerca per foglio e particella; temperatura delle superfici Landsat (41 giornate estive 2023-2026) con l'aria della stazione SIR Firenze Università; qualità dell'aria 2025 dalle 6 stazioni ARPAT di Firenze (la più vicina, FI-MOSSE, a 745 m dal riquadro).

- Ricognizione del catalogo regionale (10 ottobre): 15 fonti nuove fuori baseline, tutte CC BY. Nella scena: farmacie, stalli per disabili, bike e car sharing, varchi dello Scudo Verde, aree giochi, cani e sportive come punti; aree verdi, pericolosità idraulica PGRA, alluvione del 1966, classi acustiche, strade in zona 30 e residenti 2011 per sezione come aree colorate sul terreno. I residenti 2011 non entrano ancora nell'accessibilità (resta sui civici).

## Limiti principali

- Ombra misurata sull'asse della rete, non sulla linea dove si cammina.

- Rete solo OSM, lato del marciapiede ignoto. Ingressi del Polo: un civico del Comune per edificio dell'Ateneo (indirizzi dal report di accessibilità dell'Ateneo), non verificati sul posto; il civico non è per forza la porta (`network/firenze_novoli/verifica_ingressi_polo.md`).
- La fermata San Donato - Università sta circa 100 m fuori dal riquadro FP: in scena c'è il terreno, non gli edifici attorno.
- Civici come punti d'indirizzo, non persone. Dal 18 ottobre (F4, D45) i residenti 2011 entrano come stima per civico (ripartizione uniforme sui civici della sezione, negozi compresi), accanto alla quota dei civici; mai al posto di essa.
- Ombra solo sui percorsi campione: non si sa quanti residenti arrivano a un rifugio camminando soprattutto all'ombra (domanda 3 del report F4).
- Pagina della verifica sul posto non provata in un browser sul worker (F4): aprirla e stamparla dal Mac.
- Vegetazione LiDAR come prisma opaco pieno: limite superiore dell'ombra.
- Altezze LiDAR 2023 con unità volumetriche 2011, portici ignoti, datum verticale non confermato.
- GTFS bus congelato valido fino al 29/10/2026: è una finestra mobile di tre settimane. Al 16/10 le fermate della zona sono identiche (più una nuova) e il tram è invariato: i calcoli usano solo le posizioni, nessun ricalcolo. Snapshot del 16/10 fuori baseline.
- Rifugi climatici (F2): ingressi = civici agli indirizzi dichiarati dal Comune, non verificati; orari ignoti (biblioteca non sempre aperta); nessuna ombra lungo il percorso; solo i 7 rifugi entro 700 m dal riquadro; Parco delle Cascine escluso (ingressi non fra i civici).
- Indicatore di costo (F2, F3): ombra di un albero adulto contro il costo d'impianto di un albero da vivaio (platano orientale 18/20 per D36; voce di piantagione scelta dall'agente, da confermare); scavo, pavimentazione, sottoservizi e manutenzione esclusi. Pensiline e tende senza prezzo nei calcoli: i costi unitari ANAC (F3) sono solo un riferimento.
- Ombra dei percorsi RC1-RC5 (F3) calcolata sul worker: da confrontare col Mac (D30).
- Mac e Linux (D39): i GeoJSON ora hanno coordinate arrotondate; il confronto dei byte col Mac è da fare (`scripts/impronte.sh`, report F3). Restano diversi fra le due macchine i GeoPackage riscritti in `data/norm` (stesso contenuto, o differenze all'ultima cifra in `h_chm`) e i gzip degli asset della scena (zlib diversa): per questi fa fede il file del Mac.
- Nessuna validazione sul posto.

## Decisioni prese dall'utente

- D12: pilota a Firenze, Novoli - Firenze Nova.
- D13: riquadro FP, destinazioni Polo, T2, Vamba; rete con margine di 700 m solo OSM.
- D14: chioma LiDAR senza albero censito inclusa nelle ombre; scelte F03-F05 confermate; scena con l'approccio di Padova.
- D17 (10 ottobre): pensilina S2 spostata alla fermata Guidoni Barsanti (a Forlanini Polo non c'è spazio, verificato su Street View).
- D16 (10 ottobre): filare S1 rifatto con la regola delle aree pedonali del Comune; la versione 1 cadeva fra carreggiata e binari T2 su Via di Novoli.
- D18 (10 ottobre): i due CSV Life Escapos tolti da tutta la storia di git (anche dal tag `pilota-pisa-z2`); copia della storia precedente in `../digital-twin-firenze-prima-pulizia.bundle`.
- D19 (10 ottobre): ingressi del Polo = 7 civici del Comune, uno per edificio dell'Ateneo (D1, D4, D5, D6, D10, D14, D15); per ogni origine vince il più vicino. Prima: due ingressi OSM (biblioteca e una corte interna).
- D20 (10 ottobre): fermata T2 San Donato - Università (`FM9055`, indicata dall'Ateneo) fra le destinazioni; R01 parte da lì (prima da Torre degli Agli). S1 rifatto in versione 3; S2 resta a Guidoni Barsanti (regola rifatta sui nuovi ingressi).
- D21 (10 ottobre): dati ARPAT usati (stazioni e archivio orario pubblico del sito, non l'API dell'app), anche nella scena online, con le due licenze delle note legali dichiarate. Supera la clausola ARPAT di D15 e la decisione aperta sui dati ARPAT.
- D22 (10 ottobre): niente webcam. Nessuna webcam pubblica entro 1 km da Novoli e nessuna fonte con licenza di riuso.
- D23 (10 ottobre): pannello della scena a schede (Livelli, Sole, Analisi, Interventi, Legenda) sul modello di Padova, tema sempre chiaro. Una variante con stile proprio (pietra serena e cotto) è stata provata e scartata da Luca. Nuove fonti fuori dalla baseline congelata: catasto, Landsat, SIR, ARPAT.
- D24 (10 ottobre): protezione civile dal Comune di Firenze (aree di attesa e di assistenza, CC BY 4.0), non da Cittadino Informato di ANCI che li ripubblica senza licenza. Da Cittadino Informato solo i punti critici per allagamento, dopo che ANCI avrà chiarito la licenza. Nella scena: icone AT e AA per le aree sul terreno disegnato (solo AA13), elenco con la distanza sotto il livello per le altre (AT18, AA14, AA15), come per le stazioni ARPAT.
- D25 (16 ottobre): primo traguardo è un ufficio del Comune di Firenze che chiede una proposta sul caso caldo estivo (ombra, rifugi climatici, costi degli interventi). Piano in [PIANO-DECOLLO.md](PIANO-DECOLLO.md).
- D26 (16 ottobre): una giornata a settimana fino a fine gennaio 2027.
- D27 (16 ottobre): il piano sta nel repo, aggiornato a ogni sessione nel suo registro.
- D28 (16 ottobre): l'MCP remoto va sulla macchina di prova.
- D29 (17 ottobre): ramo `agente/f1` unito su `main` dopo `make test`, lint e validate verdi sul Mac; CI verde.
- D30 (17 ottobre): dati del worker = copia di `data/raw` e `data/norm` del Mac (baseline, stessi job_id); `data/work` (semilavorati di Pisa) non copiata. In più, percorsi campione e test indipendenti dagli identificativi `adr_fi_*`, usando `CODICECIVI` (domanda 1, a+c).
- D31 (17 ottobre): l'MCP sulla macchina di prova lo installa chi gestisce la macchina, seguendo `service/INSTALLA-REMOTO.md`, con token unico per i colleghi e proxy HTTPS; l'agente fa da supporto. (domanda 2).
- D32 (17 ottobre): i 7 rifugi climatici entro 700 m entrano ora fra le destinazioni, dopo D30 (domanda 3).
- D33 (17 ottobre): costi degli interventi con l'indicatore "metri quadri d'ombra per mille euro" solo per i filari, dichiarando che le pensiline non hanno un prezzo pubblico; in parallelo ricerca di prezzari comunali riusabili per le pensiline. Nessun costo ipotetico senza fonte (domanda 4).
- D34 (17 ottobre): `playwright` fuori dai requirements, installato quando serve; gli esempi del documento tecnico restano quelli del 10 ottobre e si rifanno dopo l'installazione remota (domande 5 e 7).
- D35 (17 ottobre): ramo `agente/f2` unito su `main` dopo `make test` verde sul Mac; l'hash di `job_e1e75455f7511f7d_archi_usati.geojson` è stato ricalcolato sul Mac (stessi valori, byte diversi su Linux).
- D36 (17 ottobre): filare S1 = platano orientale, circonferenza 18/20 (voce TOS26_PR.P45.003.A91, 412,07 euro). Regola: specie da ombra più piantata dal Comune entro 400 m dal tratto fra gli alberi del censimento con circonferenza fino a 25 cm, escluse le forme colonnari (cipressi, pioppi cipressini e tremuli): platano orientale, 29 alberi, circonferenza mediana 17 cm (32 e 18,8 cm entro 800 m). L'indicatore diventa un numero solo; resta dichiarato che l'ombra è a maturità e il prezzo è di un albero da vivaio (domanda 1 del report F2).
- D37 (17 ottobre): pensiline: chiedere all'ufficio del Comune il costo del piano delle 72 pensiline per gli autobus (62 nuove e 10 sostituite, approvato dalla Soprintendenza a giugno 2026, importo non pubblicato). Intanto, come ordine di grandezza dichiarato: Prezzario Piemonte 2025 (CC BY 4.0) e costi unitari ricavati dagli open data ANAC sui contratti pubblici (CC BY-SA 4.0, non CC BY come scritto in origine: vedi D41). Controllati il 17 ottobre senza voci utili: prezzario Puglia 2023 (nessuna voce per pensiline o tende), comunicati del Comune. Restano fuori dai calcoli le cifre di stampa (Roma: 10 mila euro una fermata normale, 20-25 mila una attrezzata) e i cataloghi dei fornitori (3.700-13.000 euro più IVA, sola fornitura) (domanda 2).
- D38 (17 ottobre): RC3 sostituito da "Polo D15 -> rifugio più vicino per rete", stessa regola di RC4 e RC5 (domanda 3). La scena va ricostruita con rifugi e percorsi RC in una prossima sessione, senza rilascio (domanda 5).
- D39 (17 ottobre): coordinate arrotondate prima di scrivere i file, così Mac e Linux producono gli stessi byte; gli sha256 versionati e la baseline degli scenari si rifanno una volta, con verifica sul Mac. Fino ad allora i calcoli che riscrivono file versionati si verificano sul Mac (domanda 6).
- D40 (18 ottobre): ramo `agente/f3` unito su `main` dopo lint, validate e `make test` verdi sul Mac. Impronte confrontate sui file veloci (rete, accessibilità, geometrie, interventi): i 53 sha256 del Mac coincidono con quelli del worker nel report F3. I file dell'ombra non sono ancora confrontati (2-3 ore di calcolo): si fa quando c'è tempo (domanda 1 del report F3, opzione c).
- D41 (18 ottobre): filare S1 con la voce di piantagione in sede stradale, 2-3 tutori e 1 m³ di terra (135,78 euro ad albero; filare 3.834,95 euro, 38,07 m² d'ombra per mille euro). Da confermare con l'ufficio del verde del Comune (domanda 2).
- D42 (18 ottobre): i costi unitari ANAC (CC BY-SA 4.0) si citano solo come riferimento nei documenti, con attribuzione ad ANAC, e non entrano nei calcoli: il resto del progetto resta CC BY (domanda 3).
- D43 (18 ottobre): pensiline S2, S5, S6 senza costo nei calcoli finché il Comune non dà quello delle 72 pensiline (D37). Nel documento per l'ufficio, come ordine di grandezza citato: mediana ANAC di 4.940 euro a pensilina, fornitura e posa, IVA esclusa (Q1 3.677, Q3 7.263) (domanda 4).
- D44 (18 ottobre): scena con il terreno di oggi; rifugi e percorsi oltre il terreno restano in elenco e tagliati. Si allarga se l'ufficio chiede di vedere i percorsi interi (domanda 5).
- D45 (18 ottobre): sessione F4 su [BRIEF-AGENTE-F4.md](BRIEF-AGENTE-F4.md): residenti stimati per civico dai residenti 2011 per sezione (dichiarata come stima, accanto alla quota dei civici); calcoli di luglio al 15 luglio come gli altri; data invernale della verifica sul posto proposta dall'agente.
- D46 (18 ottobre): ramo `agente/f4` unito su `main` dopo lint, validate e `make test` verdi sul Mac. I 17 job d'ombra della sessione F4 rifatti sul Mac: stessi job_id, geometrie identiche byte per byte (`make impronte`: 55 righe uguali al worker), cambiano solo durate e orari. Difetto noto: `shadow/esposizione.py` legge `ru_maxrss` come KB, ma su macOS è in byte, quindi sul Mac la memoria massima esce 1.024 volte troppo grande (domanda 5 del report F4).
- D47 (18 ottobre): le dieci domande del caso caldo vanno all'ufficio del Comune come bozza al primo incontro; il giro si rifà con le loro parole (domanda 1).
- D48 (18 ottobre): residenti ripartiti su tutti i civici della sezione (D45), con la sensibilità sui soli civici neri accanto (domanda 2).
- D49 (18 ottobre): "camminando soprattutto all'ombra" si calcola nella prossima sessione: ombra alle 14 del 15 luglio sul percorso di ogni civico entro 15 minuti dal rifugio più vicino, soglia 50% del percorso in ombra, dichiarata come scelta nostra da far validare all'ufficio; calcolo a blocchi per la memoria del worker (domanda 3).
- D50 (18 ottobre): verifica sul posto di R01 sabato 12 dicembre 2026 alle 11:00, 13:00 e 14:30, riserva sabato 19 dicembre (si rifà la pagina con i due comandi del report F4). La pagina va aperta e stampata una volta sul Mac (domanda 4).
- D51 (18 ottobre): sessione F5 su [BRIEF-AGENTE-F5.md](BRIEF-AGENTE-F5.md), in ordine di priorità: ombra sui percorsi dei civici verso i rifugi (D49), difetti 4, 5, 7 e 8 dell'MCP, scheda per il primo incontro con l'ufficio, orari dei rifugi, prototipo dell'ombra sul marciapiede solo su R01 (fuori dai risultati ufficiali).
- D15: obiettivo POC sugli open data; Pisa accantonata nel tag `pilota-pisa-z2`; solo fonti riusabili (Life Escapos tolto); ARPAT solo con licenza dichiarata.

## Decisioni aperte (dell'utente)

1. Comune, DISIT o progetti di ricerca (DANTE, MIRIFICUS): concorrenza o collaborazione. Decisione dopo il POC.

## Prossimi passi possibili

Revisione del codice: R1-R6 chiusi. Due regole emerse dalle correzioni:
- Chi modifica `analysis/accessibilita.py` o `shadow/ombre.py` deve aggiornare il loro hash in `scenarios/firenze_novoli/baseline.json`, con una nota che riporta l'hash vecchio, e rieseguire il confronto degli scenari: se la modifica non deve cambiare i risultati, deve uscire identico a `confronto.json`; altrimenti va rifatto `scenarios/run.sh`. Senza questo passo `compare_scenarios` rifiuta il confronto (`incompatible_baseline`).
- La cache del servizio si svuota da sola quando cambiano il codice dei motori o i file di dati che leggono (impronta in `service/cache/<area>/impronta.txt`). Gli job_id non cambiano.

1. Altri difetti aperti del servizio emersi da F11 (elenco in `nl/firenze_novoli/REPORT.md`, punti 4-10). I primi tre sono chiusi il 10 ottobre: tool `list_scenarios`, metriche `served_count_*`, accessibilità verso almeno una di più destinazioni (le tre fermate T2 insieme: 53% dei civici entro 10 minuti). Il test del registro NL e i replay sono passati nella revisione; il giro con un nuovo client non è stato rifatto.
2. Prossima sessione: "camminando soprattutto all'ombra" (D49) e correzione della memoria misurata su macOS (D46). Da chiedere al Comune: costo del piano delle 72 pensiline (D37), voce di piantagione del filare (D41); da mostrare all'ufficio: le dieci domande in bozza (D47).
3. Validare sul posto un percorso e un intervento: ingressi, linea effettiva del marciapiede e ombra osservata. Kit pronto per R01 in `docs/verifica-posto/` (F4): sabato 12 dicembre 2026, ore 11:00, 13:00 e 14:30.

## Come lavora la sessione

Integratore (sessione principale) + subagent Sonnet per task, ognuno nella sua cartella. I subagent non possono scrivere file `.md`: restituiscono il testo e l'integratore lo salva. L'integratore riesegue sempre i test prima del commit.
