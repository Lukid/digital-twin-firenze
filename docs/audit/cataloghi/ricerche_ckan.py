#!/usr/bin/env python3
"""Ricerche tematiche CKAN (Toscana e dati.gov.it); salva query, conteggi e sintesi per dataset."""
import json, urllib.request, urllib.parse, datetime
UA = {"User-Agent": "Mozilla/5.0 (audit)"}
PORTALS = {"toscana": "https://dati.toscana.it/api/3/action/package_search",
           "nazionale": "https://www.dati.gov.it/opendata/api/3/action/package_search"}
QUERIES = ["Pisa grafo stradale", "Pisa piste ciclabili", "Pisa alberi", "Pisa verde pubblico", "Pisa edifici", "Pisa scuole",
           "Pisa fermate trasporto", "Pisa civici", "Pisa DBTopografico", "Pisa ortofoto", "Pisa LiDAR", "Pisa servizi sanitari",
           "Comune di Pisa", "Pisa idrografia", "Pisa musei", "Pisa parcheggi", "Pisa accessibilità"]
out = {"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "queries": []}
for p, base in PORTALS.items():
    for q in QUERIES:
        u = base + "?" + urllib.parse.urlencode({"q": q, "rows": 50})
        import time
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90) as r:
                    j = json.load(r)["result"]
                break
            except Exception as e:
                err = str(e); time.sleep(3)
        else:
            out["queries"].append({"portal": p, "q": q, "error": err}); continue
        out["queries"].append({"portal": p, "q": q, "count": j["count"], "results": [
            {"name": x["name"], "title": x["title"], "notes": (x.get("notes") or "")[:200], "org": (x.get("organization") or {}).get("name"),
             "license_id": x.get("license_id"), "license_title": x.get("license_title"),
             "modified": x.get("metadata_modified"), "formats": sorted({(r.get("format") or "") for r in x["resources"]}),
             "urls": [r.get("url") for r in x["resources"]][:3]} for x in j["results"]]})
json.dump(out, open("campioni/ckan-ricerche-tematiche.json", "w"), ensure_ascii=False, indent=1)
