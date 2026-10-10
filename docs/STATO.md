# Stato del progetto

Aggiornato al 10 ottobre 2026: POC di Firenze Novoli completo nei quattro punti chiesti (accessibilità, ombre, scenari, scena alla Padova), con servizio MCP. Punto di ripartenza per la prossima sessione.

## In una riga

Gemello digitale pilota di Firenze, area Novoli - Firenze Nova (riquadro FP di 2 km²), costruito solo da open data con licenza che ne permette il riuso, per mostrarne le potenzialità. Pisa è accantonata nel tag git `pilota-pisa-z2` (D15).

## Fatto su Firenze (ogni consegna ha un REPORT e un test rieseguito dall'integratore)

| Task | Dove | Controllo |
|---|---|---|
| F01 audit e riquadro | `docs/audit-firenze.md`, `docs/audit-firenze/` | approvato (D13) |
| F02 contratti a più aree | `contracts/` (ADR-F02.md) | `contracts/.venv/bin/python contracts/validate.py` |
| F03 acquisizione, 14 fonti | `pipeline/` (REPORT-F03.md) | `pipeline/.venv/bin/python pipeline/validate_records.py` |
| F04 rete e ingressi | `network/` (REPORT-F04.md) | `pipeline/.venv/bin/python network/test_rete_firenze.py` |
| F05 edifici e verde | `geometry/` (REPORT-F05.md) | `pipeline/.venv/bin/python geometry/test_geometrie_firenze.py` |
| F06 accessibilità | `analysis/` (REPORT-F06.md) | `bash analysis/run.sh` |
| F07 ombre | `shadow/` (REPORT-F07.md) | `pipeline/.venv/bin/python shadow/test_ombre.py` (90 s) |
| F08 scenari | `scenarios/` (REPORT-F08.md) | `bash scenarios/run.sh` (15 min senza cache) |
| F09 scena 3D, con livelli accessibilità, ombra e scenari | `scene/firenze_novoli/` (ADR-F09.md) | `pipeline/.venv/bin/python scene/firenze_novoli/test_build.py` e verifica nel browser |
| F10 servizio e MCP `dt-firenze` | `service/` (REPORT-F10.md) | `service/.venv/bin/python service/test_service.py` |

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/

Ricerca sui gemelli già esistenti a Firenze: `docs/research/gemelli-firenze.md`.

## Risultati principali (non validati sul posto)

- Accessibilità a 1,2 m/s, quote sui 3.296 civici entro 10 minuti: Polo delle Scienze Sociali 24% (mediana 15 min), scuola Vamba 39%, fermate T2 30% e 39%. La scelta dell'ingresso del Polo sposta i percorsi più delle quote.
- Ombra sui percorsi fermata T2 → Polo, mezzogiorno: a luglio R01 è al sole per oltre il 90%; a settembre l'ombra sale al 21-27% su R01 e al 43-44% su R02. Alberi e vegetazione LiDAR pesano 2-6 punti su R01, quasi nulla su R02.
- Scenari: filare su R01 -0,61 minuti di sole a mezzogiorno di luglio (da -0,37 a -0,79 con la chioma), nullo sul lato opposto: il lato del marciapiede è l'incertezza dominante. Pensilina alla fermata bus Forlanini del Polo: con soli edifici l'area di attesa passa da 0% a 40% d'ombra; con la vegetazione LiDAR è già all'85% (probabile sovrastima del LiDAR, da controllare).

## Limiti principali

- Rete solo OSM, lato del marciapiede ignoto, ingressi del Polo da verificare.
- Civici come punti d'indirizzo, non persone.
- Vegetazione LiDAR come prisma opaco pieno: limite superiore dell'ombra.
- Altezze LiDAR 2023 con unità volumetriche 2011, portici ignoti, datum verticale non confermato.
- GTFS bus congelato valido fino al 29/10/2026.
- Nessuna validazione sul posto.

## Decisioni prese dall'utente

- D12: pilota a Firenze, Novoli - Firenze Nova.
- D13: riquadro FP, destinazioni Polo, T2, Vamba; rete con margine di 700 m solo OSM.
- D14: chioma LiDAR senza albero censito inclusa nelle ombre; scelte F03-F05 confermate; scena con l'approccio di Padova.
- D15: obiettivo POC sugli open data; Pisa accantonata nel tag `pilota-pisa-z2`; solo fonti riusabili (Life Escapos tolto); ARPAT solo con licenza dichiarata.

## Decisioni aperte (dell'utente)

1. Comune, DISIT o progetti di ricerca (DANTE, MIRIFICUS): concorrenza o collaborazione. Decisione dopo il POC.
2. Dati ARPAT: solo dataset con licenza dichiarata (dati.toscana.it). Fuori dal POC.
3. Prima del primo push: ripulire la storia di git dai due CSV Life Escapos (restano nel commit di F01). Deciso dall'utente il 10 ottobre: farlo prima del push.

## Prossimi passi possibili

1. Filare di S1: alcuni alberi cadono sul bordo della carreggiata (posti a 3 m dall'asse della rete). Da spostare sul marciapiede prima di mostrarlo a terzi.
2. Verifica in linguaggio naturale su Firenze (rifare `nl/`: domande, registro, confronto con le mappe).
3. Controllo sull'ortofoto della vegetazione LiDAR vicino all'area di attesa del Polo e degli ingressi del Polo.
4. Spostare in una cartella a parte, o togliere dal ramo principale, i file di Pisa (`fieldwork/`, `nl/`, `preview/`, `scene/` vecchia, output Pisa in `analysis/`, `shadow/`, `scenarios/`); poi puntare `contracts/validate.py` (riga 58) a `scenarios/firenze_novoli/baseline.json`.
5. Copiare three.js nella cartella della scena per l'uso senza rete.

Da segnalare: nel progetto ARPAT (`arpat/config/services.php`, riga 35) c'è un segreto scritto nel codice come valore predefinito: va tolto e cambiato.

## Come lavora la sessione

Integratore (sessione principale) + subagent Sonnet per task, ognuno nella sua cartella. I subagent non possono scrivere file `.md`: restituiscono il testo e l'integratore lo salva. L'integratore riesegue sempre i test prima del commit.
