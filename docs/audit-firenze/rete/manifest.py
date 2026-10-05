#!/usr/bin/env python3
"""Scrive manifest.json con byte e sha256 di script, campioni e input grezzi."""
import hashlib, json, os, glob
os.chdir(os.path.dirname(os.path.abspath(__file__)))
RAW = "../../../data/raw/fi_audit_20261001"
fs = sorted(glob.glob("*.py") + glob.glob("*.sh") + glob.glob("campioni/*") + [f"{RAW}/barriere.zip", f"{RAW}/rifugi.geojson"] + glob.glob(f"{RAW}/walking/*"))
m = [dict(path=f, bytes=os.path.getsize(f), sha256=hashlib.sha256(open(f, "rb").read()).hexdigest()) for f in fs]
assert all(x["bytes"] > 0 for x in m)
json.dump(dict(fonti="vedi REPORT.md", file=m), open("manifest.json", "w"), indent=1)
print(len(m), "file")
