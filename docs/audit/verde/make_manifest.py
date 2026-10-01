#!/usr/bin/env python3
# Genera manifest.json. Il timestamp è l'mtime del file in UTC (momento di scrittura del campione).
import os,json,hashlib,datetime,re,glob
SIT="https://sit.comune.pisa.it/arcgis/rest/services/"
def url(f):
    b=os.path.basename(f)
    if b=='zone.json': return '(bbox definiti in questo audit, non una fonte)'
    if m:=re.match(r'ckan_(\d+)\.json',b):
        i=int(m.group(1)); 
        for l in open('campioni/ckan_log.tsv'):
            p=l.rstrip('\n').split('\t')
            if int(p[0])==i:
                base="https://dati.toscana.it/api/3/action" if 'toscana' in p[1] else "https://www.dati.gov.it/opendata/api/3/action"
                return f"{base}/package_search?q={p[2]}&rows=20"
    if m:=re.match(r'ckan_pkg_(.+)\.json',b): return f"https://dati.toscana.it/api/3/action/package_show?id={m.group(1)}"
    if m:=re.match(r'sit_psi_layer_(\d+)\.json',b): return f"{SIT}PSI/MapServer/{m.group(1)}?f=json"
    return {'ckan_log.tsv':'(derivato da ckan_queries.sh)','catalogo_pisa_titoli.json':'https://opendata.comune.pisa.it/catalogo-opendata?page=0..132 (scan_catalogo_pisa.py)',
     'sit_psi_service.json':SIT+'PSI/MapServer?f=json','sit_verde_conteggi.json':'(derivato da sit_verde.py, query su '+SIT+')',
     'osm_stats.json':'https://overpass-api.de/api/interpreter (osm_alberi.py)','osm_analisi.json':'(derivato da analisi_osm.py)',
     'comunicato_rinnovo_arboreo.html':'https://www.comune.pisa.it/Novita/Comunicati/Rinnovo-arboreo-il-Comune-di-Pisa-prosegue-gli-incontri-con-le-associazioni-ambientaliste',
     'censimento_mappa_alberi_old_url_410.html':'https://www.comune.pisa.it/it/ufficio-scheda/20099/Censimento-e-Mappa-degli-alberi.html (risposta HTTP 410, pagina non trovata)',
     'spazio_verde.html':'https://www.comune.pisa.it/Argomenti/Ambiente/Spazio-verde','dataset_page.html':'https://www.comune.pisa.it/Amministrazione/Documenti-e-dati/Dataset','sitemap.html':'https://www.comune.pisa.it/content/view/sitemap/2',
     'arpi_885149.html':'https://arpi.unipi.it/handle/11568/885149','cop_stl_mapserver.json':'https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_StreetTreeLayer_2018/MapServer?f=pjson',
     'cop_stl_layer0.json':'.../UA_StreetTreeLayer_2018/MapServer/0?f=pjson','cop_stl_layer2.json':'.../UA_StreetTreeLayer_2018/MapServer/2?f=pjson',
     'cop_stl_conteggi_zone.json':'.../MapServer/0/query (returnCountOnly, bbox zona)','cop_stl_sample_Z1.geojson':'.../MapServer/0/query (5 feature, bbox Z1, outSR 4326)',
     'spod_1_rest_licenses.json':'http://opendata.comune.pisa.it/SpodCkanApi/api/1/rest/licenses','spod_2_rest_package.json':'http://opendata.comune.pisa.it/SpodCkanApi/api/2/rest/package'}.get(b) \
     or (re.match(r'osm_Z\d',b) and 'https://overpass-api.de/api/interpreter (osm_alberi.py)') or ('https://opendata.comune.pisa.it/'+b[3:-5].replace('_','/',1)+' (variante, vedi riproduci.sh)' if b.startswith('od_') else '?')
rows=[]
for f in sorted(glob.glob('campioni/*')+['zone.json']):
    if os.path.isdir(f): continue
    d=open(f,'rb').read()
    rows.append({'path':f,'url':url(f),'timestamp_utc':datetime.datetime.fromtimestamp(os.path.getmtime(f),datetime.timezone.utc).isoformat(timespec='seconds'),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()})
json.dump(rows,open('manifest.json','w'),ensure_ascii=False,indent=1)
print(len(rows),'file;','zero byte:',[r['path'] for r in rows if r['bytes']==0],'; url ignoti:',[r['path'] for r in rows if r['url']=='?'])
