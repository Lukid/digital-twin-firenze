# Audit rete pedonale: Z1-Z4

Data: 1 ottobre 2026. Redatto dall'agente rete (T01) e salvato dall'integratore. Misure da `campioni/metriche_osm.json`; checksum in `manifest.json` (26 file, nessuno a 0 byte); rigenerazione con `riproduci.sh`.

Riquadri usati (EPSG:4326 S,W,N,E), proposti dall'agente e non approvati:
- Z1: 43.7140,10.3940,43.7210,10.4060 (0,75 km²)
- Z2: 43.7050,10.3880,43.7150,10.4040 (1,43 km²)
- Z3: 43.7000,10.4350,43.7110,10.4500 (1,48 km²); il primo riquadro non conteneva l'ospedale ed è stato corretto
- Z4: 43.7215,10.3995,43.7315,10.4150 (1,34 km²)

## Sintesi

- Fonte della rete: solo OSM (Overpass, lento: 429/504 frequenti). Nessun dato ufficiale con marciapiedi o attraversamenti di Pisa trovato.
- SIT STRADE: 705 poligoni senza attributi, non è un grafo. CTR 2022 del SIT: 299.607 linee con codici numerici senza legenda (contenuto non dimostrato).
- Grafo regionale iternet.zip (460 MB) e DBT 1:10.000 Pisa del 2010 (411 MB): esistono, non scaricati, contenuto non verificato.
- CKAN con "Pisa + viabilità": 0 risultati (non prova di assenza: il SIT non è in CKAN).
- Z1: 17,9 km di rete dedicata, 58% strade senza tag sidewalk, 58 nodi crossing, 25 destinazioni (21 università) tutte con ingresso mappato, 279 ingressi.
- Z2: 30,9 km, 46% senza tag, 173 crossing (129 con tattile), 267 ingressi, 7 destinazioni su 11 con ingresso. Zona meglio mappata.
- Z3: 10,6 km (7 km/km²), 69% senza tag, 124 crossing ma solo 21 tratti crossing, solo 4 ingressi (ospedale di Cisanello quasi senza accessi mappati), 12,9 km fuori dalla componente maggiore (25 componenti).
- Z4: 24,5 km, 48% senza tag ma 16,3 km di marciapiedi disegnati (il tag sottostima), 147 crossing, solo 2 con kerb, 5 destinazioni su 10 con ingresso.

## Misure (Z1 / Z2 / Z3 / Z4)

- Rete dedicata (footway, path, pedestrian, steps, cycleway), km: 17,85 / 30,88 / 10,61 / 24,48
- Rete percorribile (con strade carrabili senza foot=no), km: 34,29 / 56,66 / 31,57 / 47,61
- Strade non di servizio, km: 14,72 / 19,12 / 11,35 / 17,52
- Con sidewalk sì o separato: 37% / 47% / 25% / 51%
- sidewalk no/none: 5% / 7% / 6% / 1%
- Senza tag: 58% / 46% / 69% / 48%
- Marciapiedi disegnati (footway=sidewalk), km: 5,65 / 13,08 / 4,42 / 16,30
- Nodi highway=crossing: 58 / 173 / 124 / 147
- Tratti footway=crossing: 44 / 103 / 21 / 95
- Crossing con tactile_paving: 44 / 129 / 28 / 74
- Crossing con kerb: 12 / 37 / 13 / 2
- Barriere totali: 157 / 288 / 49 / 242 (bollard 64 / 22 / 1 / 4; gate 36 / 87 / 11 / 53; barrier=kerb 54 / 163 / 20 / 175, che sono interruzioni di marciapiede e non ostacoli)
- Ingressi entrance=*: 279 / 267 / 4 / 88 (con tag wheelchair 7 / 1 / 1 / 1)
- Componenti connesse: 6 / 8 / 25 / 16; km nella maggiore 40,45 / 62,50 / 28,80 / 55,05; km fuori 0,34 / 2,50 / 12,85 / 1,98
- Destinazioni (scuole, asili, università, ospedali): 25 / 11 / 1 / 10
- Fermate bus: 17 / 42 / 14 / 39
- Destinazioni con ingresso entro 80 m dal centroide (proxy grezzo): 25 / 7 / 1 / 5

## Metodo

`scarica_osm.py` scarica ways highway e nodi crossing, barrier, entrance, kerb nel riquadro. `analizza_osm.py` misura lunghezze (equirettangolare, solo segmenti con punto medio nel riquadro) e componenti (nodi condivisi, ways interi).

Limiti: grafo non tagliato al riquadro (componenti con possibili artefatti ai bordi); tag assente non prova assenza del marciapiede; nodi e tratti crossing sono due convenzioni e non si sommano; snapshot 1 ottobre 2026 senza versione OSM; Overpass da sostituire con estratto regionale in T03. Nessun controllo sul terreno.

## Criteri per fonte (esistenza / accesso / contenuto / riuso)

- OSM: sì / sì, con 429-504 / valido e misurato / ODbL.
- SIT STRADE: sì / sì / no, poligoni senza attributi / non dichiarato.
- SIT CTR 2022 layer 1: sì / sì per riquadro, statistiche rifiutate (HTTP 400), niente paginazione / non dimostrato, codici layer 201, 203, 501, 207, 107, 101 senza legenda / non dichiarato.
- Grafo regionale grafo-civici: sì / HEAD 200, 460.484.895 byte, 10 ottobre 2025 / non verificato, di natura veicolare / CC BY da catalogo.
- DBT10K Pisa 2010: sì / HEAD 200, 411.509.203 byte / non ispezionato, scala 1:10.000 / CC BY da catalogo.
- DBT 1:2.000: sì in catalogo / il link porta alla Cartoteca interattiva / file per Pisa non verificato / CC BY da catalogo.
- CKAN, ricerche marciapiedi, rete pedonale, grafo stradale: risultati di altri Comuni, nessuno di Pisa. dati.gov.it: 2 risultati non su Pisa.

## Rilievo stimato (stima, non misura)

- Z3: prioritario (ingressi, percorsi interni).
- Z1: limitato (ingressi e varchi ZTL).
- Z2 e Z4: a campione su 5-10 percorsi (marciapiedi, attraversamenti, rampe).

## Licenza

OSM ODbL, attribuzione "© OpenStreetMap contributors". Unire OSM ad altri dati in un solo database distribuito comporta la condivisione alla pari; i risultati prodotti (mappe, percorsi) richiedono solo attribuzione. Fonti regionali: CC BY dal campo del catalogo. SIT comunale: condizioni non riportate nei metadati, da accertare.

## Lacune

Ingressi (Z3, Z4), rampe/kerb, larghezze e pendenze, legenda CTR, DBT 1:2.000 per Pisa non verificato.

## File

`scarica_osm.py`, `scarica_poi.py`, `analizza_osm.py`, `analizza_poi.py`, `riproduci.sh`, `manifest.json`, `campioni/` (osm_Z1-Z4, osm_poi, metriche_osm, risposte SIT e CKAN, intestazioni HTTP).
