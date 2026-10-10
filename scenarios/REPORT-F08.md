# REPORT F08: scenari su Firenze Novoli

Data: 10 ottobre 2026. Comando: `bash scenarios/run.sh` (circa 15 minuti la prima volta, 1-2 minuti con la cache). Test 13 su 13. Risultati `not_validated_locally`. S1 rifatto il 10 ottobre (versione 2): vedi "Correzione del filare".

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
- S2: pensilina 6 x 2 m (intradosso 2,5 m, tetto 3,0 m) alla fermata bus "Forlanini Polo Scienze Sociali".
  - Non alle fermate T2: hanno già la pensilina (campo `pensilina` = 1 nel dataset del Comune sulle fermate tram; in OSM non risulta).
  - Questa fermata: OSM la dà con `shelter=no` (verifica OSM del 15/02/2026), a 55 m dal secondo ingresso del Polo. Area di attesa 8 x 4 m.
  - Scartata la fermata "Nuovo Palazzo di Giustizia" vicino a Vamba (84 m, senza pensilina): il Polo è la destinazione principale.
- Dimensioni dichiarate, fattibilità ignota per tutti (sottoservizi, spazio radicale, proprietà del suolo, permessi, specie).

## Correzione del filare (10 ottobre)

- La versione 1 metteva gli alberi a 3 m fissi dall'asse, da 220 a 280 m di R01, su Via di Novoli.
- Lì Via di Novoli ha due carreggiate a senso unico con i binari della T2 in mezzo (a 5 e 9 m dall'asse). Il lato del sole è quello dei binari: gli alberi cadevano fra la corsia e il binario, l'albero 1 su una strada laterale, l'albero 3 su un attraversamento. Verifica su OSM (API del 10/10/2026, vie 353999361, 508460468, 700263559) e sulle aree pedonali del Comune.
- Il validatore non lo vedeva perché la rete non contiene i binari. Ora segnala `fuori_area_pedonale` per ogni albero fuori dalle aree di circolazione pedonale del Comune (e per le pensiline con meno di metà impronta dentro).
- Tolta la variante "lato opposto": il lato ora viene dai dati. Sul tratto nuovo dall'altro lato non c'è area pedonale.
- Il -0,61 minuti della versione 1 non vale più.
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
- Base LiDAR, 15 luglio: punta da 85,5% a 86,0%; giornata +2,9 punti. Massimo +15,4 punti alle 15:00.
- Base LiDAR, 15 settembre: punta +1,0 punti; giornata +0,5 punti.
- Solo edifici, 15 luglio: punta da 0% a 39,8%; giornata +17,2 punti.
- Solo edifici, 15 settembre: punta +29,2 punti; giornata +8,6 punti.
- La vegetazione LiDAR copre già buona parte dell'area di attesa. Con il prisma opaco pieno è un limite superiore: il beneficio di S2 nella base principale è probabilmente sottostimato. Da controllare a occhio sul posto o sull'ortofoto.

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
- Scelta di S2 verificata nei dati.
- `interventi.geojson`: 21 Point (alberi) e 1 Polygon (pensilina), EPSG:4326.
- Nessuna stringa Pisa, z2, Pellico o Battisti nei file prodotti.

## Limiti

- Ombra misurata sull'asse della rete, non sulla linea dove si cammina.
- Vegetazione LiDAR come prisma opaco pieno: riduce il beneficio dei nuovi interventi.
- Tratto di S1 scelto fra 13 finestre a pari merito.
- Aree pedonali del Comune senza legenda dei codici e senza data di rilievo: usate solo come geometria. Fuori dalla baseline degli scenari (sha256 in `tratto_s1.json`).
- S2: la pensilina cade per il 76% fuori dalle aree pedonali, sopra una pista ciclabile (segnalazione `fuori_area_pedonale`). Da rivedere come il filare.
- Varianti calcolate su due soli casi.
- Pesi dei tratti in civici, non persone. Nessun flusso pedonale misurato.
- Ombra binaria, nessuna conversione in comfort. Nessuna crescita degli alberi.
- Interventi ipotetici, fattibilità ignota. Nessuna validazione sul posto.
- `contracts/validate.py` legge ancora la baseline degli scenari di Pisa: da puntare a `scenarios/firenze_novoli/baseline.json` quando si spostano i file di Pisa.
