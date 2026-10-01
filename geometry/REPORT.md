# T05: edifici e verde Z2

Data: 1 ottobre 2026. Redatto dall'agente T05 e salvato dall'integratore. `geometry/build.sh` (circa 35 s); test `pipeline/.venv/bin/python geometry/test_geometrie.py`: OK (rieseguito dall'integratore). Il test ha intercettato e fatto correggere un volume derivato con altezza massima negativa.

## Edifici (Z2: 1.069 volumi; buffer: 3.107 measured, 125 derived)

- 1.034 measured: unità volumetriche 2010, quota base `uv_qs`, altezza `uv_av`. Tolleranza ±0,5 m: ipotesi, la fonte non dichiara incertezza.
- 35 derived (OSM senza unità volumetrica): 23 volumi e 12 coperture OSM (`building=roof`, fra cui 7 pensiline da 1.900-3.200 m², probabilmente la stazione).
- Regola post-2010: edificio OSM coperto da unità volumetriche per meno del 30%. Geometria = OSM meno unione delle unità volumetriche, scartate le parti sotto 10 m².
- Altezza derived: mediana DSM 2021 sul poligono eroso di 1 m, meno DTM 10 m calibrato su `uv_qs` (offset +0,12 m, sigma 0,69 m), meno il bias DSM-`uv_av` (+0,47 m). Intervallo ±1,4 m, ×1,5 con alberi entro 2 m. Flag: 7 sotto 2,5 m, 3 con DSM non attendibile, 1 con vegetazione possibile.
- Confronto DSM e `uv_av`, calibrato su 2.656 volumi del buffer (≥ 40 m², senza alberi entro 2 m; p10/p90 dello scarto -0,72/+1,63 m), soglia 3 m dopo il bias: 15 DSM più alto (possibili sopraelevazioni), 4 DSM più basso, 11 demolizione probabile (fra cui volumi da 900 e 2.570 m²), 1 scarto con vegetazione, 123 non confrontati (sotto 40 m²), 880 ok.
- Unità volumetriche e DSM non sono indipendenti: l'intervallo è ottimistico.
- Portici e volumi sospesi: "ignoto" ovunque. Per le coperture OSM c'è solo la quota del tetto.

## Alberi (Z2: 453)

- Fonti: 373 solo OSM, 75 solo DBT10K 2010, 5 DBT10K + OSM. Nel buffer 307 DBT10K e 834 OSM, solo 10 fusi: i due inventari quasi non si sovrappongono.
- Abbinamento: vicini reciproci entro 3 m fusi in un albero con entrambe le fonti (geometria DBT10K, distanza registrata). Fra 3 e 6 m restano due alberi con `candidato_altra_fonte` (25 nel buffer, 24 in Z2). Oltre 6 m separati. Nessuna fusione silenziosa.
- Copernicus non incluso: nei campioni dell'audit ci sono solo conteggi, nessuna geometria, e non sono alberi singoli.
- Chioma, altezza d'imposta e diametro del tronco: 453 su 453 solo stimati (min/tipico/max da `parametri_chiome.json`).
- Altezza: 278 derived da DSM (p95 entro 2,5 m, almeno 6 pixel di vegetazione), 175 classe "ignota" (4-25 m), nessuna altezza OSM plausibile. 2 alberi con specie, 2 con posizione dentro un edificio.
- DSM: 462 gruppi di vegetazione (≥ 20 pixel, 41.900 m²) senza albero puntuale entro 5 m. Inventario molto incompleto o falsi positivi (pensiline, mezzi): non verificabile da desk.
- Controllo: fra gli alberi con altezza da DSM il 59% supera 10 m, contro il 37% del censimento 2017. L'indizio DSM tende a sovrastimare.

## Giudizio G2 per Z2: fattibile con riserve

- Edifici: sì. Altezza misurata per il 97% dei volumi, intervalli espliciti, terreno coerente (sigma 0,7 m). Riserve: datum verticale non confermato, nessun riferimento indipendente, 30 volumi con scarto grande, portici ignoti.
- Alberi: solo come intervalli di sensibilità, non come ombra "reale". Per T09: baseline "ombra da edifici documentati" più uno scenario alberi con intervalli.

## Sopralluogo (`sopralluogo_z2.json`, 115 oggetti)

Corridoio provvisorio: retta fra fermata Pellico (PI4390) e ingresso Battisti, fascia di 60 m. Da sostituire con il percorso sul grafo T04.

- Priorità 1 (60): 54 alberi solo OSM (posizione, specie, altezza, chioma, imposta), 3 unità volumetriche con scarto DSM grande, 2 volumi derivati, 1 copertura OSM.
- Priorità 2 (42): 39 edifici alti (≥ 9 m, entro 25 m dal percorso: altezza e portico), 3 alberi presenti nel 2010.
- Priorità 3 (13): portico sì/no sul fronte strada.
- In più: altezza assoluta di 3-5 edifici come riferimento indipendente; quota d'imposta delle pensiline della stazione.

## Lacune

- Classi delle chiome senza citazione bibliografica (nessun accesso esterno), dichiarato nel file.
- Tolleranza delle unità volumetriche ±0,5 m: ipotesi.
- Censimento comunale e DTM LiDAR non acquisiti.
- Volumi sospesi non modellati.
- Aggiunta la libreria scipy in `pipeline/.venv`.

## File

`build.sh`, `build_geometrie.py`, `test_geometrie.py`, `parametri_chiome.json`, `edifici_z2.geojson` (681 KB), `alberi_z2.geojson` (251 KB), `report_z2.json`, `sopralluogo_z2.json`; `data/norm/geometry/geometrie_z2.gpkg` (layer volumi, alberi, vegetazione_dsm, osm_stato; non versionato).
