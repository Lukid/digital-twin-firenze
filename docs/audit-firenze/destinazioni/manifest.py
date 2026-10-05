#!/usr/bin/env python3
"""manifest.json: path, URL di origine, byte, sha256 di campioni/ e dei dati grezzi in data/raw/fi_audit_20261001/ (non versionati)."""
import os, json, hashlib
H = os.path.dirname(os.path.abspath(__file__)); C = H + '/campioni/'; R = os.path.abspath(H + '/../../../data/raw/fi_audit_20261001/')
DB = 'https://data.comune.fi.it/datastore/download.php?id='
CM = 'https://dati.cittametropolitana.fi.it/geonetwork/srv/api/records/cmfi:a507767e-63e2-4856-9711-5e9a9ea96a76/attachments/'
URL = {
 'fi_scuole2627.csv': 'file già presente (scuole statali MIM 2026/27, stesso contenuto di cf_statali.geojson: stessi 222 codici)',
 'cf_statali.geojson': DB + '7857&type=99&format=url&file_format=geojson&file_id=23125',
 'cf_paritarie.geojson': DB + '7856&type=99&format=url&file_format=geojson&file_id=23121',
 'cm_form_ed_scolastici.zip': CM + 'form_ed_scolastici.zip',
 'cm_form_ed_scolastici_accessi.zip': CM + 'form_ed_scolastici_accessi.zip',
 'gest.zip': 'https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/1f62d551-65f4-49f8-9a99-e19b02077be3/download/gest.gtfs',
 'gtfs_at.zip': 'https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs (feed in aggiornamento continuo: lo sha256 cambia)',
 'osm_fi.json': 'https://overpass-api.de/api/interpreter (query in osm_fi.ql, bbox "contesto" di ../RIQUADRO.json)',
 'osm_careggi.json': 'https://overpass-api.de/api/interpreter (query in osm_careggi.ql, amenity=hospital in 43.77,11.20,43.82,11.28, solo per ottenere il poligono di Careggi)',
 'osm_fi.ql': 'generato da osm_firenze.sh', 'osm_careggi.ql': 'generato da osm_firenze.sh',
}
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
out = []
for base, lab in ((C, 'campioni/'), (R + '/', 'data/raw/fi_audit_20261001/')):
    for n in sorted(os.listdir(base)):
        p = base + n
        if not os.path.isfile(p) or n == 'at_dl.log' or (base == R + '/' and n not in URL): continue
        u = URL.get(n) or ('https://dati.toscana.it/api/3/action/package_show?id=' + n[5:-5] if n.startswith('ckan_') else 'prodotto da analizza_fi.py o osm_firenze.sh')
        out.append({'path': lab + n, 'origine': u, 'byte': os.path.getsize(p), 'sha256': sha(p)})
json.dump({'data_audit': '2026-10-05', 'file': out}, open(H + '/manifest.json', 'w'), indent=1, ensure_ascii=False)
print(len(out), 'file nel manifest')
