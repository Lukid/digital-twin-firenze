"""Scarica le Unità volumetriche (WFS Regione Toscana, owsedificato) per le zone Z1-Z4 e le salva come JSON."""
import json, sys, os, urllib.request, urllib.parse, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE
W="https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato"
NS={"gml":"http://www.opengis.net/gml/3.2","wfs":"http://www.opengis.net/wfs/2.0","ms":"http://mapserver.gis.umn.edu/mapserver"}
def page(bbox,start,count=500):
    s,w,n,e=bbox
    p={"SERVICE":"WFS","VERSION":"2.0.0","REQUEST":"GetFeature","TYPENAMES":"rt_edif.unitavolumetriche","COUNT":count,"STARTINDEX":start,
       "SRSNAME":"EPSG:4326","BBOX":f"{s},{w},{n},{e},urn:ogc:def:crs:EPSG::4326"}
    return urllib.request.urlopen(W+"&"+urllib.parse.urlencode(p),timeout=120).read()
def parse(raw):
    out=[]
    for m in ET.fromstring(raw).iter("{%s}member"%NS["wfs"]):
        f=m[0]; rec={}
        for c in f:
            tag=c.tag.split("}")[1]
            if tag=="GEOMETRY":
                polys=[]
                for pl in c.iter("{%s}Polygon"%NS["gml"]):
                    rings=[]
                    for pos in pl.iter("{%s}posList"%NS["gml"]):
                        v=list(map(float,pos.text.split())); rings.append([(v[i+1],v[i]) for i in range(0,len(v),2)])
                    polys.append(rings)
                rec["polys"]=polys
            elif tag!="boundedBy": rec[tag]=(c.text or "").strip()
        out.append(rec)
    return out
if __name__=="__main__":
    for z,b in ZONE.items():
        allr=[];st=0
        while True:
            raw=page(b,st); r=parse(raw); allr+=r
            if len(r)<500: break
            st+=500
        json.dump(allr,open(f"campioni/rt_uv_{z}.json","w"))
        print(z,len(allr))
