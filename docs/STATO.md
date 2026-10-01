# Stato del progetto

Aggiornato al 1 ottobre 2026, fine della seconda sessione (T12 chiuso, commit 8d94082). Punto di ripartenza per la prossima sessione.

## In una riga

Pilota Z2 (Stazione / Sant'Antonio / Corso Italia): dati, rete, accessibilità, ombre, scenari, scena e server MCP funzionano in locale e hanno test; verifica delle domande in linguaggio naturale fatta (T12); manca la verifica sul posto (T11) e la demo (T13).

## Fatto (ogni consegna ha un REPORT.md e un test rieseguito dall'integratore)

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

- Pilota Z2 (D03), CRS EPSG:7791, stato di accessibilità `outside_model` incluso.
- Motore grafico: libreria cartografica web con estrusioni (ADR-T08, proposta dell'agente, non ancora confermata esplicitamente).

## Decisioni aperte (dell'utente)

1. Licenza dei layer SIT comunali (oggi solo uso interno del prototipo).
2. Richiesta al Comune del censimento alberi.
3. Segnalazione al Comune dei tre layer SIT pubblici che dichiarano operazioni di scrittura (non testato).
4. Sopralluogo: data, rilevatori, giornata corta (priorità 1, circa 6,5 h) o completa; orari della scuola; conferma delle tolleranze in `fieldwork/protocollo.json` e congelamento (`python3 fieldwork/importa_esiti.py --congela`); altezza alla gronda o media.
5. Rendere obbligatorio l'ingresso nelle richieste sulle scuole (consiglio: no, fino al sopralluogo).
6. Confermare ADR-T08.
7. Cancellare `data/work/` (4,2 GB di estratti rigenerabili).
8. Quali difetti aperti di T12 correggere prima della demo (vedi Prossimi passi, punto 1).
9. Riferimento visivo indicato dall'utente il 1/10/2026: https://padova-digital-twin.ekore.tech/ («il risultato a cui vorrei arrivare»). Da decidere: estendere la scena oltre Z2 e quali livelli (D11 nel piano, task T15 nel backlog; vedi Prossimi passi, punto 0).

## Risultati principali (non validati sul posto)

- Accessibilità a 1,2 m/s su 2.224 civici: Battisti 52,5% entro 10 min (p50 9,7 min); fermata Pellico 66,3%. 21 civici vietati (accesso privato), 55 con dati insufficienti.
- Ombra su R01 Pellico → Battisti, 15 settembre: 91% in ombra all'ingresso, 46% all'uscita (12:30-13:30). Il lato del marciapiede cambia fino a 20 punti: è l'incertezza dominante.
- Scenari: filare S1 -0,58 min di sole a mezzogiorno su R01 (intervallo fino a -0,12), quasi nullo sul lato opposto; pensilina S2 utile solo sull'area di attesa (ombra da 0 a 31%).
- La scelta dell'ingresso della scuola è il parametro che sposta di più l'accessibilità.

## Limiti noti trasversali

- Rete solo OSM, lato del marciapiede ignoto, ingressi da verificare.
- Altezze edifici del 2010 (post-2010 da DSM 2021), datum verticale non confermato, portici ignoti.
- Chiome tutte stimate; inventario alberi incompleto.
- Civici SIT come punti d'indirizzo (non persone), licenza non dimostrata.
- GTFS congelato valido fino al 21/10/2026.

## Prossimi passi

0. **Obiettivo di presentazione (Padova)**. Il gemello di Padova è un atlante di tutta la città: edifici con tetti colorati, verde 3D, nomi dei luoghi, ricerca per via, civico e particella catastale, parcheggi, ferrovia e tram, temperatura delle superfici da satellite (Landsat, 100 m, per data, con confronto fra giornate), qualità dell'aria ARPAV, webcam. Motore 3D proprio, città divisa in riquadri a due livelli di dettaglio. Non mostra calcoli di accessibilità o scenari. Rispetto a Pisa: noi abbiamo il motore di analisi e MCP, ci mancano la qualità della scena, l'estensione oltre Z2 e i livelli informativi. Domattina: fissare D11 (estensione e livelli), poi avviare T15 e decidere se rifare il confronto di ADR-T08 su un campione più grande.
1. **Correzioni da T12 prima della demo** (dettaglio in `nl/REPORT.md`, Difetti aperti). Ordine consigliato, da confermare (decisione 8):
   - tool `list_scenarios`: oggi il client non trova filare e pensilina senza che l'utente gli dia gli ID. Piccolo: legge `scenarios/scn_*.json`.
   - ombra per orario nell'output di `compute_shadow`: oggi solo medie e min/max, la mappa invece ha i valori per orario. Medio.
   - accessibilità verso "almeno una" di più destinazioni (caso stazione, 9 fermate): oggi lo schema accetta 20 destinazioni ma il motore una. Medio, tocca `analysis/`.
   - dopo la demo: campo per l'ora ambigua, conteggio dei civici raggiunti, replay via MCP, differenza 7.606/2.224 civici in `inspect_dataset`.
   Dopo ogni correzione: `service/test_service.py`, `nl/test_nl.py`, e ripetere le domande 6, 9, 12 e 13 con un client nuovo.
2. **T11 validazione**: sopralluogo con `fieldwork/scheda.html`, import esiti, correzioni separate dalle verifiche, report con tolleranze. Serve prima la decisione 4.
3. **T13 demo e consegna**: dopo T11 e il punto 1. Il GTFS congelato scade il 21/10/2026: se la demo è dopo, va rigenerato lo snapshot.
4. Eventuale T14 (chat web) solo dopo decisione D09.

Nota per la ripartenza: il client MCP rilegge le descrizioni dei tool all'avvio della sessione; i manifest dei job di T12 sono versionati in `nl/manifest/`, la cache `service/cache/` no.

## Come lavora la sessione

Integratore (sessione principale) + subagent Sonnet per task, ognuno nella sua cartella. I subagent non possono scrivere file `.md`: restituiscono il testo e l'integratore lo salva. L'integratore riesegue sempre i test prima del commit.
