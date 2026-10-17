# Temperatura dell'aria giornaliera (massima e minima), stazione SIR Firenze Università TOS01001096

- Identificativo: `src_sir_termo_firenze`
- Editore: Regione Toscana, Settore Idrologico e Geologico Regionale (SIR)
- Scheda del catalogo: https://dati.toscana.it/dataset/termometri
- Risorsa scaricata: https://www.sir.toscana.it/archivio/dati.php
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-SA-4.0
- Verifica: verificata con riserva
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://www.sir.toscana.it/licenze
- Nota: Pagina Licenze del SIR: "I dati pubblicati dal Settore Idrologico e Geologico Regionale (SIR) - Regione Toscana sono distribuiti con licenza Creative Commons Attribuzione-CondividiAlloStessoModo 4.0 Internazionale (CC BY-SA 4.0)". Attribuzione: "Settore Idrologico e Geologico Regionale (SIR) - Regione Toscana. Dati distribuiti con licenza Creative Commons CC BY-SA 4.0."
- Riserva: Condividi allo stesso modo: i derivati di questo livello (meteo.json.gz) vanno distribuiti in CC BY-SA 4.0. La scheda del catalogo (anagrafica stazioni) dice cc-by-sa, le sue risorse A1_PublicDomain: vale la pagina del SIR. Dati dichiarati pre-validati.

## Date

- Data del dato: 2023-01-01
- Nota sul periodo: massime e minime giornaliere 2023-2026 della stazione, dati pre-validati; ora solare
- Ultima modifica della scheda del catalogo: 2025-11-12 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_sir_termo_firenze_20261010` | 2026-10-10T16:22:49Z | 2023-01-01 | 39ebcc88c788 | no |

## Campi usati

`Tmax`, `Tmin`

Unità: `tmax` °C, `tmin` °C

Sistema di riferimento dichiarato: EPSG:3003 (posizione della stazione dall'anagrafica WFS del SIR (Gauss-Boaga, quota 84 m s.l.m.), convertita in EPSG:7791)

## Controlli

- serie normalizzata: superato. vedi data/norm/firenze_novoli/sir_termo_firenze.json
- distanza dal riquadro: superato. 1,3 km a est del riquadro FP, in città: rappresentativa della zona, non del singolo isolato
- validazione: avviso. il SIR dichiara i dati pre-validati: possono cambiare

## Limiti

- Una stazione a 1,3 km dal riquadro: temperatura dell'aria di stazione, non del riquadro. Licenza share-alike.
- validazione: il SIR dichiara i dati pre-validati: possono cambiare
- Licenza con riserva: vedere sopra.

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
