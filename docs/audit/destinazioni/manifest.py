#!/usr/bin/env python3
"""Scrive manifest.json: path, URL di origine, timestamp UTC (mtime del file, dichiarato), byte, sha256 per ogni file in campioni/."""
import os, json, hashlib, datetime, re
H = os.path.dirname(os.path.abspath(__file__)); C = H + '/campioni/'
SIT = 'https://sit.comune.pisa.it/arcgis/rest/services/Hosted/'
MIM = 'http://dati.istruzione.it/opendata/opendata/catalogo/elements1/'
GT = 'https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs'
PROV = 'https://maps.provincia.pisa.it/metarepo2/api/datasets/edifici_scolastici/download'
OV = 'https://overpass-api.de/api/interpreter (query in osm_zona.sh, around:raggio+250 m dal centro di zone.json)'
URL = {
 'sit_scuole.geojson': SIT + 'Scuole_infanzia_materne_primarie_e_secondarie/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson',
 'sit_plessi.geojson': SIT + 'Plessi_scolastici/FeatureServer/6/query?where=1=1&outFields=*&outSR=4326&f=geojson',
 'sit_istituti.geojson': SIT + 'Istituti_Comprensivi/FeatureServer/7/query?where=1=1&outFields=*&outSR=4326&f=geojson',
 'sit_edifici.geojson': SIT + 'edifici_scolastici/FeatureServer/4/query?where=1=1&outFields=*&outSR=4326&f=geojson',
 'sit_layer_scuole.json': SIT + 'Scuole_infanzia_materne_primarie_e_secondarie/FeatureServer/0?f=json',
 'sit_layer_plessi.json': SIT + 'Plessi_scolastici/FeatureServer/6?f=json',
 'sit_layer_civici.json': SIT + 'Civici_puntuali_View/FeatureServer/0?f=json',
 'ckan_edifici_scolastici_provpisa.json': 'https://dati.toscana.it/api/3/action/package_show?id=edifici-scolastici',
 'ckan_dati_gov_mim_scuole_statali.json': 'https://www.dati.gov.it/opendata/api/3/action/package_show?id=informazioni-anagrafiche-scuole-statali',
 'provincia_edifici_scolastici_raw.csv': PROV + ' (RISORSE/edifici_prov_pisa_Opendata_pubblicato.csv nello ZIP)',
 'provincia_edifici_scolastici_metadato.rdf': PROV + ' (METADATO_E_LICENZA/edifici_scolastici_r1.rdf nello ZIP)',
}
def url(n):
    if n in URL: return URL[n]
    m = re.match(r'sit_(\w+)\.service\.json', n)
    if m: return SIT + m.group(1) + '/FeatureServer?f=json'
    m = re.match(r'sit_civici_(Z\d)\.geojson', n)
    if m: return SIT + 'Civici_puntuali_View/FeatureServer/0/query (distance=raggio_m dal centro di ' + m.group(1) + ' in zone.json, outSR=4326, f=geojson)'
    if re.match(r'osm_Z\d\.json', n): return OV
    if re.match(r'osmc_Z\d\.json', n): return 'https://overpass-api.de/api/interpreter (riquadro canonico di ../ZONE.json, query in ricalcolo_osm.sh)'
    if n.startswith('gtfs_') and not n.startswith('gtfs_fermate') and not n.startswith('gtfs_verifica'): return GT + ' (estratto dallo ZIP, non conservato: 185529498 byte, sha256 2c00c8a604c60fb72c409715dcc8f2f20ef151f0fe389c5a3d08db2f217102c7, scaricato 2026-10-01T13:22Z)'
    if n.startswith('trenitalia_'): return 'https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/4f85393b-357d-443d-8378-65de4198505f/download/trenitalia.gtfs (estratto dallo ZIP, non conservato: 6127610 byte, sha256 a262c5bdfccd98a5c7e7ae08eea8eecb3189222f34c1015f5d4608faf3efc152, scaricato 2026-10-01T13:40Z)'
    return 'derivato: analizza.py / verifica_gtfs.py / treni_pisa.py da fonti elencate in REPORT.md'
out = []
for n in sorted(os.listdir(C)):
    p = C + n; b = open(p, 'rb').read()
    out.append(dict(path='campioni/' + n, url=url(n), timestamp_utc=datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), byte=len(b), sha256=hashlib.sha256(b).hexdigest()))
json.dump(dict(nota='timestamp_utc = data di modifica del file locale, convertita in UTC, non l\'intestazione HTTP della fonte. File grandi non conservati: vedi url.', file=out), open(H + '/manifest.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'file; zero byte:', [o['path'] for o in out if o['byte'] == 0])
