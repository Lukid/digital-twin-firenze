#!/usr/bin/env python3
"""Scarica i metadati dei 663 dataset di StatPortal (API CKAN v2 del Comune di Pisa) in un solo file."""
import json, urllib.request, concurrent.futures as cf
B = "https://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/dataset"
UA = {"User-Agent": "Mozilla/5.0 (audit)"}
def get(u):
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = str(e)
    return {"_error": err, "_url": u}
ids = get(B)
with cf.ThreadPoolExecutor(8) as ex:
    data = list(ex.map(lambda i: get(f"{B}/{i}"), ids))
json.dump(data, open("campioni/od-statportal-dataset.json", "w"), ensure_ascii=False)
print(len(data), sum(1 for d in data if "_error" in d), "errori")
