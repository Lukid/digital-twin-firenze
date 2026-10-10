# REPORT F08: scenari su Firenze Novoli

Data: 10 ottobre 2026. Comando: `bash scenarios/run.sh` (circa 15 minuti la prima volta, 1-2 minuti con la cache). Test 13 su 13. Risultati `not_validated_locally`.

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
- S1: filare di 7 alberi di classe "medio" tipica (11 m, chioma 6 m, imposta 2,5 m), interasse 8 m, a 3 m dall'asse, sul tratto di 60 m di R01 più al sole.
  - R01: fermata T2 Torre degli Agli → ingresso predefinito del Polo, 1.198 m.
  - Scelta del tratto: massima frazione media al sole il 15 luglio 12:30-13:30 (caso con vegetazione LiDAR tipica). A parità: media 8-18, poi il primo lungo il percorso. Escluse finestre con attraversamenti, ponti, sottopassi o scale.
  - Tratto scelto: da 220 a 280 m dalla fermata, sole al 100%. Le finestre a pari merito sono 598 su 984: la posizione esatta è arbitraria dentro quel gruppo.
  - R01 intera è al sole al 92% a mezzogiorno di luglio.
  - Lato: ipotesi, quello da cui arriva il sole alle 13:00 del 15 luglio.
  - Varianti: chioma minima (4 m, imposta 3,5 m, altezza 8 m), chioma massima (9 m, 2,0 m, 14 m), lato opposto.
- S2: pensilina 6 x 2 m (intradosso 2,5 m, tetto 3,0 m) alla fermata bus "Forlanini Polo Scienze Sociali".
  - Non alle fermate T2: hanno già la pensilina (campo `pensilina` = 1 nel dataset del Comune sulle fermate tram; in OSM non risulta).
  - Questa fermata: OSM la dà con `shelter=no` (verifica OSM del 15/02/2026), a 55 m dal secondo ingresso del Polo. Area di attesa 8 x 4 m.
  - Scartata la fermata "Nuovo Palazzo di Giustizia" vicino a Vamba (84 m, senza pensilina): il Polo è la destinazione principale.
- Dimensioni dichiarate, fattibilità ignota per tutti (sottoservizi, spazio radicale, proprietà del suolo, permessi, specie).
- Segnalazione: l'albero 1 di S1 sta a meno di 3 m dall'asse di una strada carrabile senza marciapiede.

## Risultati principali

Delta rispetto a S0, base con vegetazione LiDAR. Minuti al sole camminando, partenza nella fascia. Negativo = meno sole.

S1, R01, 15 luglio:
- Punta: minuti al sole da 15,35 a 14,74 (-0,61). Ombra da 8,0% a 11,6% (+3,6 punti).
- Giornata: -0,48 minuti, ombra +2,8 punti.
- Il filare agisce da 11:00 in poi: -0,35 minuti alle 11:00, -0,63 alle 12:30, fino a -0,81 per una partenza alle 19:00.

S1, R01, 15 settembre:
- Punta: -0,33 minuti, ombra da 26,6% a 28,7%.
- Giornata: -0,28 minuti.
- Massimo -0,83 minuti alle 10:00, quasi nullo alle 16:30.

Varianti di S1 (minuti al sole, punta; giornata fra parentesi):
- 15 luglio: chioma min -0,37 (-0,30), tipica -0,61 (-0,48), chioma max -0,79 (-0,64), lato opposto 0,00 (-0,18).
- 15 settembre: chioma min -0,22 (-0,16), tipica -0,33 (-0,28), chioma max -0,46 (-0,38), lato opposto 0,00 (-0,11).
- A mezzogiorno il lato opposto non dà beneficio: il lato è l'incertezza dominante.

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
- Validazione e segnalazioni (edificio, fuori riquadro, carreggiata). Fattibilità sempre ignota.
- Determinismo di `scenario_id` e `job_id`.
- S0 uguale al motore senza scenario; S0 contro S0 con delta zero ovunque.
- Un albero aggiunto non riduce mai l'ombra.
- Condizioni comuni fra scenari confrontati.
- Coerenza delle varianti.
- Scelta di S2 verificata nei dati.
- `interventi.geojson`: 28 Point (alberi) e 1 Polygon (pensilina), EPSG:4326.
- Nessuna stringa Pisa, z2, Pellico o Battisti nei file prodotti.

## Limiti

- Percorsi sull'asse della rete: lato del marciapiede ignoto.
- Vegetazione LiDAR come prisma opaco pieno: riduce il beneficio dei nuovi interventi.
- Tratto di S1 scelto fra 598 finestre a pari merito.
- Varianti calcolate su due soli casi.
- Pesi dei tratti in civici, non persone. Nessun flusso pedonale misurato.
- Ombra binaria, nessuna conversione in comfort. Nessuna crescita degli alberi.
- Interventi ipotetici, fattibilità ignota. Nessuna validazione sul posto.
- `contracts/validate.py` legge ancora la baseline degli scenari di Pisa: da puntare a `scenarios/firenze_novoli/baseline.json` quando si spostano i file di Pisa.
