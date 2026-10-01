# ADR-T02: contratti dati del pilota Z2

Stato: proposta, 1 ottobre 2026. Redatto dall'agente T02 e salvato dall'integratore. Controllo: `contracts/.venv/bin/python contracts/validate.py` (31 validi passano, 10 non validi respinti).

## Decisioni

1. **CRS operativo: EPSG:7791** (RDN2008 / UTM 32N, assi E,N), non EPSG:6707. Stessi parametri, ma nel registro EPSG 6707 ha assi N,E: leggere una coppia E,N come 6707 sposta il punto a (4,46; 45,41) invece di (10,40; 43,71). Verificato con pyproj dall'integratore.
2. **RDN2008 e non EPSG:3003**: le fonti regionali (unità volumetriche, DSM, DTM, WFS/WMS) sono già in RDN2008/UTM 32N. Il SIT in 3003 si converte una sola volta in ingresso; l'accuratezza della trasformazione va verificata in T03.
3. Fattore di scala UTM 0,9996 al meridiano centrale (9 E): errore di lunghezza nell'ordine dello 0,04%. Lunghezze e aree in piano, fatto dichiarato.
4. Fonti in lon/lat (OSM, GTFS) trattate come RDN2008 geografico (EPSG:6706). Scarto atteso sotto 1 m, non misurato.
5. Ordine fisso [E, N]. I limiti di range dello schema (E 166000-834000, N 3900000-5300000) respingono coppie scambiate e lon/lat. Precisione 0,01 m.
6. Formati: GeoJSON in EPSG:7791 con membro `crs` URN (deroga a RFC 7946, letta dagli strumenti GIS desktop); per il web si deriva un file 4326 a parte. GeoPackage per archivio e revisione, Parquet per tabelle, JSON per manifest.
7. **Datum verticale: `non_confermato`**. Le fonti non lo dichiarano, coerenza solo indiretta (circa 1 m). Nessun geoide assunto. Ogni manifest porta `vertical_datum_status`. Le altezze relative non dipendono dal datum.
8. Tempo: Europe/Rome. Timestamp RFC 3339 con offset (generati in UTC, suffisso Z). Orari GTFS come stringhe del giorno di servizio (fino a 26). Azimut solare orario da Nord.
9. **ID stabili** dall'ID originario, mai dalla posizione: `src_`, `snp_<slug>_<AAAAMMGG>`, `bas_`, `aoi_`, `dst_<categoria>_<codice>` (es. `dst_school_piee82101p`, `dst_stop_pi4390`), `ent_`, feature `<tipo3>_<fonte>_<id>` (es. `bld_rt_...`, `way_osm_...`). `job_id` = `job_` + 16 hex dello sha256 del JSON canonico (tool, inputs, params): stesso input, stesso job, quindi cache e replay. `manifest_id` usa le stesse cifre.
10. **Classificazione obbligatoria** di ogni valore: `measured` / `derived` / `estimated` / `scenario` (ID in inglese, etichette italiane in `conventions.json`). Nei file geografici è la mappa `cls` per attributo. Una stima senza incertezza è respinta; le dimensioni di scenario devono essere `scenario`.
11. **Stati di accessibilità**: `reachable`, `isolated`, `insufficient_data`, `forbidden`, `outside_model` (il quinto viene da SPEC_ANALISI). Le componenti isolate restano nei conteggi del manifest.
12. **Licenza**: `clear`, `clear_with_reserve`, `conflict`, `unproven`. Se non è `clear` serve `reserve_note`. Con `conflict` o `unproven` la ridistribuzione è esclusa (`permitted_use` solo `internal_prototype` o `none`), come per SIT e LiDAR.
13. Snapshot: sha256 e byte obbligatori se lo stato è ok. Uno scarico fallito richiede errore e `previous_snapshot_id` e non sostituisce l'ultimo valido.
14. MCP: 9 tool con input/output in `mcp.schema.json`. `additionalProperties: false` ovunque (niente SQL o codice libero), soglie e limiti numerici nei parametri. Ogni output è un risultato oppure `tool_error` (`ambiguous_destination`, `limit_exceeded`, `insufficient_data`, `outside_capability`, ...).
15. I manifest descrivono il metodo, non il prodotto software. I nomi di strumenti compaiono solo nei file tecnici di `sample/`.

## Verifiche

- `validate.py`: oltre agli schemi controlla che `job_id` sia l'hash dell'input, che `manifest_id` sia coerente e che ogni attributo del campione abbia la sua classe.
- Campione `sample/z2_campione.geojson`: 26 oggetti (scuola Battisti, 3 ingressi OSM non verificati, fermate PI4390/PI4389/PI4074, 8 tratti di rete, 3 attraversamenti, 8 unità volumetriche), con sha256 delle fonti in `provenance`. Si rigenera con `sample/costruisci_campione.py`.
- Due lettori indipendenti (`sample/verifica_lettori.py`): Python con librerie geospaziali e Node senza librerie, con proiezione inversa scritta a mano. Concordano su conteggi, bbox, lunghezza rete 1269,61 m, area edifici 3657,67 m², distanza scuola-Pellico 665,63 m, ritorno a lon/lat entro 6 mm.
- I valori nei manifest di esempio (quota servita 0,31, frazione d'ombra 0,18, conteggi degli stati) sono illustrativi e dichiarati tali nel campo `limits`.

## Punti aperti

1. Approvare EPSG:7791 al posto di 6707.
2. Nessun GIS desktop nel test dei lettori: aprire il campione in un GIS desktop prima di T08.
3. Confermare `outside_model` come quinto stato.
4. Scarto WGS84/RDN2008 e accuratezza della trasformazione da EPSG:3003: da misurare in T03 con punti noti.
5. Datum verticale da confermare con la Regione.
6. GeoPackage non prodotto (mancano strumenti locali): in T03 se serve.
7. Il job copre solo walk, shadow e compare. Formato del grafo e tabelle Parquet da concordare in T04.
8. GTFS e unità volumetriche negli esempi sono `clear_with_reserve`; SIT e LiDAR non sono ancora in uno snapshot.
