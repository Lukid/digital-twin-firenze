#!/usr/bin/env python3
"""Scarica da Overpass la rete pedonale per Z1-Z4 (bbox s,w,n,e). Salva JSON in campioni/ e aggiorna manifest."""
import json, hashlib, time, urllib.request, urllib.parse, os, datetime, sys
UA = {"User-Agent": "digital-twin-pisa-audit/0.1 (audit T01; ai@netseven.it)"}
ZONE = {  # bbox approssimative ~1,2 x 1,2 km, non approvate
 "Z1": (43.7140, 10.3940, 43.7210, 10.4060),
 "Z2": (43.7050, 10.3880, 43.7150, 10.4040),
 "Z3": (43.7000, 10.4350, 43.7110, 10.4500),
 "Z4": (43.7215, 10.3995, 43.7315, 10.4150),
}
URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
Q = """[out:json][timeout:120];
(
 way["highway"]({b});
 node["highway"="crossing"]({b});
 node["barrier"]({b});
 node["entrance"]({b});
 node["kerb"]({b});
 node["railway"="crossing"]({b});
);
out body geom;
"""
os.makedirs("campioni", exist_ok=True)
man = []
sel = sys.argv[1:] or list(ZONE)
for z in sel:
    s, w, n, e = ZONE[z]
    q = Q.format(b=f"{s},{w},{n},{e}")
    body = None
    for u in URLS*3:
        if body: break
        try:
            data = urllib.parse.urlencode({"data": q}).encode()
            r = urllib.request.urlopen(urllib.request.Request(u, data, UA), timeout=180)
            body = r.read()
        except Exception as ex:
            print(z, u, ex, file=sys.stderr); body = None; time.sleep(20)
    if not body: continue
    p = f"campioni/osm_{z}.json"
    open(p, "wb").write(body)
    man.append(dict(path="docs/audit/rete/"+p, url=u+" (POST, query in scarica_osm.py, bbox "+f"{s},{w},{n},{e})",
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
    time.sleep(3)
mp = "campioni/_osm_manifest.json"
old = [m for m in (json.load(open(mp)) if os.path.exists(mp) else []) if m["path"] not in {x["path"] for x in man}]
json.dump(old + man, open(mp, "w"), indent=1)
