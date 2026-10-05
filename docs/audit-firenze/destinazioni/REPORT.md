# F01 Firenze: destinazioni (scuole, università, fermate, Careggi)

Data audit: 2026-10-05. Riquadri da ../RIQUADRO.json (FA, FB, "contesto"), non approvati. Distanze in EPSG:7791 (RDN2008 / UTM 32N). Numeri da `analizza_fi.py` (campioni/risultati.json e CSV).

## 1. Fonti e licenze

Scuole
- MIM, scuole statali 2026/27: `fi_scuole2627.csv`, 222 codici meccanografici con punto. È identico (stessi 222 codici) al dataset del Comune di Firenze `anagrafica-scuole-statali-2026_27` su dati.toscana.it. Non sono due fonti indipendenti.
- Comune di Firenze, scuole paritarie 2026/27: `anagrafica-scuole-paritarie-2026_27` (GeoJSON, punti). Scaricato.
- Città Metropolitana di Firenze, "Edifici scolastici" (scuole censite dall'anagrafe provinciale): poligoni degli edifici (2544) e punti degli accessi agli edifici (608), con codice meccanografico. Aggiornamento CKAN 2026-04-24. È l'unica fonte con gli accessi.
- OSM via Overpass, riquadro "contesto": amenity=school/kindergarten/college, childcare con building=kindergarten, building=school/kindergarten, entrance=*.
- Licenze: OSM ODbL. Città Metropolitana cc-by. Comune di Firenze (statali e paritarie): su CKAN è indicata IODL 2.0, non CC BY 4.0. Da verificare quale vale per il CSV MIM. Il file contiene plessi, anche se la descrizione parla di "sedi principali".

Università
- OSM amenity=university e building=university, poligoni e nodi entrance=*.

Trasporto
- Tram: GTFS GEST S.p.A., risorsa `GEST.gtfs` del dataset regionale `rt-oraritb` (CKAN dati.toscana.it, cc-by). Contiene solo le linee T2 e T1.3 (routes.txt). T1 Scandicci non è presente come linea. Calendario con `calendar_dates` dal 2026-08-10 al 2026-12-30, nessun `calendar.txt`.
- Bus: GTFS Autolinee Toscane (stesso dataset, cc-by). Valido solo dal 2026-10-05 al 2026-10-25 (feed_info). Non contiene tram. Servizio calcolato per mercoledì 2026-10-07.
- OSM: railway=tram_stop, highway=bus_stop.
- Lacuna: il GTFS dei treni e dei bus scolastici non è stato usato. Nessun feed copre la T1.

Ospedale: poligono OSM `amenity=hospital`, scaricato con una ricerca su 43.77,11.20,43.82,11.28 (più larga del contesto, solo per avere l'intero poligono).

## 2. Conteggi per riquadro

Aree: FA e FB hanno 1,717 km² ciascuno (circa 1323 x 1367 m). Il contesto ha 14,288 km².

Scuole (conteggio per fonte; FA / FB / contesto)
- MIM statali, codici: 0 / 3 / 48. Sedi distinte (codici entro 30 m uniti): 0 / 1 / 24.
- Comune paritarie, codici: 0 / 0 / 11. Sedi distinte: 0 / 0 / 9.
- Città Metropolitana, poligoni edificio: 9 / 29 / 312 (comprendono anche nidi e secondarie). Punti accesso: 0 / 2 / 49.
- OSM amenity scuola/infanzia/college: 3 / 4 / 30 (con nome: 2 / 4 / 27). Edifici building=school senza amenity e non sovrapposti: 1 / 0 / 3.
- OSM entrance=* (qualsiasi tipo): 2 / 5 / 64.

Scuole presenti nei riquadri
- FA: nessuna scuola MIM o paritaria. Dentro FA c'è solo un asilo OSM senza nome (way 235790241, a 249 m dalla scuola MIM più vicina) più altre due feature OSM.
- FB: una sola sede, Vamba (infanzia FIAA86002A e primaria FIEE86002G, Via Giardino della Bizzarria 1), più il codice FIMM700011 "Nuovo complesso penitenziario" (vedi discordanze). In OSM in FB anche "Istituti Paritari Cavour Pacinotti" (nodo) e "Nido dei Bimbi" (asilo aziendale), entrambi senza corrispondenza nel MIM o tra le paritarie.
- Appena fuori da FA: Bargellini (Via di Novoli 72) a 10 m dal bordo, Fanciulli (Via Petrocchi 17) a 34 m.

Discordanze tra le fonti (campioni/scuole_concordanza_fonti.csv, scuole_solo_osm.csv)
- Nel contesto 59 codici MIM o paritarie: 54 hanno una scuola OSM entro 150 m, 44 hanno un accesso Città Metropolitana con lo stesso codice. Senza alcuna corrispondenza in OSM e CM: 4, tutte paritarie (Allori, La Nave, Preziosissimo Sangue, Villa Ramberg). San Gaspare del Bufalo ha l'accesso CM ma OSM a 300 m.
- OSM senza MIM né paritaria entro 150 m: 3 nel contesto (Cavour Pacinotti, Nido dei Bimbi, un asilo senza nome). Gli asili nido non sono nelle fonti MIM.
- Coordinate MIM sospette: FIMM700011 (indirizzo Via Minervini) cade sullo stesso punto di Vamba, in Via Giardino della Bizzarria: errore di geocodifica. FICT702009 "Centro territoriale distretto 11-13" (Via San Donato 46/48/50) cade sul punto di Beato Angelico, Via Leoncavallo 12.
- FIAA859015 "Mameli" (Via Santucci 5) cade a 13 m dal poligono OSM "Calamandrei": nome diverso nelle due fonti.
- I 3 codici Sassetti-Peruzzi e quello del penitenziario non hanno accesso CM.

Università (campioni/universita_osm.csv)
- Polo delle Scienze Sociali: 4 poligoni OSM (area unita 25.261 m²): il poligono d'insieme (w83537185) e gli edifici D1, D14, D15. Gli edifici D4, D5, D6 sono relazioni OSM senza geometria usata.
- Il 99% dell'area è in FB, 0% in FA. Centroide a 11.230959 E, 43.792984 N.
- Ingressi OSM entro 15 m dal poligono: 2, entrambi `entrance=main`, nessuno con il tag wheelchair. Tutti e 2 sono in FB.
- Altri nodi OSM amenity=university in FB: Aula studio, First Lab (punti).

Fermate (campioni/fermate_gtfs_contesto.csv, tram_candidate.csv). Servizio mercoledì 2026-10-07; stop_id per palo e direzione.
- Tram GEST: FA 1 fermata (T2), FB 1 (T2), contesto 16 (T1.3 e T2). 414 partenze al giorno per le fermate T2.
- Bus AT, fermate con servizio e linee: FA 37 fermate, 12 linee; FB 55 fermate, 15 linee; contesto 233 fermate (238 nel feed), 41 linee.
- OSM: tram_stop FA 2 nodi, FB 2 (1 nome ciascuno, due versi), contesto 27 nodi su 15 nomi. bus_stop FA 27, FB 38, contesto 199. Il GTFS ha più fermate di OSM (FA 37 contro 27, FB 55 contro 38, contesto 238 contro 199): OSM è incompleto, o il GTFS conta più pali.

## 3. Distanze dal bordo (metri; positivo = dentro il riquadro)

Soglia richiesta: almeno circa 700 m. Il semilato minimo di FA e FB è 661 e 662 m: nessuna destinazione può raggiungere 700 m dal bordo, nemmeno al centro. Il criterio non è soddisfacibile con riquadri di questa misura.

Migliori candidati per riquadro
- FA scuola: nessuna dentro. Università: nessuna dentro. Tram: Novoli - Palazzi Rossi (T2) a 45 m.
- FB scuola: Vamba a 174 m (stesso punto del codice penitenziario). Università: Polo Scienze Sociali, centroide a 109 m (l'edificio D14 a 68 m). Tram: Novoli - Regione Toscana (T2) a 9 m.
- Fuori dai riquadri ma vicinissime: T2 Novoli - Torre degli Agli, a 180 m fuori FA e a 5 m fuori FB; T2 San Donato - Università a 144 m fuori FB.

Ingressi mappati
- Polo: 2 entrance=main in OSM (nessuno con wheelchair).
- Vamba: 0 ingressi OSM entro 15 m dal poligono; 1 punto di accesso Città Metropolitana (a 28 m dal punto MIM, uno per codice).
- Fermate tram: 3 o 4 elementi OSM (fermata e piattaforma) entro 40 m da ogni fermata GTFS.

## 4. Careggi

Poligono OSM "Azienda Ospedaliera Universitaria di Careggi" (way 25293016, 362.128 m²), distanza minima dal riquadro in EPSG:7791:
- FA: 1066 m.
- FB: 687 m.

Altre strutture: Centro Traumatologico Ortopedico FA 1381 m, FB 979 m. Meyer FA 1710 m, FB 1405 m. Nessun riquadro tocca il poligono. La fermata T1.3 "Careggi - Ospedale" è fuori da entrambi (FA a 1416 m dal bordo, FB a 1014 m).

## 5. Proposta

FB è meglio di FA per le destinazioni: dentro FB ci sono il Polo (99% dell'area), una scuola e una fermata T2; dentro FA c'è solo una fermata T2. FB è anche più vicino a Careggi (687 m contro 1066 m). Nessuno dei due soddisfa la soglia di 700 m dal bordo.

Destinazioni principali
- FB: Polo delle Scienze Sociali (università). Alternativa: scuola Vamba (unica sede scolastica in FB).
- FA: Novoli - Palazzi Rossi (fermata T2), l'unica destinazione dentro, a 45 m dal bordo. FA non ha scuole né università dentro: sconsigliato per questo scopo.

Riquadro corretto di circa 2 km², con il Polo al centro. A è la proposta; B e C sono i riferimenti. Il lato è 1,42 km (semilato 710 m), calcolato in `analizza_fi.py` da `centri_proposta.json`.
- A (consigliato): bbox S,W,N,E = 43.78677, 11.2219, 43.7992, 11.24002 (2,01 km²). Dentro: Polo 100%, 7 sedi scolastiche statali (17 codici), 1 sede paritaria (2 codici), 4 fermate T2 (Ponte all'Asse, Buonsignori - Leonardo da Vinci, San Donato - Università, Novoli - Regione Toscana), 65 fermate bus con servizio. Careggi a 653 m dal riquadro. Il Polo risulta a 690 m dal bordo, non 710, perché il riquadro in gradi è ruotato rispetto alla griglia UTM.
- B (compromesso): bbox 43.79178, 11.21694, 43.80422, 11.23506 (2,02 km²), centrato sul centro di FB. 2 sedi, 2 fermate T2, 58 fermate bus, Polo 100% dentro ma vicino al bordo, Careggi a 599 m.
- C (centrato su FA): bbox 43.79578, 11.21194, 43.80822, 11.23006. 1 sede, 1 fermata T2, 41 fermate bus, Polo 0%, Careggi a 981 m.

Attenzione: A sposta il riquadro verso sud-est e si allontana da Firenze Nova, che è la parte che dà il nome al pilota. La scelta è dell'utente (decisione aperta 1). La scansione completa dei riquadri centrati su ogni scuola, fermata e sul Polo è in campioni/scansione_riquadri_centrati.csv.

## 6. Limiti

- OSM è uno snapshot Overpass del 2026-10-05; entrance=* è poco mappato (nessuna scuola ha ingressi entro 15 m). Il conteggio degli ingressi usa 15 m dal poligono per scuole e Polo, 40 m per le fermate.
- MIM e Comune sono la stessa fonte. I codici meccanografici sono più delle sedi: 24 sedi distinte nel contesto contro 48 codici.
- Il GTFS AT vale solo fino al 2026-10-25. Il GTFS GEST non ha la T1. Il giorno scelto è un mercoledì, non un giorno scolastico verificato.
- Il Polo include solo i 4 poligoni con nome "Polo delle Scienze Sociali"; gli edifici D4, D5, D6 sono relazioni OSM e non entrano nella geometria.
- Le fermate GTFS contano un palo per direzione e non sono deduplicate con OSM.
- Il confronto con la soglia di 700 m usa il centroide dell'edificio, non il bordo più vicino.
- Il riquadro corretto è una proposta geometrica, non verificata su popolazione o edifici residenziali.
- Non sono stati contattati enti né pubblicato nulla.

Riproduzione: `docs/audit-firenze/destinazioni/riproduci.sh` (circa 4,5 minuti, scarica circa 170 MB di GTFS AT; lo sha256 di gtfs_at.zip cambia a ogni scaricamento).
