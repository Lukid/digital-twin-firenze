# F07: ombre su Firenze Novoli

Data: 10 ottobre 2026, numeri aggiornati dopo D19 e D20 (calcolo del 10 ottobre, `sintesi.json`). Motore `shadow/ombre.py` versione 0.3.0. Non validato sul posto.

## Cosa è cambiato

- Il motore non ha più costanti di Pisa. Area, baseline, file di geometria e coordinate del sole vengono dall'area corrente (`DT_AOI`, default `aoi_firenze_novoli`, tramite `pipeline/lib.py` e `contracts/aree.json`).
  - Baseline: `bas_firenze_novoli_20261009`.
  - File: `data/norm/firenze_novoli/geometry/geometrie_firenze_novoli.gpkg`.
  - Snapshot: unità volumetriche, OSM, DSM e DTM 2023, censimento alberi.
  - Sole calcolato nel centro del riquadro (43,798; 11,226). Verità di riferimento del sole rigenerate con l'algoritmo SPA in quel punto.
- Testi, limiti e manifest senza "Pisa" né "Z2". Un test lo verifica.
- I volumi con `presente_2023` falso (183 demolizioni probabili) non proiettano ombra.
- Nuovo `shadow/veg_lidar.py`: poligoni della chioma LiDAR senza albero censito.
- Nuovi casi `veg_lidar_min`, `veg_lidar_tipico`, `veg_lidar_max`: edifici, alberi e vegetazione LiDAR.
- Nuova uscita `tratti`: GeoJSON EPSG:4326 dei tratti di percorso in ombra, per percorso, ora e caso. Parametro opzionale `tratti_casi` in `compute_shadow`, firma compatibile.
- Il job_id usa l'hash del contenuto dei poligoni, non del file: identico a ogni ricostruzione.
- `run.py`, `run.sh` e `test_ombre.py` riscritti per Firenze. `verifica_raster.py` resta ma è fuori dal flusso (finestra e dati di Pisa).
- Con `DT_AOI=aoi_z2` il motore non parte più: Pisa resta nel tag `pilota-pisa-z2`.

## Vegetazione LiDAR (D14)

- Il layer `vegetazione_lidar` di F05 ha solo il baricentro di ogni cluster. `veg_lidar.py` rifà la maschera di F05: CHM 2023 almeno 2,5 m, fuori da edifici UV e OSM (buffer 0,5 m), a più di 7,5 m da ogni albero censito, cluster di almeno 20 m².
- Coerenza con F05: 4.117 cluster e 553.709,5 m², uguali.
- Esclusi i 279 cluster `liscia` (probabili tetti non mappati, 53.873 m²). Restano 3.838 cluster, 499.837 m².
- Forma: prisma opaco sull'impronta del cluster. `z_hi` = 95° percentile del CHM nel cluster. `z_lo` = frazione di `z_hi`: 0,25 tipico, 0,4 min, 0,15 max.
- Le frazioni sono i percentili p50, p90 e p10 del rapporto imposta / altezza degli alberi censiti di Novoli (0,25, 0,41, 0,14), con imposta limitata a metà altezza.
- L'ombra sul suolo dipende poco da `z_lo`, tranne sotto la chioma.

## Comandi

- Tutto: `bash shadow/run.sh` (circa 10 minuti).
- Solo vegetazione: `pipeline/.venv/bin/python shadow/veg_lidar.py` (circa 10 s).
- Solo analisi: `pipeline/.venv/bin/python shadow/run.py [--rapido]`.
- Solo test: `pipeline/.venv/bin/python shadow/test_ombre.py` (circa 90 s).

## Impostazione

- Percorsi da `network/firenze_novoli/percorsi_campione.geojson`, sull'asse della rete, verso l'ingresso del Polo più vicino per rete, `ent_civ_d15` (D19):
  - R01: dalla fermata T2 San Donato - Università, 428,6 m (D20; prima partiva da Torre degli Agli).
  - R02: dalla fermata T2 Novoli - Regione Toscana, 711,5 m.
- Date: 15 luglio e 15 settembre 2026, ogni 30 minuti fra 8:00 e 19:00, passo spaziale 1 m, passo temporale 5 min, 1,2 m/s.
- Fasce: punta 12:30-13:30 e giornata intera.
- Casi: edifici (h_min, h, h_max); edifici e alberi (min, tipico, max); più vegetazione LiDAR (min, tipico, max).
- Il 15 settembre alle 19:00 il sole è sotto 5 gradi: istante non calcolato (`sole_basso_fuori_supporto`).

## Risultati principali

Frazione media del percorso in ombra, valore tipico (intervallo min-max).

| Percorso, data, fascia | Edifici | Edifici e alberi | Con vegetazione LiDAR |
|---|---|---|---|
| R01, 15 luglio, punta | 29,0% (22,3-30,6) | 29,0% | 29,5% |
| R01, 15 luglio, giornata | 49,1% (46,1-51,0) | 49,1% | 49,7% |
| R01, 15 settembre, punta | 70,2% (66,8-71,5) | 70,2% | 71,8% (71,6-71,8) |
| R01, 15 settembre, giornata | 68,1% (65,4-69,8) | 68,1% | 69,5% |
| R02, 15 luglio, punta | 15,0% (11,2-15,9) | 15,0% | 15,3% |
| R02, 15 luglio, giornata | 33,1% (30,6-34,5) | 33,1% (33,1-33,5) | 33,5% (33,5-33,9) |
| R02, 15 settembre, punta | 41,5% (38,7-43,0) | 41,5% | 42,4% (42,3-42,4) |
| R02, 15 settembre, giornata | 51,1% (49,1-52,5) | 51,3% (51,1-51,5) | 52,0% (51,8-52,3) |

- Minuti al sole camminando, 15 settembre, punta: R01 1,9 (edifici), 1,9 (con alberi), 1,8 (con vegetazione LiDAR) su 6,0 di cammino; R02 5,9, 5,9 e 5,8 su 9,9.
- Su tutti e due i percorsi l'ombra viene quasi solo dagli edifici: gli alberi censiti non cambiano R01 e spostano R02 di 0,2 punti al massimo, la vegetazione LiDAR aggiunge meno di 2 punti.
- A mezzogiorno di luglio R01 è al sole per il 71% e R02 per l'85%.
- Dettaglio per ora e caso in `shadow/firenze_novoli/sintesi.json` (`frazione_per_ora`).

## File prodotti

- Versionati in `shadow/firenze_novoli/`: `sintesi.json`, `tratti_ombra_2026-07-15.geojson` e `tratti_ombra_2026-09-15.geojson` (casi `base`, `alberi_tipico`, `veg_lidar_tipico`), `manifest/` (job `job_9f53a7f2ba439f75` per il 15 luglio e `job_036f7d4e2464e6d0` per il 15 settembre).
- Grandi in `data/norm/firenze_novoli/shadow/`: poligoni della vegetazione, righe CSV e sintesi per job.

## Limiti

- Percorsi sull'asse della rete: il lato del marciapiede è ignoto. A Pisa era l'incertezza dominante; qui non è stata misurata.
- Vegetazione LiDAR come prisma opaco pieno con altezza h95: tende a sovrastimare l'ombra. Include siepi e arbusti da 2,5 m in su; auto e catenarie non filtrate. Chioma invernale non modellata (volo di giugno 2023).
- I cluster `liscia` sono esclusi come probabili tetti, senza certezza.
- Edifici nuovi solo dove li ha OSM. Portici ignoti trattati come pieni. Altezze LiDAR 2023 con unità volumetriche 2011. Datum verticale non confermato.
- Demolizioni probabili escluse sulla base del solo LiDAR 2023.
- Censimento alberi solo pubblico. Chiome come ellissoidi idealizzati, imposta sempre stimata.
- Sole sotto 5 gradi non calcolato.
- Convergenza dei passi verificata solo su un caso sintetico. Nessuna sensibilità sul lato del marciapiede.
- Nessuna osservazione di campo.
