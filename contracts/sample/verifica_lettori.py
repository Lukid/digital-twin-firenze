"""Esegue i due lettori e confronta i risultati. Uso: docs/audit/edifici/.venv/bin/python verifica_lettori.py"""
import json, subprocess, sys, pathlib
d = pathlib.Path(__file__).parent
a = json.loads(subprocess.check_output([sys.executable, d/"leggi_python.py"]))
b = json.loads(subprocess.check_output(["node", d/"leggi_node.js"]))
ko = []
if a["counts"] != b["counts"]: ko.append("conteggi")
for k in ("bbox",):
    if any(abs(x-y) > 0.01 for x, y in zip(a[k], b[k])): ko.append(k)
for k, tol in (("network_length_m", 0.01), ("building_area_m2", 0.01), ("school_to_pellico_m", 0.01)):
    if abs(a[k]-b[k]) > tol: ko.append(k)
if any(abs(x-y) > 1e-7 for x, y in zip(a["school_lonlat_pyproj"], b["school_lonlat_node"])): ko.append("lonlat")
if abs(a["school_lonlat_pyproj"][0]-a["school_lonlat_gdal"][0]) > 1e-7: ko.append("gdal")
if max(a["max_roundtrip_err_deg"], b["max_roundtrip_err_deg"]) > 1e-7: ko.append("roundtrip")
if a["axes"] != ["east", "north"]: ko.append("assi")
print("LETTORI CONCORDI" if not ko else f"DISCORDANZE: {ko}")
sys.exit(bool(ko))
