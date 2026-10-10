# F04: rete pedonale e ingressi, Firenze Novoli - Firenze Nova

Consegna iniziale: 9 ottobre 2026. Ingressi, percorsi, default e limiti aggiornati il 10 ottobre dopo D19/D20; test Firenze rieseguito nella revisione del codice (9 controlli su 9 OK). I test di Pisa citati nella consegna iniziale non sono stati rieseguiti. Ricostruzione: `network/build_firenze.sh` (circa 90 s, di cui 70 s per leggere il file OSM da 384 MB). Solo test: `pipeline/.venv/bin/python network/test_rete_firenze.py`.

## Riproduzione

- Tutto: `network/build_firenze.sh`. Imposta `DT_AOI=aoi_firenze_novoli` ed esegue: `estrai_osm.py`, `build_rete.py`, `destinazioni_firenze.py`, `percorsi_firenze.py`, `scarto_crs_firenze.py`, `test_rete_firenze.py`. `DT_REEXTRACT=1` rifà l'estrazione OSM.
- Parametrizzazione: `network/rete_lib.py` legge `DT_AOI` (default `aoi_firenze_novoli`, D15) e ha una mappa `AREE` con i nomi per area (fonte OSM, nome dei file, cartelle di uscita). Pisa resta nel tag storico e non viene verificata dai test correnti.
- `estrai_osm.py` e `build_rete.py` sono gli stessi script di Pisa, solo con i nomi presi da `rete_lib`. Le regole sono quelle di Pisa, `network/regole.json` non è stato toccato (stesso `regole_sha256` nei due manifest).
- Script Firenze a parte: `destinazioni_firenze.py`, `percorsi_firenze.py`, `scarto_crs_firenze.py`, `test_rete_firenze.py`. Motivo: Battisti, GTFS bus, civici SIT e i casi di Pisa sono scritti nel codice di `destinazioni.py` e `percorsi.py`, e Pisa non si può rieseguire per provare un refactor. Gli script nuovi importano `Snapper`, `percorso`, `permissivo` e le altre funzioni di `rete_lib`.
- Output pesanti (non versionati): `data/norm/firenze_novoli/network/` con `rete_firenze_novoli.{gpkg,graphml,pkl}`, `osm_estratto.pkl`, `origini_snap.gpkg`.
- Output in git: `network/firenze_novoli/` (manifest, componenti, destinazioni, ingressi, snapping, barriere, percorsi campione, scarto CRS).

## Area

Riquadro FP più 700 m per lato, EPSG:7791: E 677626,54-680521,44, N 4850435,36-4853256,26. Il riquadro è E 678326,54-679821,44, N 4851135,36-4852556,26. Fonte OSM: snapshot `snp_osm_firenze_20261009`, sha256 uguale a quello della baseline `bas_firenze_novoli_20261009`.

## Grafo (`grf_firenze_novoli_osm_20261009`)

- 6.600 nodi, 9.009 archi, 294,07 km nell'area allargata, 91,26 km nel riquadro. Le chiavi `z2_en`, `km_in_z2` e l'attributo `in_z2` hanno nomi storici: per Firenze indicano il riquadro, come in `lib.py`.
- Per tipo di arco: strada 4.000 (141,8 km), sentiero 2.618 (103,8 km), marciapiede disegnato 707 (34,6 km), attraversamento 1.520 (10,6 km), sottopasso 80 (1,8 km), ponte 47 (1,2 km), scala 37 (0,3 km).
- Marciapiede: presente 13,1 km, separato 34,1 km, assente 3,2 km, ignoto 92,1 km, non applicabile 151,6 km. Non certificati (ignoto o assente): 95,3 km. Il "separato" è molto più alto di Pisa (4,5 km): a Firenze i marciapiedi sono mappati come way a parte.
- Attraversamenti: 1.520 tratti su 686 way OSM (un attraversamento è spesso spezzato in 2-5 tratti), 889 nodi crossing. Tipo: zebra 559, semaforo 266, marked 127, senza tipo 535.
- Barriere puntuali: 109 nodi passabili "da verificare" (80 cancelli, 11 sbarre, 8 blocchi, 5 dissuasori, 4 cycle barrier), 13 nodi bloccanti (tutti cancelli o sbarre con access=private, no o customers).
- Esclusi (segmenti): access=private 584 (20,0 km), classe non pedonale senza foot 274 (11,5 km), access=no 58, area a poligono 53 (7,5 km), foot=no 48, access=customers 32, costruzione 23, tunnel stradale senza marciapiede 20, banchina ferroviaria 18, proposed 17, track 15, traffic_calming 15, ferrovia 14, raceway 10, use_sidepath 1.
- Componenti: 52. Principale 282,8 km (96,2%). Le altre 51 sommano 11,3 km e 23 toccano il riquadro (7,3 km). Motivi: 41 adiacenti a tratti esclusi (per lo più access=private), 28 solo service non collegata, 9 connessioni mancanti sotto 3 m, 8 tagli del buffer, 1 con scale o sottopasso collegato a un solo capo, 1 senza motivo (lacuna o isolamento vero).
- Vicoli ciechi veri nel riquadro: 185 (113 al bordo del buffer sono tagli, non vicoli).
- Il tram corre anche in strada: strade e attraversamenti lo incrociano. Il test tollera fino a 7 m di sovrapposizione per singolo binario (massimo osservato 6,3 m; a Pisa il limite è 5 m).

## Regole e correzioni

- Regole identiche a Pisa (`regole.json`). Le way con `railway=*` e le banchine del tram non entrano (come a Pisa per le banchine ferroviarie): la banchina di una fermata T2 non è modellata.
- Nessuna correzione manuale per Firenze (`correzioni.geojson` non creato).
- Il grafo di controllo (`permissivo`) include anche i tratti `classe_non_pedonale_senza_foot` come "restrizione documentata", come a Pisa.

## Destinazioni e ingressi (`destinazioni.json`)

Tutte `da_verificare`. Il servizio MCP le mostrerà come destinazione `desk_candidate` e ingressi `unverified`, con la stessa mappatura di Pisa. Tutti gli ingressi predefiniti sono agganciati entro 40 m.

1. `dst_university_w83537185`, Polo delle Scienze Sociali. Il Polo non ha codice ufficiale: id proposto dalla way OSM 83537185 (perimetro d'insieme, 25.261 m²). Edifici: D1, D14, D15 (way) e D4, D5, D6 (relazioni), tutti dentro il perimetro.
   - Ingressi attuali: 7 civici del Comune, uno per edificio dell'Ateneo (D1, D4, D5, D6, D10, D14, D15), id `ent_civ_d*`. Per ogni origine viene scelto il più vicino per tempo. Sostituiscono i due ingressi OSM iniziali (D19); punti e porte non verificati sul posto. Evidenze in `firenze_novoli/verifica_ingressi_polo.md`.
   - Barriere del Comune: 10 schede dentro il perimetro, 8 Accessibile e 2 Parzialmente Accessibile (conteggio verificato dall'integratore su `destinazioni.json`).
2. `dst_school_fiee86002g` (Vamba primaria) e `dst_school_fiaa86002a` (Vamba infanzia). Due destinazioni, perché sono due codici MIM. Nessun ingresso OSM entro 25 m dal perimetro (way 781536026). Ingresso: accesso della Città metropolitana, `ent_cm_FIEE86002G_0` e `ent_cm_FIAA86002A_0`, stesso punto (a circa 22 m dal punto MIM), raccordo 3,45 m. Schede: 2 (scuola e asilo nido "Via Torre degli Agli snc", entrambe Accessibile).
3. `dst_tram_fm9056` (Novoli - Regione Toscana) e `dst_tram_fm9057` (Novoli - Torre degli Agli), T2, 422 corse il 9/10/2026. Ingresso: punto GTFS (`ent_gtfs_fm9056`, raccordo 4,6 m; `ent_gtfs_fm9057`, raccordo 1,4 m). Le `stop_position` OSM stanno sul binario e non sono ingressi pedonali.
4. `dst_tram_fm9055`, T2 San Donato - Università: aggiunta con D20, indicata dall'Ateneo per il Polo; circa 100 m fuori da FP, dentro il margine della rete. Ingresso `ent_gtfs_fm9055`. R01 parte da questa fermata.
5. Punto sul perimetro: implementato (`rete_lib.punto_perimetro`), usato solo se mancano ingressi OSM e CM. Nessuna destinazione lo usa oggi; il test 5 ne controlla il funzionamento sul perimetro del Polo.

Barriere architettoniche del Comune (222 in città, 63 nel riquadro: 25 Accessibile, 22 Parzialmente Accessibile, 16 Non accessibile):

- Sono attributo della destinazione (`barriere_comune`, schede dentro il perimetro con tolleranza 5 m) e dell'edificio (`barriere_edifici.json`: 58 su 63 agganciate a un edificio OSM entro 25 m, solo informativo). Mai attributo dell'arco: il test 4 verifica che nessun arco abbia campi di scheda.
- La destinazione d'uso "Universit?" ha il carattere accentato perso nel dbf (limite già noto dall'audit).

## Snapping delle origini (`snapping_report.json`)

- Origini: 3.296 civici del Comune nel riquadro (3.095 neri, 201 rossi), limite 40 m e 6 candidati come a Pisa. Agganciati 3.128 (94,9%), `insufficient_data` 168.
- I 168 non agganciati: 82 raccordi bloccati da edifici, 49 senza archi entro 40 m, 21 da tratti esclusi, 16 da edificio e tratto escluso. Mai agganciati a forza.
- Distanza civico-arco più vicino senza vincoli: p50 3,6 m, p95 28,2 m, p99 46,4 m (Pisa 41 m), max 62,8 m. Raccordo registrato: p50 3,4 m, p99 35,5 m, max 39,6 m. Oltre 20 m: 254 civici.
- Conteggi per stato rispetto al Polo (insieme degli ingressi predefiniti): `reachable` 3.112, `forbidden` 15, `isolated` 1, `insufficient_data` 168.
  - `forbidden` = agganciati a componenti collegate al Polo solo dal grafo di controllo: 12 civici di via del Ponte di Mezzo 27 (tunnel stradale senza marciapiede), piazza Artom 5 (stesso motivo), via della Verna 3 e via Salvador Allende 19/G/7 (access=private).
  - `isolated`: via delle Tre Pietre 2/P (collegata solo a un tratto di ferrovia).
- Agganciati per tipo di arco: sentiero 2.065, marciapiede disegnato 496, strada 560, sottopasso 7. Per marciapiede dell'arco: non applicabile 2.565, ignoto 507, presente 41, separato 12, assente 3.

## Percorsi campione (`percorsi_campione.json` e `.geojson`)

Ricalcolati con `accessibilita.calcola` nella revisione del 10 ottobre. Il test F06 li confronta con F04 entro le tolleranze degli arrotondamenti. Lunghezze comprensive dei raccordi; attraversamenti contati per arco originale, senza duplicare le parti create dallo snapping.

| Percorso | Origine → destinazione | Lunghezza (m) | Attraversamenti |
|---|---|---:|---:|
| R01 | T2 San Donato - Università → Polo D15 | 428,6 | 0 |
| R02 | T2 Regione Toscana → Polo D15 | 711,4 | 2 |
| R03 | T2 Regione Toscana → Polo D1 | 889,5 | 2 |
| R04 | Civico campione → Polo D15 | 235,9 | 3 |
| R05 | Civico campione → Polo D4 | 496,1 | 5 |
| R06 | Civico campione → Polo D15 | 956,1 | 10 |
| R07 | Civico campione → Polo D4 | 1195,2 | 6 |
| R08 | Civico di R05 → Vamba | 785,6 | 1 |
| R09 | T2 Torre degli Agli → Vamba | 416,6 | 3 |
| R10 | Civico di R05 → T2 Regione Toscana | 940,5 | 8 |

- V01: `forbidden`, 1217,9 m solo sul grafo di controllo; restrizioni access=private.
- V02: `forbidden`, 452,9 m solo sul grafo di controllo; restrizioni tunnel_stradale_senza_marciapiede.

I percorsi non sono verificati sul posto. R01 non passa più dai cancelli del percorso precedente da Torre degli Agli.

## Scarto 3003 → 7791 su Firenze (`scarto_crs.json`)

Stesso metodo di `checks.check_3003`: poligoni degli edifici scolastici della Città metropolitana (3003 nativo, trasformati senza shift di datum) contro le unità volumetriche regionali (7791 nativo), vertici entro 3 m, coppie con IoU ≥ 0,5.

- 132 coppie, 1.321 vertici. Differenza (unità volumetrica meno poligono trasformato): dE mediana -0,17 m, dN mediana -0,84 m, modulo mediano 0,86 m, p95 1,33 m, max 2,9 m.
- Pisa, stesso confronto: modulo mediano 1,43 m (128 vertici), p95 2,5 m. Lo scarto di Firenze è sotto il metro e non è peggiore di Pisa.
- Limite: sono due dati disegnati a mano (volo del 2011), quindi è un limite superiore dello scarto della trasformazione. Resta uno scostamento sistematico di circa 0,8 m verso sud, trascurabile rispetto al limite di snapping di 40 m. La griglia IGM ufficiale non è disponibile in locale (come a Pisa). L'operazione Helmert di `checks.py`, che a Pisa dava 0 coppie, non è inclusa.

## Test (`test_rete_firenze.py`, 9/9)

1. Percorso fermata Regione Toscana → Polo trovato, lunghezza tra 1 e 2 volte la diretta.
2. V01 (access=private) e V02 (tunnel stradale) rifiutati dal grafo e presenti sul grafo di controllo con la restrizione attesa; nessun nodo bloccante nel grafo.
3. Nessun arco su ferrovie, tram o banchine o sovrapposto a un binario per più di 7 m.
4. foot e access rispettati, ID univoci, marciapiede ignoto mai dichiarato, attraversamenti e scale presenti, nessun campo scheda sugli archi.
5. Ogni destinazione agganciata a un ingresso (id nel formato di `conventions.json`, classe dichiarata, `da_verificare`); Polo con 7 civici degli edifici, Vamba con accesso CM, 3 fermate T2; barriere come attributo; punto sul perimetro funzionante.
6. Origini: non agganciate = `insufficient_data`, stati che sommano al totale, `forbidden` > 0.
7. Regressione sugli archi invertiti (distanze di rete = calcolo indipendente).
8. Manifest coerente con snapshot e baseline (sha256, `graph_id`, `aoi_id`).
9. Default Firenze senza `DT_AOI`.

## Lacune per l'analisi (F06)

- Marciapiede ignoto su 92 km (31%): il tag assente non prova l'assenza. Nessuna larghezza, pendenza o rampa: nessuna certificazione di accessibilità.
- Conteggio attraversamenti: `riassunto()` conta i tratti, non le way. I percorsi di Firenze riportano anche `attraversamenti_way`.
- Polo: i 7 civici degli edifici sono candidati, non porte verificate. Orari documentati nelle condizioni di accesso; cancelli, accessi reali e percorsi interni da verificare.
- Vamba: un solo accesso nei dati, condiviso dai due codici. L'asilo nido "Torre degli Agli snc" cade nel perimetro e finisce tra le schede.
- Tram: la banchina non è modellata. Il punto GTFS è agganciato al più vicino arco pedonale (raccordo 1,4-4,6 m). Fermate bus non incluse tra le destinazioni (GTFS bus scade il 29/10/2026).
- 80 cancelli passabili per ipotesi (presenti su R06 e R10; il nuovo R01 non ne attraversa), 53 aree a poligono (piazze) non modellate, 185 vicoli ciechi nel riquadro da controllare.
- 15 civici `forbidden` su 3.296: 13 per tunnel stradale senza marciapiede (potrebbe essere un passaggio pedonale vero), 2 per access=private.
- Civici rossi (201) inclusi come origini: sono ingressi commerciali, non abitazioni.
- Il marciapiede "separato" (34 km) è alto: verificare che il profilo di analisi lo tratti come marciapiede presente.
- I motori F06-F10 sono stati portati su Firenze; rimangono nomi interni storici per compatibilità. I difetti attuali sono nella [revisione del codice](../docs/REVISIONE-CODICE-20261010.md).
- Scarto CRS: vedi sopra, non è una misura pura. Datum verticale non toccato.
