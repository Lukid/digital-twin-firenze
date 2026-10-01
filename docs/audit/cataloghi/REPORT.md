# Cataloghi e condizioni di riuso trasversali

Audit del 1 ottobre 2026. Solo letture HTTP pubbliche, nessun contatto, account o acquisto. Redatto dall'agente cataloghi (T01) e salvato dall'integratore.

## 1. Ricostruzione dei campioni

15 file su 15 coincidono (byte e sha256) con `docs/research/manifest.json`. Anche `docs/research/` non ha file a 0 byte e coincide con il manifest (non modificato).

Note:
- Le URL non sono nel manifest originale: sono state dedotte da FONTI.md. Il match certifica il contenuto, non l'URL originale.
- `ckan-nazionale-pisa-count.json` richiede `facet.field=["organization"]` (senza: 226 byte, stesso count 147).
- `pisa-ciclabili-service.json` richiede `f=json` (con `f=pjson` 3148 byte).
- `ckan-toscana-pisa.json` (3.375.867 byte) identico a distanza di ore.
- verde, alberi, pilota: stesso JSON vuoto da 215 byte. La query di pilota non è documentata (ipotizzata `Pisa AND pilota`).

## 2. StatPortal del Comune

- API CKAN v1/v2 su `/SpodCkanApi/api`; 663 dataset scaricati (`campioni/od-statportal-dataset.json`), zero errori.
- Licenza: `cc-by` e `isopen=true` per tutti i 663, identico per tutti (probabile default). Scheda HTML senza licenza; pagina download con segnaposto `$img_license` non risolto.
- Date metadati: 2015 (304), 2016 (272), 2017 (87), massimo 2017-11-16.
- Risorse tutte dichiarate CSV, ma le URL restituiscono 200 con JSON d'errore. Download reale via e-mail e quiz: non eseguito, contenuti non verificati.
- 256 dataset sono statistiche web/Wi-Fi/sanzioni; circa 22 georiferiti.
- Pertinenti (2015-2017, contenuto non scaricato): Grafo stradale (fonte Regione Iter.net, apr. 2015), Piste ciclabili agg. 2010 (file Pisamo), Stradario 2015 (tabellare), Plessi scolastici nov. 2015, CTP (senza descrizione), pericolosità idraulica, rete fognaria, contenitori raccolta.
- Verde ed edifici: nessuna corrispondenza per parole chiave (non prova assenza).

## 3. SIT ArcGIS (`campioni/sit-inventario.json`)

- 27 servizi root e 11 Hosted. `copyrightText` vuoto in ogni servizio e layer.
- Scheda sito (agg. 21/02/2025): consultazione "GRATUITO", cartografia basata sulla Carta Tecnica Regionale, pagina con "servizio online al momento non disponibile" mentre i REST rispondono. PDF condizioni: generico (privacy, costi), niente riuso.
- Data di modifica solo sugli Hosted; nei MapServer root non c'è data (il nome "Base_CTR_2023" con layer `ctr_pisa_cascina_2022` non certifica l'epoca).
- Hosted FABBRICATI_PEG, STRADE, TERRENI_PEG espongono Create/Update/Delete (non testato).
- Pertinenti:
  - Piste_ciclabili: 144 linee, EPSG:3003.
  - Toponomastica stradario: 1354 linee; "parchi giardini luoghi di interesse": 27 poligoni, solo toponimi (unico verde del SIT).
  - Hosted/STRADE: 705 poligoni di sedime, 2026-03-17.
  - Civici_puntuali_View: 32.335 punti, 2026-09-30.
  - Base_CTR_per_POC CTR_areale_edif: 47.555 poligoni, campi Id/tipo/area, nessuna quota.
  - Base_CTR_2023: 299.607 linee, campi lin3d_id/brk_id, non provano altezze.
  - periodizzazione_edificato: 45.360 poligoni, campo Anno.
  - Catasto_View: Fabbricati 27.650, agg. 2024-02-01.
  - FABBRICATI_PEG: 3909 punti, 2026-07-14.
  - edifici_scolastici: 97 poligoni, 2025-11-24; Scuole: 90 punti, 2025-11-24; Plessi: 23; Istituti_Comprensivi: 7.
  - Base_DBTopografico: solo tile. Battenti/TR200: raster senza studio di origine.
- Non trovati nel SIT: alberature, chiome, fermate, ingressi, attraversamenti.

## 4. CKAN Toscana e dati.gov.it

Query in `ricerche_ckan.py` (17 per portale).

- Zero risultati: "Pisa civici", "Pisa DBTopografico", "Pisa idrografia", "Pisa parcheggi", "Pisa accessibilità"; sul regionale anche `Pisa AND verde`, `Pisa AND alber*`.
- Dei 130 risultati regionali per `q=Pisa`: 69 Provincia di Pisa (scuole, alunni, pendolarismo, incidenti), 14 Regione, 8 Artea, 6 Trafair, 3 ARPAT. La data 2026-09-30 della Provincia è la ripubblicazione del record.
- dati.gov.it: nessuna organizzazione "Comune di Pisa" (solo AOU Pisana, 3 dataset). I conteggi grandi delle query multi-parola sono in OR e non contano dataset su Pisa.
- Utili:
  - DBT10K foglio Pisa: cc-by; 411.509.203 byte, HTTP 200; dati 2010, scala 1:10.000.
  - Iter.net grafo stradale: 460.484.895 byte, HTTP 200, licenza non sul file.
  - LiDAR: cc-by, solo link Cartoteca.
  - GTFS rt-oraritb: cc-by, GET 200 application/zip, Range ignorato; scaricati 77 MB poi interrotto, non validato.
  - Musei Provincia: CC BY 4.0, 82 musei, 34 a Pisa; coordinate probabilmente EPSG:3003, da confermare.
  - Zone umide: CC BY 4.0, non scaricato.
  - Mappatura acustica Comune di Pisa 2008: 3 dataset RNDT, CC BY 4.0, URL risorse vuoti.
  - Trafair aria: cc-by, non scaricato.

## 5. Tabella fonte per fonte

Formato: esiste / accesso / contenuto verificato / licenza / redistribuzione.

- StatPortal: sì / metadati sì, download rotto o con e-mail / no / cc-by solo in API, scheda vuota / non dimostrata.
- SIT servizi (incl. Hosted scuole, civici, plessi): sì / sì / parziale (schemi, conteggi, 1 record) / nessuna / non dimostrata (un endpoint pubblico non prova una licenza).
- SIT Catasto_View: sì / sì / parziale / nessuna, origine catastale / non dimostrata, rischio aggiuntivo.
- SIT Base_DBTopografico: sì / solo tile / no / nessuna / non dimostrata.
- DBT10K Pisa: sì / sì / no / cc-by / condizionata (attribuzione), 2010, 1:10.000.
- Grafo Iter.net: sì / sì / no / non sul file, atto 2013 BY o BY-SA / condizionata, da accertare (BY-SA = condivisione alla pari).
- LiDAR: sì (link) / pagina / no / cc-by / condizionata, copertura Pisa non provata.
- GTFS Toscana: sì / sì / parziale, non validato / cc-by / condizionata.
- Musei Provincia: sì / sì / sì / CC BY 4.0 / condizionata (attribuzione), la più chiara.
- Mappatura acustica 2008: sì / risorse senza URL / no / CC BY 4.0 / non verificabile.
- ARPAT aria: sì / sì / sì (CSV, vedi FONTI.md) / note legali del sito CC BY-NC-SA 3.0 IT, nessuna indicazione specifica per l'archivio / no o non dimostrata (clausola NC).
- Istat basi territoriali: sì / pagina / no / non riportata nella pagina letta / non dimostrata.
- OSM: sì / sì / non verificato qui / ODbL / condizionata (attribuzione, condivisione alla pari dei database derivati).
- Geoscopio / Open Geodata Regione: sì / sì / no / CC BY o CC BY-SA secondo atto 2013 / condizionata.

## Lacune e alternative

- Nessun layer comunale ha licenza esplicita. Alternativa: geometrie da fonti regionali CC BY (DBT10K, Iter.net, CTR) e OSM; layer SIT come uso interno del prototipo finché l'ente non conferma per iscritto (eventuale contatto a cura dell'utente).
- SIT scolastici: i più aggiornati per le destinazioni ma senza licenza; alternative OSM, DBT10K, Musei Provincia.
- Verde e alberi: nessuna fonte aperta in questi cataloghi (vedi audit verde).
- Da fare: wizard StatPortal (e-mail e quiz), download completo e validazione di GTFS e DBT10K, conferma CRS dei Musei.
- La selezione "pertinenti" dei dataset StatPortal usa parole chiave e descrizioni, non l'ispezione dei dati.

## File

`campioni/` (42 file, 7,2 MB, nessuno a 0 byte), `manifest.json`, `riproduci.sh`, `inventario_sit.py`, `ricerche_ckan.py`, `scarica_statportal.py`, `genera_manifest.py`.
