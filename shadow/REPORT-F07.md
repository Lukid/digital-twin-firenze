# F07: ombre su Firenze Novoli

Data: 10 ottobre 2026. Motore `shadow/ombre.py` versione 0.3.0. Non validato sul posto.

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

- Percorsi da `network/firenze_novoli/percorsi_campione.geojson`, sull'asse della rete, verso l'ingresso predefinito del Polo `ent_osm_n11152998932`:
  - R01: dalla fermata T2 Torre degli Agli, 1.198 m.
  - R02: dalla fermata T2 Regione Toscana, 708 m.
- Date: 15 luglio e 15 settembre 2026, ogni 30 minuti fra 8:00 e 19:00, passo spaziale 1 m, passo temporale 5 min, 1,2 m/s.
- Fasce: punta 12:30-13:30 e giornata intera.
- Casi: edifici (h_min, h, h_max); edifici e alberi (min, tipico, max); più vegetazione LiDAR (min, tipico, max).
- Il 15 settembre alle 19:00 il sole è sotto 5 gradi: istante non calcolato (`sole_basso_fuori_supporto`).

## Risultati principali

Frazione media del percorso in ombra, valore tipico (intervallo min-max).

| Percorso, data, fascia | Edifici | Edifici e alberi | Con vegetazione LiDAR |
|---|---|---|---|
| R01, 15 luglio, punta | 4,1% (3,3-4,3) | 6,3% (4,4-9,1) | 8,0% (5,8-10,9) |
| R01, 15 luglio, giornata | 11,0% (9,6-12,8) | 14,3% (11,7-20,0) | 17,0% (14,0-22,7) |
| R01, 15 settembre, punta | 21,0% (18,7-22,6) | 24,3% (22,7-26,7) | 26,6% (24,6-29,3) |
| R01, 15 settembre, giornata | 36,8% (34,2-38,5) | 43,0% (39,1-47,7) | 45,6% (41,5-50,2) |
| R02, 15 luglio, punta | 16,8% (13,1-17,7) | 16,8% | 17,1% |
| R02, 15 luglio, giornata | 33,7% (31,2-35,1) | 33,7% (33,7-34,1) | 34,0% (34,0-34,4) |
| R02, 15 settembre, punta | 43,4% (40,8-44,9) | 43,4% | 44,3% |
| R02, 15 settembre, giornata | 52,4% (50,5-53,8) | 52,5% (52,4-52,8) | 53,3% (53,1-53,6) |

- Minuti al sole camminando, 15 settembre, punta: R01 13,2 (edifici), 12,6 (con alberi), 12,3 (con vegetazione LiDAR) su 16,6 di cammino; R02 5,7, 5,7 e 5,6 su 9,8.
- R01 passa vicino a molti alberi: alberi e vegetazione pesano da 2 a 6 punti.
- R02 non ha quasi alberi censiti sul percorso: gli alberi non cambiano il risultato, la vegetazione LiDAR aggiunge meno di 1 punto.
- A mezzogiorno di luglio R01 è al sole per oltre il 90%: è il candidato naturale per uno scenario di filare.
- Dettaglio per ora e caso in `shadow/firenze_novoli/sintesi.json` (`frazione_per_ora`).

## File prodotti

- Versionati in `shadow/firenze_novoli/`: `sintesi.json`, `tratti_ombra_2026-07-15.geojson` e `tratti_ombra_2026-09-15.geojson` (casi `base`, `alberi_tipico`, `veg_lidar_tipico`), `manifest/` (job `job_859254156d6848ac` e `job_a8aeee0223eedafa`).
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
