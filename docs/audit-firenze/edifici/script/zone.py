"""Riquadri F01 letti da docs/audit-firenze/RIQUADRO.json (S,W,N,E in EPSG:4326). CRS di lavoro EPSG:7791."""
import json, os
from pyproj import Transformer
_R=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../RIQUADRO.json")))
ZONE={k:tuple(v["bbox"]) for k,v in _R["zone"].items()}
CTX=tuple(_R["contesto"]["bbox"])
T=Transformer.from_crs(4326,7791,always_xy=True)
def bbox_m(b):
    s,w,n,e=b; xs,ys=zip(*[T.transform(x,y) for x in (w,e) for y in (s,n)]); return min(xs),min(ys),max(xs),max(ys)
def tiles(b):
    x0,y0,x1,y1=bbox_m(b); return [f"32_{x}_{y}.ASC" for x in range(int(x0//500*500),int(x1)+1,500) for y in range(int(y0//500*500),int(y1)+1,500)]
if __name__=="__main__":
    for z,b in ZONE.items(): print(z,[round(v) for v in bbox_m(b)],tiles(b))
