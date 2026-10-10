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

## Peso sui risultati

- Da E1 all'estremo nord-est dell'asse (civico Pandette 37) ci sono 191 m in linea d'aria: 2,5-3 minuti a 1,2 m/s. È lo stesso ordine del passo delle soglie (5 minuti).
- F06 lo mostra già: con il solo E1 le quote a 5/10/15 minuti sono 12,2% / 24,4% / 45,9%, con il solo E2 12,6% / 26,3% / 41,7%. I 10 archi più usati coincidono in 1 caso su 10.

## Decisione aperta (dell'utente)

Ingresso rappresentativo del Polo:
1. Lasciare E1, la biblioteca (situazione attuale), dichiarando che è un solo punto a un estremo del Polo.
2. Usare come ingressi i civici del Comune lungo l'asse di Via delle Pandette, con l'ingresso più vicino per ogni origine (F06 ha già il calcolo con più ingressi). È un cambio di modello: rifà F06 e, a cascata, scena, servizio e i job della verifica F11.
3. Usare solo i civici confermati universitari dalle schede del Comune (2, 9, 21, 32, 35). Stesse conseguenze del punto 2.

Senza un sopralluogo nessuna delle tre opzioni è verificata.
