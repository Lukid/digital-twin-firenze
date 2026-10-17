# REPORT F2: accessibilità ai rifugi climatici su Firenze Novoli

17 ottobre 2026, decisione D32. Quanti civici del riquadro raggiungono a piedi il più vicino dei rifugi climatici del Comune. Stesso motore e stesse regole di F06 ([REPORT-F06.md](REPORT-F06.md)).

## Destinazioni

I 7 rifugi del Comune entro 700 m dal riquadro FP (il margine della rete), dalle due fonti della baseline: `src_fi_rifugi_aree` (aree fresche) e `src_fi_rifugi_biblioteche` (biblioteche), dato dichiarato del 18 giugno 2026, CC BY 4.0.

Ingresso = civico del Comune all'indirizzo d'ingresso dichiarato dalla fonte, cercato per via e numero fra i 13.987 civici dell'area allargata. Ogni ingresso porta anche il `CODICECIVI` (D30).

| Destinazione | Rifugio | Ombra dichiarata | Ingresso (civico del Comune) |
|---|---|---|---|
| `dst_refuge_rif_fi_02399` | Giardino di Piazza delle Medaglie d'Oro | 70% | Via Arcangelo Corelli 19; Via Francesco Baracca 135/D |
| `dst_refuge_rib_fi_6` | Biblioteca Filippo Buonarroti | - | Viale Alessandro Guidoni 188 |
| `dst_refuge_rif_fi_01523` | Giardino di piazza dei Cavalieri di Vittorio Veneto | 97% | Via Luigi Morandi 2 |
| `dst_refuge_rif_fi_01631` | Giardino di via Luigi Morandi | 71% | Via Guglielmo Jervis 13 |
| `dst_refuge_rif_fi_05409` | Giardino di via Arturo Toscanini | 81% | Via Arturo Toscanini 20 |
| `dst_refuge_rif_fi_02394` | Giardino di via Arturo Toscanini | 81% | Via Arturo Toscanini 5 |
| `dst_refuge_rif_fi_01545` | Giardino di piazza Giacomo Puccini | 78% | Piazza Giacomo Puccini 24/A |

8 ingressi, tutti agganciati alla componente principale della rete (raccordo da 0,3 a 7,0 m). Medaglie d'Oro ha due ingressi: per ogni civico vince il più vicino. La fonte scrive "Viale Guidoni 188" e "135d": i civici del Comune sono "Viale Alessandro Guidoni 188" e "135/D".

Escluso: Parco delle Cascine, Galoppatoio dei Barberi (`rif_fi_02556`, 698 m). I suoi indirizzi d'ingresso (Piazzale dell'Indiano 3, Viale delle Cornacchie 2) non sono fra i civici dell'area allargata.

## Risultato

Job versionato `job_e1e75455f7511f7d` (manifest in `analysis/firenze_novoli/manifest/`, riepilogo in `riepilogo.json`, chiave `rifugi`). Accessibilità verso almeno uno dei 7, profilo 1,2 m/s, snapping 40 m, 3.296 civici del riquadro. Fra parentesi l'intervallo a 0,8-1,4 m/s.

| Soglia | Civici | Quota |
|---|---|---|
| 5 minuti | 467 (187-674) | 14,2% (5,7-20,4%) |
| 10 minuti | 1.289 (868-1.409) | 39,1% (26,3-42,8%) |
| 15 minuti | 1.858 (1.289-2.198) | 56,4% (39,1-66,7%) |

- Tempo mediano dei civici raggiungibili 12,75 minuti (10,9-19,1), 90° percentile 22,1 minuti; distanza mediana 918 m.
- Stati: 3.112 raggiungibili, 168 senza aggancio, 15 vietati, 1 isolato: gli stessi di F06.
- Rifugio più vicino, per numero di civici: Biblioteca Buonarroti 1.071, Medaglie d'Oro 667, Cavalieri di Vittorio Veneto 623, Puccini 501, Toscanini 20 134, Toscanini 5 116, Morandi 0.
- Fonti nel manifest: civici, OSM, aree fresche e biblioteche (snapshot del 9 ottobre).

Confronto con la stima non versionata del report F1 (39,1% entro 10 minuti, 26,3-42,8%): coincide in tutte le cifre pubblicate, compresi 5 e 15 minuti, mediana e civici per rifugio. La stima di F1 usava le stesse funzioni del motore e gli stessi ingressi; il report F1 parlava di 9 ingressi, ma per i 7 rifugi gli indirizzi dichiarati sono 8.

## Dal servizio

`compute_walk_access` con i 7 `destination_ids` ritrova lo stesso `job_id`. `list_destinations` ha la categoria nuova `cooling_refuge` (aggiunta al contratto MCP) e gli alias "rifugi", "rifugi climatici", "aree fresche".

## Limiti

- Ingressi non verificati sul posto: il civico all'indirizzo dichiarato non è per forza il cancello del giardino o la porta della biblioteca.
- Orari: la biblioteca non è sempre aperta (orari sul sito del Comune); orari e chiusure dei giardini non noti. Il calcolo li tratta come sempre accessibili.
- Nessuna ombra lungo il percorso: il tempo è quello del cammino minimo, non del percorso più ombreggiato.
- Civici, non persone: punti d'indirizzo del Comune, non residenti.
- Solo i rifugi entro 700 m dal riquadro: un civico vicino al bordo può avere un rifugio più vicino fuori dalla rete. Parco delle Cascine escluso.
- Rete OSM non verificata, marciapiede ignoto sul 35% dei metri percorsi.

## Cosa è cambiato

- `network/destinazioni_firenze.py`: i 7 rifugi, categoria `cooling_refuge`, ingressi di classe `civico_ingresso_rifugio`.
- `analysis/accessibilita.py`: fonti dei rifugi nei dataset dei job verso i rifugi. Hash del motore aggiornato in `scenarios/firenze_novoli/baseline.json` con nota; confronto degli scenari rieseguito, identico a `confronto.json`.
- `analysis/run.py`: i rifugi non hanno i 4 profili e le sensibilità per destinazione; un solo job verso il più vicino dei 7, in fondo.
- Rete: il grafo non cambia (le destinazioni si agganciano dopo). `origini_snap.gpkg` riscritto con lo stesso contenuto: rimesso il file della baseline (sha256 `28f2739c...`).
- Manifest e job esistenti: stessi `job_id` e stesse metriche (controllo sul ricalcolo, escluse le date di esecuzione).

## Comandi

- `pipeline/.venv/bin/python network/destinazioni_firenze.py` (dalla cartella `network/`, come in `build_firenze.sh`)
- `pipeline/.venv/bin/python analysis/run.py`, poi `pipeline/.venv/bin/python analysis/test_accessibilita.py` (test 11: rifugi)
- `service/.venv/bin/python service/test_service.py`

Nota per chi riesegue `analysis/run.py` su Linux: gli asset `*_archi_usati.geojson` in `data/norm/firenze_novoli/analysis/` escono diversi alla sesta cifra decimale da quelli calcolati sul Mac, e il test 9 di `test_accessibilita.py` fallisce sugli sha256. Sul worker li ho rimessi uguali al Mac prendendo le coordinate dai GeoJSON versionati (stesso arrotondamento): tutti e 20 tornano con lo sha256 del manifest.
