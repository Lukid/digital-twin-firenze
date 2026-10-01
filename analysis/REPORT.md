# T06: accessibilità pedonale Z2 (analisi A)

Data: 1 ottobre 2026. Redatto dall'agente T06 e salvato dall'integratore. `bash analysis/run.sh` esegue analisi e test in pochi secondi: 10 blocchi di assert OK (rieseguito dall'integratore). Risultati `not_validated_locally`.

## Difetto trovato in T04

In `network/rete_lib.py` (`con_agganci`) 1.116 archi su 3.901 sono memorizzati con verso (u,v) opposto alla geometria, mentre l'offset dello snap è misurato sulla geometria: le origini o gli ingressi su quegli archi ricevono i tratti parziali sul lato sbagliato. T06 usa una versione corretta in `analysis/accessibilita.py`, senza toccare `network/`.

- Effetto sui percorsi campione: R05 524,3 m (T04: 561,5), R09 363,2 m (T04: 400,4); gli altri entro 0,3 m.
- Su tutte le origini vale distanza di rete ≥ linea d'aria.
- Da correggere alla radice in `network/rete_lib.py` e rigenerare i percorsi campione.

## Stati

Su 2.224 origini: 2.148 reachable, 21 forbidden, 55 insufficient_data, 0 isolated, 0 outside_model.

I 21 civici su cmp_14 e cmp_24 (indicati come isolated in T04) sono `forbidden`: sono collegati solo da tratti access=customers (18) o access=private (3), cioè da restrizioni documentate, come V01. `isolated` resta per le componenti scollegate anche sul grafo di controllo o escluse dal profilo: oggi nessuna.

## Profili e soglie

Ipotesi di esperimento, non attribuite a gruppi di persone, come da SPEC.

- base 1,2 m/s; lento 0,8; rapido 1,4 (velocità della SPEC).
- ridotta: 0,8 m/s, scale escluse, 10 s per attraversamento (ipotesi dell'agente). Mancano pendenze, larghezze e rampe: non certifica accessibilità.
- Soglie 5/10/15 min dalla SPEC. Deviazione alta: rapporto ≥ 1,5 con linea d'aria ≥ 100 m (ipotesi).

## Risultati (profilo base, quota delle 2.224 origini entro 5/10/15 min)

- Battisti: 10,2% / 52,5% / 84,7%. Tempo p50 9,7 min, p90 15,6, massimo 23,7. Rete p50 695 m.
- Pellico: 30,4% / 66,3% / 74,2%. Tempo p50 7,3 min, p90 18,9, massimo 31,0. Rete p50 524 m.
- Deviazione mediana 1,32 (Battisti) e 1,33 (Pellico); p90 1,56 e 2,34. Origini con deviazione alta: 400 e 535 (soglia larga: circa un quinto delle origini).
- Quota entro 10 min per profilo (Battisti / Pellico): lento 19,4% / 44,1%; rapido 65,2% / 69,9%; ridotta 17,8% / 42,4%.
- Il profilo ridotta aggiunge circa 45 m di rete mediana verso Battisti: 734 origini allungano il percorso per evitare la scala.
- 592 origini verso Battisti passano da una scala di 38 gradini (`edg_osm_22717629_11480720548_11480720545`, due archi di 13 e 18 m). 596 attraversano cancelli "da verificare".
- Marciapiede ignoto: 8,6% dei metri di rete verso Battisti, 12,6% verso Pellico.

## Tratti più usati a marciapiede ignoto (priorità per il sopralluogo)

- Battisti: via Corridoni (`edg_osm_521878072_285181910_3760169296`, 829 origini), piazza della Stazione (504), via Montanelli (circa 395).
- Pellico: tratto di 5,8 m su via Pellico (`edg_osm_1077907317_5264115226_9882762242`, 1.335 origini), rotatoria e via Pellico (circa 1.230).
- Elenco completo in `analysis/out/riepilogo.json` (`archi_ignoti_piu_usati`).

## Sensibilità (profilo base)

- Snapping 20/40/60 m: reachable 2.103 / 2.148 / 2.164; insufficient_data 102 / 55 / 39. Quota entro 10 min Battisti 51,4% / 52,5% / 52,9%, Pellico 65,4% / 66,3% / 66,6%. p50 stabile entro 0,1 min: cambia la copertura, non gli indicatori.
- Ingresso Battisti: con tutti i 9 ingressi vince il più vicino (1.236 origini su Corridoni 35, 888 su via Vespucci 16); la quota entro 10 min sale a 57,8% e il p50 scende da 9,65 a 8,97 min. Con i singoli ingressi contigui la quota va da 48,7% a 54,4%. I 10 tratti più usati cambiano del tutto. Gli ingressi contigui sono di altri edifici: la variante è un limite superiore, non una stima.

## Asset e codice

- `analysis/out/accessibilita_battisti.geojson` e `accessibilita_pellico.geojson` (632 KB l'uno, EPSG:4326): 2.224 civici con stato, tempo per i 4 profili e metri a marciapiede ignoto, più destinazione e archi più usati.
- `analysis/out/riepilogo.json`: aggregati e sensibilità.
- `analysis/manifest/`: 8 manifest e job, validi per gli schemi di `contracts/`, con sha256 degli asset. Il `job_id` include la versione del metodo e lo sha256 del grafo.
- `data/norm/analysis/` (non versionata): tabelle delle origini, archi usati, report.
- Libreria: `compute_walk_access(destination_id, origin_family, profile, thresholds_min, snap_limit_m, entrance_ids, out_dir)` in `analysis/accessibilita.py`.

## Per T07

`mcp.compute_walk_access.input` ammette nel profilo solo `speed_m_s` e `snap_limit_m` e come origini solo `points` o `grid`. Va esteso con `crossing_penalty_s`, `stairs`, `entrance_ids` e la famiglia di origini `civici_sit_z2`.

## Limiti

Rete OSM non verificata sul posto. Civici SIT come punti d'indirizzo, non residenti, con licenza non dimostrata (solo uso interno). Velocità e penalità ipotesi. Nessuna validazione locale (T11).

## Da verificare al sopralluogo

1. Quale ingresso della Battisti è in uso: è la scelta che sposta di più i risultati.
2. La scala da 38 gradini e i cancelli usati da quasi tutte le origini.
3. Il marciapiede nei tratti ignoti più usati.
4. Il lato della fermata Pellico e la rotatoria.
5. I 21 civici di via Poerio (access=private o customers) e i 55 non agganciati.
