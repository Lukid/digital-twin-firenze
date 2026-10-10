# F03: acquisizione e normalizzazione Firenze Novoli - Firenze Nova

Data: 9 ottobre 2026. Redatto dall'agente F03 e salvato dall'integratore, che ha rieseguito i test (record, contratti, servizio, rete, verifica NL: tutto ok).

## Riproduzione

- Tutto: `DT_DAY=20261009 pipeline/run_firenze.sh` (circa 10 minuti con i download, circa 50 s con i file già in `data/raw`). Usa `pipeline/.venv`; nessun pacchetto aggiunto (serve `inflate64`, già installato con `py7zr`).
- Singole fonti: `pipeline/run_firenze.sh osm uv` (nomi: alberi civici barriere rifugi_aree rifugi_bibl uv dtm dsm osm gtfs_tram gtfs_bus tram_fermate scuole cm_edscol).
- Passi: `pipeline/.venv/bin/python pipeline/fonti_firenze.py acquire|sources|baseline`, `pipeline/norm_firenze.py [lavoro|report]`, poi `validate_records.py` e `contracts/validate.py`.
- Area scelta con `DT_AOI` (default `aoi_z2`). `lib.py` legge riquadro e margine da `contracts/aree.json`; per `aoi_z2` il risultato è identico a prima (verificato anche dall'integratore: `buf_en` invariato).
- Output: `data/raw/<fonte>/<AAAAMMGG>/` (originali intatti), `data/norm/firenze_novoli/` (GeoPackage e GeoTIFF), `pipeline/snapshots/`, `pipeline/sources/`, `pipeline/baselines/`, `pipeline/report_firenze.json`, `pipeline/t17_firenze.json`. `data/` non è versionata.
- Riacquisire lo stesso giorno riscarica il WFS delle unità volumetriche e può cambiarne lo sha256 (causa non indagata): `fonti_firenze.py baseline` avvisa se uno snapshot diverge dalla baseline congelata, e `--force` la rifà.

## Area

Riquadro FP (D13) più 700 m per lato, in EPSG:7791.

- Area allargata: E 677626,54-680521,44, N 4850435,36-4853256,26 (circa 2,9 x 2,8 km).
- Riquadro FP: E 678326,54-679821,44, N 4851135,36-4852556,26.
- Conteggi riportati come allargata / riquadro. Il riquadro è contato per intersezione con FP.

## Copertura e licenze per fonte

1. Alberi del Comune: 82.263 alberi in città oggi (dataset aggiornato ogni giorno: 82.235 e 82.225 nelle copie dell'audit). Allargata / riquadro: 8.491 / 2.917. Solo specie e circonferenza (altezza e chioma da CHM in F05). `clear` (CC BY 4.0).
2. Civici del Comune: 13.987 / 3.296. Punti d'indirizzo. `clear`. Nativi in EPSG:3003.
3. Barriere architettoniche: 222 / 63. Schede di edifici (rilievo 2013), non ostacoli sul percorso. `dbf` letto come cp850 (con ISO-8859-1 "università" diventa `universit\x85`). `clear`.
4. Rifugi climatici: aree fresche 7 / 1; biblioteche 1 / 0. `clear`.
5. Unità volumetriche regionali (WFS in EPSG:7791, volo 2011): 7.987 / 1.876. `clear_with_reserve` (licenza dedotta dalla politica regionale, come a Pisa).
6. DTM e DSM LiDAR 2023 del Comune (0,5 m, volo del 27/06/2023, foglie presenti): 49 tessere da 500 m per prodotto (343 MB ciascuno in `data/raw`), estratte con richieste Range dallo zip cittadino (Deflate64). Mosaico ritagliato sull'area allargata: 5643 x 5790 celle, 0% nodata, GeoTIFF float32 EPSG:7791. DTM 27,6-74,0 m, DSM 25,3-122,2 m. `clear`, `stored: false`. CRS 7791 assunto dal prefisso `32_` (confermato dalle quote nell'audit), datum verticale non dichiarato.
7. OSM, estratto Centro Italia dell'8/10/2026 (384.857.630 byte): strade 4.596 / 1.502, nodi con tag 20.281 / 5.829, edifici 3.885 / 714. `clear` (ODbL).
8. GTFS tram (GEST): 12 / 2 fermate, valido 10/08-30/12/2026, solo T2 e T1.3 (la T1 non c'è). Fermate in riquadro: Novoli - Regione Toscana e Novoli - Torre degli Agli (T2). `clear_with_reserve` (risorsa senza licenza).
9. GTFS bus (Autolinee Toscane): 189 / 59 fermate, valido 09/10-29/10/2026 (la copia dell'audit scadeva il 25/10), 184.543.418 byte. `clear_with_reserve`.
10. Fermate tram del Comune: 10 / 2. `clear`.
11. Scuole statali 2026/27 (MIM ripubblicate dal Comune): 37 / 7. Vamba presente come `dst_school_fiee86002g` e `dst_school_fiaa86002a`. IODL 2.0, `clear_with_reserve`, solo `internal_prototype`.
12. Edifici scolastici della Città metropolitana: 229 poligoni / 32; accessi 36 / 6. Coprono tutti i gradi (la fonte include il DB del Comune di Firenze): chiude il dubbio di F01 sulle sole secondarie. `clear_with_reserve` (risorse senza licenza), `internal_prototype`.
13. Life Escapos: tolto il 10 ottobre 2026 (D15), licenza CC BY-NC 4.0.

Destinazioni verificate nei layer: Polo delle Scienze Sociali come 6 edifici OSM (D1, D14, D15 e le relazioni D4, D5, D6, assenti dalla geometria dell'audit); scuola Vamba; 2 fermate T2 in FP.

## T17: fonte → dataset del catalogo o lacuna

Verifica sul portale regionale il 9/10/2026 (licenza di scheda e di risorse in `pipeline/t17_firenze.json`). Il rimando sta in `dataset_url` e in `provenance.note` dei record di fonte.

- Alberi: `42cd1073-521f-4040-9491-e993d03663a4` (cc-by-4.0).
- Civici: `11430710-56eb-4444-bd6f-c5433155afc5` (cc-by-4.0).
- Barriere: `92033b63-0598-4449-9007-22127abe505a` (cc-by-4.0).
- Rifugi: `rifugi_climatici_aree_fresche`, `rifugi_climatici_biblioteche` (cc-by-4.0).
- DTM e DSM 2023: `dtm-lidar-2023`, `dsm-lidar-2023` (cc-by-4.0).
- GTFS tram e bus: `rt-oraritb` (scheda cc-by; la risorsa del tram non ha licenza, quella dei bus sì).
- Fermate tram del Comune: `607b8031-252b-4442-950a-7b4452d9db8f` (cc-by-4.0).
- Scuole statali: `anagrafica-scuole-statali-2026_27` (IODL 2.0).
- Edifici scolastici della Città metropolitana: `edifici-scolastici-citta-metropolitana-di-firenze` (scheda cc-by, risorse senza licenza).
- Lacuna, unità volumetriche: sul portale esistono per altri 40 comuni, non per Firenze; fonte il WFS regionale. Proposta di pubblicazione da fare alla Regione.
- Lacuna, OSM: fonte aperta esterna, non è sul catalogo. Marciapiedi, attraversamenti e ingressi non hanno altra fonte nel catalogo.
- Nessuna fonte è usata senza licenza verificata: ogni record ha `evidence_url` e stato `clear` o `clear_with_reserve`.

## Trasformazioni e controlli

- Layer in `data/norm/firenze_novoli/`: EPSG:7791, coordinate a 0,01 m, ID univoci (asserzione in `finish`), classi per attributo nella colonna `cls` (verificate su tutti i 16 layer).
- ID: `tre_fi_<ID>`, `adr_fi_<ID>`, `bar_fi_<pk_id>`, `rif_fi_<cod_area>`, `dst_school_<codice MIM minuscolo>`, `dst_tram_<stop_code>`, `dst_stop_<stop_code>`, `bld_rt_<uv_id>`, `bld_osm_*`, `way_osm_*`, `nod_osm_*`. Dove la fonte non ha un ID univoco la chiave è codice più rango spaziale: `bld_cm_<COD_MECCAN>_<n>`, `acc_cm_<CODICE>_<n>`, `stp_fi_<nome>_<n>`.
- 3003 → 7791 (civici, barriere, tram, Città metropolitana): stesso metodo di Pisa (nessuno shift di datum). Lo scarto non è stato misurato su Firenze (a Pisa 0,35 m).
- lon/lat → 7791 (alberi, rifugi, scuole, OSM, GTFS): trattati come RDN2008 geografico (ADR-T02).
- LiDAR: reticolo da 0,5 m delle tessere conservato (bordi su multipli di 0,5 m); un campione del mosaico coincide con la tessera di origine.
- GTFS: corse del 9/10/2026 sommate per fermata (tram 4.236, bus 20.750); tutte le 12 fermate del tram e 188 su 189 dei bus hanno servizio.
- Fallimenti: durante lo sviluppo un download è fallito su `tram_fermate.zip` perché il server comprimeva al volo (byte diversi da Content-Length). `lib.download` ora chiede `Accept-Encoding: identity`.

## Validazioni

- `validate_records.py`: tutto ok (15 snapshot e 15 record nuovi, più quelli di Pisa).
- `contracts/validate.py`: 46 validi passano (la baseline di Firenze è il nuovo), 23 non validi respinti.
- Baseline `bas_firenze_novoli_20261009`: 14 snapshot; sha256 e stato di licenza coincidono con gli snapshot. L'id è in `baseline_ids` di `aoi_firenze_novoli`.
- Test di Pisa rieseguiti dopo le modifiche: `service/test_service.py`, `network/test_rete.py`, `nl/test_nl.py` ok. La normalizzazione di Pisa non è stata rieseguita: le sue chiamate usano i default invariati.

## Lacune

- Scarto 3003 → 7791 non misurato su Firenze. Via a basso costo per F04: poligoni della Città metropolitana (3003) contro unità volumetriche (7791), stesso metodo di `checks.check_3003`.
- Datum verticale di DTM, DSM e unità volumetriche non dichiarato; CRS del LiDAR 2023 assunto.
- Non acquisiti: "Luoghi freschi a Firenze" (terzo dataset dei rifugi, non richiesto), scuole paritarie (0 in FP), siti alberi del rilievo celerimetrico (solo quota, già misurata dall'audit), DB topografico (le unità volumetriche bastano, D13).
- Unità volumetriche del 2011: gli edifici nuovi vanno controllati sul LiDAR in F05. Nessuna fonte per portici e volumi sospesi.
- Per F04: grafo da OSM, marciapiedi e ingressi poveri (audit rete). Per F05: altezza edifici e chiome da nDSM e CHM (DSM di giugno).
- Il GTFS dei bus scade il 29/10/2026; il tram non ha la T1.
- La licenza IODL 2.0 delle scuole non è stata valutata giuridicamente rispetto a CC BY.
- ID con rango spaziale (Città metropolitana, fermate tram del Comune): chiave di contenuto, ma da confermare rispetto alla regola "mai posizione in elenco".
- Prefisso `dst_stop_` comune a Pisa e Firenze: nessuna collisione finché le aree stanno in file separati, da gestire in F07.
