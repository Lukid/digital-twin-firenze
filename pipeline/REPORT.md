# T03: acquisizione e normalizzazione Z2

Data: 1 ottobre 2026. Redatto dall'agente T03 e salvato dall'integratore.

## Riproduzione

- Tutto: `DT_DAY=20261001 pipeline/run.sh` (crea `pipeline/.venv` se manca; circa 40 s con i file già in `data/raw`, più i download).
- Singole fonti: `pipeline/run.sh osm uv` (nomi: gtfs_at gtfs_tren osm uv dsm dtm10 civici scuole edscol dbt10k iternet).
- Passi: `pipeline/.venv/bin/python pipeline/{acquire,normalize,inspect_big,checks,sources,validate_records,report}.py`.
- Output: `data/raw/<fonte>/<AAAAMMGG>/` (originali intatti), `data/norm/*.gpkg` e `*.tif`, `pipeline/snapshots/`, `pipeline/sources/`, `pipeline/report.json`. `data/` non è versionata; `data/work/` (4,3 GB di estratti) si può cancellare.

## Area

Z2 più 500 m per lato, calcolata da `docs/audit/ZONE.json`. EPSG:7791: E 611559,81-613703,67, N 4839437,71-4841400,77 (circa 2,1 x 2,0 km). Z2 da sola: E 612059,81-613203,67, N 4839937,71-4840900,77. Conteggi: buffer / Z2.

## Copertura e licenze per fonte

1. GTFS Autolinee Toscane: 185.529.498 byte, sha256 identico all'audit. Fermate 92 / 40. Corse e linee del 1/10 coincidono con l'audit. `clear_with_reserve`. Scade il 21/10/2026 (`feed_end_date`).
2. GTFS Trenitalia: valido 15/01-12/12/2026. 1 stazione (Pisa Centrale, 248 corse). `clear_with_reserve`.
3. OSM: estratto Centro Italia del 30/09/2026, 384 MB; Overpass non usato. L'URL "latest" dava 502: si scarica il file con la data (`OSM_URL` per aggiornarlo). Strade 2.251 / 737, nodi con tag 4.880 / 1.859 (834 alberi, 427 attraversamenti, 540 ingressi nel buffer), edifici 2.879 / 938. Gli ingressi della scuola dell'audit ci sono. `clear` (ODbL).
4. Unità volumetriche (WFS, richieste direttamente in EPSG:7791): 3.107 / 1.034, nessun duplicato fra pagine. Volo 2010. `clear_with_reserve`.
5. DSM 1 m 2021 (WMS): 1963x2144 pixel, nessun nodata. DTM 10 m: 196x214, 0,51% nodata (-9999) mascherato. Surrogato del download ufficiale, datum verticale non dichiarato. `clear_with_reserve`.
6. SIT: civici 7.606 / 2.224, scuole 18 / 6, edifici scolastici 18 / 6. `unproven`, solo `internal_prototype`. Civici nativi in EPSG:3857. Le scuole non hanno il codice MIM: nessun `dst_` ufficiale dal solo SIT.
7. DBT10K Pisa: 411.509.203 byte, cc-by con licenza PDF nel pacchetto. Nel buffer: 3.107 unità volumetriche (gli stessi oggetti del WFS), 307 alberi puntuali (2010), 382 aree verdi, 23 aree pedonali, 929 aree stradali, quote e curve di livello. EPSG:3003 con Z. Solo ispezionato (`pipeline/ispezione_big.json`), utile per T05.
8. Iter.net: 460.484.895 byte, licenza BY o BY-SA da accertare. Nel buffer: 1.114 elementi stradali, 330 strade, 6.288 civici, 1 stazione. Solo ispezionato, utile per T04 come confronto con OSM.

Licenze di GTFS e DBT10K confermate con gli strumenti MCP CKAN. Unità volumetriche, DSM, DTM e Iter.net non sono nel catalogo CKAN: licenze dai metadati dell'audit.

## Trasformazioni (`pipeline/crs_check.json`)

- 3003 → 7791: unità volumetriche DBT10K (3003) contro WFS (7791), stessi 3.107 oggetti, 25.652 vertici abbinati. Scarto costante dE +0,32 m, dN -0,13 m, mediana 0,35 m, massimo 0,38 m.
- Nessuno shift di datum applicato: la griglia IGM ufficiale non è disponibile in locale; un Helmert a 3 parametri peggiora la sovrapposizione delle impronte SIT (IoU 0,07 contro 0,54).
- SIT contro regionale: 128 vertici di 11 edifici scolastici, scarto mediano 1,4 m (dE +1,0, dN -0,6). È digitalizzazione diversa, non solo trasformazione.
- lon/lat → 7791 (OSM, GTFS): 2.237 vertici, mediana 0,08 m, massimo 0,15 m. Conferma l'ipotesi dell'ADR (sotto 1 m).
- Nessuna correzione di offset applicata.

## Validazioni

- 11 snapshot e 11 record di fonte validi (`pipeline/.venv/bin/python pipeline/validate_records.py`, rieseguito dall'integratore: tutto ok).
- `contracts/validate.py`: 31 validi passano, 10 non validi respinti.
- Fallimento simulato (URL OSM inesistente): snapshot `failed` con `previous_snapshot_id` valido per lo schema; il normalizzatore usa l'ultimo snapshot ok.
- ID univoci su ogni layer; CRS 7791 con precisione 0,01 m; classi per attributo nella colonna `cls`.

## Lacune

- Licenza SIT non dimostrata (decisione aperta).
- Datum verticale di DSM, DTM e unità volumetriche non dichiarato; DSM e DTM letti via WMS.
- DTM LiDAR 1 m non acquisito (non copre Pisa, licenza in conflitto).
- ID SIT non ufficiali (`objectid_1`, `fid`): possono cambiare se il layer viene ricreato.
- Nessuna stima né scenario: classi solo measured o derived.
- DBT10K e Iter.net non normalizzati; raster in GeoTIFF, non in GeoPackage.
