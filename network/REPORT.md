# T04: rete pedonale e ingressi Z2

Data: 1 ottobre 2026. Redatto dall'agente T04 e salvato dall'integratore. `network/build.sh` (circa 90 s, ripetibile); test `pipeline/.venv/bin/python network/test_rete.py`: 6/6 OK (rieseguito dall'integratore).

## Regole (`regole.json`, lette dal builder)

- Percorribili: footway, pedestrian, path, steps, living_street, residential, service, unclassified, tertiary, secondary, primary (e _link), banchine bus. Ciclabili e strade a scorrimento solo con foot esplicito.
- foot prevale su access. Esclusi foot=no, use_sidepath, customers e access=private, no, customers, permit. Marcati: destination, unknown.
- Fuori: way railway=*, banchine ferroviarie (anche le scale per oltre il 50% dentro una banchina), strade in tunnel senza marciapiede, aree a poligono (area=yes). Restano i sottopassi pedonali.
- Strade senza marciapiede taggato: percorribili con `marciapiede_stato=ignoto` e `marciapiede_dichiarato=false`. Scale, ponti, layer, tunnel e attraversamenti (nodi e tratti) conservati. Due way si collegano solo se condividono un nodo.
- Cancelli passabili "da verificare", bloccati solo se access o foot lo vietano. Muri e recinzioni bloccano.
- `forbidden`: nessun percorso sul grafo verificato, ma collegamento presente sul grafo di controllo che riaggiunge i tratti vietati.

## Grafo (`grf_z2_osm_20261001`; GeoPackage, GraphML e pkl in `data/norm/network/`)

- 3.065 nodi, 3.901 archi, 122,3 km nel buffer, 35,3 km in Z2. ID `nod_osm_<id>` e `edg_osm_<way>_<da>_<a>`.
- Marciapiede: 51,2 km ignoto, 3,2 km assente, 13,4 km presente, 4,5 km separato. 37 scale, 101 archi in sottopasso o tunnel, 442 tratti di attraversamento.
- Esclusi: 121 segmenti access=private, 110 banchina, 58 classe non pedonale, 32 use_sidepath, 32 aree, 29 tunnel stradali, 28 foot=no. 5 nodi bloccanti.
- L'audit T01 contava 56,7 km percorribili in Z2 perché includeva private, foot=no e service, qui esclusi.

## Componenti (`componenti.json`)

30 componenti. La principale ha 117,6 km; le altre 29 sommano 4,6 km e solo 6 toccano Z2 (circa 0,23 km). Motivi plausibili: 18 tagli del buffer, 18 adiacenti a tratti esclusi, 15 solo service non collegata, 5 connessioni mancanti (meno di 3 m senza nodo comune), 5 con scale o sottopasso collegati a un solo capo.

## Destinazioni (`destinazioni.json`)

- 41 destinazioni, tutte agganciate a un ingresso e tutte "da verificare": Battisti e 40 fermate GTFS di Z2 (inclusa Pellico). Raccordo delle fermate al massimo 5,8 m.
- Battisti: 9 ingressi OSM entro 25 m dal perimetro (gli 8 dell'audit più via Vespucci 18). 1 probabile ingresso scuola: `ent_osm_n6532183886`, entrance=main, nel perimetro, senza civico. 8 probabile edificio contiguo: fuori perimetro di 10-23 m, su edifici residenziali o alberghieri, civici 29, 33, 35 di via Corridoni e via Vespucci, mai il 42.

## Snapping delle origini (`snapping_report.json`)

- Civici SIT agganciati 2.169 su 2.224, limite 40 m (p99 della distanza civico-arco 41 m). Raccordo p50 3,5 m, p99 27,5 m, massimo 39,1 m.
- 55 non agganciati = `insufficient_data`: 26 raccordi bloccati da edifici, 25 senza archi entro 40 m, 4 da tratti esclusi.
- Il raccordo non attraversa edifici, tratti esclusi o nodi bloccanti; le origini non si agganciano agli attraversamenti.
- 21 civici agganciati a componenti isolate (cmp_14, cmp_24): in T06 vanno trattati come `isolated`.

## Confronto con Iter.net (`confronto_iternet.json`)

Grafo veicolare del 2019: 18,1 km in Z2, senza marciapiedi, attraversamenti o scale. OSM carrabile copre l'86% di Iter.net entro 10 m; Iter.net copre il 75% dell'OSM carrabile e il 65% del pedonale. 1.794 dei 2.224 civici SIT hanno un civico Iter.net con lo stesso numero entro 25 m. Utile come controllo della viabilità, non per il caso A.

## Percorsi campione (`percorsi_campione.json` e `.geojson`)

- R01 Pellico → ingresso scuola: 755 m (deviazione 1,13), 1 attraversamento, 97 m a marciapiede ignoto.
- R02 Pellico → ingresso contiguo di via Corridoni: 745 m, 3 attraversamenti. Cambiare ingresso cambia di 10 m la lunghezza e gli attraversamenti.
- R03 fermata Corridoni 1 → ingresso: 67 m, marciapiede dichiarato.
- R04-R07 civici a circa 150, 400, 700 e 1.000 m in linea d'aria: 163, 562, 861 e 1.113 m, con 1-4 attraversamenti.
- R08 fermata stazione PI0001 → ingresso: 518 m.
- R09 civico di R05 → Pellico: 400 m.
- V01 via Poerio 3 → Battisti: `forbidden`. Collegata al resto solo da 3 archi access=private: 429 m sul grafo di controllo, rifiutato sul grafo verificato.
- Nessun percorso campione usa scale o sottopassi.

## Test (`test_rete.py`)

1. Percorso Pellico → Battisti trovato.
2. V01 rifiutato dal grafo ma presente sul grafo di controllo; nodi bloccanti assenti.
3. Nessun arco su way ferroviarie o sovrapposto a binari o banchine per più di 5 m per singolo binario (esclusi sottopassi e ponti).
4. foot e access rispettati, ID univoci, marciapiede ignoto mai dichiarato.
5. Ogni destinazione agganciata a un ingresso entro 40 m.
6. Origini non agganciate = `insufficient_data`, mai forzate.

## Correzioni

`correzioni.geojson` è vuoto, con lo schema delle correzioni nella nota. Nessuna correzione motivata finora.

## Da verificare al sopralluogo

- Ingresso reale della Battisti: il main OSM non ha civico; i civici 29-35 di via Corridoni sono classificati contigui solo dalla geometria. Orari e cancello non noti.
- Via Poerio 3 e 5: strada con civici ma access=private in OSM. Tre cancelli access=private bloccano la rete.
- Lato della fermata Pellico (piattaforma OSM rispetto al punto GTFS).
- 134 vicoli ciechi veri in Z2 (per lo più passi carrai); 33 aree a poligono non modellate (piazze, banchine), possibili falsi vicoli ciechi.
- 182 cancelli senza tag access, passabili per ipotesi.
- 8 nodi con layer sospetto; un passaggio a livello al bordo nord-ovest del buffer (il test tollera fino a 5 m per binario).
- Larghezze, pendenze, kerb e rampe quasi assenti: nessuna certificazione di accessibilità.
- Civici SIT `unproven`: solo uso interno del prototipo.

## File

`build.sh`, `estrai_osm.py`, `build_rete.py`, `destinazioni.py`, `confronto_iternet.py`, `percorsi.py`, `rete_lib.py`, `test_rete.py`, `regole.json` e gli output citati. Grafo e origini in `data/norm/network/`. Aggiunta networkx in `pipeline/.venv`.
