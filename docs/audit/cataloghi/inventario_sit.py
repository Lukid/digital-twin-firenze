#!/usr/bin/env python3
"""Inventario read-only dei servizi ArcGIS del SIT di Pisa: metadati di servizio e layer, conteggi."""
import json, urllib.request, urllib.parse, datetime, sys
S = "https://sit.comune.pisa.it/arcgis/rest/services"
UA = {"User-Agent": "Mozilla/5.0 (audit)"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
            return json.load(r)
    except Exception as e:
        return {"_error": str(e)}
def ms(t):
    return datetime.datetime.fromtimestamp(t / 1000, datetime.timezone.utc).strftime("%Y-%m-%d") if t else None
root = get(S + "?f=json")
names = [s["name"] + "|" + s["type"] for s in root["services"]]
for f in ("Hosted",):
    names += [s["name"] + "|" + s["type"] for s in get(f"{S}/{f}?f=json")["services"]]
out = []
for n in names:
    name, typ = n.split("|")
    base = f"{S}/{name}/{typ}"
    j = get(base + "?f=json")
    rec = {"service": name, "type": typ, "url": base,
           "copyrightText": j.get("copyrightText"), "serviceDescription": j.get("serviceDescription") or j.get("description"),
           "capabilities": j.get("capabilities"), "documentInfo": j.get("documentInfo"),
           "spatialReference": (j.get("spatialReference") or {}).get("wkid"), "error": j.get("_error") or (j.get("error") or {}).get("message"), "layers": []}
    ei = j.get("editingInfo") or {}
    rec["lastEditDate"] = ms(ei.get("lastEditDate"))
    for l in (j.get("layers") or []):
        lj = get(f"{base}/{l['id']}?f=json")
        cnt = None
        if "FeatureServer" in typ or "MapServer" in typ:
            c = get(f"{base}/{l['id']}/query?where=1%3D1&returnCountOnly=true&f=json")
            cnt = c.get("count")
        lei = lj.get("editingInfo") or {}
        rec["layers"].append({"id": l["id"], "name": l["name"], "geometryType": lj.get("geometryType") or l.get("geometryType"),
            "count": cnt, "copyrightText": lj.get("copyrightText"), "description": (lj.get("description") or "")[:300],
            "lastEditDate": ms(lei.get("lastEditDate")), "dataLastEditDate": ms(lei.get("dataLastEditDate")),
            "nFields": len(lj.get("fields") or []), "fields": [f["name"] for f in (lj.get("fields") or [])][:40],
            "capabilities": lj.get("capabilities"), "maxRecordCount": lj.get("maxRecordCount")})
    out.append(rec)
    print(name, typ, len(rec["layers"]), rec["error"] or "", file=sys.stderr)
json.dump(out, open("campioni/sit-inventario.json", "w"), ensure_ascii=False, indent=1)
