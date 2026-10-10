# Stato del progetto

Aggiornato al 10 ottobre 2026: POC di Firenze Novoli completo nei quattro punti chiesti (accessibilità, ombre, scenari, scena alla Padova), con servizio MCP e verifica in linguaggio naturale (F11). Punto di ripartenza per la prossima sessione.

## In una riga

Gemello digitale pilota di Firenze, area Novoli - Firenze Nova (riquadro FP di 2 km²), costruito solo da open data con licenza che ne permette il riuso, per mostrarne le potenzialità. Pisa è accantonata nel tag git `pilota-pisa-z2` (D15): i suoi file ancora sul ramo principale non sono più mantenuti e non girano con i motori attuali.

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
| F11 verifica in linguaggio naturale | `nl/firenze_novoli/` (REPORT.md) | `service/.venv/bin/python nl/firenze_novoli/test_nl.py` (30 s) |

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/

Ricerca sui gemelli già esistenti a Firenze: `docs/research/gemelli-firenze.md`.

## Risultati principali (non validati sul posto)

- Accessibilità a 1,2 m/s, quote sui 3.296 civici entro 10 minuti: Polo delle Scienze Sociali 24% (mediana 15 min), scuola Vamba 39%, fermate T2 30% e 39%. La scelta dell'ingresso del Polo sposta i percorsi più delle quote.
- Ombra sui percorsi fermata T2 → Polo, mezzogiorno: a luglio R01 è al sole per oltre il 90%; a settembre l'ombra sale al 21-27% su R01 e al 43-44% su R02. Alberi e vegetazione LiDAR pesano 2-6 punti su R01, quasi nulla su R02.
- Scenari: filare su R01 (versione 2, alberi dentro le aree pedonali del Comune) -0,55 minuti di sole a mezzogiorno di luglio, da -0,23 a -0,81 con la chioma; a settembre -0,57. Pensilina (versione 2) alla fermata bus Guidoni Barsanti: a mezzogiorno di luglio l'area di attesa passa da 0% a 40% d'ombra.

## Limiti principali

- Ombra misurata sull'asse della rete, non sulla linea dove si cammina.

- Rete solo OSM, lato del marciapiede ignoto. Ingressi del Polo controllati sull'ortofoto 2024/2025, non sul posto: E1 (predefinito) è l'ingresso della biblioteca, E2 è dubbio (`network/firenze_novoli/verifica_ingressi_polo.md`).
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
- D15: obiettivo POC sugli open data; Pisa accantonata nel tag `pilota-pisa-z2`; solo fonti riusabili (Life Escapos tolto); ARPAT solo con licenza dichiarata.

## Decisioni aperte (dell'utente)

1. Comune, DISIT o progetti di ricerca (DANTE, MIRIFICUS): concorrenza o collaborazione. Decisione dopo il POC.
2. Dati ARPAT: solo dataset con licenza dichiarata (dati.toscana.it). Fuori dal POC.
3. Ingresso rappresentativo del Polo: E1 biblioteca (oggi) oppure i sette civici degli edifici dell'Università (indirizzi dal report di accessibilità dell'Ateneo, tutti presenti nei civici del Comune). La seconda rifà F06 e a cascata scena e servizio.
4. Fermata T2 del Polo: l'Ateneo indica San Donato - Università (`FM9055`, 340-540 m dagli edifici), che non è fra le destinazioni; R01 parte da Torre degli Agli (circa 1,2 km). Aggiungerla rifà F06, F07, F08, scena e servizio. Dettagli per i punti 3 e 4 in `network/firenze_novoli/verifica_ingressi_polo.md`.

## Prossimi passi possibili

1. Spostare in una cartella a parte, o togliere dal ramo principale, i file di Pisa (`fieldwork/`, `nl/` tranne `nl/firenze_novoli/`, `preview/`, `scene/` vecchia, output Pisa in `analysis/`, `shadow/`, `scenarios/`); poi puntare `contracts/validate.py` (riga 58) a `scenarios/firenze_novoli/baseline.json`.
2. Copiare three.js nella cartella della scena per l'uso senza rete.
3. Difetti aperti del servizio emersi da F11 (elenco in `nl/firenze_novoli/REPORT.md`): tool che elenca gli scenari, conteggio dei civici raggiunti, accessibilità verso almeno una di più destinazioni.

Da segnalare: nel progetto ARPAT (`arpat/config/services.php`, riga 35) c'è un segreto scritto nel codice come valore predefinito: va tolto e cambiato.

## Come lavora la sessione

Integratore (sessione principale) + subagent Sonnet per task, ognuno nella sua cartella. I subagent non possono scrivere file `.md`: restituiscono il testo e l'integratore lo salva. L'integratore riesegue sempre i test prima del commit.
