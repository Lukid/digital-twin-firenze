"""manifest.json: per ogni file in campioni/ percorso, fonte, data (mtime = ora del download o dell'elaborazione), byte, sha256."""
import os, json, hashlib, datetime, re
CK="https://dati.toscana.it/api/3/action/package_show?id="
WFS="https://www502.regione.toscana.it/ows2/com.rt.wms.RTmap/wms?map=owsedificato&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=rt_edif.unitavolumetriche"
def url(f):
    m=re.match(r"ckan_pkg_(.+)\.json$",f)
    if m: return CK+m[1]
    if f in("verde_stats.json","chm_stats.json") or f.startswith("alberi_F"): return "derivato locale (script/*.py) da data/raw/fi_audit_20261001 (alberi.geojson, siti alberi) e dal DSM/DTM 2023"
    if f=="ckan_firenze_catalogo.json": return "package_search con fq=organization:comune-di-firenze su dati.toscana.it (script/ckan_firenze_catalogo.py), 1.992 dataset, titoli, note, licenza, risorse"
    if f.startswith("rt_uv_"): return WFS+" (bbox del riquadro "+f[6:8]+")"
    if f.startswith("osm_buildings_"): return "Overpass API, way/relation[building] nel riquadro "+f[14:16]
    if f.startswith("lidar"): return "SHA-256 delle tessere ASCII scaricate con script/fetch_lidar.py e script/fetch_lidar2017.py (dati grezzi in data/raw/fi_audit_20261001/lidar, non versionati)"
    return "derivato locale (script/*.py), non scaricato"
NOTE={}
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); files=[]
for f in sorted(os.listdir(os.path.join(root,"campioni"))):
    p=os.path.join(root,"campioni",f); b=open(p,"rb").read()
    files.append(dict(path="campioni/"+f,url=url(f),data_utc=datetime.datetime.fromtimestamp(os.path.getmtime(p),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),**({"licenza_nota":NOTE[f]} if f in NOTE else {})))
assert all(x["bytes"]>0 for x in files)
json.dump({"nota":"data_utc = mtime del file","files":files},open(os.path.join(root,"manifest.json"),"w"),indent=1,ensure_ascii=False); print(len(files),"file")
