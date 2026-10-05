"""Riquadri F01 da docs/audit-firenze/RIQUADRO.json (S,W,N,E in EPSG:4326). CRS di lavoro EPSG:7791."""
import json, os
from shapely.geometry import box
_R=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../RIQUADRO.json")))
ZONE={k:tuple(v["bbox"]) for k,v in _R["zone"].items()}
def poly4326(b): s,w,n,e=b; return box(w,s,e,n)
