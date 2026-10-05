# Audit rete pedonale e barriere: FA e FB (F01)

Data: 5 ottobre 2026. Misure da `campioni/metriche_osm.json` e `campioni/metriche_dati.json`; checksum in `manifest.json`. Riquadri da `docs/audit-firenze/RIQUADRO.json`, non approvati dall'utente (EPSG:4326 S,W,N,E):
- FA: 43,796, 11,213, 43,808, 11,229 (1,72 km²), candidato D12 Novoli - Firenze Nova
- FB: 43,792, 11,218, 43,804, 11,234 (1,72 km²), variante spostata a sud-est verso il campus di Novoli. Si sovrappone a FA per circa metà dell'area.

## Sintesi

- Rete migliore: FB, in modo netto. Ha il doppio dei km di rete dedicata (40,3 contro 19,6), più del doppio degli attraversamenti (246 contro 117 nodi), quasi 3 volte i marciapiedi con tag (30% contro 12% delle strade) e più schede di accessibilità del Comune agganciabili (11 contro 4).
- Nessuno dei due riquadri raggiunge Z2 di Pisa. Il confronto più pesante è su marciapiedi disegnati (0,6 e 1,9 km contro 13,1 km) e ingressi mappati (2 e 5 contro 267).
- Il punto debole comune è la mancanza di marciapiedi: in FA l'87% delle strade non di servizio non ha alcun tag sidewalk (68% in FB, 46% in Z2). Non prova che manchino sul terreno, prova che manca il dato.
- Le "barriere" del Comune sono schede di accessibilità di edifici e luoghi (2064 in tutta Firenze), non ostacoli lungo il percorso. Solo il 13% (FA) e il 21% (FB) cade a meno di 10 m da un arco OSM.
- Walking City: nessun tratto nei due riquadri. Rifugi climatici: nessuno nei due riquadri (il più vicino a 45 m da FB e 465 m da FA).

## Fonti e licenze

- OpenStreetMap via Overpass (query in `scarica_osm.py`: way highway; nodi crossing, barrier, entrance, kerb, railway crossing). Snapshot del 5 ottobre 2026, senza versione OSM. Licenza ODbL, attribuzione "© OpenStreetMap contributors". Overpass ha dato 504 e timeout; lo script riprova da solo.
- Barriere del Comune di Firenze: "Censimento delle barriere architettoniche e urbanistiche", dati.toscana.it, pacchetto `92033b63-0598-4449-9007-22127abe505a`, CC BY 4.0. File `data/raw/fi_audit_20261001/barriere.zip` (shapefile puntuale, EPSG:3003). Descrizione del catalogo: archivio "aggiornato al 2013", 2064 schede su edifici pubblici o privati d'uso pubblico. I file dentro lo zip sono datati 13 settembre 2016. Metadati CKAN in `campioni/ckan_barriere_firenze.json`.
- Walking City del Comune di Firenze: 7 dataset su dati.toscana.it (Percorso 1-7), CC BY 4.0. Scaricati via CKAN `package_search` (q=walking city). Il formato dichiarato è KML ma i file sono KMZ compressi, salvati in `data/raw/fi_audit_20261001/walking/`. Metadati in `campioni/ckan_walking_city.json`.
- Rifugi climatici: `data/raw/fi_audit_20261001/rifugi.geojson` (41 aree, multipoligoni EPSG:4326). Licenza CC BY 4.0 secondo l'audit dei cataloghi.

## Metriche OSM per riquadro (FA / FB, confronto con Z2 di Pisa)

Stesso metodo di T01 (`analizza_osm.py` adattato: stessa definizione di rete dedicata, che include cycleway; lunghezze solo per segmenti con punto medio nel riquadro).

- Rete dedicata (footway, path, pedestrian, steps, cycleway), km: 19,59 / 40,32 / Z2 30,88
- di cui ciclabili (cycleway), km: 3,99 / 6,02
- Rete percorribile (dedicata più strade senza foot=no), km: 57,35 / 79,46 / Z2 56,66
- Strade non di servizio, km: 20,74 / 28,42 / Z2 19,12
- Con sidewalk sì o separato: 12% / 30% / Z2 47%
- sidewalk no o none: 1% / 3% / Z2 7%
- Senza tag sidewalk: 87% / 68% / Z2 46%
- Marciapiedi disegnati (footway=sidewalk), km: 0,59 / 1,91 / Z2 13,08 (9 e 24 tratti)
- Nodi highway=crossing: 117 / 246 / Z2 173
- Tratti footway=crossing: 84 / 162 / Z2 103 (nodi e tratti sono due convenzioni, non si sommano)
- Crossing con tactile_paving: 59 / 154 / Z2 129 (50% e 63% dei nodi; Z2 75%)
- Crossing con kerb: 2 / 15 / Z2 37
- Nodi con kerb=*: 5 / 37
- Barriere puntuali totali: 28 / 67 / Z2 288. Cancelli (gate) 15 / 38, sbarre (lift_gate) 3 / 4, bollard 0 / 2, kerb 3 / 9. I barrier=kerb sono interruzioni di marciapiede e non ostacoli.
- Ingressi entrance=*: 2 / 5 / Z2 267. Nessuno con tag wheelchair.
- Componenti connesse: 29 / 26 / Z2 8
- Km nella componente maggiore: 63,91 / 89,40 / Z2 62,50
- Km fuori dalla componente maggiore: 3,09 / 3,46 / Z2 2,50
- Componenti sotto 100 m: 17 / 11. Sono per lo più artefatti ai bordi: il grafo non è tagliato al riquadro, come in T01.
- Tag sulle vie dedicate: surface 115 / 388, lit 66 / 193, incline 2 / 7, tactile_paving 3 / 12.

## Barriere architettoniche del Comune

Attributi utili per il grafo (colonne dello shapefile):
- `grado_acce`: tre classi, Accessibile, Parzialmente Accessibile, Non Accessibile. È l'unico indicatore di gravità. A Firenze: 526 / 695 / 843.
- `destinaz_u`: destinazione d'uso (giardino, scuola, uffici, chiesa, parcheggio, università, musei ecc.), 442 valori distinti con maiuscole e grafie miste.
- `indirizzo`, `quartiere` (Q1-Q5), `utoe`, `scheda` (numero) e `url` (link al PDF della scheda di rilievo).
- Non ci sono tipo di barriera, data di rilievo per scheda, larghezze o pendenze. L'unica indicazione temporale è "aggiornato al 2013" nel catalogo.

Per riquadro:
- FA: 30 schede. Accessibile 7, parzialmente 17, non accessibile 6. Destinazioni principali: giardino 6, uffici 5, asilo nido 2, scuola 2.
- FB: 52 schede. Accessibile 21, parzialmente 18, non accessibile 13. Destinazioni principali: giardino 9, uffici 7, università 6, chiesa 2, cimitero 2, scuola 2.

Aggancio alla rete OSM (rete percorribile, distanza dal punto al segmento più vicino, in EPSG:32632):
- FA: 4 su 30 (13,3%) a meno di 10 m. Distanza mediana 19,5 m.
- FB: 11 su 52 (21,2%) a meno di 10 m. Distanza mediana 16,6 m.
- I punti sono posizionati sul lotto o sull'edificio, non sul marciapiede davanti all'ingresso. Un aggancio automatico entro 10 m è quindi inaffidabile. Servono una soglia più larga (20-30 m) con controllo a campione, oppure l'aggancio per indirizzo.

## Walking City

- 7 percorsi, 115 tratti, 95,4 km in tutta Firenze.
- Km nei riquadri: 0,00 in FA e 0,00 in FB. Il percorso più vicino è a 33 m dal bordo di FB e a 477 m dal bordo di FA.
- I percorsi sono tracciati lineari per sport e camminata (es. "Parco dell'Albereta - Giardini sull'Arno"), senza attributi di accessibilità. Valore limitato per questo pilota.

## Rifugi climatici

Attributi: `cod_area`, `nome_area`, `percentuale_ombreggi`, `ingresso`, `descrizione`. Multipoligoni.
- Nessun rifugio dentro FA o FB.
- Il più vicino a entrambi è "Giardino di Piazza delle Medaglie d'Oro": 45 m dal bordo di FB, 465 m dal bordo di FA.
- Nel riquadro di contesto il conteggio non è stato fatto.

## Giudizio

- Riquadro con la rete migliore: FB. Più rete dedicata, più attraversamenti con tattile e kerb, più marciapiedi (disegnati e con tag), più schede di accessibilità e un rifugio a 45 m.
- FA ha una rete percorribile sufficiente per i calcoli di raggiungibilità (57 km), ma è molto più povero di marciapiedi mappati e ingressi.
- Per un gemello di qualità Z2, in entrambi serve un arricchimento: rilievo dei marciapiedi e degli ingressi, oppure una fonte ufficiale.

## Limiti

- Solo OSM, snapshot senza versione. Un tag mancante non prova l'assenza. In FA il tag sidewalk sembra sottostimare più che in Pisa: 0,59 km di footway=sidewalk su 20,74 km di strade non di servizio.
- Il grafo non è tagliato al riquadro: le componenti hanno artefatti ai bordi, e i km della "componente maggiore" comprendono anche rete fuori dal riquadro (stesso metodo di T01).
- Le barriere del Comune sono schede su edifici (rilievo del 2013, file del 2016), con un solo campo di gravità a 3 classi e senza data per scheda. Non descrivono marciapiedi o attraversamenti.
- Codifica del dbf non dichiarata: letto come cp850, che rende correttamente "università". Una variante "Universit?" (con "?" nel file sorgente) resta persa.
- Il pacchetto del catalogo ha un solo file attivo: aggiornamenti dopo il 2016 non risultano.
- Nessun controllo sul terreno. Nessun ente contattato, nulla pubblicato.

## File e riproduzione

In `docs/audit-firenze/rete/`: `scarica_osm.py` e `analizza_osm.py` (adattati da T01, leggono RIQUADRO.json), `scarica_altri.py` (CKAN e KMZ Walking City), `analizza_dati.py` (barriere, aggancio, Walking City, rifugi), `manifest.py`, `manifest.json`, `riproduci.sh`, `campioni/`.

Riprodurre: `docs/audit-firenze/rete/riproduci.sh`. Richiede `data/raw/fi_audit_20261001/barriere.zip` e `rifugi.geojson`.
