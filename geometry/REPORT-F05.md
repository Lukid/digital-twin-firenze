# F05: edifici e verde di Firenze Novoli

Data: 9 ottobre 2026. Redatto dall'agente F05, salvato dall'integratore. `bash geometry/build_firenze.sh` (circa 15 s); test `pipeline/.venv/bin/python geometry/test_geometrie_firenze.py`: OK, rieseguito dall'integratore.

## Riproduzione

- `bash geometry/build_firenze.sh` (esporta `DT_AOI=aoi_firenze_novoli`, poi costruisce e collauda). Richiede `data/norm/firenze_novoli/` di F03.
- Script a parte, `geometry/build_firenze.py`, invece di parametrizzare `build_geometrie.py`. `build_geometrie.py` è lineare, ha area e file di Pisa nel corpo (DSM 1 m, DTM 10 m da WMS ricalibrato, alberi OSM/DBT) e non si importa senza rieseguirlo. Parametrizzarlo avrebbe toccato Pisa. Si riusano `lib.AOI` (sola lettura), `parametri_chiome.json` e la forma degli output.
- Input: `rt_uv_firenze_novoli`, `osm_firenze`, `fi_alberi`, `fi_dsm2023_0.5m`, `fi_dtm2023_0.5m`, `fi_escapos_alberi`.
- Output pesanti: `data/norm/firenze_novoli/geometry/geometrie_firenze_novoli.gpkg` (layer volumi, alberi, vegetazione_lidar, osm_stato) e `escapos_verifica.csv` (per albero, solo in `data/`).
- Output in git: `geometry/firenze_novoli/{edifici_fp,alberi_fp}.geojson` (4326, solo FP, 1,4 MB e 1,8 MB) e `report_firenze_novoli.json`.

## Area

Riquadro FP (D13) più 700 m, EPSG:7791. Edifici e alberi sono calcolati sull'area allargata (gpkg). Il geojson ha solo FP. Conteggi riportati come FP / allargata.

## Edifici

- Volumi: 1.952 / 8.266. Sono 1.876 / 7.987 unità volumetriche (UV 2011), più 76 / 279 da OSM senza UV: volumi nuovi 73 / 238, coperture OSM (`building=roof`) 3 / 41.
- Altezza di un'UV:
  - nDSM 2023 (DSM meno DTM), mediana sull'impronta erosa di 1 m, se area almeno 40 m² e almeno 20 celle valide: classe `derived`, fonte `lidar_2023+uv_rt_2011`.
  - Altrimenti `uv_av` 2011, classe `measured`.
  - FP: 1.442 `derived` e 510 `measured`. Allargata: 6.004 e 2.262.
  - Restano in `h_uv` e `h_lidar` entrambe le altezze.
- Intervalli:
  - Se nDSM e UV concordano (scarto dopo bias sotto 3 m): fascia fra i due valori ±0,5 m.
  - Se differiscono molto: ±1,88 m (metà p10-p90 dello scarto, include l'errore delle UV, quindi prudente).
  - Se resta uv_av: ±0,5 m, ipotesi come a Pisa (la fonte non dichiara incertezza).
- Scarto nDSM meno `uv_av` su 5.930 impronte (almeno 40 m², senza alberi censiti entro 2 m, area allargata): mediana +0,61 m, p10 -1,33, p90 +2,43, MAE 1,75. Il bias +0,61 è più alto del +0,37 dell'audit (campione diverso). Il bias si sottrae solo per i flag, non per l'altezza.
- Quota di spiccato: `uv_qs` meno DTM 2023 su 7.960 UV: mediana -0,03 m, sigma robusta 0,61, MAE 0,70.
- Cambiamenti dopo il 2011 (flag su UV, FP / allargata):
  - ok 1.224 / 5.270.
  - non_confrontato (sotto 40 m²) 435 / 1.978.
  - lidar_piu_alto (sopraelevazioni o ampliamenti probabili) 98 / 308.
  - lidar_piu_basso 44 / 147.
  - demolizione_probabile 51 / 183 (nDSM sotto 1 m con `uv_av` almeno 3 m). Hanno `presente_2023` falso e restano nel file con altezza UV.
  - lidar_sotto_1m 21 / 86 (volume basso, nDSM indistinguibile dal terreno, resta `uv_av`).
  - scarto_con_vegetazione 3 / 15.
- Edifici nuovi: OSM coperto da UV per meno del 30% (301 "senza_uv" e 702 "parziale" in tutto). Geometria = OSM meno UV, parti sotto 10 m² scartate. Altezza da nDSM mediana. Allargata: 185 confermati dal LiDAR (almeno 2,5 m), 94 sotto 2,5 m o senza LiDAR (probabili baracche o pensiline, flag `sotto_2_5m`). 6 senza altezza (`lidar_insufficiente`), restano nel layer con altezza nulla.
- OSM e LiDAR contro UV: 1.445 UV hanno meno del 30% coperto da OSM. Di queste 790 hanno nDSM alto, quindi manca OSM, non l'edificio. Solo 131 sono `demolizione_probabile`. OSM non serve come prova di demolizione: 36 delle 183 demolizioni probabili hanno OSM che le copre per almeno l'80% (da verificare a vista, forse tettoie o impronte con il tetto sotto 1 m).
- Edifici nuovi presenti solo nel LiDAR (né UV né OSM): non ricostruiti. Nel layer `vegetazione_lidar` i cluster a pendenza bassa sono candidati (62 in FP, area `liscia`), ma non si distinguono da alberi o altro con certezza.
- Portici e volumi sospesi: "ignoto" su tutti i volumi. Il nDSM li include come tetto, ma il suolo sotto è modellato come terreno.

## Alberi (2.917 in FP, 8.491 allargata)

Chiome misurate e stimate separate e contate:

| | FP | Allargata |
|---|---|---|
| Chioma misurata (`derived`) | 2.050 (70%) | 6.218 |
| Chioma stimata (`estimated`) | 867 | 2.273 |
| di cui poche celle di chioma | 655 | 1.616 |
| di cui CHM sotto 2,5 m entro 3 m | 169 | 556 |
| di cui in edificio | 42 | 99 |
| di cui coperto da edificio | 1 | 2 |

- Regole di misura:
  - Posizione e specie dal censimento (`measured`).
  - CHM = DSM meno DTM. Le celle con CHM almeno 2,5 m e fuori dalle impronte (UV e OSM, +0,5 m) vanno all'albero censito più vicino entro 7,5 m (Voronoi): le chiome vicine si dividono e l'unione non cambia.
  - Gli alberi con il punto dentro un edificio non fanno da seme e non tolgono celle ai vicini.
  - Altezza = p95 del CHM entro 3 m dal tronco nelle celle dell'albero. Intervallo ±(1 m + 10%), ipotesi.
  - Diametro chioma = cerchio equivalente dell'area delle celle. Intervallo ±30%, con limite alto ×1,6 se la chioma è confinante o vicina a un edificio (può essere troncata). Altezza d'imposta sempre `estimated` (parametri di classe, tetto 0,7 h): il CHM non la dà.
- Regole di stima (chioma `estimated`):
  - In edificio.
  - Almeno metà della finestra di 3 m sotto edificio.
  - Meno di 12 celle di chioma entro 3 m.
  - Altezza oltre 40 m.
  - Se anche il CHM massimo entro 3 m è sotto 2,5 m: motivo `sotto_2_5m`, altezza 2-4 m e chioma della classe piccola (giovane o tolto).
  - Altrimenti: classe da circonferenza (diametro tronco = circ/π, soglie a metà fra i diametri tipici di `parametri_chiome.json`: piccolo, medio, grande). Valori da specie+classe (p10-p50-p90 di altezza e diametro sugli alberi misurati, solo con almeno 30 misurati, 39 combinazioni, 399 stime FP) oppure dalla classe del JSON. Circonferenza nulla o oltre 4,7 m: classe "ignota" (33 in FP).
- Segnalazioni: vicino a edificio 174 / 570, chioma confinante 920 / 3.745, doppioni entro 1 m 6 / 47.
- Misurati FP: altezza p10-p50-p90 5,2 - 8,7 - 16,2 m; diametro chioma 2,9 - 5,8 - 10,6 m.
- Chioma LiDAR nell'allargata (CHM ≥ 2,5 m, fuori edifici): 958.301 m² totali. 293.414 m² assegnati ad alberi misurati, 7.297 ad alberi stimati, 657.590 senza albero censito (giardini privati, parchi, siepi). Cluster di almeno 20 m² senza albero: 911 (122.085 m²) in FP, 4.117 (553.710 m²) allargata, nel layer `vegetazione_lidar`. È un'ombra potenziale mancante, perché il censimento è solo pubblico.

## Verifica interna su Life Escapos (CC BY-NC 4.0)

In git solo aggregati (n, mediana, MAE, r). Scarto = pipeline meno `h_m`.

| Campione | Misura | n | Mediana | MAE | r |
|---|---|---|---|---|---|
| 24 in FP (tutti misurati) | h CHM p95 | 24 | -0,08 m | 0,13 m | 0,965 |
| 24 in FP | h CHM massimo (sensibilità) | 24 | +0,08 m | 0,12 m | 0,976 |
| 24 in FP | diametro chioma contro `crn_w_m` | 24 | -0,32 m | 0,60 m | 0,644 |
| 50 allargata (48 misurati, 2 stimati) | h CHM p95 | 48 | -0,10 m | 0,20 m | 0,990 |
| 50 allargata | h CHM massimo | 48 | +0,14 m | 0,23 m | 0,995 |
| 50 allargata | h pipeline, misurata o stimata | 50 | -0,10 m | 0,40 m | 0,811 |
| 50 allargata | diametro chioma contro `crn_w_m` | 48 | +0,04 m | 0,69 m | 0,892 |

- Stima dalla sola circonferenza (classe del JSON, senza LiDAR, quindi non circolare): sui 50, altezza tipica contro `h_m` mediana -0,32 m, MAE 1,10 m, r 0,715, intervallo min-max copre l'88%. Sui 24 FP mediana -0,27, MAE 0,46, copertura 100%, r non definito perché sono tutti della stessa classe.
- Limite di indipendenza: l'accordo con `h_m` non prova nulla di indipendente. `dbh_cm` coincide con la circonferenza del censimento divisa π, `h_m` ha precisione piena e provenienza non documentata, quindi probabile derivazione dallo stesso LiDAR. È un controllo di coerenza interna, non una validazione. Serve una misura di campo.
- Campione piccolo e poco vario: 36 su 50 sono Celtis australis, 24 in FP.
- Scelta a priori, non tarata sul campione: p95 invece del massimo (a Pisa il p95).

## Datum verticale

Non confermato (convenzione `datum_verticale`). Coerenza interna: `uv_qs` meno DTM 2023 mediana -0,03 m, MAE 0,70 m, n 7.960 (audit F01: -0,14 m su 1.419). Nessuna correzione sistematica applicata. Le altezze relative non dipendono dal datum. `z_base` degli alberi è la quota DTM 2023 nel punto (`derived`, incertezza 0,61 m dalla sigma robusta delle UV contro DTM).

## Test

- `pipeline/.venv/bin/python geometry/test_geometrie_firenze.py`: id univoci, conteggi coerenti con il report, intervalli ordinati, classi per attributo, `presente_2023` falso solo per demolizioni, nessuna chioma misurata in edificio, misurate più stimate uguali al totale con motivi che sommano, imposta sotto la chioma, campione Escapos 24 e 50, soli aggregati e nessun campo o id Escapos in file versionati, limite di indipendenza scritto.
- Impronte con sovrapposizione oltre il 50%: 0.

## Lacune per le ombre (F06-F10)

- Portici e volumi sospesi ignoti. Impronte UV del 2011: edifici nuovi solo dove li ha OSM, nessun edificio da solo LiDAR.
- Chiome: forma ellissoidale idealizzata opaca (nessuna trasparenza né LAI). Il volo è del 27/06/2023 con le foglie: la chioma invernale non è modellata. Chiome confinanti e vicine a edifici possono essere troncate (flag, intervallo alto ×1,6).
- Alberi privati non censiti: 657.590 m² di chioma senza albero (553.710 m² in cluster di almeno 20 m²) non hanno un oggetto. F06 deve decidere se usarli come chiome (proposta dell'agente: sì, dal CHM direttamente) o dichiarare ombra solo da edifici e alberi pubblici.
- Intervalli di altezza e diametro: ipotesi non tarate su misure indipendenti. Il LiDAR include vegetazione bassa, auto e catenarie sopra 2,5 m (non filtrate).
- Il bias nDSM-UV non è sottratto dall'altezza: l'altezza LiDAR di un edificio può essere di circa 0,6 m sopra uv_av (gronda contro colmo non documentato).
