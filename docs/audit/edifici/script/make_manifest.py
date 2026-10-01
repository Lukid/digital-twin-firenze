"""Genera manifest.json: per ogni file in campioni/ percorso, URL sorgente, timestamp UTC (data di ultima modifica del file, = ora del download), byte, sha256."""
import os, json, hashlib, datetime, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE
SIT="https://sit.comune.pisa.it/arcgis/rest/services/"
WFS="https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato"
WMSM="https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia"
def bb(z): s,w,n,e=ZONE[z]; return f"bbox(S,W,N,E)={s},{w},{n},{e}"
def url(f):
    z=(re.search(r"_(Z\d)",f) or [None,None])[1]
    if f.startswith("sit_periodizzazione_Z"): return SIT+"periodizzazione_edificato_share/MapServer/1/query ("+bb(z)+", returnZ)"
    if f.startswith("sit_ctrpoc_Z"): return SIT+"Base_CTR_per_POC/MapServer/1/query ("+bb(z)+", returnZ)"
    m=re.match(r"sit_(.+)\.json$",f)
    if m: return SIT+m.group(1).replace("_MapServer_","/MapServer/").replace("_FeatureServer_","/FeatureServer/").replace("Hosted_","Hosted/").replace("_MapServer","/MapServer").replace("_FeatureServer","/FeatureServer")+"?f=json"
    if f.startswith("rt_uv_Z"): return WFS+"&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=rt_edif.unitavolumetriche ("+bb(z)+")"
    if f=="rt_uv_describe.xml": return WFS+"&SERVICE=WFS&VERSION=2.0.0&REQUEST=DescribeFeatureType&TYPENAMES=rt_edif.unitavolumetriche"
    if f=="rt_edificato_wfs_caps.xml": return WFS+"&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities"
    if f=="rt_edificato_wms_caps.xml": return "https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato&SERVICE=WMS&REQUEST=GetCapabilities"
    if f=="rt_morfologia_wms_caps.xml": return WMSM+"&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
    if f=="rt_morfologia_wcs_caps.xml": return WMSM+"&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities (risposta: errore 400)"
    m=re.match(r"(dtm|dsm|dtm10)_Z\d_(\d+)_(\d+)_(\d+)\.tif",f)
    if m: return WMSM+f"&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=(vedi script/fetch_raster.py)&CRS=EPSG:32632&BBOX={m[2]},{m[3]},+{m[4]}m&FORMAT=image/tiff"
    if f.startswith("osm_buildings_"): return "Overpass API, way/relation[building] nel bbox della zona ("+bb(z)+")"
    m=re.match(r"ckan_(.+)\.json$",f)
    if m and m[1]!="ricerche_edifici": return "https://dati.toscana.it/api/3/action/package_show?id="+m[1]
    if f=="ckan_ricerche_edifici.json": return "package_search su dati.toscana.it, dati.gov.it, opendata.comune.pisa.it (query nel file)"
    if f=="geonetwork_lidar_1m.xml": return "https://www502.regione.toscana.it/geonetwork/srv/api/records/r_toscan:f3ff89ee-49fa-4487-89fe-c69ae58ecd0c/formatters/xml"
    if f=="geometa_261ec.htm": return "https://www502.regione.toscana.it/geoscopio/geometa/html/r_toscan_261ec1b2-bf25-4973-b853-ac08e060ec62.htm"
    if f=="geometa_dsm2021.htm": return "https://www502.regione.toscana.it/geoscopio/geometa/html/r_toscan_c5c907bf-50cc-4a76-8787-abc547509c8d.htm"
    m=re.match(r"geoscopio_wms_(.+)\.htm$",f)
    if m: return f"http://www502.regione.toscana.it/geoscopio/servizi/wms/{m[1]}.htm"
    return "derivato locale (script/*.py), non scaricato"
note={"sit_Hosted_edifici_scolastici_FeatureServer_0.json":"risposta di errore (63 byte), non un layer"}
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files=[]
for f in sorted(os.listdir(os.path.join(root,"campioni"))):
    p=os.path.join(root,"campioni",f); b=open(p,"rb").read()
    files.append(dict(path="campioni/"+f,url=url(f),downloaded_utc=datetime.datetime.fromtimestamp(os.path.getmtime(p),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),**({"note":note[f]} if f in note else {})))
assert all(x["bytes"]>0 for x in files),"file a 0 byte"
json.dump({"generato":"timestamp = mtime del file (ora del download per i file scaricati, dell'elaborazione per i derivati)","files":files},open(os.path.join(root,"manifest.json"),"w"),indent=1,ensure_ascii=False)
print(len(files),"file")
