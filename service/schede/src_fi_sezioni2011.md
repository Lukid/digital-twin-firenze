# Sezioni di censimento 2011 (Comune di Firenze)

- Identificativo: `src_fi_sezioni2011`
- Editore: Comune di Firenze
- Scheda del catalogo: https://dati.toscana.it/dataset/8a7483e6-5f01-497e-99c5-2458d348eb07
- Risorsa scaricata: https://data.comune.fi.it/datastore/download.php?id=6440&type=99&format=url&file_format=shp&file_id=20109
- Nella baseline congelata `bas_firenze_novoli_20261009`: no, fonte aggiunta dopo (usata nella scena e nella stima dei residenti per civico, non nei calcoli di accessibilità e ombra)

## Licenza

- Licenza: CC-BY-4.0
- Verifica: verificata
- Uso consentito: ridistribuzione consentita, con l'attribuzione richiesta dalla licenza
- Evidenza: https://dati.toscana.it/dataset/8a7483e6-5f01-497e-99c5-2458d348eb07
- Nota: Scheda e risorse del catalogo regionale: CC BY 4.0 (package_show del 2026-10-09). Verificata il 2026-10-10.

## Date

- Data del dato: 2011-10-09
- Nota sul periodo: confini delle sezioni del censimento 2011; file dello zip del 2020-10-14
- Ultima modifica della scheda del catalogo: 2026-02-11 (non è la data del dato)

Scarichi validi:

| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |
|---|---|---|---|---|
| `snp_fi_sezioni2011_20261010` | 2026-10-10T18:03:55Z | non dichiarato (confini 2011, file del 2020-10-14) | 3c2466fcbe90 | no |

## Campi usati

`CODSEZ2011`, `CODCOMPLSE`

Sistema di riferimento dichiarato: EPSG:3003 (CRS letto dal .prj dello shapefile e convertito in EPSG:7791)

## Controlli

- sezioni in area allargata: superato. 278 oggetti
- residenti: avviso. popolazione del censimento 2011 (src_rt_censimento2011): quindici anni fa, nessun dato per sezione più recente sul catalogo

## Limiti

- Residenti del 2011: l'accessibilità resta calcolata sui civici; i residenti entrano solo nella stima per civico (D45, strumento estimate_residents), accanto alla quota dei civici.
- residenti: popolazione del censimento 2011 (src_rt_censimento2011): quindici anni fa, nessun dato per sezione più recente sul catalogo

Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.
