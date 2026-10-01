# Riferimento Padova: approccio, stack e cosa riprendere per Pisa

Data: 1 ottobre 2026. Documento tecnico interno. Fonte: visita con browser automatico di https://padova-digital-twin.ekore.tech/ e lettura dei file pubblici che la pagina scarica (`index.html`, `app.js`, `data-r40/assets/boot.js`, un riquadro di edifici). Nessun accesso al codice sorgente o al backend. Decisione collegata: D11 nel [piano](PIANO.md), task T15-T17 nel [backlog](BACKLOG.md).

L'utente l'ha indicato come «il risultato a cui vorrei arrivare», anche per stack, librerie e approccio.

## 1. Cosa fa

- Atlante 3D di tutta Padova: edifici con tetti, monumenti modellati a mano, verde 3D, strade e piazze, corsi d'acqua, nomi dei luoghi, cartografia di contesto.
- Ricerca per via, civico, edificio, foglio e particella catastale; scheda dell'edificio con civici e particelle collegati.
- Mobilità: parcheggi auto e bici, ferrovia e stazione, tram con rotaie e fermate.
- Ambiente: stazioni ARPAV (aria, idrometri) con ultimi valori; temperatura delle superfici da satellite per data, con confronto fra giornate, differenza in °C e frequenza; webcam pubbliche.
- Nessun calcolo di accessibilità, ombre analitiche o scenari. Le ombre sono quelle del motore grafico.

## 2. Stack osservato

- Motore 3D generico (three.js, revisione 180 nel bundle), non una libreria cartografica. Luce direzionale con mappe d'ombra, materiali standard, istanze per alberi e oggetti ripetuti. Un solo `app.js` di circa 0,9 MB.
- Sito interamente statico. Nessun server di tile e nessun database a runtime: le chiamate dinamiche sono solo contatore visite e telemetria.
- Asset precotti da una pipeline offline: ogni file è un `.js` che chiama `PadovaThreeAssets.receive(chiave, base64(gzip(JSON)))`. Funziona con qualunque hosting statico e cache del browser.
- Sistema di riferimento locale: origine geografica e matrice da ECEF a piano locale in metri; tutte le geometrie sono già nel piano del motore.
- Città in 156 riquadri di circa 330 m di raggio, ognuno con due livelli di dettaglio (`low` circa 0,1 MB, `high` circa 1,2 MB) caricati per distanza. Le geometrie sono già pronte per la GPU: posizioni, normali, colori e indici in Float32 base64, raggruppati per materiale.
- `boot` (circa 10 MB decompressi): elenco riquadri con hash, terreno da DTM a passo 10 m con texture, 11.259 alberi (punto, altezza, raggio), 3.855 strade con attributi, luoghi, stazioni ambientali, tram, fonti e limiti.
- Ogni asset ha `sha256` e dimensione; ogni fonte ha titolo, data, licenza, URL e, dove serve, hash del file scaricato.
- I limiti sono scritti nei dati e mostrati: per esempio «altezze OSM o stime EUBUCCO, nessun rilievo architettonico», «ARPAV, Landsat e orari del tram non sono stati inventati», «associazioni non univoche restano punti autonomi, nessuna attribuzione per vicinanza».

## 3. Fonti di Padova e equivalente per Pisa

| Livello | Padova | Pisa o Toscana | Stato per noi |
|---|---|---|---|
| Edifici | Carta tecnica regionale Veneto (IODL 2.0) | DBT 10K Regione Toscana, unità volumetriche 2010 | già usato in Z2 |
| Altezze | OSM, EUBUCCO, stime dichiarate | unità volumetriche 2010 e DSM 2021 Regione Toscana | già usato in Z2; EUBUCCO da valutare per il resto della città |
| Terreno | DTM LiDAR Veneto, passo 10 m | DTM e DSM LiDAR Regione Toscana | DSM usato; DTM da acquisire per tutta la città |
| Ortofoto | AGEA 2024, 20 cm, solo WMS | ortofoto Regione Toscana via WMS (già usata dal widget mappa di ARPAT) | da verificare anno e condizioni |
| Alberi | OSM più altezza della chioma da CHM v2 (Meta e WRI, CC BY 4.0) | stesso CHM v2 globale; OSM | **nuovo per noi**: può sostituire le chiome stimate di T05 |
| Civici | Comune, CC BY 4.0 | civici SIT (licenza non dimostrata); ANNCSU nazionale | resta aperta la decisione 1 |
| Catasto | Agenzia delle Entrate WFS, CC BY 4.0 | stesso servizio nazionale, copre Pisa | **nuovo per noi** |
| Mobilità | OSM, GTFS del gestore | OSM, GTFS Autolinee Toscane | GTFS congelato in Z2, scade il 21/10 |
| Aria | feed JSON ARPAV, istantanea con aggiornamento ogni 600 s | ARPAT, vedi sezione 4 | da fare |
| Temperatura superfici | Landsat | Landsat Collection 2 | in FONTI, non acquisito |
| Contesto | tile vettoriali da OSM | stesso | già usato |

## 4. ARPAT

Dati storici dall'archivio orario pubblico di ARPAT: vedi [FONTI.md](FONTI.md).

## 5. Portale regionale e MCP CKAN

Verifica del 1 ottobre 2026 con il server MCP CKAN:

- 12.452 dataset. Prime organizzazioni: LaMMA 6.443, Comune di Firenze 1.992, Comune di Arezzo 983, Regione Toscana 440, Provincia di Pisa 69, ARPAT 59.
- Il Comune di Pisa non pubblica su dati.toscana.it: il suo catalogo è StatPortal più il SIT ArcGIS.
- ARPAT: 59 dataset di indicatori annuali (aria, acque, balneazione, campi elettromagnetici, pollini), aggiornati al 2022-2023, più la struttura della rete di monitoraggio dell'aria in JSON. Niente dati orari.
- DTM, DSM, database topografico e ortofoto della Regione non sono su CKAN (stanno sul geoportale regionale). Su CKAN ci sono solo DTM e DSM del Comune di Firenze e casi di piccoli comuni.

Idea: costruire la scena e i livelli partendo dal catalogo, con il server MCP CKAN per scoperta e ispezione e i nostri adattatori per scaricare, controllare e versionare. Dove la fonte non è su CKAN (geoportale, SIT, archivio ARPAT), registrarlo come lacuna del catalogo. Il gemello diventa anche un banco di prova del portale: quali dati servono a una città e non ci sono, con proposta di pubblicazione o di harvesting.

### Confronto fra territori sul catalogo (1 ottobre 2026)

Livelli chiave per scena e analisi cercati su dati.toscana.it:

- Provincia di Pisa (69 dataset): livelli del piano territoriale, vincolo monumentale, musei, teatri, strutture ricettive, edifici scolastici, strade provinciali, incidenti 2005-2010. Utile come contesto; niente edifici, alberi o civici urbani.
- Comune di Firenze (1.992): censimento alberi pubblici aggiornato ogni giorno, siti alberi da rilievo celerimetrico, DTM e DSM LiDAR 2023 (anche 2017 e 2007), civici, censimento delle barriere architettoniche, percorsi pedonali Walking City, rifugi climatici (spazi ombreggiati da alberi per oltre il 70%). Copre quasi tutte le domande del progetto, ma è una città grande: il pilota sarebbe un quartiere.
- Comune di Siena (328, circa 53.000 abitanti): edificato e edificato minore, civici e toponimi, area stradale, aree di circolazione pedonale, verde urbano, destinazione d'uso catastale. Manca un censimento degli alberi (si userebbe l'altezza delle chiome da CHM).
- Comune di Arezzo (983): edifici, civici, accessi agli edifici, area stradale, aree di circolazione pedonale, periodizzazione degli edifici, DTM a 5 m. Manca un censimento degli alberi.
- Comune di Pisa: nessun dataset su dati.toscana.it.

Riuso del lavoro fatto se si cambia territorio: contratti, servizio e MCP, motori di accessibilità, ombre e scenari, scena e verifica NL si riusano; vanno rifatti acquisizione, rete, ingressi, edifici, verde e protocollo di campo (T03-T05, T11).

## 6. Cosa riprendere e cosa no

Riprendere:
- sito statico con asset precotti per riquadri e due livelli di dettaglio, con hash;
- fonti, date, licenze e limiti dentro i dati, mostrati nell'interfaccia;
- livelli informativi: ricerca, catasto, mobilità, ambiente, temperatura delle superfici;
- cura della resa: tetti, verde, colori, etichette dei luoghi.

Non riprendere:
- ombre del motore grafico come risultato: per Pisa i numeri restano quelli di T09;
- monumenti modellati a mano senza rilievo, se non dichiarati come tali.

Da mantenere nostro: motore di analisi, manifest, MCP del progetto, verifica sul posto.

## 7. Domande aperte

1. Estensione: Z2, centro storico o tutta Pisa (D11).
2. Motore grafico: rifare il confronto di ADR-T08 su un campione più grande con i tetti; la via di Padova è un motore 3D generico con asset precotti.
3. ARPAT: chiedere il consenso per proxy e dati; licenza dei dati.
4. Portale regionale: quali fonti proporre di pubblicare (DBT, LiDAR, ortofoto via harvesting dal geoportale; dati del Comune di Pisa).
