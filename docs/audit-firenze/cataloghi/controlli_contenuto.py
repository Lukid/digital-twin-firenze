#!/usr/bin/env python3
"""Scarica i GeoJSON piccoli e il censimento alberi (23 MB) e riporta numero di elementi, campi, CRS dichiarato e se compare un campo di licenza.
Scarica anche gli indirizzi harvest_url delle schede (portale del Comune) per vedere se rispondono."""
import json, os, urllib.request, urllib.error, tempfile, hashlib
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "..", "..", "research")
UA = {"User-Agent": "Mozilla/5.0 (audit)"}
pk = json.load(open(os.path.join(R, "ckan-toscana-fi-pacchetti.json")))["packages"]
G = {n: next(r["url"] for r in p["resources"] if r["format"] == "GeoJSON") for n, p in pk.items() if any(r["format"] == "GeoJSON" for r in p["resources"])}
out = {"geojson": {}, "harvest_url": {}}
for n, u in G.items():
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read()
    j = json.loads(b); f = j["features"]
    props = sorted({k for x in f for k in (x.get("properties") or {})})
    out["geojson"][n] = {"url": u, "byte": len(b), "sha256": hashlib.sha256(b).hexdigest(), "elementi": len(f), "crs": j.get("crs"),
                         "tipi_geometria": sorted({(x.get("geometry") or {}).get("type") or "null" for x in f}), "campi": props,
                         "campi_licenza": [k for k in props if "lic" in k.lower()], "primo_vertice": (f[0].get("geometry") or {}).get("coordinates") if f else None}
for n, p in pk.items():
    u = next((e["value"] for e in p["extras"] if e["key"] == "harvest_url"), None)
    if not u: continue
    try: c = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).status
    except urllib.error.HTTPError as e: c = e.code
    except Exception as e: c = str(e)[:60]
    out["harvest_url"][n] = {"url": u, "code": c}
json.dump(out, open(os.path.join(R, "ckan-toscana-fi-contenuto.json"), "w"), ensure_ascii=False, indent=1)
cod = {}
for v in out["harvest_url"].values(): cod[str(v["code"])] = cod.get(str(v["code"]), 0) + 1
print(len(out["geojson"]), "GeoJSON letti; harvest_url per codice:", cod)
