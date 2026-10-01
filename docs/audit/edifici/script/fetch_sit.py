import json, sys, urllib.request, urllib.parse
sys.path.insert(0, __import__('os').path.dirname(__file__))
from zone import ZONE
B="https://sit.comune.pisa.it/arcgis/rest/services/"
LAYERS={"periodizzazione":"periodizzazione_edificato_share/MapServer/1","ctrpoc":"Base_CTR_per_POC/MapServer/1"}
def q(layer, bbox, extra=""):
    s,w,n,e=bbox
    p={"where":"1=1","geometry":f"{w},{s},{e},{n}","geometryType":"esriGeometryEnvelope","inSR":4326,"spatialRel":"esriSpatialRelIntersects",
       "outFields":"*","returnGeometry":"true","returnZ":"true","outSR":4326,"f":"geojson"}
    url=B+LAYERS[layer]+"/query?"+urllib.parse.urlencode(p)
    return json.load(urllib.request.urlopen(url,timeout=120))
if __name__=="__main__":
    for l in LAYERS:
        for z,b in ZONE.items():
            d=q(l,b)
            if d.get("exceededTransferLimit"):   # limite 2000: ripete su 4 quadranti e unisce per id
                s_,w_,n_,e_=b; ms,mw=(s_+n_)/2,(w_+e_)/2; feats={}
                for sub in ((s_,w_,ms,mw),(s_,mw,ms,e_),(ms,w_,n_,mw),(ms,mw,n_,e_)):
                    dd=q(l,sub); assert not dd.get("exceededTransferLimit"), "ancora troncato"
                    for f in dd["features"]: feats[f["id"]]=f
                d["features"]=list(feats.values()); d.pop("exceededTransferLimit",None)
            json.dump(d,open(f"campioni/sit_{l}_{z}.geojson","w"))
            print(l,z,len(d.get("features",[])),d.get("exceededTransferLimit"),d.get("error"))
