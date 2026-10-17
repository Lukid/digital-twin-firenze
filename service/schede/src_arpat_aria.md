# Qualità dell'aria ARPAT, dati orari 2025 della rete regionale (stazioni del comune di Firenze)

- Identificativo: `src_arpat_aria`
- Editore: ARPAT, Agenzia regionale per la protezione ambientale della Toscana
- Scheda del catalogo: nessuna. I dati orari e l'anagrafica delle stazioni non sono su dati.toscana.it: sul catalogo ARPAT ha solo indicatori annuali fino al 2022-2024 e la risorsa "Struttura della rete di monitoraggio della qualità dell'aria in Toscana" (cc-by) punta a un JSON che oggi rimanda alla home del sito. Da segnalare: link morto e archivio orario da pubblicare sul catalogo.
- Pagina della fonte: https://www.arpat.toscana.it/datiemappe/qualita-dellaria-dati-orari/
- Risorsa scaricata: https://www.arpat.toscana.it/app/uploads/2026/05/FI_DATI_QA_2025_CSV.zip
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: non specificata per i dati orari (note legali ARPAT)
- Verifica: verificata con riserva
- Uso consentito: solo prototipo interno: verificare prima di ridistribuire
- Evidenza: https://www.arpat.toscana.it/note-legali
- Nota: Note legali ARPAT: "Salvo dove diversamente specificato, i contenuti del sito Web di ARPAT sono distribuiti con licenza Creative Commons Attribuzione – Non commerciale – Condividi allo stesso modo 3.0 Italia (CC BY-NC-SA 3.0)"; "Ai sensi delle Linee Guida Nazionali per la Valorizzazione del Patrimonio Informativo Pubblico, le banche banche dati distribuite in formato vettoriale sono rilasciate – dove non diversamente specificato – con licenza Creative Commons Attribution 4.0 International (CC-BY 4.0)"; "Salvo diversa indicazione le informazioni contenute nel sito Web ARPAT sono fornite a scopo informativo." La pagina dei dati orari non indica una licenza. Indicatori annuali PM10 e NO2 (solo per il tipo di stazione): schede del catalogo regionale cc-by.
- Riserva: Non è scritto quale delle due licenze delle note legali vale per i CSV orari: se vale CC BY-NC-SA 3.0, niente uso commerciale e derivati nella stessa licenza. Uso deciso da Luca il 10/10/2026 (D21): pubblicato anche nella scena online, con entrambe le licenze dichiarate; per uso commerciale chiedere conferma ad ARPAT.

## Date

- Data del dato: dal 2025-01-01 al 2025-12-31
- Nota sul periodo: archivio orario 2025 (PM10 e PM2,5 giornalieri), dichiarato validato dall'intero ciclo di validazione; il 2026 non è pubblicato come download

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_arpat_aria_20261010` | 2026-10-10T16:25:34Z | dal 2025-01-01 al 2025-12-31 | 70bdeb1ced6d | no |

## Campi usati

`STAZIONE`, `PARAMETRO`, `DATA (formato AAAAMMGG)`, `ORA FINE MISURA (solare)`, `MEDIA ORARIA`, `VALIDITA'`

Unità: `media_oraria` µg/m³ a 20 °C (CO mg/m³), `media_giornaliera` µg/m³ a temperatura ambiente (PM10, PM2,5)

Sistema di riferimento dichiarato: undeclared (coordinate delle pagine stazione "N:... - E:..." senza sistema dichiarato: Gauss-Boaga fuso Ovest (EPSG:3003) dedotto dai valori (FI-MOSSE cade in Via delle Mosse); convertite in EPSG:7791 come i civici)

## Controlli

- stazioni selezionate: superato. 6 stazioni della rete regionale nel comune di Firenze (nessun'altra entro 3 km dal riquadro)
- stazioni nel riquadro FP: avviso. nessuna: la più vicina (FI-MOSSE) è a circa 750 m; valori di stazione, non rappresentano il riquadro
- anno in corso: avviso. il 2026 non è pubblicato come download: passa solo dall'API dell'app, esclusa

## Limiti

- stazioni nel riquadro FP: nessuna: la più vicina (FI-MOSSE) è a circa 750 m; valori di stazione, non rappresentano il riquadro
- anno in corso: il 2026 non è pubblicato come download: passa solo dall'API dell'app, esclusa
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
