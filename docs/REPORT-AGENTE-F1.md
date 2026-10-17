# Report dell'agente: fase F1

Sessione autonoma del 17 ottobre 2026 sul worker VPS, ramo `agente/f1`, secondo [BRIEF-AGENTE-F1.md](BRIEF-AGENTE-F1.md). Aggiornato alla fine di ogni compito.

## Stato in breve

| Compito | Stato | Commit | Verifica |
|---|---|---|---|
| 0 Ambiente riproducibile | non fatto del tutto: dati di oggi diversi dalla baseline, 5 test falliscono | vedi sotto | `make lint` ok, `make validate` ok, `make test` no |
| 1 MCP remoto in sola lettura | in corso | | |
| 2 Schede delle fonti | fatto, da committare | | `service/.venv/bin/python service/test_schede.py`: OK, 36 fonti, 14 nella baseline |
| 3 Prompt per l'agente | in corso | | |
| 4 Pagina di metodo | fatto, da committare | | `pipeline/.venv/bin/python scene/firenze_novoli/test_build.py`: tutti ok |
| 5 Documento tecnico | bozza scritta | | `service/test_schede.py` controlla la tabella delle fonti |

## Compito 0 - Ambiente riproducibile

Non fatto del tutto: `make lint` e `make validate` passano, `make test` no. Il codice non c'entra: i dati scaricati oggi non sono più quelli della baseline del 9 ottobre. Mi sono fermato qui come chiede il brief e ho documentato le differenze; i compiti successivi usano i dati di oggi, con le differenze dichiarate.

Ambiente:
- `python3.12 -m venv` fallisce sul worker: manca `ensurepip` (pacchetto di sistema `python3.12-venv`, serve sudo). Ripiego: `python3.12 -m venv --without-pip` e pip installato nel venv dalla sua wheel ufficiale. Poi `pip install -r requirements.txt` nei due venv, senza errori.
- `ruff` non c'era: aggiunto a `pipeline/requirements.txt` (0.11.0, la versione della CI) e `make lint` ora usa `pipeline/.venv/bin/python -m ruff`, così funziona anche senza ruff globale.

Dati (`data/`, 1,7 GB): scaricati con `DT_DAY` fissato ai giorni degli snapshot registrati (9, 10 e 16 ottobre), così i file finiscono nelle cartelle attese. Gli snapshot riscritti dallo scarico sono stati confrontati e poi riportati alla versione di git (copia in scratchpad). Confronto degli sha256 delle 14 fonti della baseline:

| Fonte | Esito | Causa |
|---|---|---|
| `snp_osm_firenze_20261009` | diverso (9fcfe51bab23 → a7f4346f7346) | l'estratto `centro-261008.osm.pbf` non è più su Geofabrik (404); usato `centro-261010.osm.pbf`, il più vicino disponibile |
| `snp_fi_civici_20261009` | diverso (3c501a28c48a → 7263e3651c4b) | il Comune ha rinumerato il campo `ID`: stessi 3.296 civici nel riquadro e 13.987 nell'area allargata, stesse posizioni, identificativi `adr_fi_*` diversi |
| `snp_fi_alberi_20261009` | diverso (53b3e903dbbe → bc4a10ab8322) | censimento aggiornato ogni giorno: 2 alberi in meno nell'area allargata, 2 cambi di classe nel riquadro; nel riquadro restano 2.917 |
| `snp_gtfs_at_firenze_20261009` | diverso (6ca6c95f0556 → ffe5c441984d) | finestra mobile di tre settimane; i calcoli usano solo le fermate |
| `snp_rt_uv_firenze_novoli_20261009` | diverso (2197d5f11058 → 43010fc2560e) | WFS riscaricato: stessi byte totali, ordine o contenuto delle pagine diverso; stessi 1.952 volumi nel riquadro |
| `snp_cm_edscol_firenze_20261009` | non scaricato | API del catalogo della Città metropolitana in manutenzione (503) per tutta la mattina; ripiego solo locale, sotto |
| le altre 8 | uguali | |

Fuori baseline: uguali 13 su 22; diversi ARPAT (pagine HTML), aree cani, aree giochi, aree verdi, stalli per disabili, Landsat (contenuto riletto dal catalogo, non analizzato), SIR (giorni fino al 16 ottobre); catasto non scaricato (il servizio WFS risponde "Richiesta non valida" alla stessa richiesta del 10 ottobre).

Ripiego per gli edifici scolastici: gli stessi due layer sono pubblicati dalla Città metropolitana anche come servizio WFS, citato nella stessa scheda del catalogo. Li ho scaricati e convertiti negli zip attesi, solo in `data/` (c'è un file `LEGGIMI-SOSTITUTO.txt` accanto). Non è lo snapshot e non è versionato. Gli ingressi delle scuole che ne escono sono identici a quelli di `network/firenze_novoli/destinazioni.json`. Un ciclo in background riprova l'API fino alle 11:50 UTC e, se torna, scarica il file vero.

Ricostruzione e confronto con i risultati versionati (i file versionati riscritti sono stati riportati alla versione di git; le differenze sono salvate in scratchpad):

- Geometrie (F05): 1.952 volumi e 2.917 alberi nel riquadro, come il REPORT. Nell'area allargata 8.489 alberi invece di 8.491 e 2 alberi del riquadro cambiano classe di circonferenza.
- Ombre (F07): `shadow/run.py` rieseguito per intero. Tutte le frazioni d'ombra e i minuti al sole di `sintesi.json` sono identici. Cambiano solo `alberi_usati` (8.392 → 8.390), un cluster di vegetazione LiDAR in più (3.838 → 3.839, +30 m²) e quindi i job_id. I numeri di REPORT-F07 restano validi.
- Accessibilità (F06): per Polo, tre fermate T2 e Vamba a 1,2 m/s tutte le metriche coincidono con i manifest versionati. I job_id cambiano perché l'hash del job contiene l'impronta del grafo, costruito dall'estratto OSM del 10 ottobre.
- Rete (F04): stessi archi e nodi per componente; cambia `km_in_z2` di tre componenti piccole. `percorsi_firenze.py` si ferma: i percorsi campione sono scritti con gli identificativi dei civici (`adr_fi_31825`, `adr_fi_99342`, ...), che non esistono più.

Esito dei test sul worker, con i dati di oggi:

| Test | Esito | Motivo |
|---|---|---|
| `make lint` | passa | |
| `make validate` | passa (54 validi, 27 non validi respinti) | |
| `geometry/test_geometrie_firenze.py` | passa | |
| `scene/firenze_novoli/test_build.py` | passa | |
| `service/test_schede.py` (nuovo) | passa | |
| `service/test_mcp_remoto.py` (nuovo) | passa, 22 s | |
| `shadow/test_ombre.py` | passa, 2 min | |
| `network/test_rete_firenze.py` | fallisce | `KeyError: 'adr_fi_31825'`: civico di V01 rinumerato |
| `analysis/test_accessibilita.py` | fallisce | `KeyError: 'adr_fi_99342'`: civico di R04 rinumerato |
| `service/test_service.py` | fallisce alla riga 57 | job_id del Polo `job_8c9ce69401b3ae91` invece di `job_9b2e74744a8d2865` (grafo diverso); i controlli dopo non sono eseguiti |
| `scenarios/test_scenari.py` | fallisce | `verifica_baseline`: hash di geometrie, grafo, origini e vegetazione LiDAR cambiati |
| `nl/firenze_novoli/test_nl.py` | fallisce | replay di `job_9b2e74744a8d2865`: job_id e parametri diversi (stesso motivo) |

Conseguenza per il servizio sul worker: `compute_walk_access` e `compute_shadow` funzionano e danno le stesse metriche con job_id nuovi; `compare_scenarios` sugli scenari salvati risponde `incompatible_baseline`, perché la baseline degli scenari controlla le impronte dei dati. È il comportamento voluto (regola sugli hash dei motori in `docs/STATO.md`), ma su questa macchina il confronto fra scenari non è disponibile.

Per avere `make test` verde serve una delle strade della domanda 1.

## Compito 2 - Schede delle fonti

Fatto.

- `service/schede.py` genera `service/schede/INDEX.md` e una scheda per ognuna delle 36 fonti di Firenze (le 14 della baseline e le 22 aggiunte per la scena; le fonti di Pisa restano fuori, D15). Legge solo file versionati: record di fonte, snapshot, `pipeline/t17_firenze.json`, baseline.
- Ogni scheda: editore, scheda del catalogo (o lacuna motivata), risorsa scaricata, presenza nella baseline, licenza con stato della verifica, uso consentito, evidenza e riserva, data del dato, scarichi validi con data, periodo e sha256, campi usati, unità, controlli, limiti.
- Regola di provenienza: la data del dato viene solo dal periodo dichiarato nel record di fonte. La data di modifica della scheda del catalogo compare a parte, con la scritta "non è la data del dato".
- Limiti: avvisi dei controlli, riserva sulla licenza e una tabella di limiti noti presi da `docs/STATO.md` e `docs/FONTI.md` (in `schede.py`, dizionario `LIMITI`).
- Nuovo strumento MCP `get_source_card`: senza argomenti l'indice, con `source_id` la scheda. Contratto in `contracts/schemas/mcp.schema.json` con esempi validi e non validi in `contracts/examples/`. Le schede sono anche risorse MCP (`schede://INDEX.md`, `schede://<source_id>.md`).
- Test `service/test_schede.py` (entra in `make test-fast` e nella CI, non richiede `data/`): schede su disco uguali a quelle generate; tutte le fonti della baseline hanno una scheda; nessun campo di licenza vuoto; date degli scarichi uguali agli snapshot; data del dato uguale al periodo dichiarato; date del catalogo marcate; strumento MCP conforme al contratto; tabella del documento tecnico aggiornata.

## Compito 4 - Pagina di metodo nella scena

Fatto.

- `scene/firenze_novoli/metodo.py` genera `scene/firenze_novoli/metodo.html`: pagina statica, senza script, con lo stile della scena (stessi colori, tema chiaro, D23).
- Contenuto: cosa calcola ogni livello di analisi (accessibilità, ombra, scenari, edifici e alberi, temperatura delle superfici, qualità dell'aria) con metodo, motore, file del risultato, report e fonti; fonti di ogni livello della scena; cosa non sappiamo (limiti di `docs/STATO.md`); limiti della rappresentazione (gli stessi di `assets/index.json`); le 36 schede delle fonti con un'ancora ciascuna; come verificare un numero.
- Raggiungibile dalla scheda Legenda della scena, sezione "Fonti e limiti" (link in `index.html`).
- Accessibilità: lingua, salto al contenuto, un solo titolo di primo livello, titoli in ordine, tabelle con `caption` e intestazioni `scope`, contorno di fuoco visibile, contrasti della scena. A 390 px di larghezza la pagina non scorre in orizzontale (le tabelle scorrono nel loro riquadro).
- Test in `scene/firenze_novoli/test_build.py` (`test_pagina_di_metodo`): pagina aggiornata rispetto a schede e indice, link presente nella scena, un'ancora per ogni fonte, nessun rimando a schede mancanti.
- Prova in locale con `python3 -m http.server` e un browser senza interfaccia installato dentro `service/.venv` (pacchetto `playwright`, browser nella cartella del pacchetto). Il pacchetto non è in `service/requirements.txt`: serve solo per gli screenshot.
- Screenshot: [scena con il link](agente-f1/scena_link_metodo.png), [pagina di metodo](agente-f1/metodo_desktop.png). Nessun rilascio.

## Compito 5 - Documento tecnico per la Regione

Bozza scritta: [DOCUMENTO-TECNICO.md](DOCUMENTO-TECNICO.md), circa 3.800 parole (8-9 pagine).

- Sezioni: obiettivo, area, fonti e licenze, motori e metodo, servizio di interrogazione per assistenti, esempi di domande con risposte reali e job_id, limiti, come si replica su un'altra area.
- Tabella delle fonti generata dalle schede (`service/schede.py --tabella`) e controllata da `service/test_schede.py`. Nella tabella l'editore della copia Landsat è descritto per funzione.
- Esempi presi dal giro di verifica del 10 ottobre (`nl/firenze_novoli/`), con i job_id versionati.
- Nessun nome di prodotto software (controllato con una ricerca dei nomi usati nel progetto), nessun importo, nessun nome di persona. Citati come protocollo e standard: MCP, JSON Schema, GTFS, WFS, EPSG; come fonti di dati: OpenStreetMap, Landsat.

## Fase F2 - preparazione (solo analisi)

### Rifugi climatici

Fonti della baseline: `src_fi_rifugi_aree` (41 aree fresche in città) e `src_fi_rifugi_biblioteche` (7 biblioteche), dato dichiarato del 18 giugno 2026. Distanze in linea d'aria dal riquadro FP:

| Rifugio | Tipo | Ombra dichiarata | Ingresso dichiarato | Distanza dal riquadro |
|---|---|---|---|---|
| Giardino di Piazza delle Medaglie d'Oro (02399) | area fresca | 70% | Via Arcangelo Corelli 19; Via Francesco Baracca 135d | dentro |
| Biblioteca Filippo Buonarroti | biblioteca | - | Viale Guidoni 188 | 37 m |
| Giardino di piazza dei Cavalieri di Vittorio Veneto (01523) | area fresca | 97% | Via Luigi Morandi 2 | 118 m |
| Giardino di via Luigi Morandi (01631) | area fresca | 71% | Via Guglielmo Jervis 13 | 235 m |
| Giardino di via Arturo Toscanini (05409) | area fresca | 81% | Via Arturo Toscanini 20 | 245 m |
| Giardino di via Arturo Toscanini (02394) | area fresca | 81% | Via Arturo Toscanini 5 | 252 m |
| Giardino di piazza Giacomo Puccini (01545) | area fresca | 78% | Piazza Giacomo Puccini 24/A | 555 m |
| Parco delle Cascine, Galoppatoio dei Barberi (02556) | area fresca | 92% | Piazzaletto dell'Indiano 3; Viale delle Cornacchie 2 | 698 m |

Nel riquadro c'è un solo rifugio; entro i 700 m del margine della rete ce ne sono altri 7 (6 aree e la biblioteca). Gli altri 34 e le altre 6 biblioteche sono oltre 700 m.

Accessibilità verso il più vicino: non calcolata. Lo strumento con più destinazioni (`compute_walk_access` con più `destination_ids`) accetta solo le destinazioni di `network/firenze_novoli/destinazioni.json`, e i rifugi non ci sono. Per calcolarla servono:
1. aggiungere i rifugi alle destinazioni in `network/destinazioni_firenze.py`, con un ingresso per indirizzo dichiarato (civico del Comune all'indirizzo dell'ingresso, come per il Polo in D19);
2. rifare la rete (`network/build_firenze.sh`) e aggiornare l'hash del motore in `scenarios/firenze_novoli/baseline.json` se cambia;
3. chiamare `compute_walk_access` con gli 8 id insieme: per ogni civico vince il più vicino.
È una modifica della rete e delle destinazioni: va decisa da Luca (domanda 3).

### Percorsi campione proposti verso i rifugi

Stesse regole di R01-R10: origine una fermata T2 o un civico a distanza nota, destinazione l'ingresso più vicino per rete, percorso minimo sul grafo, stato "da verificare". Ombra non calcolata.

| Proposta | Origine | Destinazione | Perché |
|---|---|---|---|
| RC1 | Fermata T2 Novoli - Regione Toscana (`ent_gtfs_fm9056`) | Giardino di Piazza delle Medaglie d'Oro, ingresso più vicino fra i due dichiarati | unico rifugio nel riquadro, fermata più vicina |
| RC2 | Fermata T2 Torre degli Agli (`ent_gtfs_fm9057`) | Biblioteca Filippo Buonarroti, Viale Guidoni 188 | rifugio al chiuso, utile nelle ore più calde |
| RC3 | Ingresso del Polo più usato (`ent_civ_d15`) | Giardino di piazza dei Cavalieri di Vittorio Veneto, Via Luigi Morandi 2 | rifugio con più ombra dichiarata (97%), vicino al Polo |
| RC4 | Civico di R05 (Via Francesco De Pinedo 17, `adr_fi_108673`) | rifugio più vicino per rete fra gli 8 | civico tipo a circa 400 m dal Polo: confronto con R05 |
| RC5 | Accesso della scuola primaria Vamba (`ent_cm_FIEE86002G_0`) | rifugio più vicino per rete fra gli 8 | uscita da scuola nei giorni caldi di giugno e settembre |

Gli ingressi dei rifugi sono indirizzi: vanno agganciati a un civico del Comune e verificati, come per il Polo.

### Prezzario pubblico

Fonte trovata: Prezzario dei Lavori della Regione Toscana 2026, sul catalogo regionale (`https://dati.toscana.it/dataset/prezzario-lavori-2026`), approvato con delibera di Giunta n. 1676 del 15/12/2025, valido dal 1 gennaio al 31 dicembre 2026. CSV per provincia, file "2026 Firenze" (`Firenze-Articolo-2026.csv`, 47.239 voci).

Licenza: 76 risorse su 83 del pacchetto 2026 dichiarano CC BY 4.0 (vocabolario nazionale delle licenze), compreso il CSV di Firenze; 7 risorse non dichiarano licenza; la scheda del pacchetto 2026 non ha il campo licenza; il pacchetto padre "Prezzario Lavori" ha licenza `cc-by`. Per il CSV di Firenze la licenza è chiara (CC BY 4.0 sulla risorsa); non è stato fatto un controllo giuridico.

Voci utili trovate (prezzo con spese generali e utili, euro, Firenze 2026):

| Codice | Voce | Unità | Prezzo |
|---|---|---|---|
| TOS26_09.V03.005.003 | Piantagione di albero in sede stradale, un tutore, terra nuova 60x60x60 cm (esclusi scavo e pianta) | cad | 43,41 |
| TOS26_09.V03.005.004 | come sopra, 2-3 tutori, terra nuova 100x100x100 cm | cad | 135,78 |
| TOS26_09.V03.005.007 | Piantagione in sede stradale con ancoraggio sotterraneo della zolla, terra 60x60x60 cm | cad | 94,99 |
| TOS26_09.V03.005.008 | come sopra, terra 100x100x100 cm | cad | 163,63 |
| TOS26_PR.P45.003.257-259 | Bagolaro (Celtis australis) in contenitore, circonferenza 16/18, 18/20, 20/25 cm | cad | 389,84; 539,99; 643,21 |
| TOS26_PR.P45.003.A90-A92 | Platano, circonferenza 16/18, 18/20, 20/25 cm | cad | 322,90; 412,07; 497,16 |
| TOS26_PR.P45.003.D37-D38 | Tiglio, circonferenza 16/18, 18/20 cm | cad | 343,88; 443,15 |

Mancano nel prezzario regionale: pensiline per le fermate (nessuna voce; "pensilina" compare solo negli impianti fotovoltaici), tende e teli ombreggianti per spazi pubblici, scavo della buca d'impianto come voce del verde (da cercare fra gli scavi), manutenzione pluriennale dell'albero (ci sono le potature). Per pensiline e tende serve un'altra fonte: prezzari comunali o capitolati di gara pubblicati con licenza di riuso. Non cercati in questa sessione.

## Domande per Luca

1. Dati del worker diversi dalla baseline (compito 0). Opzioni:
   - a) copiare `data/` dal Mac al worker (e poi sulla macchina di staging): stessi job_id, `make test` verde, nessuna modifica. **Raccomandata**, anche per l'installazione remota.
   - b) congelare una nuova baseline con i dati di oggi (`fonti_firenze.py baseline --force`, vietato in questa sessione) e rifare F04-F11: numeri uguali, job_id e REPORT da aggiornare.
   - c) rendere i percorsi campione e i test indipendenti dagli identificativi dei civici (chiave = indirizzo o posizione): serve comunque, perché il Comune può rinumerare di nuovo. Da fare insieme ad a) o b).
