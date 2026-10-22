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
5. [Revisione del codice](docs/REVISIONE-CODICE-20261010.md): difetti confermati, priorità, verifiche eseguite e limiti della revisione.

Prossimo lavoro: vedi i prossimi passi in [docs/STATO.md](docs/STATO.md).

## Licenza

- Codice: [EUPL-1.2](LICENSE).
- Documenti e dati prodotti dal progetto: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.it).
- Dati derivati da OpenStreetMap (rete pedonale, percorsi e risultati calcolati sulla rete, mappa di base della scena): [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), © OpenStreetMap contributors.
- Estratto dei costi unitari ANAC (`docs/research/anac-pensiline/`): CC BY-SA 4.0, © Autorità Nazionale Anticorruzione.

Ogni dato derivato riporta anche le licenze e le attribuzioni delle fonti da cui viene: sono nelle schede in `service/schede/` e nei manifest dei calcoli.
