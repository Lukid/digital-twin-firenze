# ADR-F09: scena 3D statica di Firenze Novoli

Stato: implementata; documentazione allineata nella revisione del 10 ottobre 2026. Sostituisce ADR-T08 (scena di Pisa, libreria cartografica).

## Decisione

La scena del pilota è un sito statico con un motore 3D generico (three.js 0.180.0, MIT, copiato in `vendor/three/`: la scena non chiede niente alla rete), sul modello osservato a Padova. Nessun server a runtime. Gli asset sono precotti da una pipeline Python offline. Funziona con `python3 -m http.server` nella cartella.

Motivi:
- Firenze Novoli ha rilievo reale (circa 38-55 m nel riquadro): il terreno 3D da DTM serve. Con la libreria cartografica serviva un servizio di terreno.
- Le ombre del sole sono del motore: luce direzionale con mappa d'ombra. Il sole è calcolato in JS per il centro del riquadro.
- Gli alberi sono istanze (2.917 chiome e tronchi): una sola chiamata di disegno per tipo.
- Gli asset correnti occupano circa 1,57 MB compressi, somma dei byte dichiarati e verificati nell'indice; libreria 3D esclusa.

## Cosa si riprende da Padova

- Motore generico, luce direzionale con ombre, istanze per gli alberi.
- Sito statico, asset gzip con sha256 e dimensione in un indice.
- Terreno da DTM LiDAR 2023, passo 10 m.
- Geometrie già nel piano locale in metri.
- Fonti e limiti scritti nei dati e mostrati nella pagina: titolo, ente, licenza, data di scarico, URL.
- Resa cartografica (aggiunta il 10 ottobre 2026): terreno chiaro con verde, acqua e strade da OSM dipinti in una texture, tetti in tono terracotta con variazione per edificio, foschia chiara e piano di fondo che fa sfumare il bordo del riquadro, nomi dei luoghi e delle vie principali.

## Cosa non si riprende

- I 156 riquadri e i due livelli di dettaglio: per 2 km² basta un solo pacchetto.
- Il formato `.js` con funzione di ricezione: i file sono `.json.gz`, letti con fetch e decompressi dal browser.
- Edifici con tetti e monumenti modellati: i volumi sono estrusioni con altezza LiDAR.
- Ortofoto sul terreno: le ortofoto regionali (2016 Consorzio TeA, 2019 e 2022 AGEA, servizio WMS `ows_ofc` della Regione Toscana) sono concesse alla Regione per fini istituzionali e non se ne consente il download (testo del servizio letto il 10 ottobre 2026). Su dati.toscana.it non c'è un'ortofoto aperta di Firenze. L'unica alternativa sarebbe chiamare il WMS dalla pagina, che va contro "la scena non chiede niente alla rete" e resta da decidere.
- Ricerca per indirizzo e webcam: nessuna webcam pubblica con licenza di riuso vicino a Novoli (D22). Catasto, temperatura delle superfici e stazioni dell'aria sono stati aggiunti il 10 ottobre (vedi sotto).

## Piano e coordinate

Origine: centro del riquadro FP in EPSG:7791. Piano del motore: x = est, y = alto, z = -nord, in metri. La quota è relativa a 48,2 m s.l.m. (`quota_riferimento_m` nell'indice). I lon/lat dei dati aperti sono trattati come RDN2008, come nel resto della pipeline.

## Formato degli asset

Cartella `assets/`. `index.json` elenca per ogni asset file, byte, byte decompressi, sha256 e numero di elementi. Contiene anche area, livelli (con le fonti di ciascuno), fonti e limiti. La pagina verifica la dimensione prima di usare un asset e verifica sha256 quando `crypto.subtle` è disponibile (contesto sicuro, per esempio localhost o HTTPS).

- `terreno.json.gz`: griglia regolare (nx, ny, passo, x0, z0), quote in centimetri relative alla quota di riferimento, medie di cella dal DTM 0,5 m.
- `edifici.json.gz`: `posizioni` (Float32 in base64, triangoli non indicizzati: tetto e muri) e un record per volume (id, numero di vertici, h, h_min, h_max, z_base, classe_h, tipo, fonte, area_m2, presente_2023, flag, h_uv, h_lidar). I volumi scendono 1,5 m sotto la quota di base.
- `alberi.json.gz`: un record per albero (x, y, z, h, chioma, imposta, tronco, specie, circonferenza, classi, motivo della stima, intervalli min e max).
- `rete.json.gz`: tratti della rete pedonale dentro il riquadro (id, nome, tipo, stato del marciapiede, lunghezza, coordinate).
- `punti.json.gz`: destinazioni e ingressi, fermate tram, scuole, rifugi (con contorno), barriere.
- `mappa.json.gz`: aree verdi e acqua (anelli di poligoni) dal layer `multipolygons` dell'estratto OSM (`data/raw/osm_firenze/…/*.osm.pbf`, letto con filtro sul riquadro più il margine) e strade dal layer `highway` di `osm_firenze.gpkg`, con larghezza indicativa per classe. La pagina li dipinge in una texture del terreno (4096 px, 2048 sul telefono).
- `etichette.json.gz`: nomi dei luoghi scelti a mano fra le aree OSM con nome (`LUOGHI` in build.py) e delle vie principali (`VIE`), con posizione nel piano. La pagina li mostra come testo HTML e nasconde quelli che si sovrappongono.
- `accessibilita.json.gz` e `ombra.json.gz`: presenti solo se esistono i dati di ingresso.
- `catasto.json.gz` (livello "Particelle catastali", fonte `src_fi_catasto`): `particelle[]` con `rif` ("foglio 42B particella 123"), `f` (foglio con allegato), `p` (particella o STRADA00n/ACQUA00n), `t` (particella, strada, acqua), `a` (poligoni, ognuno [esterno, buchi...], anelli piatti [x, z, ...] nel piano del motore a 2 decimali); `fogli[]` con `f`, punto dell'etichetta `x`, `z` dentro FP, `agg` (data di aggiornamento del foglio) e `a`. Ogni edificio in `edifici.json.gz` ha `cat`: i riferimenti delle particelle che contengono almeno il 50% della sua superficie (al massimo una, `[]` se nessuna). È un aggancio geometrico, non verificato sugli atti.
- `temperature.json.gz`: temperatura delle superfici Landsat 8-9 su una griglia di 30 m (x0, z0 centro della prima cella, riga 0 a nord). Una griglia per data in decimi di °C (-32768 = non valido), più la media delle date valide, il numero di date sopra 40 °C e le date valide per cella. La pagina la dipinge su una copia del terreno, semitrasparente, e legge una cella al clic.
- `meteo.json.gz`: massime e minime giornaliere della stazione SIR Firenze Università (CC BY-SA 4.0) e le date Landsat, per confrontare superficie e aria nello stesso giorno. Non ha una riga nel pannello: compare nel livello temperature.
- `aria.json.gz`: 6 stazioni ARPAT con valori di stazione, nessuna interpolazione e nessuna mappa. Tutte fuori dal riquadro, con `fuori_riquadro` true e distanza in metri. Per ogni inquinante: media annua 2025, superamenti nel senso del D.Lgs. 155/2010, limite, percentuale di dati validi (sotto il 90% la media non vale ai fini di legge) e ultimo valore. Il 2026 è escluso perché esce solo dall'API dell'app ARPAT. La pagina le mostra come elenco nella scheda Analisi.
- Temperatura, meteo e aria sono opzionali: build.py li scrive solo se esistono i file normalizzati. Il catasto e i tematismi sono invece costruiti sempre e richiedono i relativi input locali.

## Pannello

Schede Livelli (sezioni La città in 3D, Mobilità, Luoghi e servizi, Catasto con ricerca), Sole, Analisi (accessibilità, ombra, temperatura, qualità dell'aria), Interventi (un riquadro per scenario con i numeri; la scelta porta la vista sull'intervento; pulsante per il sole del calcolo), Legenda (tutti i colori, fonti e limiti). Struttura e stile sul modello di Padova, tema sempre chiaro (D23). Una variante con stile proprio (pietra serena e cotto, schede a pulsanti) è stata provata e scartata.

## Livelli analitici (input GeoJSON EPSG:4326)

build.py li include se esistono e li salta se mancano. Cartelle `analysis/firenze_novoli/` e `shadow/firenze_novoli/` (opzioni `--analysis` e `--shadow`).

Accessibilità: file `accessibilita*.geojson`, uno per destinazione, feature Point (un civico). Proprietà: id, civico, minuti (null se non raggiungibile), stato (ok, non_raggiungibile, dati_insufficienti, vietato), destinazione, destinazione_nome, profilo. Alias accettati per l'output del motore F06: t = minuti, ind = civico, stati reachable, isolated, insufficient_data, forbidden. Colori: fino a 5, 5-10, 10-15, oltre 15 minuti. Gli stati diversi da ok sono anelli grigi: non significano "lontano".

Ombra sui percorsi: file `ombra_percorsi*.geojson`, feature LineString o MultiLineString. Proprietà: id, frazione_ombra (0 sole, 1 ombra), istante (per esempio 2026-07-15T13:00), lunghezza_m. La pagina offre un selettore dell'istante; il livello mostra il calcolo di quell'istante, non segue il cursore dell'ora. Accetta anche l'uscita del motore F07 (`tratti_ombra_*.geojson`): si disegnano solo i tratti in ombra del caso `veg_lidar_tipico`, i vuoti lungo il percorso sono al sole.

## Livello Scenari (interventi ipotetici)

Mostra gli interventi del modulo scenari (F08), per vedere con lo slider dell'ora come cambiano le ombre. Spento all'avvio. Non calcola nulla: disegna gli interventi e riporta i numeri già calcolati.

- Input: `scenarios/firenze_novoli/interventi.geojson` (EPSG:4326), opzione `--scenarios` di build.py. Point = albero nuovo (id, scenario, h, chioma_d, imposta); Polygon = pensilina (id, scenario, z_lo, z_hi).
- Numeri chiave letti da `scenarios/firenze_novoli/confronto.json`: caso con vegetazione LiDAR, 15 luglio, 12:30-13:30; per S2 anche il caso con soli edifici. Se F08 viene rieseguito basta ricostruire gli asset.
- Asset `interventi.json.gz`: un record per scenario (id, etichetta, alberi, pensiline, numeri, fattibilità). Senza il file l'asset non viene scritto e la casella è disabilitata.
- Selettore: S1 filare tipico, chioma minima, chioma massima; S2 pensilina alla fermata bus Guidoni Barsanti; S5 Regione Toscana e S6 Di Novoli Sn. I numeri delle pensiline riguardano la rispettiva area di attesa.
- Resa: alberi in magenta (colore assente dagli altri livelli), pensilina come volume con quattro pali. Tutto proietta ombra del motore. Il pulsante "Vai all'intervento" accende il livello e inquadra l'intervento.
- Scheda al clic: scenario, dimensioni, numeri chiave e "Fattibilità: ignota". Gli interventi sono ipotesi di studio, non progetti.

Limiti:
- Le ombre mostrate sono quelle del motore grafico; i numeri della scheda vengono dal motore F07 e possono differire dall'impressione visiva.
- Il filare (versione 3 di F08, dopo D20) sta dentro le aree di circolazione pedonale del Comune, da 1,5 a 5 m dall'asse. Anche la pensilina S2 (versione 2) sta dentro le aree pedonali, con 1,5 m di passaggio libero.
- La quota della pensilina usa il terreno a 10 m al centro del contorno.

## Comandi

- Costruire: `pipeline/.venv/bin/python scene/firenze_novoli/build.py`
- Test: `pipeline/.venv/bin/python scene/firenze_novoli/test_build.py`
- Servire: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi aprire http://localhost:8765/

## Limiti

- three.js è copiato in `vendor/three/` (solo `three.module.min.js`, `three.core.min.js`, `OrbitControls.js` e la licenza; versione in `vendor/three/README.md`): per cambiare versione si sostituiscono i tre file, la importmap di `index.html` non cambia. `test_build.py` controlla che i file della importmap esistano.
- Altezze: LiDAR 2023 confrontato con le unità volumetriche 2011. Volumi senza tetti a falde. Portici e volumi sospesi ignoti, non disegnati.
- Alberi: 867 su 2.917 hanno la chioma stimata. Tronco disegnato con almeno 25 cm di diametro.
- Terreno a 10 m, senza ortofoto.
- Le ombre del motore sono illustrative: le chiome proiettano ombra piena. Per l'analisi valgono i dati del modulo ombre.
- Le fonti con riserva di licenza (unità volumetriche regionali, scuole, accessi CM) restano segnalate nella scheda e nell'elenco fonti.
- La scheda si apre con mouse e tocco, non da tastiera. Da tastiera si usano pannello, ora, livelli e vista.
- Sole con algoritmo semplificato (circa 0,1 gradi), fuso Europe/Rome.
- Provato su Chromium emulato, non su un telefono vero. Scheda al clic su alberi e punti non provata.

- Una costruzione interrotta può eliminare gli asset precedenti e lasciare il vecchio indice: problema aperto R6 della revisione del codice. La scena non è stata ricostruita durante questa revisione.
