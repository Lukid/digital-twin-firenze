#!/usr/bin/env python3
"""manifest.json: path, URL, timestamp UTC (mtime), byte, sha256 dei file prodotti. Segnala file a 0 byte."""
import json, os, hashlib, datetime, glob
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.normpath(os.path.join(H, "..", "..", "research"))
D = "https://dati.toscana.it/api/3/action/"
URL = {
 "ckan-toscana-fi-ricerche.json": D + "package_search?q=<termine>&rows=20 (28 termini, ricerche_ckan_fi.py)",
 "ckan-toscana-fi-comune-firenze.json": D + "package_search?fq=organization:comune-di-firenze&rows=500&start=<n>",
 "ckan-toscana-fi-pacchetti.json": D + "package_show?id=<id> (37 dataset di layers.py)",
 "ckan-toscana-fi-url.json": "GET con Range sugli URL delle risorse (verifica_url.py)",
 "ckan-toscana-fi-contenuto.json": "GeoJSON delle risorse e harvest_url delle schede (controlli_contenuto.py)",
 "ckan-toscana-fi-gtfs-tram.json": "analisi di gest.gtfs (verifica_url.py)",
 "ckan-toscana-fi-gtfs-autolinee.json": "analisi del feed autolinee, 176 MB non conservato (verifica_url.py)",
 "gest.gtfs.zip": "https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/resource/1f62d551-65f4-49f8-9a99-e19b02077be3/download/gest.gtfs",
}
files = []
for p in sorted(glob.glob(os.path.join(R, "ckan-toscana-fi-*.json")) + glob.glob(os.path.join(H, "campioni", "*")) + [os.path.join(H, "inventario.json")]):
    b = open(p, "rb").read(); n = os.path.basename(p)
    files.append({"path": os.path.relpath(p, os.path.join(H, "..", "..", "..")), "url": URL.get(n, "inventario.py (derivato dai dump)"),
                  "timestamp_utc": datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
zero = [x["path"] for x in files if x["bytes"] == 0]
json.dump({"nota": "timestamp_utc = ora di scrittura del file. Il feed GTFS autolinee (176.482.531 byte) non è conservato: sha256 in ckan-toscana-fi-gtfs-autolinee.json",
           "files": files, "file_a_zero_byte": zero}, open(os.path.join(H, "manifest.json"), "w"), indent=1, ensure_ascii=False)
print(len(files), "file; a zero byte:", zero)
