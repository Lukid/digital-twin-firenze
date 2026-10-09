# Audit dei dati e proposta di riquadro, Firenze (F01)

Data: 5 ottobre 2026. Sintesi dell'integratore sui cinque audit in `docs/audit-firenze/` (destinazioni, rete, edifici, verde, cataloghi). Ogni numero rimanda al REPORT.md della cartella, dove ci sono script, campioni, manifest con sha256 e `riproduci.sh`. Nessun contatto con enti, nessuna pubblicazione, nessuna verifica sul campo.

## 1. Riquadri confrontati

Riquadri in `docs/audit-firenze/RIQUADRO.json` (di lavoro, non approvati), usati da tutti gli audit:

- FA: candidato D12, lon 11,213-11,229, lat 43,796-43,808 (1,72 km²).
- FB: stesso riquadro spostato a sud-est verso il campus di Novoli, lon 11,218-11,234, lat 43,792-43,804 (1,72 km²). Si sovrappone a FA per il 46%.

## 2. Confronto per criterio

### Destinazioni (destinazioni/REPORT.md)

- FA: nessuna scuola statale o paritaria, nessuna sede universitaria. Una fermata T2 (Novoli - Palazzi Rossi) a 45 m dal bordo. Due scuole (Bargellini, Fanciulli) appena fuori, a 10 e 34 m dal bordo.
- FB: Polo delle Scienze Sociali (99% dell'area), scuola Vamba (infanzia e primaria), una fermata T2. 55 fermate bus con servizio e 15 linee, contro 37 e 12 in FA.
- Careggi: fuori da entrambi, a 1.066 m da FA e 687 m da FB.
- Con riquadri di questa misura (semilato 661 m) nessuna destinazione può stare a 700 m dal bordo, cioè avere dentro tutto il bacino dei 10 minuti. Vedi la proposta al punto 3.
- Scuole: MIM e Comune sono la stessa anagrafe (stessi 222 codici). Fonte indipendente per gli accessi: edifici scolastici della Città metropolitana. Due coordinate MIM sbagliate nel contesto.

### Rete pedonale (rete/REPORT.md)

- FB è migliore in modo netto: 40,3 km di rete dedicata contro 19,6, 246 attraversamenti contro 117, strade con tag marciapiede 30% contro 12%.
- Entrambi sotto Z2 di Pisa: marciapiedi disegnati 0,6 e 1,9 km contro 13,1, ingressi mappati 2 e 5 contro 267.
- Le barriere del Comune sono schede di accessibilità di edifici (rilievo 2013), non ostacoli sul percorso: utili come attributo della destinazione, poco come attributo dell'arco.
- Walking City e rifugi climatici: nessuno dentro i riquadri. Un rifugio a 45 m da FB.

### Edifici e quote (edifici/REPORT.md)

- Base: unità volumetriche regionali del 2011 via WFS, altezza su tutti gli oggetti. FA 972, FB 1.459. Il Comune non pubblica impronte con altezza.
- LiDAR 2023 del Comune (0,5 m, CC BY 4.0): scaricabile per tessere, senza vuoti su FA e FB. Altezza da nDSM contro UV: scarto mediano +0,37 m, MAE 1,84 m.
- Datum verticale coerente: spiccato UV meno DTM 2023, mediana -0,14 m. A Pisa era rimasto non confermato.
- Portici e volumi sospesi: nessuna fonte verificata, come a Pisa.

### Verde (verde/REPORT.md)

- Censimento alberi: FA 1.614 (9,4 per ettaro), FB 2.469 (14,4). Specie e circonferenza, niente altezza né chioma.
- Altezze da CHM 2023. Su 50 alberi Life Escapos lo scarto è +0,15 m, ma l'accordo è troppo stretto (r 0,992) per dirlo indipendente: h_m potrebbe venire dallo stesso LiDAR. Serve una misura di campo.
- Life Escapos: 50 alberi in FA, 14 in FB (nell'area in comune).

### Fonti e licenze (cataloghi/REPORT.md)

- Comune di Firenze: quasi tutto CC BY 4.0 e scaricabile (alberi, LiDAR 2023 e 2017, civici, barriere, rifugi, aree pedonali, aree verdi, fermate tram).
- Licenze diverse: scuole del Comune IODL 2.0; Life Escapos CC BY-NC 4.0; DB topografico regionale 1:2.000 in conflitto (scheda cc-by, risorsa CC BY-SA 4.0) e non scaricabile da CKAN; GTFS del tram senza licenza sulla risorsa.
- Da non usare: `escapos_mobile_measurements` (misure fisiologiche di persone), `edilizia-scolastica` della Regione (licenza non commerciale).
- GTFS: tram GEST (solo T2 e T1.3, la T1 non compare), bus Autolinee Toscane con finestra di tre settimane (fino al 25/10/2026).
- Lacune del portale: altezza degli edifici, marciapiedi e attraversamenti, ingressi, altezza e chioma degli alberi, CHM, LiDAR solo come zip unico della città, campo CRS delle schede inaffidabile.

### Gemelli esistenti (da RIFERIMENTO-PADOVA.md, sezione 5)

| | Comune di Firenze | DISIT (Snap4City) | Questo progetto |
|---|---|---|---|
| Cosa ha | Modelli 3D, LiDAR, strati su verde, mobilità, UNESCO, energia; microclima annunciato | Gemello 3D web pubblico del centro, sensori, traffico, inquinanti, what-if; codice aperto | Accessibilità pedonale verso destinazioni, ombra sui percorsi, scenari, domande in linguaggio naturale con calcoli tracciati |
| Accesso | Interno, nessuna consultazione pubblica indicata | Pubblico | Da definire |
| Sovrapposizione | 3D, alberi, microclima | 3D, what-if | |

Il 3D di DISIT dichiara gli edifici del centro: la copertura di Novoli non è verificata. La decisione su concorrenza o collaborazione resta aperta (decisione 4).

## 3. Proposta

Riquadro proposto: FP in `RIQUADRO.json`, cioè FB allargato a circa 2 km² intorno al suo centro (variante B dell'audit delle destinazioni): lat 43,79178-43,80422, lon 11,21694-11,23506 (2,02 km²). Motivi:

- contiene il Polo delle Scienze Sociali per intero, due sedi scolastiche e due fermate T2, contro nessuna scuola e nessuna università in FA;
- rete OSM migliore di FA su ogni metrica;
- più alberi ed edifici che fanno ombra, utile per B;
- contiene il 52% di FA, il candidato D12 verso Firenze Nova, a differenza della variante centrata sul Polo.

Destinazione principale proposta: Polo delle Scienze Sociali (due ingressi mappati in OSM). Seconda famiglia: fermate T2 e scuola Vamba.

Il bacino dei 10 minuti non sta dentro un riquadro di 2 km². Proposta: il riquadro delimita scena e dati di dettaglio; la rete per l'accessibilità si acquisisce con un margine di 700 m intorno, solo da OSM.

Alternative:

- Riquadro centrato sul Polo (variante A dell'audit, lat 43,78677-43,7992, lon 11,2219-11,24002): 7 sedi scolastiche e 4 fermate T2, ma esce da Firenze Nova.
- FA com'è: tiene tutti i 50 alberi Life Escapos, ma non ha destinazioni dentro. Sconsigliato.

Da contare in F03 sul riquadro scelto: alberi Life Escapos, edifici, civici.

## 4. Decisioni per l'utente

Decise il 9 ottobre 2026 (D13 nel piano): riquadro FP, rete con margine di 700 m, Life Escapos solo per verifica interna (i due campioni vanno tolti da git prima di aggiungere un remote), DB topografico solo se le UV non bastano.


1. Riquadro: proposta FB allargato, alternative sopra.
2. Rete con margine di 700 m oltre il riquadro: sì o no.
3. Life Escapos (CC BY-NC 4.0): usarlo solo per verifica interna, chiedere un permesso al Comune, o non usarlo. Se non si usa, vanno tolti da git i due campioni che ne riportano i valori (`verde/campioni/chm_vs_escapos.csv` ed `escapos_vs_censimento.csv`) prima di aggiungere un remote. In ogni caso non dimostra il CHM: serve una misura di campo.
4. DB topografico regionale (conflitto CC BY e CC BY-SA): servirebbe solo se le UV via WFS non bastano.

## 5. Limiti

- Tutto da desk: OSM snapshot del 5 ottobre, nessun sopralluogo.
- Le UV sono del 2011: gli edifici più recenti vanno controllati sul LiDAR 2023.
- I conteggi sulla variante B allargata vengono dall'audit delle destinazioni; rete, edifici e verde sono misurati su FA e FB.
- Le due fonti sugli edifici scolastici della Città metropolitana si contraddicono (solo secondarie superiori secondo i cataloghi, anche nidi e primo ciclo secondo le destinazioni): da chiarire in F03.
