# Audit destinazioni caso A: Z1-Z4

Data: 1 ottobre 2026. Redatto dall'agente destinazioni (T01) e salvato dall'integratore. File in `campioni/`, URL e sha256 in `manifest.json` (45 file, nessuno a 0 byte), rigenerazione con `riproduci.sh` (rieseguito per intero, stesso sha256 del GTFS).

Zone = cerchi tracciati a mano (`zone.json`), non perimetri ufficiali; Z1 e Z4 si sovrappongono:
- Z1: 43,7200 N 10,3999 E, raggio 550 m
- Z2: 43,7095 N 10,4010 E, raggio 650 m
- Z3: 43,7100 N 10,4370 E, raggio 750 m
- Z4: 43,7235 N 10,4090 E, raggio 750 m

## 1. Esito per fonte

- **SIT Pisa punti scuole** (Hosted/Scuole_infanzia.../0): GET ok, 90 punti (27 infanzia, 25 primarie, 13 nidi, 12 nidi privati, 12 secondarie I grado, 1 polo 0-6), nessuna superiore. Ultima modifica layer 2025-11-24, alcuni "temporaneamente spostato". Riuso non dichiarato (copyrightText e licenseInfo vuoti).
- **SIT edifici scolastici** (layer 4): 97 poligoni, solo via e civico; nessun nome, quota o ingresso. Plessi (23) e istituti comprensivi (7): bacini, non destinazioni.
- **SIT civici** (Civici_puntuali_View/0): 32.335 punti; attributi indirizzo, sezione_censuaria_istat (numero locale, non codice Istat completo), quartiere, plesso. Licenza non dichiarata.
- **MIM anagrafe 2026/27**: file statali 13 MB, 88 sedi a Pisa; paritarie 17 (file non elencato nel catalogo, URL dedotto). Nessuna coordinata, indirizzi irregolari. CC BY 4.0 (metadati dati.gov.it).
- **Provincia di Pisa edifici scolastici** (superiori), dato 2017-07-25: 24 edifici a Pisa, senza coordinate, con flag barriere/rampe/ascensore (dichiarati, non verificati). CKAN CC BY 4.0, file di licenza nello ZIP CC BY 2.0 IT.
- **Sedi UniPi**: solo pagine HTML. CKAN regionale "università di pisa sedi" e "unipi edifici": 0 risultati (non prova di assenza).
- **OSM** via Overpass per zona (base 2026-10-01 13:29-13:30Z; 504/429 frequenti, 406 senza user agent): 98 oggetti di istruzione nelle zone, 30 senza nome. ODbL.
- Interrogati senza esito per Pisa: dataset scuole del Comune di Firenze (solo Firenze), ricerca edilizia scolastica georeferenziata.

## 2. GTFS bus (Autolinee Toscane, risorsa di rt-oraritb)

- Scaricato 2026-10-01T13:22Z, 185.529.498 byte. feed_info 20261001-20261021.
- `calendar.txt`: 7.625 servizi tutti a zero; servizio solo da `calendar_dates` (13.052 eccezioni tipo 1). Attivi oggi (giovedì) 815 servizi, 28.586 corse. Il 21/10 ha 3 servizi: utilizzabile fino al 20/10.
- Integrità: 33.872 fermate senza duplicati né coordinate mancanti; 218.914 corse con servizio, linea e shape esistenti; 5.907.403 passaggi senza orfani; ore fino a 26.
- Mancano `wheelchair_boarding` e `wheelchair_accessible`; `location_type` sempre 0; `route_type` solo 3. Agenzie UPI (32 linee) ed EXPI (51). Risorse "scolastico" separate, non scaricate.
- Per zona (cerchio), fermate / servite oggi / linee / corse:
  - Z1: 21 / 20 / 18 / 2.212
  - Z2: 45 / 44 / 35 / 8.555
  - Z3: 21 / 20 / 6 / 1.681
  - Z4: 44 / 42 / 13 / 2.574
- Fermate con una fermata OSM entro 40 m: 20, 44, 21, 42. Dettaglio in `gtfs_fermate_zone.csv`.
- Trenitalia: calendar_dates 2026-01-15/2026-12-12; Pisa Centrale 248 passaggi oggi (43,70823 10,39839), San Rossore 120.

## 3. Concordanza fra fonti

Regole grezze: via+civico, nome, OSM entro 120 m.

- Scuole SIT (raggio + 400 m) / con riscontro MIM / con oggetto OSM entro 120 m / di cui con ingressi OSM: Z1 6/4/2/1; Z2 15/14/11/5; Z3 10/8/6/1; Z4 12/8/9/6. Totale 43: MIM 34, OSM 28, con ingressi 13.
- Oggetti OSM di istruzione per zona: 37, 23, 3, 34.
- Sedi universitarie OSM: Z1 circa 30 oggetti nominati; Z2 2; Z3 0 entro 1.000 m (zero risultati, non prova); Z4 circa 16.
- Discordanze: Nicola Pisano (SIT piazza S. Francesco 3, MIM via San Lorenzo 1); Parmeggiani (SIT via Firenze 12, MIM/OSM 14); Gereschi (SIT "viaviale", MIM "VIA VIALE", OSM via Umberto Viale 16); Carducci (MIM/Provincia San Zeno 3, SIT edifici San Zeno 51).
- Ingressi: solo OSM (main, yes, staircase, emergency); tag wheelchair su pochissimi oggetti (Z1 4, Z2 1, Z3 0, Z4 0). Il conteggio ingressi è nel riquadro dell'oggetto + 10 m e può includere edifici adiacenti. Accessibilità degli edifici: solo Provincia (superiori, 2017).

## 4. Candidate e origini

Ingresso da verificare ovunque. Dettaglio in `candidati_caso_A.json`.

- **Z1 Liceo Artistico Russoli**, via San Frediano 13 (OSM way/232482921). MIM PISD05000L, Provincia 0500260315 (barriere e rampe presenti, 2017). Ingressi OSM 3. Fermate GTFS entro 300 m: 3 (Santa Maria 1 e 2, Pacinotti 2). Civici entro 500/1.000 m: 3.031/7.523. Nessuna scuola pubblica infanzia/primaria nel nucleo storico del layer SIT.
- **Z2 Primaria Battisti**, via Corridoni 42 (way/695634299). SIT, MIM PIEE82101P. Ingressi 8 (include una scala e ingressi di via Vespucci, forse edificio contiguo). Fermate 7 (Corridoni 1 a 71 m, Cattaneo 1 e 2, Bonaini 2...). Civici 1.873/6.768.
- **Z3 Primaria Gereschi**, via U. Viale 16 (way/211388929, check OSM 2025-07-27). SIT, MIM PIEE832048 (indirizzo troncato). Ingressi 2 (main). Fermate 4. Civici 333/1.437.
- **Z4 Secondaria I grado Fibonacci**, via Lalli 4 (way/128401172). SIT, MIM PIIC831007 e PIMM831018. Ingressi 3. Ambiguità: relation/4032458 "Istituto Leonardo Fibonacci" con 33 ingressi nel riquadro. Fermate 9. Civici 1.926/7.176.
- Alternative universitarie: Z1 Polo Carmignani (way/92930420, check 2026-07-16, 2 ingressi) o Palazzo della Sapienza (relation/1729449); Z4 Polo Fibonacci (way/217538423, 7 ingressi).
- Fermate come destinazione: Z2 Pellico PI4390 (583 corse), Z1 Lungarno Gambacorti 1 PI4164 (454), Z3 Martin Lutero 4 PI4254 (164), Z4 Buonarroti 3 PI4040 (113).
- Origini: civici SIT entro 1.000 m dalla destinazione. Un civico non è un residente. Alternativa per pesare: sezioni Istat 2021, non ancora scaricate. Ripiego: griglia.

## 5. Lacune e azioni

- Ingressi reali: sopralluogo sui quattro candidati.
- Licenza SIT: chiarimento dal Comune (decisione dell'utente).
- Superiori senza coordinate: geocodificare indirizzi MIM/Provincia sui civici SIT (non fatto).
- UniPi: nessun elenco strutturato; OSM provvisorio.
- GTFS: snapshot periodico, scade il 20/10; verificare le risorse scolastiche.
- Z3: rivedere il centro della zona con il polo di Cisanello.
- Overpass instabile: estratto locale se servono molte query.
- Il sha256 del GTFS nel manifest si riferisce al download del 2026-10-01; `riproduci.sh` stampa quello corrente.

## 6. Licenze

- SIT: non dichiarata.
- MIM: CC BY 4.0.
- Provincia: CC BY 4.0 (catalogo) o CC BY 2.0 IT (file).
- GTFS: CC BY (campo license_id regionale; condizioni specifiche del feed non trovate).
- OSM: ODbL, attribuzione e condivisione alla pari.

## File

`manifest.json`, `riproduci.sh`, `zone.json`, `analizza.py`, `verifica_gtfs.py`, `treni_pisa.py`, `osm_zona.sh`, `osm_tutte.sh`, `manifest.py`, `campioni/` (6,9 MB).

## Addendum: ricalcolo sui riquadri canonici

Riquadri in `docs/audit/ZONE.json`. I numeri per cerchio delle sezioni 2-4 non valgono per i riquadri: valgono quelli qui sotto. Dati in `campioni/ricalcolo_zone_canoniche.json` e `candidati_canonici.json`; manifest aggiornato (50 file, nessuno a 0 byte). Script nuovi `ricalcolo.py`, `ricalcolo_osm.sh` aggiunti a `riproduci.sh` (non rieseguito per intero dopo l'aggiunta).

Conteggi (fermate GTFS / servite oggi / linee / passaggi; scuole SIT; sedi MIM; OSM scuole e universitari; civici SIT):
- Z1: 23 / 23 / 22 / 4.701; SIT 6; MIM 9; OSM 12 scuole, 33 universitari; civici 4.060
- Z2: 38 / 37 / 34 / 6.860; SIT 5; MIM 6; OSM 9 scuole, 1 universitario; civici 2.135
- Z3: 10 / 10 / 6 / 1.099; SIT 0; MIM 0; OSM 0 e 0 (zero risultati, non prova di assenza); civici 304
- Z4: 34 / 31 / 13 / 1.627; SIT 4; MIM 6; OSM 12 scuole, 9 universitari; civici 1.464

Confronto MIM grezzo per via.

Candidate dentro il riquadro (ingresso da verificare):
- Z1: Liceo Artistico Russoli, via San Frediano 13 (43,71885; 10,39935). Invariata.
- Z2: Primaria Battisti, via Corridoni 42 (43,70737; 10,40463). Invariata.
- Z3: nessuna scuola. Fermata Martin Lutero 4, PI4254 (43,70742; 10,43850), 164 corse oggi, 6 fermate entro 300 m, civici 412 / 1.023 entro 500 / 1.000 m. Alternativa: Ospedale Cisanello - Pinchera PI4034. Gereschi e le scuole di via di Parigi e via Puglia sono a ovest, fuori dal riquadro.
- Z4: Istituto Arcivescovile Santa Caterina, piazza Santa Caterina 4 (43,72171; 10,40532). SIT (nido privato allo stesso indirizzo), MIM paritarie (4 codici), OSM. 1 solo ingresso OSM; il punto è a circa 20 m dal bordo sud del riquadro. 12 fermate entro 300 m, civici 1.735 / 6.749. Alternativa con più ingressi: nido L'Isola delle Farfalle, via Lucchese (SIT + OSM, 4 ingressi, senza MIM).

Origini invariate: civici SIT entro 1.000 m dalla destinazione.
