# Edifici, altezze e terreno per Z1-Z4 (gate G2)

Audit del 1 ottobre 2026. Redatto dall'agente edifici (T01) e salvato dall'integratore. Tutto rigenerabile con `riproduci.sh`; URL, byte e sha256 in `manifest.json` (56 file, nessuno a 0 byte).

Zone di circa 1 km², riquadri (S,W,N,E, EPSG:4326) in `script/zone.py`, proposti dall'agente e non approvati:
- Z1: 43.7130,10.3940,43.7210,10.4080
- Z2: 43.7040,10.3910,43.7125,10.4050
- Z3: 43.7010,10.4360,43.7100,10.4510
- Z4: 43.7215,10.4000,43.7295,10.4160

## 1. Fonti: esistenza, accesso, contenuto, riuso

- **Unità volumetriche (UV) regionali** (WFS `https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato`, layer `rt_edif.unitavolumetriche`): esiste; GetFeature GML con filtro per riquadro riuscito (JSON non ammesso). Contenuto: altezza `uv_av` e quota suolo `uv_qs` in tutti i 3.121 oggetti delle 4 zone, volo luglio 2010, scala 1:2.000; nessun edificio posteriore. Riuso: capabilities Fees e AccessConstraints "none", nessuna licenza per layer; vale la politica regionale open geodata (CC BY / CC BY-SA, atto 2013). Citare la fonte.
- **DSM 1 m 2021** (WMS `wmsmorfologia`, layer `iddsm2021.1m.rt`): GetMap `image/tiff` float32, massimo 4096 px. Da autocorrelazione di immagini (GSD 15 cm). Metadati: "non sottoposto alle consuete verifiche di conformità", Regione esclusa da responsabilità sui derivati. CC BY, titolarità Regione.
- **DTM 1 m da LiDAR 2019-2021** (`iddtm.1m.irs`): GetMap riuscito ma valori zero su Z1-Z4. Sonda a griglia su Pisa: dato presente solo a sud e a est. Licenza CC BY-NC-SA, proprietà Italian Remote Sensing, concesso a RT per distribuzione ad altri enti pubblici: non riusabile liberamente.
- **DTM 10 m** (`iddtm.10m.rt`): scaricato, CC BY. Scarto rispetto a `uv_qs`: MAE 0,4-1,1 m.
- **DB topografico 1:2.000** (CKAN `dbt2k`): la risorsa punta alla cartoteca Geoscopio (pagina con sessione); download per foglio non esercitato. Il dataset `database-topografico-1-2-000` (aggiornato 2026, foto 2024) è del Comune di Chianni, non Pisa.
- **SIT comunale**: `periodizzazione_edificato_share/1` (45.360 oggetti) e `Base_CTR_per_POC/1` (47.555). Query per riquadro riuscita, limite 2000 oggetti, senza paginazione (Z2 su `Base_CTR_per_POC` troncata, risolta con 4 quadranti: 2.128). Poligoni 3D senza attributo di altezza; la Z (3-5 m) è quota del terreno. `tipo` quasi sempre vuoto: gli edifici non si distinguono dagli altri areali. `copyrightText` vuoto, nessuna licenza: riuso non documentato. `Hosted/Base_DBTopografico` è solo tile; `Base_CTR_2023/1` solo linee; `Hosted/edifici_scolastici` ha restituito una risposta di errore di 63 byte.
- **OSM** (Overpass): scaricate tutte le 4 zone dopo molti tentativi (timeout, 429, 504). ODbL: attribuzione e condivisione alla pari delle basi derivate.
- **Cataloghi**: API CKAN regionale e dati.gov.it ok; l'indirizzo CKAN del Comune ha risposto 404. Nel catalogo regionale 80 risultati "unità volumetriche" di singoli comuni, nessuno è Pisa (zero risultati, non prova di assenza). Dati nazionali: non approfonditi.
- **Datum verticale**: non dichiarato nei metadati letti (solo RDN2008 / UTM 32N). Evidenza indiretta: DSM, DTM 10 m e `uv_qs` coerenti entro circa 1 m. Da confermare con la Regione.
- Il GetMap WMS è un surrogato del download ufficiale: ricampionamento e traslazioni sub-pixel non verificati.

## 2. Numeri per zona (UV, volo 2010)

Tre conteggi distinti di "edificio": UV (porzioni ad altezza omogenea), edifici distinti `edifc_id`, UV senza `edifc_id`.

- Z1: 923 UV, 787 edifici, 136 senza id, altezza 100%
- Z2: 998 UV, 689 edifici, 309 senza id, altezza 100%
- Z3: 238 UV, 180 edifici, 58 senza id, altezza 100%
- Z4: 962 UV, 713 edifici, 249 senza id, altezza 100%

L'altezza è misurata (restituzione fotogrammetrica) ma vale solo per gli oggetti presenti nel 2010. Decili `uv_av`: Z1 4,0-18,3 m; Z3 2,9-17,7 m.

Portici: `uv_por` = "al suolo" ovunque nelle 4 zone (anche Borgo Stretto), mentre è popolato per circa 3.000 UV nella regione: attributo non popolato qui, non assenza di portici. Volumi sospesi: nessuna fonte li rileva; il DSM non vede sotto una copertura.

OSM (edifici; con `height`; con `building:levels`; senza nessuno dei due; centro fuori da ogni UV 2010):
- Z1: 1.202; 6 (0,5%); 208 (17%); 991; 92
- Z2: 908; 1; 404 (45%); 503; 70
- Z3: 214; 0; 46 (21%); 168; 66 (31%)
- Z4: 806; 0; 220 (27%); 586; 46

`min_height` 0 ovunque; `building=roof` Z1 2, Z2 15, Z3 5, Z4 4.

Post-2010 (indicatore approssimato): poligoni `Base_CTR_per_POC` ≥ 40 m² fuori da ogni UV: Z1 149/1.449, Z2 113/1.227, Z3 61/384, Z4 115/1.211. È un limite superiore (include aiuole e altri areali). Gli edifici OSM fuori UV sono un indicatore più pulito: Z3 31%.

## 3. Coerenza fra fonti

- OSM vs UV (abbinamento per punto interno): 6 edifici con `height`, differenza mediana -1,1 m, scarto assoluto medio 1,5 m (campione troppo piccolo). 817 edifici con soli piani: `uv_av` per piano mediana 3,85 m (decili 3,0 e 5,1). Usare i piani darebbe un'altezza stimata, non misurata.
- UV vs DSM 2021 su 582 volumi ≥ 40 m² dentro i tile da 500 m (`campioni/ndsm_confronto.csv`). Quota tetto (DSM p90 meno `uv_qe`), mediana:
  - Z1 +2,4 m (10°-90° pct 0,5 : 5,4; scarto assoluto medio 2,8)
  - Z2 +1,1 m (-0,3 : 4,8; 2,3)
  - Z3 +1,0 m (-0,5 : 3,3; 1,6)
  - Z4 +1,2 m (0,1 : 2,5; 1,4)
- Datum con suolo da anello 2-4 m: Z2 -0,1, Z3 +0,2, Z4 -0,1 m; Z1 non affidabile (strade strette, l'anello cade sui tetti).
- Il DSM sopra `uv_av` è atteso: vede colmi, comignoli, abbaini e variazioni dopo il 2010, mentre `uv_av` è un'altezza di corpo. Non è un errore di una fonte; nessuna delle due è un riferimento indipendente.
- Campione di 16 edifici (4 per zona) in `campioni/campione_coerenza.csv`.

## 4. Terreno

Pisa è piana (2-5 m s.l.m.). Il DTM 10 m basta per la quota di base; non regge sottopassi, argini, scarpate. La quota di base è già in `uv_qs`. Il DTM 1 m LiDAR non è utilizzabile (nessun dato nelle zone) né riusabile (NC-SA, enti pubblici).

## 5. Lacune e alternative

- Edifici post-2010 senza altezza: DSM 2021 meno terreno, precisione non verificata (avvertenza regionale) e da ripulire dalla vegetazione. Alternativa: rilievo locale su pochi siti.
- Portici e volumi sospesi: nessuna fonte; censimento o rilievo locale sulle strade del caso ombra.
- Chiome: fuori scopo di questo audit; il DSM le include senza separarle.
- Download ufficiale per foglio (DB topografico 1:2.000, LiDAR/DSM) dalla cartoteca non esercitato (serve sessione browser): prossimo passo. WMS usato come surrogato.
- SIT comunale senza licenza: verifica con l'ente prima di redistribuire. Nessun contatto avviato.
- Versione più recente delle UV per Pisa non trovata (tutte 2010). Dati nazionali non esaminati.

## 6. Giudizio provvisorio G2

Fattibile per gli edifici esistenti al 2010, con riserve. Altezza misurata per volume e quota suolo ci sono in tutte le zone, datum coerente con DSM 2021.

- Z4 e Z2 più solide (scarto contro DSM 1,4-2,3 m).
- Z1: buone altezze ma portici irrisolti e scarto 2,8 m.
- Z3 la più debole: 238 volumi e 31% di edifici OSM fuori dal 2010.
- Il terreno non blocca.

Prima di chiudere G2: confronto con un riferimento indipendente (rilievo o LiDAR di terzi) e sensibilità della quota ombreggiata a 1-2 m di incertezza.

## File

`manifest.json`, `riproduci.sh`, `campioni/` (25 MB, file singoli sotto 2 MB), `script/` (zone, fetch_sit, fetch_rt_uv, fetch_raster, fetch_osm, analizza_ndsm, analizza_osm_uv, campione16, make_manifest), `.venv/` locale (shapely, pyproj, rasterio, numpy; non versionato). Output chiave: `campioni/statistiche_zone.json`, `ndsm_confronto.csv`, `osm_vs_uv.csv`, `campione_coerenza.csv`.
