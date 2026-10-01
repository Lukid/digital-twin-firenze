# Brief comune per gli agenti T01

Leggere prima: `docs/PIANO.md`, `docs/SPEC_ANALISI.md`, `docs/FONTI.md`, `docs/BACKLOG.md` (sezione T01).

## Zone candidate di lavoro (non approvate)

Insieme iniziale per rendere confrontabili i risultati. Si possono proporre altre zone con motivazione.

- Z1 Santa Maria / Piazza dei Cavalieri: sedi universitarie del centro, scuole, tessuto storico denso.
- Z2 Stazione Centrale / Sant'Antonio / Corso Italia: fermate, nodo intermodale, scuole.
- Z3 Cisanello: polo ospedaliero e universitario, edilizia recente, viabilità ampia.
- Z4 Porta a Lucca / Pratale: quartiere residenziale con scuole e verde.

Dimensione di riferimento: 0,5-2 km² per zona, più il contesto esterno necessario.

## Regole

- Distinguere per ogni fonte: esistenza, accessibilità tecnica, contenuto valido, condizioni di riuso.
- Una query con zero risultati si registra come tale, non come prova di assenza.
- Non trasformare stime in misure, né metadati in promesse di contenuto.
- Niente contatti con enti, acquisti, account, installazioni globali, pubblicazioni.
- Strumenti locali consentiti: curl, python3 con librerie già presenti, venv locale nella propria cartella se serve.
- Niente codice applicativo: solo script di download/ispezione riproducibili.
- Testi in italiano con accenti veri (è, à, perché, ecc.). Mai apostrofi al posto degli accenti.

## Consegna (per ogni agente, nella propria cartella `docs/audit/<tema>/`)

1. `REPORT.md`: fonti trovate, esito per i quattro criteri, copertura per zona Z1-Z4, lacune, alternative concrete.
2. `campioni/`: risposte e campioni scaricati (contenere i file sotto ~20 MB; per file grandi salvare solo intestazioni/estratti e annotare URL e dimensione).
3. `manifest.json`: per ogni file path, URL, timestamp UTC del download, byte, sha256.
4. `riproduci.sh`: comandi che rigenerano i campioni.
5. Controllare a fine lavoro che nessun file salvato abbia 0 byte (in passato i campioni sono andati persi).
