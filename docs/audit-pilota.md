# Audit dei dati e proposta del pilota (T01)

Data: 1 ottobre 2026. Sintesi dell'integratore sui cinque audit in `docs/audit/` (rete, edifici, verde, destinazioni, cataloghi). Ogni numero rimanda al report della cartella relativa, dove ci sono campioni, manifest con sha256 e `riproduci.sh`. Nessun contatto con enti, acquisto o pubblicazione. Nessuna verifica sul campo: tutto quello che segue è da desk.

## 1. Zone confrontate

Riquadri canonici in `docs/audit/ZONE.json` (zone di lavoro, non approvate), circa 1-1,2 km² ciascuna:

- Z1 Santa Maria / Piazza dei Cavalieri
- Z2 Stazione / Sant'Antonio / Corso Italia
- Z3 Cisanello
- Z4 Porta a Lucca / Pratale

Nota sui confini: edifici, verde (addendum) e destinazioni (addendum) usano i riquadri canonici. La rete usa riquadri propri molto vicini, salvo Z1 più piccolo (0,75 km²) e Z4 spostato di circa 100-500 m a est; per la rete valgono le percentuali, non i km assoluti. Da riallineare in T03.

## 2. Confronto per criterio

### Destinazioni (destinazioni/REPORT.md, addendum)

- Z1: 6 scuole SIT, 33 oggetti universitari OSM, 23 fermate (22 linee). Candidata: Liceo Artistico Russoli.
- Z2: 5 scuole SIT, 38 fermate (34 linee, il nodo più servito), stazione di Pisa Centrale ai margini. Candidata: Primaria Battisti.
- Z3: nessuna scuola né sede universitaria nelle fonti usate dentro il riquadro, 10 fermate (6 linee). Candidata possibile solo una fermata (Martin Lutero 4) o l'ospedale.
- Z4: 4 scuole SIT, 9 oggetti universitari OSM, 34 fermate (13 linee). Candidata: Istituto Santa Caterina, al bordo sud del riquadro, con 1 solo ingresso mappato.

### Rete pedonale (rete/REPORT.md)

Fonte: solo OSM. Nessun dato ufficiale con marciapiedi o attraversamenti trovato.

- Z1: 58% strade senza tag marciapiede, 279 ingressi mappati, 6 componenti. Strade strette e varchi ZTL.
- Z2: 46% senza tag, 173 attraversamenti (129 con tattile), 267 ingressi, 8 componenti. La zona mappata meglio.
- Z3: 69% senza tag, 4 ingressi, 25 componenti con 12,9 km fuori dalla componente maggiore. La peggiore.
- Z4: 48% senza tag ma 16,3 km di marciapiedi disegnati, 88 ingressi, 16 componenti, kerb quasi assenti.

### Edifici e quote (edifici/REPORT.md)

Fonte chiave: unità volumetriche del DB topografico regionale, altezza misurata sul 100% degli oggetti, ma volo 2010.

- Z1: 923 volumi; scarto rispetto al DSM 2021 2,8 m; portici non rilevati.
- Z2: 998 volumi; scarto 2,3 m.
- Z3: 238 volumi; 31% degli edifici OSM non presenti nel 2010.
- Z4: 962 volumi; scarto 1,4 m, il più basso.

Terreno: DTM 10 m regionale sufficiente (Pisa piana). Il DTM LiDAR 1 m non copre le zone e ha licenza NC-SA per soli enti pubblici.

### Verde (verde/REPORT.md, addendum)

- Censimento comunale (18.074 piante, 2017): esiste ma non è accessibile; licenza sconosciuta.
- OSM, alberi per km²: Z1 284, Z2 352, Z3 102, Z4 379. Diametro chioma compilato al massimo nello 0,4%, altezza d'imposta mai.
- Copernicus Street Tree 2018: poligoni di chioma senza specie né altezza (45 / 35 / 26 / 45).
- In nessuna zona le chiome sono modellabili da misure.

### Licenze (cataloghi/REPORT.md)

- Chiare: OSM (ODbL), fonti regionali (CC BY: unità volumetriche secondo la politica open geodata, DSM, DTM 10 m, DBT10K, GTFS), MIM (CC BY 4.0).
- Non dichiarate: tutti i layer SIT comunali (scuole, civici, edifici, PSI) e lo StatPortal.
- Da evitare: ARPAT (NC-SA), DTM LiDAR 1 m (NC-SA, enti pubblici).

### Verificabilità sul posto

Non valutata sul campo. Da desk: Z1 e Z2 sono raggiungibili a piedi dalla stazione; Z3 richiede più spostamenti ed è la zona dove il rilievo servirebbe di più.

## 3. Raccomandazione

**Pilota proposto: Z2 (Stazione / Sant'Antonio / Corso Italia).** Motivi:

- rete OSM più completa (attraversamenti, ingressi, poche componenti);
- nodo del trasporto pubblico più servito, utile per il caso A con le fermate come seconda famiglia di destinazioni;
- candidata con più fonti concordi (SIT, MIM, OSM) e più ingressi mappati;
- altezze misurate con scarto contenuto (2,3 m) e densità di alberi OSM fra le più alte, utile per B.

**Alternativa: Z1**, se il caso d'uso privilegia le sedi universitarie. Ha più destinazioni universitarie e ingressi mappati, ma portici non rilevati e scarto altezze più alto: più difficile per B.

**Esclusa per ora: Z3.** Nessuna scuola nel riquadro, rete frammentata, edilizia recente senza altezze. Andrebbe ridisegnata verso ovest (Gereschi, via di Parigi, via Puglia) e rifatta da capo.

Z4 è valida per B (altezze più coerenti, più alberi) ma ha la destinazione più debole per A.

Nessun ente è stato consultato: la raccomandazione è tecnica, non dice nulla sull'interesse di un utilizzatore.

## 4. Caso A riproducibile (obiettivo)

- Destinazione: Primaria Battisti, via Corridoni 42 (43,70737; 10,40463). Ingresso reale da verificare: 8 ingressi OSM, alcuni forse di un edificio contiguo.
- Origini: civici SIT entro 1.000 m (6.768). Un civico non è un residente; per pesare servono le sezioni Istat 2021 (non ancora scaricate). Il SIT non ha licenza dichiarata: per un uso esterno al prototipo servono alternative o una conferma del Comune.
- Seconda destinazione possibile: fermata Pellico PI4390 (583 corse oggi).
- Rete: OSM, estratto locale congelato (non Overpass) in T03.
- Prova minima: 5-10 percorsi campione verificati sul posto, almeno un percorso vietato.

## 5. Condizioni minime per B

Separate da A: A può procedere anche se B non le soddisfa.

1. Edifici: unità volumetriche 2010 come base; edifici post-2010 nel corridoio individuati e con altezza da DSM 2021 o da rilievo.
2. Portici e volumi sospesi del corridoio rilevati sul posto (nessuna fonte li riporta).
3. Alberi del corridoio: posizione da OSM/Copernicus verificata sul posto, altezza e diametro chioma rilevati o stimati con intervalli dichiarati. Il censimento comunale, se accessibile, sostituirebbe parte del rilievo.
4. Sensibilità della quota d'ombra a 1-2 m di incertezza sulle altezze.
5. Un riferimento indipendente per l'errore assoluto delle altezze (rilievo su pochi edifici).

Corridoio da scegliere al sopralluogo, sul percorso fra la fermata e la scuola candidata. Esito provvisorio G2: favorevole per gli edifici con riserve, sfavorevole per le chiome senza rilievo.

## 6. Output minimo T01: verifica

- Tre aree confrontate con evidenze e raccomandazione: sì, quattro (sezioni 2-3).
- Una scuola/sede/fermata candidata con ingresso da verificare e famiglia di origini: sì (sezione 4).
- Fonte della rete e completezza; necessità di rilievo: sì. Solo OSM; rilievo a campione in Z2 su 5-10 percorsi (marciapiedi, attraversamenti, rampe).
- Percentuale di edifici con altezze documentate: sì, 100% dei volumi 2010; post-2010 stimati con OSM. Chiome separate dalla posizione: sì, non disponibili.
- Riuso, download e campione per ogni fonte; zeri registrati come tali: sì (cataloghi/REPORT.md e ogni report).
- Dimensione degli input e stima aggiornata: sezione 7.

## 7. Dimensione degli input e stima aggiornata

Input:
- campioni salvati in `docs/audit/`: circa 48 MB in git;
- da scaricare in T03: GTFS 185 MB (scade il 20/10, va congelato), DBT10K Pisa 411 MB, grafo Iter.net 460 MB, estratto OSM regionale, tile DSM 1 m per l'area pilota;
- tutto gestibile in locale, nessuna infrastruttura necessaria.

Stima, in giornate equivalenti, rispetto a PIANO.md sezione 6:
- Fase 0: lavoro da desk fatto. Restano il sopralluogo, il brief per l'interlocutore e la revisione: 1-2 giorni.
- Fase 1: invariata (5-8). Si aggiungono estratto OSM locale e congelamento GTFS; si risparmia sulle altezze, già misurate per il 2010.
- Fase 2: invariata (8-12).
- Fase 3: da 10-18 a 12-20, per il rilievo di alberi e portici nel corridoio. Se il censimento comunale diventa accessibile, si torna verso la stima originale.
- Fase 4: invariata (5-8).

Sono stime di pianificazione, non preventivi.

## 8. Decisioni aperte (dell'utente)

1. Chiedere al Comune la licenza dei layer SIT (scuole, civici, edifici). Fino ad allora: solo uso interno del prototipo.
2. Chiedere al Comune l'accesso al censimento degli alberi (formato, campi, data, licenza).
3. Approvare Z2 come pilota, oppure Z1.
4. Pianificare un sopralluogo in Z2: ingressi della scuola, 5-10 percorsi, un corridoio per B.
5. Eventuale segnalazione al Comune: tre layer SIT pubblici (FABBRICATI_PEG, STRADE, TERRENI_PEG) dichiarano operazioni di scrittura. Non testato.

## 9. Lacune principali

- Ingressi reali: nessuna fonte li ha; da rilevare.
- Marciapiedi, rampe, larghezze, pendenze: solo OSM parziale.
- Altezze post-2010 e portici: assenti.
- Chiome: assenti.
- Licenza SIT: non dichiarata.
- Datum verticale delle fonti regionali: non dichiarato, coerente per evidenza indiretta.
- Overpass instabile: estratto locale in T03.
