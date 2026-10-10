# Gemello digitale di Firenze Novoli

Prototipo di gemello digitale dell'area Novoli - Firenze Nova (riquadro di 2 km²), costruito solo da open data con licenza che ne permette il riuso. Mostra accessibilità pedonale, ombra sui percorsi, confronto di interventi (filari, pensiline) in una scena 3D statica, e risponde a domande tramite un server MCP con calcoli tracciati. **Stato e prossimi passi: [docs/STATO.md](docs/STATO.md).**

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/

Riferimento di presentazione: il [gemello di Padova](https://padova-digital-twin.ekore.tech/) (D11, analisi in [docs/RIFERIMENTO-PADOVA.md](docs/RIFERIMENTO-PADOVA.md)).

Il primo pilota su Pisa Z2 è accantonato (D15): il suo stato finale è nel tag git `pilota-pisa-z2`. Il 10 ottobre 2026 i file di Pisa sono stati tolti dal ramo principale (`fieldwork/`, `preview/`, la scena e la verifica NL di Pisa, gli output di Pisa in `analysis/`, `shadow/`, `scenarios/`). Restano gli script di rete e geometria di Pisa (`network/build.sh`, `geometry/build.sh` e i loro test), non più mantenuti.

## Documenti operativi

1. [Piano](docs/PIANO.md): scopo, decisioni, fattibilità, architettura, fasi e criteri.
2. [Specifiche delle analisi e MCP](docs/SPEC_ANALISI.md): metodi, metriche, contratti, limiti e verifiche.
3. [Fonti](docs/FONTI.md): evidenze raccolte e verifiche mancanti.
4. [Backlog per agenti](docs/BACKLOG.md): incarichi, dipendenze e consegne.

Prossimo lavoro: vedi i prossimi passi in [docs/STATO.md](docs/STATO.md).
