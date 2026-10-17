# Cartografia catastale WFS (particelle e fogli), Agenzia delle Entrate, riquadro FP

- Identificativo: `src_fi_catasto`
- Editore: Agenzia delle Entrate
- Scheda del catalogo: nessuna. La cartografia catastale non è su dati.toscana.it: è un servizio nazionale dell'Agenzia delle Entrate (WFS INSPIRE).
- Pagina della fonte: https://www.agenziaentrate.gov.it/portale/cartografia-catastale-wfs
- Risorsa scaricata: https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://www.agenziaentrate.gov.it/portale/cartografia-catastale-wfs
- Nota: Pagina del servizio: dati sotto CC BY 4.0 con citazione obbligatoria della titolarità: "Agenzia delle Entrate, cartografia catastale WFS, CC BY 4.0".

## Date

- Data del dato: non dichiarata: vale lo stato alla data di scarico
- Nota sul periodo: aggiornamento dichiarato per foglio (BEGINLIFESPANVERSION dei fogli, il più recente 2026-10-06 nel riquadro); stato alla data di scarico

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_catasto_20261010` | 2026-10-10T16:11:46Z | non dichiarato (cartografia catastale aggiornata dall'Agenzia per foglio (BEGINLIFESPANVERSION dei fogli); stato alla data di scarico) | dfa2b6b7fc28 | no |

## Campi usati

`NATIONALCADASTRALREFERENCE`, `LABEL`, `NATIONALCADASTRALZONINGREFERENCE`, `BEGINLIFESPANVERSION`, `ORIGINALMAPSCALEDENOMINATOR`

Sistema di riferimento dichiarato: EPSG:6706 (GML in RDN2008 geografico con assi lat,lon (unica proiezione offerta); convertito in EPSG:7791. Scarico limitato al riquadro FP (particelle che lo intersecano))

## Controlli

- particelle in area allargata: superato. 1631 oggetti
- fogli in area allargata: superato. 21 oggetti
- fabbricati: avviso. il servizio non pubblica i fabbricati: solo particelle (con strade e acque) e fogli
- valore dei confini: avviso. cartografia catastale: confini indicativi, non probatori

## Limiti

- Confini indicativi, non probatori; solo riquadro FP.
- fabbricati: il servizio non pubblica i fabbricati: solo particelle (con strade e acque) e fogli
- valore dei confini: cartografia catastale: confini indicativi, non probatori

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
