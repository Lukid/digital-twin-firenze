"""Edifici OSM per FA e FB (Overpass). Salva campioni/osm_buildings_<zona>.json con tag e geometria."""
import sys, os, json, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE
EP=["https://overpass.private.coffee/api/interpreter","https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]
def run(q):
    for ep in EP*2:
        try:
            req=urllib.request.Request(ep,data=urllib.parse.urlencode({"data":q}).encode(),headers={"User-Agent":"digital-twin-pisa-audit/0.1"})
            return json.load(urllib.request.urlopen(req,timeout=90))
        except Exception as e: print("retry",ep,str(e)[:60]); time.sleep(5)
for z,(s,w,n,e) in ZONE.items():
    p=os.path.join(os.path.dirname(__file__),f"../campioni/osm_buildings_{z}.json")
    if os.path.exists(p) and "--force" not in sys.argv: print(z,"già presente"); continue
    d=run(f'[out:json][timeout:90];(way["building"]({s},{w},{n},{e});relation["building"]({s},{w},{n},{e}););out tags geom;')
    if d is None: print(z,"download non completato"); continue
    json.dump(d,open(p,"w")); print(z,len(d["elements"]))
