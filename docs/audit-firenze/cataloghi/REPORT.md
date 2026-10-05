# Cataloghi e licenze per il ciclo Firenze (F01)

Audit del 5 ottobre 2026. Solo letture HTTP pubbliche e API CKAN di dati.toscana.it. Nessun contatto con enti, nessuna pubblicazione.

## 1. Metodo

- Ricerche per parola chiave sul catalogo regionale: 28 termini, con conteggi. Dump in `docs/research/ckan-toscana-fi-ricerche.json`.
- Elenco dei 1.992 dataset del Comune di Firenze: titolo, licenza, formati, data, frequenza. Dump in `ckan-toscana-fi-comune-firenze.json`.
- `package_show` dei 37 dataset che coprono i layer del ciclo F, scelti da `layers.py`. Dump in `ckan-toscana-fi-pacchetti.json`.
- Verifica dei download: 87 URL provati con GET parziale (Range 0-65535, redirect seguiti). Si registrano codice, URL finale, dimensione dichiarata e natura dei primi byte (zip, json, html). Dump in `ckan-toscana-fi-url.json`.
- Contenuto: letti per intero gli 11 GeoJSON disponibili, con numero di elementi, campi e CRS dichiarato (`ckan-toscana-fi-contenuto.json`). Provati anche gli indirizzi `harvest_url` delle schede.
- GTFS: il feed del tram (1,2 MB) e il feed autolinee (176.482.531 byte) sono stati scaricati per intero e analizzati. Si contano fermate e linee nel riquadro di contesto di `RIQUADRO.json` (`ckan-toscana-fi-gtfs-*.json`). Il feed autolinee non è conservato; ne resta lo sha256.
- Licenza: confronto fra `license_id` della scheda e `license_type` di ogni risorsa. Le sigle sono normalizzate (per esempio A21_CCBY40 diventa CC BY 4.0). Conflitto = famiglie diverse (BY, BY-SA, NC).
- Il campo "dato" è `modified` della scheda, cioè la data dichiarata dall'ente. "Scheda" è `metadata_modified`, cioè la data di raccolta sul portale. Le due date possono divergere.

## 2. Inventario

Tutti i dataset del Comune sono CC BY 4.0, salvo i casi segnalati. Codici HTTP: 206 = GET parziale accettato, 200 = il server ignora Range. La colonna "Formati" elenca le risorse della scheda. La tabella generata dallo script è in `inventario-tabella.txt`.

| Layer | Dataset (id) | Organizzazione | Formati | Licenza (scheda; risorse) | Dato; scheda | Frequenza | Download |
|---|---|---|---|---|---|---|---|
| Alberi pubblici (censimento) | 42cd1073-521f-4040-9491-e993d03663a4 | Comune di Firenze | GeoJSON, RDF, SHP | CC BY 4.0; CC BY 4.0 | 05-10-2026; 2026-10-05 | DAILY | 206; SHP 3,4 MB, GeoJSON 23,2 MB, RDF 90,6 MB |
| Siti alberi da rilievo celerimetrico | fc7e03ee-9406-42ce-b176-0767b67ed299 | Comune di Firenze | SHP, ZIP (dxf) | CC BY 4.0; CC BY 4.0 | 17-08-2017; 2026-02-11 | AS_NEEDED | 206; 0,9-1,1 MB |
| DTM LiDAR 2023 | dtm-lidar-2023 | Comune di Firenze | URL (zip ASCII grid), WMS | CC BY 4.0; CC BY 4.0 | 27-06-2023; 2026-02-11 | NOT_PLANNED | 206; zip 922,7 MB (redirect a datigis.comune.fi.it) |
| DSM LiDAR 2023 | dsm-lidar-2023 | Comune di Firenze | URL (zip ASCII grid), WMS | CC BY 4.0; CC BY 4.0 | 27-06-2023; 2026-02-11 | NOT_PLANNED | 206; zip 1.038,3 MB |
| DTM e DSM LiDAR 2017 | dtm-2017; dsm-2017 | Comune di Firenze | URL, WMS | CC BY 4.0; CC BY 4.0 | 02-05-2017; 2026-02-11 | NOT_PLANNED | 206; zip 186,7 e 208,1 MB |
| Civici | 11430710-56eb-4444-bd6f-c5433155afc5 | Comune di Firenze | SHP, WMS | CC BY 4.0; CC BY 4.0 | 05-10-2026; 2026-10-05 | AS_NEEDED | 206; SHP 6,1 MB |
| Barriere architettoniche | 92033b63-0598-4449-9007-22127abe505a | Comune di Firenze | SHP, KML | CC BY 4.0; CC BY 4.0 | 03-06-2015; 2026-02-11 | NOT_PLANNED | 206; SHP 112 kB |
| Percorsi Walking City (7 percorsi base) | 7 dataset (id in inventario.json) | Comune di Firenze | KML (kmz) | CC BY 4.0; CC BY 4.0 | 20-10-2017; 2026-02-11 | NOT_PLANNED | 206; da 1 a 5 kB ciascuno |
| Rifugi climatici | rifugi_climatici_aree_fresche; rifugi_climatici_biblioteche; 2d881d20-8b0c-47c7-8acb-a4dd42fe71ee (luoghi freschi) | Comune di Firenze | GeoJSON, SHP, KML, WMS | CC BY 4.0; CC BY 4.0 | 04-07-2019 e 18-06-2026; 2026-02-11 e 2026-06-19 | AS_NEEDED | 206; da 2 kB a 0,2 MB |
| Life Escapos | life_escapos_mobile_measurements (50 alberi); escapos_mobile_measurements; lifeescapos_nuovopignone; lifeescapos_giardinolippi | Comune di Firenze | GeoJSON, SHP, WMS | CC BY-NC 4.0; CC BY-NC 4.0 | 12-02-2026; 2026-02-13 | AS_NEEDED | 206; da 16 kB a 0,3 MB |
| Edifici, Comune (cassone edilizio da rilievo celerimetrico) | 6a0a42f0-3b1f-4498-8de1-a57b592cee59 | Comune di Firenze | SHP, ZIP (dxf) | CC BY 4.0; CC BY 4.0 | 07-08-2017; 2026-02-11 | NOT_PLANNED | 206; SHP 2,7 MB, ZIP 4,2 MB |
| Edifici, DB topografico regionale 1:2.000 | dbt2k | Regione Toscana | SHP | cc-by; CC BY-SA 4.0 (conflitto) | 15-10-2015; 2020-03-30 | ANNUAL | La risorsa è una pagina HTML (cartoteca), non un file |
| Edifici, DB topografico regionale 1:10.000 | dbt10k-li-pi-pt-po-si | Regione Toscana | ZIP (7z) | cc-by (versione non indicata); CC BY 4.0 | 20-04-2015; 2020-03-31 | UNKNOWN | 206; fogli 118-487 MB. Livorno, Pisa, Prato, Pistoia, Siena: Firenze non c'è |
| CTR regionale 1:2.000 e 1:10.000 | ctr2k; ctr10k | Regione Toscana | SHP, TIFF, DXF, WMS | cc-by (versione non indicata); CC BY 4.0 | 15-10-2015; 2020-03-31 | UNKNOWN | Tutte le 10 risorse puntano alla pagina HTML della cartoteca, nessun file |
| GTFS tram (GEST) | rt-oraritb, risorsa gest.gtfs | Regione Toscana | ZIP | cc-by; risorsa senza licenza | 01-11-2023; 2026-09-08 | UPDATE_CONT | 206; 1,19 MB, zip valido |
| GTFS bus (Autolinee Toscane) | rt-oraritb, risorsa AUTOLINEE_TOSCANE.gtfs | Regione Toscana | ZIP | cc-by; CC BY 4.0 | stesso dataset | UPDATE_CONT | 200 (Range ignorato); 176,5 MB, zip valido |
| Fermate e tracciato tram (Comune) | 607b8031-252b-4442-950a-7b4452d9db8f; 23160550-904f-4765-8fc9-89c88dc60226 | Comune di Firenze | SHP, KML, WMS | CC BY 4.0; CC BY 4.0 | 11-03-2025 | AS_NEEDED, NOT_PLANNED | 206; da 3 a 24 kB |
| Quartieri (5 poligoni) | 5e08844a-c0d8-4d64-a3b2-d1ab58d9283f | Comune di Firenze | SHP, KML, WMS | CC BY 4.0; CC BY 4.0 | 16-02-2012; 2026-02-11 | NOT_PLANNED | 206; SHP 31 kB |
| Scuole, Comune (anagrafe MIM 2026/27, statali 222 punti, paritarie 109) | anagrafica-scuole-statali-2026_27; anagrafica-scuole-paritarie-2026_27 | Comune di Firenze | CSV, GeoJSON, SHP, WMS | IODL 2.0 (non CC BY); IODL 2.0 | 18-09-2026; 2026-09-19 | NOT_PLANNED | 206; da 9 a 87 kB |
| Edifici scolastici, Città metropolitana | edifici-scolastici-citta-metropolitana-di-firenze | Città metropolitana di Firenze | WMS, ZIP | cc-by (versione non indicata); risorse senza licenza | 13-02-2014; 2026-04-24 | IRREG | 200; zip 44 e 341 kB |
| Aree pedonali e aree stradali (Comune) | 4b49d9a5-6b91-451d-b7c3-73ea6cd3e83b; a44ea551-7b09-4d0d-af64-7c08159e9316 | Comune di Firenze | GeoJSON, SHP, KML | CC BY 4.0; CC BY 4.0 | 09-02-2026 e 26-05-2025 | AS_NEEDED, WEEKLY | 206; aree stradali SHP 2,0 MB. La risorsa KML delle aree stradali restituisce una pagina di errore HTML |
| Aree verdi (Comune) | d0ffa579-e002-4dc3-94b4-d69207cae114 | Comune di Firenze | GeoJSON, SHP, RDF | CC BY 4.0; CC BY 4.0 | 05-10-2026; 2026-10-05 | AS_NEEDED | 206; GeoJSON 5,4 MB |
| OSM | non su CKAN | - | - | ODbL | - | - | Alternativa: estratto Italia centro da Geofabrik, 384.457.431 byte, 206 |
| Scuole, MIM (fonte primaria) | non su CKAN | MIM | - | non verificata | - | - | Il Comune ripubblica la stessa anagrafe in IODL 2.0 |

Nota dell'integratore sugli edifici scolastici della Città metropolitana: questo audit li descrive come sole secondarie superiori (competenza provinciale), l'audit delle destinazioni vi ha trovato 2.544 poligoni e 608 accessi, con nidi e scuole del primo ciclo fra i poligoni. Da chiarire in F03 prima di usarli come fonte degli ingressi.

Contenuto verificato sui GeoJSON (tutti scaricati e letti):
- Alberi: 82.225 punti, campi CIRCONF_CM, CODSITO_ALBERO, ID, NOME_COMUNE, QUARTIERE, SPECIE. Nessun campo di altezza o chioma. FONTI.md riporta 82.235: il dataset si aggiorna ogni giorno, differenza di 10 da capire in F03.
- Life Escapos alberi: 50 punti, campi h_m, can_h_m, canopy_area_m2, dbh_cm, crn_w_m, lai, species, più stime di assorbimento.
- Rifugi climatici: 41 aree fresche (poligoni) e 7 biblioteche (punti).
- Aree pedonali: 394 poligoni con attributi di accessibilità (bici, carrozzine, persone).
- Aree verdi: 1.687 poligoni.
- Nessun campo di licenza dentro i dati. Gli zip degli shapefile contengono solo shp, shx, dbf, prj (e cst per Escapos), nessun file di metadati o licenza.

GTFS nel riquadro di contesto:
- Tram (feed GEST): linee T2 e T1.3, route_type 0, 61 fermate totali, 16 nel riquadro di contesto (tra cui Novoli, Careggi, Morgagni-Università, Peretola Aeroporto). Calendario dal 10-08-2026 al 30-12-2026, senza `feed_info`. La T1 non compare con quel nome: da controllare in F03.
- Bus (feed Autolinee Toscane): 946 linee tutte route_type 3, 33.833 fermate, 238 fermate e 40 linee nel riquadro di contesto. Finestra del feed dal 05-10-2026 al 25-10-2026 (tre settimane).
- Il feed autolinee non contiene il tram: il tram è in un file a parte.

## 3. Conflitti e anomalie di licenza

Conflitti veri (scheda e risorse dicono cose diverse):
- DB topografico regionale 1:2.000 (`dbt2k`): scheda "cc-by", risorsa A31_CCBYSA40, cioè CC BY-SA 4.0. Per gli edifici regionali la condivisione alla pari cambierebbe i vincoli sulla redistribuzione. Da chiarire prima di usarlo. Per Pisa il conflitto analogo era sul LiDAR: a Firenze il LiDAR del Comune è coerente (CC BY 4.0 ovunque).

Anomalie minori:
- Versione CC non indicata nella scheda (`cc-by` senza 4.0): dbt10k, ctr2k, ctr10k, rt-oraritb, edifici scolastici della Città metropolitana. Nelle risorse la versione c'è (CC BY 4.0) tranne dove la licenza manca.
- Licenza assente sulle risorse: tre dei GTFS (tft, toremar, gest cioè il tram) e le risorse dei dataset della Città metropolitana. La scheda dice cc-by, la risorsa tace.
- Scuole del Comune: IODL 2.0, non CC BY. È una licenza aperta che richiede attribuzione; compatibilità con gli altri layer da valutare.
- Comune di Firenze, elenco completo: 1.957 dataset cc-by-4.0, 26 iodl2, 7 cc-by-nc-4.0, 1 cc-by-nc-sa-4.0, 1 cc-by-sa-3.0-it.
- Altra licenza non commerciale nel catalogo regionale: `edilizia-scolastica` (Regione), scheda other-nc, risorse C1_Unknown. Non è nel nostro elenco di layer: non usarla senza chiarimento.
- Dati personali: `escapos_mobile_measurements` ha 50 righe di misure fisiologiche di partecipanti (HRV, battito RR) con data e ora. Non servono al progetto: non usarle.

### Life Escapos, CC BY-NC 4.0 (decisione aperta dell'utente)

- La licenza consente l'uso solo se non è "principalmente rivolto a un vantaggio commerciale o a un compenso monetario". Un progetto di un'azienda privata, svolto a pagamento per un ente, rientra con ogni probabilità nell'uso commerciale. Anche un uso solo interno di verifica (confronto altezze con LiDAR) è un'area grigia, e ogni derivato eredita il divieto commerciale.
- Una via è chiedere al Comune di Firenze, titolare dei dati, un permesso scritto o una licenza diversa per l'uso di verifica. La decisione e l'eventuale contatto sono dell'utente.

## 4. Lacune del catalogo per questo uso

Cosa serve a una città per un gemello pedonale e non c'è sul portale:
1. Altezza degli edifici. Il Comune pubblica le impronte da rilievo celerimetrico 2017 (cassone edilizio, geometria PolygonZ), ma non c'è un attributo di altezza né un layer di volumetrie. Il DB topografico regionale 1:2.000 non è scaricabile da CKAN (risorsa = pagina della cartoteca sul geoportale, e conflitto di licenza). Il DB topografico 1:10.000 su CKAN non copre Firenze. Fonte alternativa: DSM meno DTM 2023 per le altezze, OSM per un confronto.
2. Rete pedonale: nessun layer di marciapiedi, attraversamenti pedonali, ingressi degli edifici. Esistono solo aree pedonali (394 poligoni), aree stradali e impianti semaforici. Fonte alternativa: OSM per marciapiedi e attraversamenti, civici per gli ingressi.
3. Altezza e chioma degli alberi. Il censimento (82.225 alberi) ha specie e circonferenza. L'altezza è solo nei 50 alberi Life Escapos (licenza NC). Serve una chioma da CHM (DSM meno DTM) o un censimento esteso.
4. Barriere architettoniche: censimento fermo al 2013 (2.064 schede, frequenza NOT_PLANNED). Copre edifici e spazi aperti, non dislivelli, pendenze, larghezze o pavimentazioni dei percorsi.
5. Walking City: la scheda dice 18 percorsi (7 base, 11 collegati), su CKAN ci sono solo i 7 base, in KMZ da 1 a 5 kB.
6. DTM e DSM: solo zip ASCII grid dell'intera città (0,9 e 1,0 GB per il 2023), senza tile, senza GeoTIFF, senza servizio di scarico per riquadro. Il WMS serve solo per visualizzare. Manca il modello delle chiome (CHM).
7. Scuole: l'anagrafe è ripubblicata dal Comune da una fonte nazionale, non la fonte primaria MIM su CKAN.
8. OSM: non su CKAN. Fonte alternativa: estratto regionale, licenza ODbL (attribuzione e condivisione alla pari dei database derivati).
9. GTFS: finestra mobile di tre settimane per le autolinee, nessun archivio storico. Il feed è un file unico di 176 MB che ignora Range. Il feed del tram non ha licenza sulla risorsa e non ha `feed_info`.
10. Metadati:
    - Il campo "sistema di riferimento" dice ROMA40/OVEST su tutte le schede del Comune, mentre i dati dichiarano EPSG:4326 (alberi, rifugi aree fresche, scuole), EPSG:3003 (rifugi biblioteche) ed EPSG:7791 (Life Escapos). Il campo è inaffidabile.
    - Gli indirizzi `harvest_url` delle schede rispondono 404 in 31 casi su 32.
    - Le date `modified` non coincidono con quelle reali (DBT 1:10.000 dichiarato 2015, fogli del 2010).
    - Una risorsa rotta: il KML delle aree stradali.
11. Nessun file di metadati o licenza dentro gli shapefile scaricabili.

## 5. Limiti

- GET parziale: dimensione e tipo da intestazioni, contenuto dei file grandi non letto (LiDAR, DBT, GTFS bus oltre stops, routes, trips, stop_times).
- Dati dichiarati dal Comune (frequenze, date, CRS) non verificati con l'ente. Le date `modified` possono essere date di rilievo, non di pubblicazione.
- I conteggi del GTFS sono sul riquadro di contesto, non sulle zone FA e FB (per quelle vedi l'audit delle destinazioni).
- Nessuna verifica del contenuto del DB topografico regionale per Firenze (non scaricabile da CKAN).
- Licenza MIM, dati personali di Escapos, compatibilità IODL 2.0 con CC BY e BY-SA non valutate giuridicamente.
- L'inventario copre i layer di `layers.py`; gli altri 1.955 dataset del Comune sono nei dump ma non letti uno per uno.

## 6. File e riproduzione

In `docs/audit-firenze/cataloghi/`: `layers.py`, `ricerche_ckan_fi.py`, `verifica_url.py`, `controlli_contenuto.py`, `inventario.py`, `genera_manifest.py`, `riproduci.sh`, `manifest.json`, `inventario.json`, `inventario-tabella.txt`.
In `docs/research/`: `ckan-toscana-fi-ricerche.json`, `ckan-toscana-fi-comune-firenze.json`, `ckan-toscana-fi-pacchetti.json`, `ckan-toscana-fi-url.json`, `ckan-toscana-fi-contenuto.json`, `ckan-toscana-fi-gtfs-tram.json`, `ckan-toscana-fi-gtfs-autolinee.json`.

Riprodurre: `docs/audit-firenze/cataloghi/riproduci.sh` (variabili opzionali: `PY` per l'interprete, `GTFS_DIR` per la cartella del feed autolinee). Il primo avvio dura circa 5 minuti.
