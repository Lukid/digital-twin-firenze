# Audit verde, alberi e chiome: Z1-Z4

Data: 1 ottobre 2026. Redatto dall'agente verde (T01) e salvato dall'integratore. Campioni in `campioni/`, comandi in `riproduci.sh`, checksum in `manifest.json` (82 file, nessuno a 0 byte).

Riquadri approssimati in `zone.json` (EPSG:4326 S,W,N,E), proposti dall'agente e non approvati:
- Z1: 43.7115,10.3920,43.7215,10.4060 (circa 1,3 km²)
- Z2: 43.7010,10.3880,43.7110,10.4050 (1,5 km²)
- Z3: 43.6900,10.4270,43.7030,10.4430 (1,9 km²)
- Z4: 43.7215,10.3880,43.7320,10.4060 (1,7 km²)

I conteggi includono gli oggetti che intersecano il bordo.

## Fonti: esistenza / accessibilità / contenuto / riuso

1. **Censimento comunale** (R3-Trees, Dip. Scienze Agrarie UniPi).
   - Esistenza: documentata (comunicato 17/04/2024, agg. 02/05/2024, `campioni/comunicato_rinnovo_arboreo.html`; scheda UniPi `campioni/arpi_885149.html`). Aggiornamento 31/12/2017, 18.074 piante, 596 località, 337 nella mappa criticità, circa 37% sopra 10 m.
   - Accessibilità: non riuscita. La pagina "Censimento e Mappa degli alberi" risponde 410; il sito attuale non ha link a mappa o dati; la pagina Dataset elenca solo Corte dei conti e pagamenti.
   - Contenuto: non verificabile; diametro chioma e altezza d'imposta non dichiarati.
   - Riuso: "Licenza sconosciuta".
2. **Catalogo open data comunale**: scansione di tutte le 133 pagine, 663 titoli (643 distinti). Nessun titolo con alber*, verde, arbore*, chiom*, piante, giardin*, parch*, bosc*. Solo titoli, dataset non aperti uno per uno. La ricerca del sito ignora il parametro (non usata). Endpoint `/SpodCkanApi/api/2/search/package`: 404 (endpoint inesistente, non zero risultati). Elenco `/rest/package`: 663 ID. Licenza spesso non indicata.
3. **SIT comunale ArcGIS**: nessun servizio verde/alberi in radice e Hosted; SIT_2013 richiede token (499). Layer PSI (Piano Strutturale Intercomunale): Viale alberato (linee, 16, layer 218/237), Parchi territoriali (67), Verde sportivo (46), Aree verdi centro storico vincolate (126), Vegetazione ripariale (127). Campi: descrizione, disciplina, nota. Data e licenza non indicate. Toponomastica layer 1 parchi/giardini: 27.
   - Conteggi per zona (Z1/Z2/Z3/Z4): Viale alberato 0/0/1/1; Parchi territoriali 1/0/4/2; Verde sportivo 0/0/0/2; Aree verdi vincolate 107/1/0/13; Vegetazione ripariale 4/0/7/0; Parchi giardini 1/2/0/3.
   - Gli zeri sono intersezione con layer di pianificazione, non assenza di alberi.
4. **CKAN dati.toscana.it e dati.gov.it** (`campioni/ckan_log.tsv`, 38 query + 7).
   - Zero su Toscana: alberate, patrimonio arboreo, chiome, tree cover, copertura arborea, canopy, Pisa verde, Pisa alberature, CHM, dbtopografico Pisa. Zero su dati.gov.it: Pisa verde, Pisa alberature.
   - "Pisa alberi": 1 risultato (EFA ARTEA, agricolo). Alberi di Firenze, Prato, Montelupo: non Pisa.
   - Alberi monumentali Regione Toscana (CC BY-SA, 2016): URL zip da 1,68 GB, non verificato, irrilevante per la baseline.
   - Uso del suolo: 1927 risultati, per lo più comunali catastali; nessun dataset regionale che copra Pisa aperto: lacuna.
5. **OSM** (ODbL, attribuzione e condivisione alla pari). Valori Z1/Z2/Z3/Z4:
   - alberi 272/426/50/516; tree_row 5/7/8/64; aree verdi 95/31/12/101
   - specie 15 (5,5%)/5 (1,2%)/0/1 (0,2%)
   - altezza 4 (1,5%)/4 (0,9%)/0/6 (1,2%)
   - diametro chioma 1 (0,4%)/0/0/0; altezza d'imposta 0/0/0/0; circonferenza 3/0/0/0
   - leaf_type 29 (10,7%)/34 (8,0%)/0/15 (2,9%)
   - date nodi: 2014-09..2026-09 / 2015-09..2026-07 / 2022-03..2025-02 / 2014-02..2026-08 (ultima modifica OSM, non data del rilievo)
   - valori sospetti: Z2 altezze 0,2-1 m; Z1 "2" e "21.5m". tree_row senza height né specie. Z3 con 50 alberi è incompleta.
6. **Copernicus**. Street Tree Layer 2018: MapServer EEA accessibile; poligoni di almeno 500 m² e larghezza 10 m su superfici artificiali; FUA PISA (IT041L2); poligoni per zona 55/42/61/88; attributi solo codice e area. Layer 2 "DOMs": contenuto ignoto. Tree Cover Density: raster 10 m, 0-100%, non scaricato né verificato, non dà alberi singoli. Licenza EEA (uso libero con citazione) letta da sintesi: da confermare sulla pagina primaria.
7. **LiDAR**: scheda regionale (CC BY, 2020), 1x1 e 2x2 m, una sola risorsa verso la Cartoteca; copertura di Pisa non dimostrata. DSM/DTM 2007/2017/2023 trovati: sono di Firenze. Altimetria 10 m troppo grossolana. Non elaborato.

## Cinque attributi

- Posizione: OSM rado (campione, non baseline); Copernicus poligoni 10 m; censimento comunale non accessibile.
- Specie: solo censimento (non accessibile); OSM 0-5,5%.
- Altezza: OSM 0-1,5% (stime); censimento: classi note solo in sintesi.
- Diametro chioma: 1 albero OSM in tutto; nessun'altra fonte.
- Altezza d'imposta: nessuna fonte.

## Chiome modellabili?

No da misure, in nessuna zona. Possibili:
- stime con posizione + classi di specie/dimensione, intervalli dichiarati, risultati d'ombra come intervalli;
- rilievo locale (clinometro e metro) su un sito pilota piccolo;
- LiDAR solo dopo aver verificato copertura ed epoca per Pisa.

## Lacune e alternative

1. Richiesta al Comune (Ufficio Verde/SIT) per formato, campi, data e licenza del censimento: non fatta, decisione dell'utente.
2. Verifica in browser di un eventuale visualizzatore R3-Trees ancora pubblico.
3. Studio UniPi sul censimento: solo scheda bibliografica.
4. LiDAR regionale: controllare la Cartoteca per un'area di prova su Pisa.
5. Rilievo locale su sito pilota.
6. Uso del suolo regionale per Pisa: da aprire.

## Note di metodo

404 e 499 non trattati come zero. Primo giro OSM fallito (HTTP 400, zeri finti) e corretto: lo script ora segnala l'errore. File regionale da 1,68 GB: parte scaricata per errore e cancellata. Nessun contatto con enti, account o installazioni.

## File

`riproduci.sh`, `manifest.json`, `zone.json`, `campioni/`, `scan_catalogo_pisa.py`, `ckan_queries.sh`, `sit_verde.py`, `osm_alberi.py`, `analisi_osm.py`, `make_manifest.py`.

## Addendum: ricalcolo sui riquadri canonici

Riquadri in `docs/audit/ZONE.json`. Risultati in `campioni/ricalcolo_zone_canoniche.json`; i dati sui riquadri iniziali restano in `campioni/riquadri_iniziali/`. Manifest aggiornato: 92 file, nessuno a 0 byte. `zone.json` e `riproduci.sh` ora usano i riquadri canonici.

Aree: Z1 1,00 km², Z2 1,06, Z3 1,21, Z4 1,14. Valori Z1 / Z2 / Z3 / Z4:
- Alberi OSM (natural=tree): 284 / 373 / 123 / 432; densità per km²: 284 / 352 / 102 / 379
- tree_row: 6 / 8 / 0 / 28
- Aree verdi OSM: 83 / 29 / 35 / 47
- Specie: 4,9% / 0,5% / 0,8% / 0,2%
- Altezza: 1,4% / 0,3% / 0% / 0%
- Diametro chioma: 0,4% / 0% / 0% / 0%
- Altezza d'imposta: 0% ovunque
- leaf_type: 10,2% / 9,1% / 0,8% / 0,2%
- Date nodi OSM: Z1 2014-09/2026-09; Z2 2015-09/2026-07; Z3 2016-12/2026-05; Z4 2014-03/2026-09
- Poligoni Copernicus Street Tree: 45 / 35 / 26 / 45
- Layer PSI: Z3 4 parchi territoriali, 3 vegetazione ripariale, 0 aree vincolate, 1 voce di toponomastica. Aree verdi vincolate centro storico: Z1 82, Z2 20, Z4 8. Verde sportivo Z4: 8. Layer di pianificazione, non rilievi.
- Valore sospetto: in Z2 l'unica altezza OSM è 0,2 m.

Z3: il giudizio "palesemente incompleta" dipendeva in gran parte dal riquadro iniziale, circa 1 km più a sud (alberi da 50 a 123). Z3 resta la zona più povera: densità circa un terzo delle altre, attributi quasi vuoti, Copernicus al minimo. Non verificato sul campo se la causa sia mappatura incompleta o poco verde reale.

Il giudizio generale non cambia: nessuna zona ha diametro chioma o altezza d'imposta misurati; le chiome restano da stimare o rilevare.

## Nota di revisione

Alla riesecuzione Overpass ha risposto 504 su Z1: `analisi_osm.py` va in errore (`KeyError 'elements'`) e la risposta d'errore sovrascrive il campione. Da correggere: controllare la risposta prima di salvarla e conservare l'ultimo campione valido.
