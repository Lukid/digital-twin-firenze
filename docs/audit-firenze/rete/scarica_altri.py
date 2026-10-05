#!/usr/bin/env python3
"""Scarica i metadati CKAN (barriere, Walking City) e i 7 KML Walking City in data/raw/fi_audit_20261001/walking/."""
import json, os, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
RAW = "../../../data/raw/fi_audit_20261001/walking"; os.makedirs(RAW, exist_ok=True); os.makedirs("campioni", exist_ok=True)
T = "https://dati.toscana.it/api/3/action/package_search?"
UA = {"User-Agent": "digital-twin-pisa-audit/0.1 (audit F01; ai@netseven.it)"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
for nome, q in (("ckan_walking_city", "walking city"), ("ckan_barriere_firenze", "barriere architettoniche Firenze")):
    open(f"campioni/{nome}.json", "wb").write(get(T + urllib.parse.urlencode({"q": q, "rows": 10})))
for p in json.load(open("campioni/ckan_walking_city.json"))["result"]["results"]:
    if not p["title"].startswith("Walking City"): continue
    n = p["title"].split()[-1]
    for r in p["resources"]:
        if r["format"] == "KML": open(f"{RAW}/walking_city_{n}.kmz", "wb").write(get(r["url"]))
