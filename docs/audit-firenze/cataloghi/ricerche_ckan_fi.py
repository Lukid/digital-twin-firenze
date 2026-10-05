#!/usr/bin/env python3
"""Interroga dati.toscana.it (CKAN 2.10): ricerche tematiche, elenco slim del Comune di Firenze, package_show dei dataset di layers.py.
Scrive docs/research/ckan-toscana-fi-*.json."""
import json, os, time, datetime, urllib.request, urllib.parse
from layers import LAYERS
B = "https://dati.toscana.it/api/3/action/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "research")
UA = {"User-Agent": "Mozilla/5.0 (audit)"}
def call(act, **k):
    u = B + act + "?" + urllib.parse.urlencode(k)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r: return json.load(r)["result"]
        except Exception as e: err = e; time.sleep(3)
    raise err
def save(n, o): json.dump(o, open(os.path.join(OUT, "ckan-toscana-fi-" + n + ".json"), "w"), ensure_ascii=False, indent=1)
ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
# 1. ricerche tematiche
Q = ["alberi", "rilievo celerimetrico", "LiDAR", "DTM", "DSM", "civici", "barriere architettoniche", "Walking City", "rifugi climatici", "Escapos",
     "edificato", "Firenze edifici", "Firenze altezza edifici", "GTFS", "tramvia", "quartieri", "scuole", "anagrafe edilizia scolastica", "dbt10k",
     "database topografico", "CTR", "ortofoto", "OpenStreetMap", "OSM", "marciapiedi", "attraversamenti pedonali", "ingressi edifici", "illuminazione pubblica"]
rs = []
for q in Q:
    r = call("package_search", q=q, rows=20)
    rs.append({"q": q, "count": r["count"], "results": [{"name": x["name"], "title": x["title"], "org": (x.get("organization") or {}).get("name"),
        "license_id": x.get("license_id"), "modified": x["metadata_modified"], "formats": sorted({(y.get("format") or "") for y in x["resources"]})} for x in r["results"]]})
save("ricerche", {"timestamp_utc": ts, "queries": rs})
# 2. Comune di Firenze: elenco slim
allp, s = [], 0
while True:
    r = call("package_search", fq="organization:comune-di-firenze", rows=500, start=s); allp += r["results"]; s += 500
    if s >= r["count"]: break
save("comune-firenze", {"timestamp_utc": ts, "count": len(allp), "datasets": [{"name": x["name"], "title": x["title"], "license_id": x.get("license_id"),
    "modified": x["metadata_modified"], "formats": sorted({(y.get("format") or "") for y in x["resources"]}),
    "frequency": next((e["value"] for e in x.get("extras", []) if e["key"] == "frequency"), None)} for x in allp]})
# 3. package_show
pk = {}
for lay, ids in LAYERS.items():
    for i in ids: pk[i] = call("package_show", id=i)
save("pacchetti", {"timestamp_utc": ts, "layers": LAYERS, "packages": pk})
print("ricerche", len(rs), "| comune firenze", len(allp), "| pacchetti", len(pk))
