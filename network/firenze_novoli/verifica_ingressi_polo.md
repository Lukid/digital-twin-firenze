# Ingressi del Polo delle Scienze Sociali: controllo sull'ortofoto

Data: 10 ottobre 2026. Controllo a tavolino, non sul posto.

## Fonte e tavole

- Ortofoto 2024/2025 della Regione Toscana, 20 cm, layer `rt_ofc.5k24.32bit` del WMS `owsofc_rt`. La Regione ne è proprietaria; il servizio dichiara `AccessConstraints: none`, ma sul layer non c'è una licenza scritta. Per questo l'ortofoto è usata solo in consultazione: non è scaricata, non è versionata e non entra nella baseline. Le ortofoto 2016, 2019 e 2022 (AGEA) vietano il download e non sono state usate.
- Dicitura del servizio: "Fonte: Regione Toscana - Base informativa territoriale regionale, art. 55 della L.R. 65/2014".
- Tavole: `pipeline/.venv/bin/python network/firenze_novoli/tavole_ingressi_polo.py`. Produce quattro SVG in `data/norm/firenze_novoli/network/tavole_polo/` (fuori da git): insieme, asse di Via delle Pandette, E1, E2. L'ortofoto si carica dal WMS quando si apre l'SVG nel browser. Sopra ci sono edifici e rete OSM, i punti OSM con entrance o barrier, i due ingressi e i civici del Comune di Via delle Pandette, Via Miele e Largo Frezza.
- `destinazioni.json` non è stato modificato: fa parte della baseline congelata `bas_firenze_novoli_20261009`.

## Esito

- E1, `ent_osm_n11152998932` (ingresso predefinito): coerente con l'ortofoto. Sta sulla piazza pedonale all'estremo sud-ovest dell'asse di Via delle Pandette, a circa 12 m dal civico Pandette 2. Per la scheda 1634 delle barriere del Comune, Pandette 2 è la Biblioteca. È quindi l'ingresso della biblioteca, non di tutto il Polo.
- E2, `ent_osm_n11152998933`: dubbio. Sta in una corte interna dell'isolato verso Via Miele, senza indirizzo, vicino al civico Miele 4. È agganciato a 9,6 m a un arco `sottopasso` (passaggio coperto di Via Giovanni Miele). Dall'alto non si vede se il passaggio è aperto né dov'è la porta.
- Il fronte vero del Polo è l'asse pedonale di Via delle Pandette: circa 30 civici del Comune su circa 200 m, dal 2 al 37, sui due lati dell'asse. Le schede barriere del Comune confermano come universitari solo i civici 2 (biblioteca), 9, 21, 32 e 35. Degli altri non si conosce la destinazione d'uso.
- L'ortofoto non mostra porte, cancelli, orari o percorsi per disabili sotto le gronde e i portici.

## Fonti dell'Università (ricerca in rete, 10 ottobre 2026)

- Il report di accessibilità dell'Ateneo ("REPORT accessibilità, Riepilogo per CAMPUS", unifisostenibile.unifi.it) dà l'indirizzo di ogni edificio del Polo:
  - D1 (scuole, segreterie): Via delle Pandette 32.
  - D4 (aule, Dipartimento di Scienze Giuridiche): Via delle Pandette 35.
  - D5 (aule, DSPS): Via delle Pandette 21.
  - D6 (aule, DISEI): Via delle Pandette 9.
  - D10 (Biblioteca): Via delle Pandette 2.
  - D14 (bar, sale lettura, aula studio): Via delle Pandette 3.
  - D15 (aule tesi, laboratori): Piazza Ugo di Toscana 5.
- Le pagine del DISEI confermano D1 = Pandette 32 e D6 = Pandette 9 e danno l'orario degli edifici: dal lunedì al venerdì, 7:30-20:00.
- Tutti e sette gli indirizzi hanno un civico nel dataset del Comune (`fi_civici`): Pandette 2, 3, 9, 21, 32, 35 lungo l'asse e Piazza Ugo di Toscana 5 (`adr_fi_32095`). Le schede barriere del Comune confermano già 2, 9, 21, 32, 35.
- Fermata del tram: l'Ateneo (booklet SECI 2026/27 e pagina "Where we are" della Scuola di Economia) indica la fermata T2 "San Donato - Università", a circa 500 m dal campus. Nel GTFS del gestore è `FM9055` (679142, 4851036 in EPSG:7791), a 340-540 m dai sette civici. Non è fra le destinazioni del progetto: D13 ha scelto le fermate `FM9056` Novoli - Regione Toscana e `FM9057` Torre degli Agli, e il percorso R01 parte da Torre degli Agli (circa 1,2 km). `FM9055` sta circa 100 m a sud del riquadro FP, dentro il margine di rete di 700 m. Nel dataset delle fermate del Comune (`fi_tram_fermate`) questa fermata manca.

## Peso sui risultati

- Da E1 all'estremo nord-est dell'asse (civico Pandette 37) ci sono 191 m in linea d'aria: 2,5-3 minuti a 1,2 m/s. È lo stesso ordine del passo delle soglie (5 minuti).
- F06 lo mostra già: con il solo E1 le quote a 5/10/15 minuti sono 12,2% / 24,4% / 45,9%, con il solo E2 12,6% / 26,3% / 41,7%. I 10 archi più usati coincidono in 1 caso su 10.

## Decisione aperta (dell'utente)

Ingresso rappresentativo del Polo:
1. Lasciare E1, la biblioteca (situazione attuale), dichiarando che è un solo punto a un estremo del Polo.
2. Usare come ingressi i civici del Comune lungo l'asse di Via delle Pandette, con l'ingresso più vicino per ogni origine (F06 ha già il calcolo con più ingressi). È un cambio di modello: rifà F06 e, a cascata, scena, servizio e i job della verifica F11.
3. Usare come ingressi i sette civici degli edifici dell'Università (Pandette 2, 3, 9, 21, 32, 35 e Piazza Ugo di Toscana 5), con l'ingresso più vicino per ogni origine. Stesse conseguenze del punto 2. È l'opzione sostenuta da fonti ufficiali dell'Ateneo e del Comune.

Decisione collegata: aggiungere la fermata T2 `FM9055` San Donato - Università fra le destinazioni e come partenza del percorso fermata-Polo. Rifà F06, F07 (R01), F08 (filare S1 su R01), scena e servizio.

Senza un sopralluogo nessuna delle tre opzioni è verificata.
