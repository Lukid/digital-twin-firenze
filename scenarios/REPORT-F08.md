# REPORT F08: scenari su Firenze Novoli

Data: 10 ottobre 2026. Comando: `bash scenarios/run.sh` (circa 15 minuti la prima volta, 1-2 minuti con la cache). Test 13 su 13. Risultati `not_validated_locally`. S1 e S2 rifatti il 10 ottobre (versione 2): vedi "Correzione del filare" e "Correzione della pensilina".

## Cosa è cambiato

- `scenarios/` non dipende più da Pisa. L'area viene da DT_AOI (default `aoi_firenze_novoli`) tramite `shadow/ombre.py`, `analysis/accessibilita.py` e `network/rete_lib.py`.
- File piccoli versionati in `scenarios/firenze_novoli/`. Dati grandi in `data/norm/firenze_novoli/scenarios/`.
- Nuovi id `scn_fi_*`, baseline `bas_firenze_novoli_20261009`.
- Baseline degli scenari congelata: 14 snapshot con sha256, grafo e regole, geometrie, poligoni della vegetazione LiDAR (hash del contenuto), parametri delle chiome, origini `address_points`, motori (ombre 0.3.0, accessibilità 0.1.0), job di riferimento di F06, condizioni.
- Ricevitori: R01 e R02, area di attesa di S2, primi 15 archi più usati verso il Polo e verso la fermata T2 Torre degli Agli.
- Condizioni come F07: 15 luglio e 15 settembre 2026, ogni 30 minuti fra 8:00 e 19:00, fasce punta 12:30-13:30 e giornata 8-19, passo 1 m e 5 minuti, 1,2 m/s.
- Un job per scenario e data calcola 9 casi in tre contesti, ognuno con un caso centrale e due estremi: solo edifici; con alberi censiti; con vegetazione LiDAR, che è la base di confronto principale (D14).
- `confronto.confronta()` restituisce i dati per data e contesto: `percorsi[data][contesto][R][fascia][metrica]`, `area_attesa_polo`, `archi_usati[data]`, `per_ora[data]`, `robustezza`. Tolti `ordina()`, `indicatori()` e `sensibilita_pesi()`.

## Scenari e regole (dichiarate prima di guardare i risultati)

- S0: nessun intervento. Delta atteso zero.
- S1: filare di 7 alberi di classe "medio" tipica (11 m, chioma 6 m, imposta 2,5 m), interasse 8 m, sul tratto di 60 m di R01 più al sole dove gli alberi trovano posto.
  - R01: fermata T2 Torre degli Agli → ingresso predefinito del Polo, 1.198 m.
  - Lato: quello da cui arriva il sole alle 13:00 del 15 luglio.
  - Posto di ogni albero: il punto più vicino all'asse, fra 1,5 e 5 m, dentro le aree di circolazione pedonale del Comune ristrette di 0,5 m e fuori dagli edifici. Fonte nuova `src_fi_aree_pedonali` (CC BY 4.0).
  - Scelta del tratto: fra le finestre dove tutti e 7 gli alberi trovano posto, massima frazione media al sole il 15 luglio 12:30-13:30 (caso con vegetazione LiDAR tipica). A parità: media 8-18, poi il primo lungo il percorso. Escluse finestre con attraversamenti, ponti, sottopassi o scale.
  - Tratto scelto: da 593 a 653 m dalla fermata, su un percorso pedonale, sole al 100%. Finestre valide 13 su 984, tutte a pari merito a mezzogiorno; 971 scartate perché manca posto per almeno un albero.
  - Alberi da 6,7 a 9,3 m dall'asse della strada più vicina. L'albero 7 è 0,2 m fuori dal riquadro (segnalazione `fuori_riquadro`).
  - R01 intera è al sole al 92% a mezzogiorno di luglio.
  - Varianti: chioma minima (4 m, imposta 3,5 m, altezza 8 m), chioma massima (9 m, 2,0 m, 14 m).
- S2: pensilina 6 x 2 m (intradosso 2,5 m, tetto 3,0 m) alla fermata bus "Guidoni Barsanti" (OSM `shelter=no`, verifica OSM del 25/04/2024), a 572 m da un ingresso del Polo.
  - Regola: fra le fermate bus del riquadro senza pensilina in OSM, la più vicina in linea d'aria a un ingresso del Polo dove, entro 8 m dal punto OSM, una fascia di 6 x 3,5 m (pensilina più 1,5 m di passaggio libero) parallela alla strada sta tutta dentro le aree pedonali del Comune, ad almeno 1,3 m dall'asse delle ciclabili e fuori dagli edifici. La pensilina occupa i 2 m dal lato della strada.
  - Area di attesa (ricevitore): impronta della pensilina allargata di 1 m per lato, 8 x 4 m.
  - Non alle fermate T2: hanno già la pensilina (campo `pensilina` = 1 nel dataset del Comune sulle fermate tram).
  - Gli id `scn_fi_s2_pensilina_attesa_polo`, `sfc_fi_attesa_polo` e `area_attesa_polo` restano per compatibilità, anche se la fermata non è più quella del Polo.
- Dimensioni dichiarate, fattibilità ignota per tutti (sottoservizi, spazio radicale, proprietà del suolo, permessi, specie).

## Correzione del filare (10 ottobre)

- La versione 1 metteva gli alberi a 3 m fissi dall'asse, da 220 a 280 m di R01, su Via di Novoli.
- Lì Via di Novoli ha due carreggiate a senso unico con i binari della T2 in mezzo (a 5 e 9 m dall'asse). Il lato del sole è quello dei binari: gli alberi cadevano fra la corsia e il binario, l'albero 1 su una strada laterale, l'albero 3 su un attraversamento. Verifica su OSM (API del 10/10/2026, vie 353999361, 508460468, 700263559) e sulle aree pedonali del Comune.
- Il validatore non lo vedeva perché la rete non contiene i binari. Ora segnala `fuori_area_pedonale` per ogni albero fuori dalle aree di circolazione pedonale del Comune (e per le pensiline con meno di metà impronta dentro).
- Tolta la variante "lato opposto": il lato ora viene dai dati. Sul tratto nuovo dall'altro lato non c'è area pedonale.
- Il -0,61 minuti della versione 1 non vale più.

## Correzione della pensilina (10 ottobre)

- La versione 1 stava alla fermata "Forlanini Polo Scienze Sociali", centrata sul punto OSM: il 76% dell'impronta cadeva sulla pista ciclopedonale.
- Street View (Via Forlanini): fra cordolo e facciata del Polo ci sono circa 5 m, con una fascia alberata di 1,5 m dove sta la palina e poi la ciclabile. Una 6 x 2 non ci sta; il posto più vicino dentro le aree pedonali è a 20 m dalla palina.
- Candidate scartate a vista su Street View (immagini 2026): "Del Prete Terzolle" ha già una pensilina (OSM non aggiornato); "Del Prete Caciolle" ha un marciapiede di circa 2,5 m contro un muro, da cui la regola del passaggio libero di 1,5 m.
- "Guidoni Barsanti": solo la palina, su un marciapiede largo davanti a un edificio. Street View usato solo per guardare, non come dato.
- Baseline degli scenari ricongelata: cambia solo l'area di attesa (tutto il resto identico, controllato); tutti i job ricalcolati.
- Il file delle geometrie era stato ricostruito alle 11:45 (stesso contenuto, hash diverso): S0 ricalcolato identico su tutte le 6.831 righe, hash aggiornato in `baseline.json` con nota.

## Risultati principali

Delta rispetto a S0, base con vegetazione LiDAR. Minuti al sole camminando, partenza nella fascia. Negativo = meno sole.

S1, R01, 15 luglio:
- Punta: minuti al sole da 15,35 a 14,80 (-0,55). Ombra da 8,0% a 11,4% (+3,4 punti).
- Giornata: -0,45 minuti, ombra +2,7 punti.
- Il filare agisce da 9:30 in poi: -0,22 minuti alle 11:00, -0,56 alle 12:30, fino a -0,82 per una partenza alle 19:00.

S1, R01, 15 settembre:
- Punta: -0,57 minuti, ombra da 26,6% a 30,2%.
- Giornata: -0,32 minuti.

Varianti di S1 (minuti al sole, punta; giornata fra parentesi):
- 15 luglio: chioma min -0,23 (-0,27), tipica -0,55 (-0,45), chioma max -0,81 (-0,65).
- 15 settembre: chioma min -0,34 (-0,16), tipica -0,57 (-0,32), chioma max -0,76 (-0,46).
- La dimensione della chioma è ora l'incertezza dominante.

S1 sugli altri ricevitori: R02, area di attesa e archi più usati non cambiano.

S2, area di attesa (frazione d'ombra):
- 15 luglio: punta da 0% a 40,1%; giornata da 13,4% a 37,0% (+23,6 punti). Massimo +41,4 punti alle 13:00.
- 15 settembre: punta da 0% a 20,6%; giornata +10,4 punti.
- Vegetazione LiDAR e alberi censiti non toccano l'area di attesa a mezzogiorno: base LiDAR e solo edifici danno la stessa punta.

Accessibilità: delta zero per costruzione (alberi e pensiline non cambiano il grafo). Verificato con hash invariati e ricalcolo del Polo e della fermata Torre degli Agli: stessi job_id e metriche di F06.

Nessun punteggio unico: indicatori separati.

## Test (`test_scenari.py`, 13 controlli)

- Baseline invariata e valida sullo schema.
- Validazione e segnalazioni (edificio, fuori riquadro, carreggiata, fuori area pedonale: il vecchio albero 3 viene segnalato, il nuovo filare no). Fattibilità sempre ignota.
- Determinismo di `scenario_id` e `job_id`.
- S0 uguale al motore senza scenario; S0 contro S0 con delta zero ovunque.
- Un albero aggiunto non riduce mai l'ombra.
- Condizioni comuni fra scenari confrontati.
- Coerenza delle varianti.
- Scelta di S2 verificata nei dati; S2 dentro le aree pedonali (nessuna segnalazione).
- `interventi.geojson`: 21 Point (alberi) e 1 Polygon (pensilina), EPSG:4326.
- Nessuna stringa Pisa, z2, Pellico o Battisti nei file prodotti.

## Scenari aggiunti il 10 ottobre (S3-S6)

- Regole dichiarate prima dei risultati: filari con la regola di S1, pensiline con la regola di S2 (`fermate_pensilina()` in costruisci.py).
- S3, filare su R02: non creato. Una sola finestra valida (481-541 m) su 570, sul tratto finale in comune con R01: gli alberi coincidono con S1 entro 0,3 m. S1 cambia già R02: -0,37 minuti al sole a mezzogiorno di luglio.
- S4, filare verso la scuola Vamba (R09, poi R08) o sulla linea dei 15 archi più usati verso la fermata T2: non creato, nessuna finestra con posto per 7 alberi. R04 e R06 (da un civico verso il Polo) hanno finestre valide, a 30 e 180 m da S1: non usati perché non sono percorsi molto usati.
- S5, pensilina alla fermata bus Regione Toscana (OSM nod_osm_6027223967, 572 m dal Polo, 74 m dalla fermata T2 omonima): area di attesa a mezzogiorno del 15 luglio da 0% a 40,0% d'ombra, giornata da 17,4% a 39,5%; 15 settembre da 0% a 21,9%.
- S6, pensilina alla fermata bus Di Novoli Sn (OSM nod_osm_3216618875, 644 m): area di attesa già all'ombra al 100% a mezzogiorno; giornata di luglio da 78,4% a 84,8%.
- S5 e S6 scelte solo dai dati, senza controllo a vista su Street View. Del Prete Terzolle è esclusa dal controllo a vista (ha già la pensilina) e anche dalla regola dei dati.
- Baseline degli scenari ricongelata: aggiunte solo le aree di attesa sfc_fi_attesa_s5 e sfc_fi_attesa_s6 (controllo nel codice); tutti i job ricalcolati; S0, S1 e S2 identici in tutti i valori.
- Test 16 su 16. Nota: le sezioni sopra riportano ancora i numeri di S1 versione 2 (tratto 593-653 m, -0,55 minuti); i valori attuali (versione 3, tratto 198-258 m, -0,36 minuti) sono in docs/STATO.md.
- Il servizio: `compare_scenarios` espone `area_attesa_polo` ma non le aree di S5 e S6, che per ora si leggono solo in `confronto.json`.

## Limiti

- Ombra misurata sull'asse della rete, non sulla linea dove si cammina.
- Vegetazione LiDAR come prisma opaco pieno: riduce il beneficio dei nuovi interventi.
- Tratto di S1 scelto fra 13 finestre a pari merito.
- Aree pedonali del Comune senza legenda dei codici e senza data di rilievo: usate solo come geometria. Fuori dalla baseline degli scenari (sha256 in `tratto_s1.json`).
- S2: fermata scelta con controllo a vista su Street View, non riproducibile dal codice; la regola dei dati da sola sceglieva fermate già coperte o strette.
- S2 a 572 m dal Polo: mostra l'effetto di una pensilina, non migliora l'accesso al Polo.
- Varianti calcolate su due soli casi.
- Pesi dei tratti in civici, non persone. Nessun flusso pedonale misurato.
- Ombra binaria, nessuna conversione in comfort. Nessuna crescita degli alberi.
- Interventi ipotetici, fattibilità ignota. Nessuna validazione sul posto.
- `contracts/validate.py` legge ancora la baseline degli scenari di Pisa: da puntare a `scenarios/firenze_novoli/baseline.json` quando si spostano i file di Pisa.
