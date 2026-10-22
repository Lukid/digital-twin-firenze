# Gemello digitale di Firenze Novoli

Prototipo di gemello digitale dell'area Novoli - Firenze Nova (riquadro di 2 km²), costruito solo da open data con licenza che ne permette il riuso. Mostra accessibilità pedonale, ombra sui percorsi, confronto di interventi (filari, pensiline) in una scena 3D statica, e risponde a domande tramite un server MCP con calcoli tracciati. **Stato e prossimi passi: [docs/STATO.md](docs/STATO.md).**

Cos'è e a cosa serve: [docs/SINTESI-PROGETTO.md](docs/SINTESI-PROGETTO.md). Come funziona, quali dati usa e quali calcoli fa: [docs/COME-FUNZIONA.md](docs/COME-FUNZIONA.md) (versione estesa in [docs/DOCUMENTO-TECNICO.md](docs/DOCUMENTO-TECNICO.md)).

Riferimento di presentazione: il [gemello di Padova](https://padova-digital-twin.ekore.tech/) (D11).

## Come si prova

Due ambienti Python 3.12, uno per cartella:

```
python3.12 -m venv pipeline/.venv && pipeline/.venv/bin/pip install -r pipeline/requirements.txt
python3.12 -m venv service/.venv  && service/.venv/bin/pip install -r service/requirements.txt
```

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/

Gli edifici non sono nel repo: le impronte vengono dalle unità volumetriche della Regione Toscana, che abbiamo verificato solo per l'uso nel prototipo, non per la ridistribuzione. Si rigenerano in locale scaricando le fonti (circa 10 minuti, rete necessaria):

```
pipeline/run_firenze.sh
geometry/build_firenze.sh
pipeline/.venv/bin/python scene/firenze_novoli/build.py
```

Per lo stesso motivo non sono nel repo i dati orari della qualità dell'aria ARPAT. I dati ricostruiti oggi possono differire dalla baseline del 9 ottobre 2026 (censimento degli alberi aggiornato ogni giorno, estratto OpenStreetMap più recente).

Test: `make test-fast` (circa 50 s) e `make test` (circa 100 s) richiedono i dati locali; `make ci` gira senza.

Il primo pilota su un'area di Pisa è stato accantonato (D15) e i suoi dati non sono nel repo. Restano gli script di rete e geometria di Pisa (`network/build.sh`, `geometry/build.sh`), non più mantenuti.

## Documenti operativi

1. [Stato](docs/STATO.md): stato, decisioni (D01-D68), limiti e prossimi passi.
2. [Piano](docs/PIANO.md): scopo, decisioni, fattibilità, architettura, fasi e criteri.
3. [Specifiche delle analisi e MCP](docs/SPEC_ANALISI.md): metodi, metriche, contratti, limiti e verifiche.
4. [Fonti](docs/FONTI.md): evidenze raccolte e verifiche mancanti.
5. [Servizio remoto](service/INSTALLA-REMOTO.md): come installare il server MCP in sola lettura.

## Licenza

- Codice: [EUPL-1.2](LICENSE).
- Documenti e dati prodotti dal progetto: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.it).
- Dati derivati da OpenStreetMap (rete pedonale, percorsi e risultati calcolati sulla rete, mappa di base della scena): [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), © OpenStreetMap contributors.
- Estratto dei costi unitari ANAC (`docs/research/anac-pensiline/`): CC BY-SA 4.0, © Autorità Nazionale Anticorruzione.

Ogni dato derivato riporta anche le licenze e le attribuzioni delle fonti da cui viene: sono nelle schede in `service/schede/` e nei manifest dei calcoli.
