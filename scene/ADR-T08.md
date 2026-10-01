# ADR-T08: motore grafico e scena Z2

Stato: proposta, 1 ottobre 2026. Redatto dall'agente T08 e salvato dall'integratore.

## Decisione

Libreria cartografica web con estrusioni (MapLibre GL 4.7.1, BSD-3), non il motore geospaziale 3D con terreno (CesiumJS 1.145.0, Apache-2.0). Nei documenti per il cliente si descrive la funzione, non il prodotto.

## Misure

Prototipo minimo per ciascuno in `scene/adr/` (con screenshot), stesso campione reale di Z2: 1.069 edifici più 453 chiome sollevate (1.522 solidi). Sfondo piatto senza tile, Chromium 1440x900, 3 avvii a freddo.

- Primo rendering con i volumi visibili: 0,47-0,56 s contro 1,33-1,86 s.
- Trasferito (libreria + dati): 1,15 MB (libreria 216 KB) contro 2,97 MB (libreria 2.038 KB).
- Richieste di rete: 5 contro 250.
- Decodificato: 1,8 MB contro 11,0 MB.
- fps con camera in rotazione: 75 per entrambi, cioè il limite dello schermo (non è una misura del massimo né di un telefono).
- Scena finale con tile: primo rendering a freddo 0,93-1,18 s su desktop, 0,71 s su telefono.

## Motivi

- Entrambi disegnano volumi sospesi e chiome sollevate (base > 0).
- Pisa è piana (rilievo 0,8-5,5 m): il terreno 3D non dà benefici. Il terreno mondiale del motore 3D richiede account e token.
- Il motore 3D costa 2,6 volte i byte e 6 volte la memoria decodificata.
- La modalità leggera su telefono è più semplice: riempimenti 2D e inclinazione 0.
- Coordinate identiche al modello (EPSG:4326 derivato da 7791).
- Il motore 3D resta l'opzione se serviranno terreno vero (da DTM) o modelli 3D dettagliati.
- Il motore non calcola ombre: mostra solo i poligoni prodotti da T09.

## Scena (`scene/`)

- Edifici 3D (misurati grigi, derivati arancio), terreno piatto, quota base in scheda.
- 12 coperture OSM, fra cui le pensiline della stazione, come volumi sospesi: base = tetto meno 0,4 m di soletta (stima, intervallo 0,2-0,8 m, dichiarata). Portici "ignoto", non disegnati.
- 453 alberi con tronco e chioma sollevata, scheda min/tipico/max. Tronco reso con almeno 0,6 m per visibilità (dichiarato).
- Rete T04 per stato del marciapiede, percorsi campione R01-R09 e V01, ingressi probabili.
- 2.224 civici T06 con selettore destinazione (Battisti, Pellico) e profilo (base, lento, rapido, ridotta). Raggiungibili in 4 classi (5/10/15 min); vietato e dati insufficienti con forme diverse e senza colori della scala, con la nota che non significano "lontano".
- Scheda civico con tempo, distanza, attraversamenti, metri a marciapiede ignoto, scale, deviazione, `job_id`, `manifest_id`, data e "non validato sul posto".
- Tabella degli indicatori T06 come alternativa testuale ai colori; legenda con conteggi, fonti, date, ipotesi e limiti.
- Layer ombre predisposto e vuoto ("Ombre non ancora calcolate"): formato in `scene/data/ombre/index.json`, GeoJSON 4326 con `job_id`, un file per istante.
- URL condivisibili (vista, destinazione, profilo, modalità leggera e livelli nell'hash). Modalità leggera manuale e automatica sotto 48 rem, senza 3D, alberi e rete.

## Apertura

```
pipeline/.venv/bin/python scene/build.py
pipeline/.venv/bin/python -m http.server 8791 --directory scene
```

Poi http://127.0.0.1:8791/index.html (non funziona da `file://`; servono rete per la libreria e i tile).

## Verifiche (browser automatico)

- Nessun errore né avviso in console, desktop e telefono.
- 80 valori della tabella (2 destinazioni x 4 profili) confrontati con `analysis/out/riepilogo.json`: 0 differenze. Conteggi per stato (2.148 / 21 / 55) coincidenti in tutti gli 8 casi.
- sha256 delle tabelle per profilo coincidenti con i manifest.
- Ripristino dello stato da URL verificato. Telefono 390 px: modalità leggera automatica, nessuno scorrimento orizzontale.
- Screenshot: `screenshot_desktop.png`, `screenshot_telefono.png`.

## Limiti

- Il build dipende da file non versionati in `data/norm/` (grafo `rete_z2.gpkg`, tabelle per profilo di T06): si ferma se mancano.
- Nella distribuzione per classi di `riepilogo.json` c'è 1 civico di scarto in 3 casi su 8 (un tempo esattamente a 15 minuti): la scena segue le quote (≤).
- Il NaN nei civici senza indirizzo è stato corretto dall'integratore in `analysis/run.py` (ora `null`, e la scrittura rifiuta i NaN).
- fps su GPU di telefono e peso compresso non misurati. Motore 3D provato solo con terreno piatto. Campione non aperto in un GIS desktop.
- Mappa non accessibile a lettori di schermo: l'alternativa è tabella, scheda e ricerca civico.
- Layer ombre provato con i 3 GeoJSON di T09 (vedi sotto); coperto solo il 15 settembre.

## Ombre T09 collegate (1 ottobre 2026)

- Import in `build.py` da `shadow/out/` (job `job_9e9333b2ee81c302`, motore 0.2.0, manifest copiato): 8:00, 13:00, 16:30 del 15 settembre, casi solo edifici e edifici + alberi tipico. Formato in `data/ombre/index.json`. Poligoni 2D semitrasparenti sotto gli edifici, anche in modalità leggera.
- Legenda con data, ora, elevazione, versione del motore, job_id, classificazione e link al manifest. URL esteso con `ot` (0800/1300/1630) e `oc` (base/alberi).
- Pannello: R01 per le 4 fasce del 15 settembre, frazione in ombra e minuti al sole con tipico e intervallo min-max, più la nota sul lato del marciapiede (fino a 20 punti) e sul percorso sull'asse.
- Verifica: 16 valori del pannello uguali a `shadow/out/riepilogo.json`, console pulita, `screenshot_ombre.png` (16:30 con alberi).
- Limite: il rendering mostra i poligoni, non verifica la geometria delle ombre (lo fa T09 con il suo controllo raster).
