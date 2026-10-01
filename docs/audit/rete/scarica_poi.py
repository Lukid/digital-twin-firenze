#!/usr/bin/env python3
"""Destinazioni rilevanti (scuole, università, ospedali, fermate) per Z1-Z4: una query Overpass, salva campioni/osm_poi.json."""
import urllib.request, urllib.parse, json, hashlib, datetime, time
ZONE = {"Z1": (43.7140, 10.3940, 43.7210, 10.4060), "Z2": (43.7050, 10.3880, 43.7150, 10.4040),
        "Z3": (43.7000, 10.4350, 43.7110, 10.4500), "Z4": (43.7215, 10.3995, 43.7315, 10.4150)}
parts = ""
for z, (s, w, n, e) in ZONE.items():
    b = f"{s},{w},{n},{e}"
    parts += f'nwr["amenity"~"^(school|university|college|hospital|kindergarten)$"]({b});nwr["highway"="bus_stop"]({b});nwr["railway"~"^(station|tram_stop)$"]({b});'
q = f"[out:json][timeout:120];({parts});out center tags;"
UA = {"User-Agent": "digital-twin-pisa-audit/0.1 (audit T01; ai@netseven.it)"}
for u in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"] * 3:
    try:
        body = urllib.request.urlopen(urllib.request.Request(u, urllib.parse.urlencode({"data": q}).encode(), UA), timeout=180).read(); break
    except Exception as ex: print(u, ex); time.sleep(20)
open("campioni/osm_poi.json", "wb").write(body)
print(len(body), hashlib.sha256(body).hexdigest(), datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), u)
