# Stato del progetto

Aggiornato al 10 ottobre 2026: POC di Firenze Novoli completo nei quattro punti chiesti (accessibilità, ombre, scenari, scena alla Padova), con servizio MCP. Il 10 ottobre Polo e fermata T2 sono stati rifatti (D19, D20) e ricalcolati da F04 a F11. Punto di ripartenza per la prossima sessione.

## In una riga

Gemello digitale pilota di Firenze, area Novoli - Firenze Nova (riquadro FP di 2 km²), costruito solo da open data con licenza che ne permette il riuso, per mostrarne le potenzialità. Pisa è accantonata nel tag git `pilota-pisa-z2` (D15); il 10 ottobre i suoi file sono stati tolti dal ramo principale, tranne gli script di rete e geometria di Pisa (`network/build.sh`, `geometry/build.sh` e i loro test), non più mantenuti.

## Fatto su Firenze (ogni consegna ha un REPORT e un test rieseguito dall'integratore)

| Task | Dove | Controllo |
|---|---|---|
| F01 audit e riquadro | `docs/audit-firenze.md`, `docs/audit-firenze/` | approvato (D13) |
| F02 contratti a più aree | `contracts/` (ADR-F02.md) | `contracts/.venv/bin/python contracts/validate.py` |
| F03 acquisizione, 15 fonti (+ aree pedonali del Comune) | `pipeline/` (REPORT-F03.md) | `pipeline/.venv/bin/python pipeline/validate_records.py` |
| F04 rete e ingressi | `network/` (REPORT-F04.md) | `pipeline/.venv/bin/python network/test_rete_firenze.py` |
| F05 edifici e verde | `geometry/` (REPORT-F05.md) | `pipeline/.venv/bin/python geometry/test_geometrie_firenze.py` |
| F06 accessibilità | `analysis/` (REPORT-F06.md) | `bash analysis/run.sh` |
| F07 ombre | `shadow/` (REPORT-F07.md) | `pipeline/.venv/bin/python shadow/test_ombre.py` (90 s) |
| F08 scenari | `scenarios/` (REPORT-F08.md) | `bash scenarios/run.sh` (15 min senza cache) |
| F09 scena 3D, con livelli accessibilità, ombra e scenari | `scene/firenze_novoli/` (ADR-F09.md) | `pipeline/.venv/bin/python scene/firenze_novoli/test_build.py` e verifica nel browser |
| F10 servizio e MCP `dt-firenze` | `service/` (REPORT-F10.md) | `service/.venv/bin/python service/test_service.py` |
| F11 verifica in linguaggio naturale | `nl/firenze_novoli/` (REPORT.md) | `service/.venv/bin/python nl/firenze_novoli/test_nl.py` (30 s); giro rifatto dopo D19-D20 |

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/ (funziona anche senza rete: three.js è in `vendor/`)

Ricerca sui gemelli già esistenti a Firenze: `docs/research/gemelli-firenze.md`.

## Risultati principali (non validati sul posto)

- Accessibilità a 1,2 m/s, quote sui 3.296 civici entro 10 minuti: Polo delle Scienze Sociali 28% (54% entro 15, mediana 14 min; 7 ingressi, il più vicino vince), scuola Vamba 39%, fermate T2 San Donato - Università 24%, Regione Toscana 30%, Torre degli Agli 39%. Con un solo ingresso del Polo la quota a 10 minuti scende al 24-28%.
- Ombra sui percorsi fermata T2 → Polo, 12:30-13:30: R01 (San Donato - Università → D15, 429 m) in ombra al 30% a luglio e al 72% a settembre; R02 (Regione Toscana → D15) al 15% e al 42%. Alberi e vegetazione LiDAR pesano meno di 2 punti.
- Scenari: filare su R01 (versione 3, stessa regola sul nuovo R01, tratto 198-258 m) -0,36 minuti di sole a mezzogiorno di luglio, da -0,11 a -0,63 con la chioma; a settembre -0,41. Pensilina alla fermata bus Guidoni Barsanti: a mezzogiorno di luglio l'area di attesa passa da 0% a 40% d'ombra.

- Scenari aggiunti (10 ottobre): pensiline S5 (fermata bus Regione Toscana, area di attesa da 0% a 40% d'ombra a mezzogiorno di luglio) e S6 (Di Novoli Sn, già all'ombra a mezzogiorno). Filari nuovi su R02 e verso Vamba non possibili con la regola di S1 (su R02 ricade su S1).
- Nuovi livelli nella scena (10 ottobre): particelle catastali con ricerca per foglio e particella; temperatura delle superfici Landsat (41 giornate estive 2023-2026) con l'aria della stazione SIR Firenze Università; qualità dell'aria 2025 dalle 6 stazioni ARPAT di Firenze (la più vicina, FI-MOSSE, a 745 m dal riquadro).

## Limiti principali

- Ombra misurata sull'asse della rete, non sulla linea dove si cammina.

- Rete solo OSM, lato del marciapiede ignoto. Ingressi del Polo: un civico del Comune per edificio dell'Ateneo (indirizzi dal report di accessibilità dell'Ateneo), non verificati sul posto; il civico non è per forza la porta (`network/firenze_novoli/verifica_ingressi_polo.md`).
- La fermata San Donato - Università sta circa 100 m fuori dal riquadro FP: in scena c'è il terreno, non gli edifici attorno.
- Civici come punti d'indirizzo, non persone.
- Vegetazione LiDAR come prisma opaco pieno: limite superiore dell'ombra.
- Altezze LiDAR 2023 con unità volumetriche 2011, portici ignoti, datum verticale non confermato.
- GTFS bus congelato valido fino al 29/10/2026.
- Nessuna validazione sul posto.

## Decisioni prese dall'utente

- D12: pilota a Firenze, Novoli - Firenze Nova.
- D13: riquadro FP, destinazioni Polo, T2, Vamba; rete con margine di 700 m solo OSM.
- D14: chioma LiDAR senza albero censito inclusa nelle ombre; scelte F03-F05 confermate; scena con l'approccio di Padova.
- D17 (10 ottobre): pensilina S2 spostata alla fermata Guidoni Barsanti (a Forlanini Polo non c'è spazio, verificato su Street View).
- D16 (10 ottobre): filare S1 rifatto con la regola delle aree pedonali del Comune; la versione 1 cadeva fra carreggiata e binari T2 su Via di Novoli.
- D18 (10 ottobre): i due CSV Life Escapos tolti da tutta la storia di git (anche dal tag `pilota-pisa-z2`); copia della storia precedente in `../digital-twin-firenze-prima-pulizia.bundle`.
- D19 (10 ottobre): ingressi del Polo = 7 civici del Comune, uno per edificio dell'Ateneo (D1, D4, D5, D6, D10, D14, D15); per ogni origine vince il più vicino. Prima: due ingressi OSM (biblioteca e una corte interna).
- D20 (10 ottobre): fermata T2 San Donato - Università (`FM9055`, indicata dall'Ateneo) fra le destinazioni; R01 parte da lì (prima da Torre degli Agli). S1 rifatto in versione 3; S2 resta a Guidoni Barsanti (regola rifatta sui nuovi ingressi).
- D21 (10 ottobre): dati ARPAT usati (stazioni e archivio orario pubblico del sito, non l'API dell'app), anche nella scena online, con le due licenze delle note legali dichiarate. Supera la clausola ARPAT di D15 e la decisione aperta sui dati ARPAT.
- D22 (10 ottobre): niente webcam. Nessuna webcam pubblica entro 1 km da Novoli e nessuna fonte con licenza di riuso.
- D23 (10 ottobre): pannello della scena a schede (Livelli, Sole, Analisi, Interventi, Legenda) sul modello di Padova, tema sempre chiaro. Una variante con stile proprio (pietra serena e cotto) è stata provata e scartata da Luca. Nuove fonti fuori dalla baseline congelata: catasto, Landsat, SIR, ARPAT.
- D24 (10 ottobre): protezione civile dal Comune di Firenze (aree di attesa e di assistenza, CC BY 4.0), non da Cittadino Informato di ANCI che li ripubblica senza licenza. Da Cittadino Informato solo i punti critici per allagamento, dopo che ANCI avrà chiarito la licenza. Nella scena: icone AT e AA per le aree sul terreno disegnato (solo AA13), elenco con la distanza sotto il livello per le altre (AT18, AA14, AA15), come per le stazioni ARPAT.
- D15: obiettivo POC sugli open data; Pisa accantonata nel tag `pilota-pisa-z2`; solo fonti riusabili (Life Escapos tolto); ARPAT solo con licenza dichiarata.

## Decisioni aperte (dell'utente)

1. Comune, DISIT o progetti di ricerca (DANTE, MIRIFICUS): concorrenza o collaborazione. Decisione dopo il POC.

## Prossimi passi possibili

1. Altri difetti aperti del servizio emersi da F11 (elenco in `nl/firenze_novoli/REPORT.md`, punti 4-10). I primi tre sono chiusi il 10 ottobre: tool `list_scenarios`, metriche `served_count_*`, accessibilità verso almeno una di più destinazioni (le tre fermate T2 insieme: 53% dei civici entro 10 minuti). Il giro NL non è stato rifatto.

Da segnalare: nel progetto ARPAT (`arpat/config/services.php`, riga 35) c'è un segreto scritto nel codice come valore predefinito: va tolto e cambiato.

## Come lavora la sessione

Integratore (sessione principale) + subagent Sonnet per task, ognuno nella sua cartella. I subagent non possono scrivere file `.md`: restituiscono il testo e l'integratore lo salva. L'integratore riesegue sempre i test prima del commit.
