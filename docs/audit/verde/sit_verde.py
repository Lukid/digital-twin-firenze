#!/usr/bin/env python3
# Conteggio feature dei layer SIT con tema verde/alberi per bbox di zona; salva campioni.
import json,urllib.request,urllib.parse,datetime,re
Z=json.load(open('zone.json')); R="https://sit.comune.pisa.it/arcgis/rest/services/"
def g(u,**p):
    return json.load(urllib.request.urlopen(u+'?'+urllib.parse.urlencode(p),timeout=60))
svc=g(R+"PSI/MapServer",f='json')
cand=[l for l in svc['layers'] if re.search(r'alber|verd|vegetaz|parco|parchi|giardin|bosc|arbore|agricol|pineta',l['name'],re.I)]
layers=[("PSI/MapServer",l['id'],l['name']) for l in cand]+[("Toponomastica_comunale/MapServer",1,"parchi giardini luoghi di interesse")]
res=[]
for s,i,n in layers:
    row={'servizio':s,'layer':i,'nome':n}
    try:
        info=g(f"{R}{s}/{i}",f='json'); row['geom']=info.get('geometryType'); row['campi']=[f['name'] for f in info.get('fields',[])]
        row['tot']=g(f"{R}{s}/{i}/query",where='1=1',returnCountOnly='true',f='json').get('count')
        for z,v in Z.items():
            if z=='nota':continue
            s_,w,n_,e=v
            row[z]=g(f"{R}{s}/{i}/query",geometry=f"{w},{s_},{e},{n_}",geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',returnCountOnly='true',f='json').get('count')
    except Exception as ex: row['errore']=str(ex)
    res.append(row); print({k:v for k,v in row.items() if k!='campi'})
json.dump({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'layers':res},open('campioni/sit_verde_conteggi.json','w'),ensure_ascii=False,indent=1)
