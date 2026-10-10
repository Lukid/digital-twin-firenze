# Stato del progetto

Aggiornato al 9 ottobre 2026: F01-F05 consegnati, riquadro approvato (D13). Prossimo: analisi F06-F10. **Cambio di territorio: il pilota passa a Firenze, Novoli - Firenze Nova (D12).** Punto di ripartenza per la prossima sessione.

## In una riga

Nuovo pilota a Firenze, area Novoli - Firenze Nova, costruito dai dati del portale regionale e sul modello di presentazione di Padova. Il primo pilota su Pisa Z2 è consegnato (dati, rete, accessibilità, ombre, scenari, scena, MCP e verifica NL, con test; sopralluogo solo preparato) e ne riusiamo motori, servizio e scena.

## Fatto sul primo pilota, Pisa Z2 (ogni consegna ha un REPORT.md e un test rieseguito dall'integratore)

| Task | Dove | Controllo |
|---|---|---|
| T01 audit e scelta pilota | `docs/audit/`, `docs/audit-pilota.md` | revisione indipendente fatta |
| T01-I brief interlocutore | `docs/brief-interlocutore.md` | nessun contatto avviato |
| T02 contratti | `contracts/` (ADR-T02.md) | `contracts/.venv/bin/python contracts/validate.py` |
| T03 acquisizione | `pipeline/` (dati in `data/`, non versionati) | `pipeline/.venv/bin/python pipeline/validate_records.py` |
| T04 rete e ingressi | `network/` | `pipeline/.venv/bin/python network/test_rete.py` |
| T05 edifici e verde | `geometry/` | `pipeline/.venv/bin/python geometry/test_geometrie.py` |
| T06 accessibilità | `analysis/` | `bash analysis/run.sh` |
| T07 servizio e MCP | `service/` | `service/.venv/bin/python service/test_service.py` |
| T08 scena | `scene/` (ADR-T08.md) | verifica nel browser, vedi ADR |
| T09 ombre | `shadow/` | `pipeline/.venv/bin/python shadow/test_ombre.py` |
| T10 scenari | `scenarios/` | `bash scenarios/run.sh` |
| T11 preparazione | `fieldwork/` (protocollo, 185 punti, scheda stampabile) | `python3 fieldwork/test_importa.py` |
| T12 verifica NL | `nl/` (25 domande, registro, replay, confronto con la mappa) | `service/.venv/bin/python nl/test_nl.py` |

Anteprima storica: `preview/` (superata da `scene/`).

## Decisioni prese dall'utente

- Nuovo pilota Firenze, Novoli - Firenze Nova (D12, 1 ottobre 2026), nonostante i gemelli già esistenti di Comune e DISIT.
- Riquadro Firenze FP, 2,02 km² (D13, 9 ottobre 2026): destinazione principale Polo delle Scienze Sociali, poi fermate T2 e scuola Vamba; rete con margine di 700 m solo OSM; Life Escapos solo per verifica interna; DB topografico solo se le UV WFS non bastano.
- Riferimento di presentazione e di approccio: gemello di Padova (D11, perimetro ancora aperto).
- Primo pilota Pisa Z2 (D03), CRS EPSG:7791 (vale anche per Firenze), stato di accessibilità `outside_model` incluso.
- Motore grafico: libreria cartografica web con estrusioni (ADR-T08, proposta dell'agente, da rivedere con la via di Padova).

## Decisioni aperte (dell'utente)

Firenze (D14 del 10 ottobre 2026: chioma LiDAR inclusa nelle ombre, scelte F03-F05 confermate, scena con l'approccio di Padova):
1. Dati ARPAT: chiedere ad ARPAT il consenso a usare il proxy dell'app "Ambiente in Toscana" (T16). Non serve al POC.
2. Contatto con Comune di Firenze o DISIT: concorrenza o collaborazione. Non serve al POC.
3. Prima di aggiungere un remote: togliere da git, anche dalla storia, i due campioni F01 con valori Life Escapos (`docs/audit-firenze/verde/campioni/chm_vs_escapos.csv`, `escapos_vs_censimento.csv`).

Pisa (primo pilota, in pausa per D14):
7. Sopralluogo T11: farlo o chiudere il pilota senza validazione sul posto.
8. Licenza dei layer SIT, richiesta del censimento alberi, segnalazione dei layer SIT scrivibili.
9. Cancellare `data/work/` (4,2 GB di estratti rigenerabili).

## Risultati principali su Pisa (non validati sul posto)

- Accessibilità a 1,2 m/s su 2.224 civici: Battisti 52,5% entro 10 min (p50 9,7 min); fermata Pellico 66,3%. 21 civici vietati (accesso privato), 55 con dati insufficienti.
- Ombra su R01 Pellico → Battisti, 15 settembre: 91% in ombra all'ingresso, 46% all'uscita (12:30-13:30). Il lato del marciapiede cambia fino a 20 punti: è l'incertezza dominante.
- Scenari: filare S1 -0,58 min di sole a mezzogiorno su R01 (intervallo fino a -0,12), quasi nullo sul lato opposto; pensilina S2 utile solo sull'area di attesa (ombra da 0 a 31%).
- La scelta dell'ingresso della scuola è il parametro che sposta di più l'accessibilità.

## Limiti noti su Pisa

- Rete solo OSM, lato del marciapiede ignoto, ingressi da verificare.
- Altezze edifici del 2010 (post-2010 da DSM 2021), datum verticale non confermato, portici ignoti.
- Chiome tutte stimate; inventario alberi incompleto.
- Civici SIT come punti d'indirizzo (non persone), licenza non dimostrata.
- GTFS congelato valido fino al 21/10/2026.

## Prossimi passi

1. F02 consegnato: registro delle aree `contracts/aree.json`, schema della baseline, origini `address_points` (`contracts/ADR-F02.md`).
2. F03 consegnato (`pipeline/REPORT-F03.md`): 15 fonti di Firenze con snapshot e sha256, T17 applicato, baseline `bas_firenze_novoli_20261009`. Comando: `DT_DAY=20261009 pipeline/run_firenze.sh`. GTFS bus valido fino al 29/10/2026.
3. F04 consegnato (`network/REPORT-F04.md`): rete OSM di 294 km (91 nel riquadro), Polo `dst_university_w83537185` con 2 ingressi, Vamba, 2 fermate T2; 3.112 civici su 3.296 raggiungibili dal Polo; scarto 3003 → 7791 mediano 0,86 m. Comando `network/build_firenze.sh`.
4. F05 consegnato (`geometry/REPORT-F05.md`): 1.952 edifici nel riquadro (1.442 con altezza LiDAR 2023), 2.917 alberi (2.050 chiome misurate, 867 stimate), verifica interna Escapos solo come coerenza. Comando `bash geometry/build_firenze.sh`.
   **Prossimo: analisi F06-F10** (accessibilità, ombre, scenari) riusando i motori di Pisa; `analysis/accessibilita.py`, `service/core.py` e `scenarios/costruisci.py` hanno ancora nomi fissi di Pisa.
5. In parallelo, da decidere: approccio di scena di Padova (T15, rifare il confronto di ADR-T08), dati ARPAT di Firenze (T16, consenso ARPAT), fonti dal portale (T17).
6. Su Pisa resta aperto solo ciò che serve a chiudere il primo pilota: difetti di T12 utili anche a Firenze (elenco scenari, ombra per orario, più destinazioni) e, se si vuole, il sopralluogo T11.

Da segnalare: nel progetto ARPAT (`arpat/config/services.php`, riga 35) c'è un segreto scritto nel codice come valore predefinito: va tolto e cambiato.

## Come lavora la sessione

Integratore (sessione principale) + subagent Sonnet per task, ognuno nella sua cartella. I subagent non possono scrivere file `.md`: restituiscono il testo e l'integratore lo salva. L'integratore riesegue sempre i test prima del commit.
