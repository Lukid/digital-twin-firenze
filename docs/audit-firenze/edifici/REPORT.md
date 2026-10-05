# F01 Edifici e quote: Firenze, riquadri FA e FB

Data: 5 ottobre 2026. Riquadri da docs/audit-firenze/RIQUADRO.json (S,W,N,E in EPSG:4326), non approvati: la scelta è dell'utente. FA e FB misurano 1,717 km² ciascuno e si sovrappongono per 0,787 km² (46%). CRS di lavoro EPSG:7791. I conteggi usano il centroide dell'oggetto dentro il riquadro, rettangolo ricalcolato in metri. Metodo ripreso da docs/audit/edifici (T01 su Pisa).

## 1. Fonti di impronte edifici e licenze

1. Unità volumetriche (UV) della Regione Toscana, servizio WFS di sola consultazione (layer rt_edif.unitavolumetriche).
   - Il download per riquadro funziona (GML, 500 oggetti per pagina).
   - Contenuto: altezza uv_av e quote uv_qe (gronda o tetto) e uv_qs (spiccato) valorizzate in tutti gli oggetti, tipo di portico (uv_dpor), uso, stato.
   - Anno del volo: 2011 in tutti gli oggetti. A Pisa il volo era luglio 2010.
   - Scala 02, la stessa dei dati di Pisa, che il report di Pisa legge come 1:2.000 (qui non verificata).
   - Licenza: nessuna per layer. Vale la politica regionale open geodata (CC BY o CC BY-SA), come a Pisa. Per Firenze non riverificata. Citare la fonte.
2. OSM (Overpass), ODbL.
3. Cassone edilizio del Comune di Firenze (dataset "Antropico - Cassone Edilizio", CC BY 4.0, rilievo celerimetrico, shapefile PolygonZ in Monte Mario Italia zona 1).
   - Non è un livello di impronte. Contiene solo 2.058 poligoni in tutta la città, ognuno è un corpo costruito continuo, ed è un file del 2014 con attributi solo di id, area e perimetro.
   - Copre il 31,5% (FA) e il 60,0% (FB) dell'area delle UV.
   - La Z c'è, il suo significato non è documentato e non è verificato.
4. Cercato e non trovato: su dati.toscana.it il Comune di Firenze (1.992 dataset, scansione completa dei titoli in script/ckan_firenze_catalogo.py) non pubblica un livello "edifici" né "unità volumetriche". Le ricerche per titolo "Edificio", "Edificato", "Unità volumetrica" danno 0 risultati.
   - Le UV su CKAN esistono per altri 40 comuni (Livorno, Siena, Arezzo, ecc.), non per Firenze.
   - Il database topografico regionale non è su CKAN. Non cercato sul geoportale.
5. Altro del Comune, non usato come impronte: "Antropico - Manufatto Edilizio" (manufatti non stabili), "Particolare Architettonico" (colonne, pilastrini).

## 2. Conteggi per riquadro

| Fonte | FA | FB | FA e FB insieme |
|---|---|---|---|
| UV Regione | 972 | 1.459 | 1.924 |
| OSM | 370 | 543 | 725 |
| Cassone Comune | 39 | 85 | 98 |

- Il WFS restituisce 981 (FA) e 1.468 (FB) oggetti perché usa l'intersezione con il bbox. Il conteggio per centroide è quello della tabella.
- Area costruita: UV 0,391 km² (FA) e 0,431 km² (FB); OSM 0,471 e 0,487; cassone 0,332 e 0,719.
- Altezza:
  - UV: 100% degli oggetti ha uv_av. Mediana 7,4 m (FA) e 8,8 m (FB); p10-p90 2,6-29,2 m (FA) e 3,0-27,1 m (FB).
  - OSM: solo 1 su 370 (FA) e 0 su 543 (FB) ha height; 5 (FA) e 27 (FB) hanno building:levels. min_height e building:min_level sono 0 in entrambi i riquadri. Un edificio di FB ha building:part.
  - Cassone: nessun attributo di altezza.
- Stato nelle UV, dati 2011:
  - FA: 768 in esercizio, 160 senza dato, 36 in costruzione, 8 in disuso.
  - FB: 1.313 in esercizio, 134 senza dato, 1 in costruzione, 11 in disuso.
- Sovrapposizione OSM e UV:
  - Centroidi OSM dentro UV: 78% (FA) e 85% (FB). Centroidi UV dentro OSM: 72% e 79%.
  - Area OSM coperta da UV: 73,5% e 78,6%. Area UV coperta da OSM: 89,3% e 89,9%.
  - Lettura: l'UV del 2011 non ha parte dell'edificato attuale. Dove c'è, OSM la copre quasi tutta.
- Controllo sul LiDAR 2023 (nDSM sotto l'impronta):
  - 21 impronte OSM su 864 testate hanno nDSM mediana sotto 1,5 m, cioè non c'è nulla di alto.
  - Celle con nDSM sopra 3 m fuori da ogni impronta (UV, OSM, cassone, con 2 m di tolleranza): 114.063 m² su 663.071 (FA) e 84.131 su 680.697 (FB). Il conteggio include gli alberi, quindi non è un conteggio di edifici mancanti.

## 3. DTM e DSM LiDAR del Comune: verifica di download

| Prodotto | Volo | Cella | Formato | Zip intero | Tessere |
|---|---|---|---|---|---|
| DTM e DSM 2023 | 27/06/2023 (foglie presenti) | 0,5 m | ASCII, tessere di 500 m (1000x1000 celle), nome 32_E_N | DTM 922.675.701 byte, DSM 1.038.346.174 byte (modificati il 19/12/2023) | 485 per prodotto |
| DTM e DSM 2017 | 29/03/2017 (foglie assenti) | 1 m | ASCII, tessere 800x1000 numerate, con .prj UTM 32 ETRS89 | DTM 186.749.009 byte, DSM 208.096.345 byte (modificati il 14/10/2020) | 409 voci di zip (con .prj e .xml) |

- Risorse trovate su dati.toscana.it (CC BY 4.0): dtm-lidar-2023, dsm-lidar-2023, dtm-2017, dsm-2017, dsm-2007 (non scaricato), più DTM 2007 e gli hillshade.
- Gli URL su dati.toscana.it rimandano con un reindirizzamento a datigis.comune.fi.it/grid/. Il server accetta richieste Range. Gli zip interi non sono stati scaricati: lo script legge l'indice dello zip da remoto ed estrae solo le tessere dei riquadri.
  - Gli zip del 2023 usano la compressione Deflate64, che lo zip di Python non legge. Lo script usa inflate64, già installato con py7zr.
  - Per il 2023: 19 tessere per DTM e 19 per DSM (127 MB e 120 MB estratti). Per il 2017: 6 tessere per DTM e 6 per DSM, scelte dalle intestazioni perché toccano FA o FB.
- Copertura: nDSM senza vuoti (0% nodata) in FA e FB, sia nel 2023 sia nel 2017.
- Riferimento: i file ASCII del 2023 non portano un CRS (il 2017 ha un .prj). EPSG:7791 assunto dal prefisso "32_" e dalle quote (UV e siti alberi concordano con il DTM, vedi sotto). Nell'intestazione 2023 la griglia è data per centro cella (XLLCENTER), nel 2017 per angolo.
- Accesso alternativo: il WMS del Comune risponde e ha i layer DTM e DSM 2023 e 2017. È un servizio di immagini: non usato per le quote.
- Non verificato: DTM e DSM della Regione (geoportale) per Firenze.

## 4. Altezza degli edifici da nDSM contro uv_av

- Metodo: nDSM = DSM meno DTM del 2023. Mediana dei valori dentro l'impronta UV ridotta di 1 m (solo impronte di almeno 40 m², con almeno 20 celle valide). 1.419 impronte UV testate: 716 in FA e 703 in FB.
- Scarto mediana nDSM meno uv_av:
  - Tutte: mediana +0,37 m, p10 -2,06, p90 +2,76, errore medio assoluto (MAE) 1,84 m. Entro 1 m il 55,2%, entro 2 m il 75,7%.
  - FA: mediana +0,07 m, MAE 1,67. FB: mediana +0,63 m, MAE 2,02.
  - Con il 90° percentile dell'nDSM invece della mediana: mediana +1,22 m, MAE 2,62.
  - Con il LiDAR 2017: mediana +0,39 m, MAE 1,80 (entro 1 m il 53,5%).
  - nDSM 2023 contro nDSM 2017, stesse impronte: mediana -0,03 m, MAE 0,51.
- Per classe di altezza UV:

| Altezza uv_av | Impronte | Mediana | MAE |
|---|---|---|---|
| sotto 4 m | 267 | +0,15 m | 3,22 m |
| 4-8 m | 355 | +0,14 m | 1,72 m |
| 8-15 m | 339 | +0,60 m | 1,34 m |
| sopra 15 m | 458 | +0,39 m | 1,51 m |

- Lettura: la mediana dell'nDSM è utilizzabile come altezza edificio, con scarto mediano sotto 1 m, ma il 25% delle impronte sbaglia di più di 2 m. Gli edifici bassi (sotto 4 m) sono i meno affidabili: a quell'altezza pesano alberi addossati e annessi. uv_av e nDSM non misurano necessariamente la stessa grandezza (gronda o colmo non è documentato per uv_av).
- Quota di spiccato: uv_qs meno DTM 2023 sotto l'impronta ha mediana -0,14 m, p10 -1,12, p90 +1,08, MAE 0,78 su 1.419 impronte. Il datum è coerente: nessuna correzione sistematica necessaria. Su Pisa il datum verticale era rimasto non confermato.
- OSM: 30 impronte hanno un'altezza (height, oppure piani per 3 m, stima dell'audit). nDSM meno altezza OSM: mediana +3,52 m, MAE 3,92. Campione piccolo; la regola dei 3 m a piano sottostima.

## 5. Portici e volumi sospesi

- UV: il campo uv_dpor (tipo di portico) vale "Al Suolo" per 964 (FA) e 1.438 (FB) impronte, "Seminterrata" per 8 e 20, "Soffitto Di Loggia" per 0 e 1. L'unico segnale esplicito di loggia o portico è quindi 1 oggetto in FB.
- Segnale empirico di volumi sospesi: 53 impronte UV hanno uv_qs oltre 2,5 m sopra il suolo del DTM (50 delle quali marcate "Al Suolo"), 48 oltre 2,5 m sotto. Ambiguo: terrazzamenti, rampe ed errori di quota danno lo stesso segno. Non è una fonte di volumi sospesi.
- Candidato da livello pedonale: "Viabilità - Area di Circolazione Pedonale (PolygonZ)" del Comune, CC BY 4.0, 9.244 poligoni in città, 321 in FA (51.311 m²) e 545 in FB (92.360 m²). La descrizione cita "marciapiedi, aree di stazionamento, portici, sottopassi". Gli attributi sono codici (acPedPos, acPedZon, acPedSed, acPedLiv, quest'ultimo vale "05" ovunque) non decodificati nei metadati. Nessun campo isola i portici: resta un candidato non verificato.
- OSM: nessun edificio con min_height o building:min_level.
- Conclusione: nessuna fonte verificata per portici e volumi sospesi. Per l'ombra l'nDSM contiene già le coperture reali dei portici, ma le superfici sotto portico appaiono come terreno nel DTM e come tetto nel DSM.

## 6. Giudizio

- Impronte: UV 2011 come base geometrica con altezza, aggiornata con OSM dove manca. Serve un controllo sul LiDAR 2023 per gli edifici nuovi. Il cassone non serve come impronte.
- Altezze: nDSM 2023 per impronta. Alternativa se serve coerenza con la data dell'edificato: uv_av 2011, con scarto mediano di circa 0,4 m.
- Il LiDAR 2023 copre senza vuoti tutti e due i riquadri e a 0,5 m è più fine del 2017.

## 7. Limiti

- Impronte non ricostruite da zero: non si sa quanti edifici siano nuovi dal 2011 a oggi. Le UV con stato "in costruzione" sono 36 in FA e 1 in FB.
- nDSM mediana dentro un'impronta UV del 2011: edifici cambiati dopo il 2011 falsano il confronto.
- Il volo 2023 (giugno) ha le foglie, il 2017 (marzo) no: alberi addossati agli edifici alzano l'nDSM 2023 più del 2017, ma lo scarto tra i due anni è piccolo (mediana -0,03 m).
- CRS del 2023 assunto, confermato indirettamente da UV (-0,14 m) e siti alberi (-0,07 m).
- Licenza delle UV regionali per Firenze non riverificata. UV e OSM vanno citate.
- Non testati: DTM e DSM della Regione per Firenze, il database topografico regionale.

## File e riproduzione

Script in `script/`, campioni in `campioni/`, checksum in `manifest.json`. Dati grezzi in `data/raw/fi_audit_20261001/` (lidar/, csEdi/, sAlbero/, acPed/), non versionati.

Riprodurre dalla radice del progetto: `docs/audit-firenze/edifici/riproduci.sh` (circa 2,5 minuti). Un'interruzione a metà del download LiDAR lascia un file a 0 byte, che lo script rifà alla riesecuzione.
