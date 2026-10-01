#!/usr/bin/env python3
# Statistiche di completezza OSM per zona dai campioni osm_Z*.json
import json,collections
out={}
for z in ['Z1','Z2','Z3','Z4']:
    el=json.load(open(f'campioni/osm_{z}.json'))['elements']
    t=[e['tags'] for e in el if e['type']=='node' and e['tags'].get('natural')=='tree'] if False else [e.get('tags',{}) for e in el if e['type']=='node' and e.get('tags',{}).get('natural')=='tree']
    rows=[e.get('tags',{}) for e in el if e.get('tags',{}).get('natural')=='tree_row']
    n=len(t)
    att=lambda L,k:sum(1 for x in L if k in x)
    green=collections.Counter((e['tags'].get('leisure') or e['tags'].get('landuse') or e['tags'].get('natural')) for e in el if e['type']!='node' and e.get('tags',{}).get('natural')!='tree_row')
    out[z]={'alberi_nodi':n,'posizione_%':100 if n else None,
      'specie_(species|taxon|genus)':sum(1 for x in t if any(k in x for k in('species','taxon','genus'))),
      'altezza_height':att(t,'height'),'chioma_diameter_crown':att(t,'diameter_crown')+att(t,'crown_diameter'),
      'circonferenza_tronco':att(t,'circumference'),'leaf_type':att(t,'leaf_type'),
      'tree_row':len(rows),'tree_row_con_height':att(rows,'height'),'tree_row_con_species':sum(1 for x in rows if any(k in x for k in('species','taxon','genus'))),
      'esempi_height':[x['height'] for x in t if 'height' in x][:6],'denotation':dict(collections.Counter(x['denotation'] for x in t if 'denotation' in x)),
      'aree_verdi_tipi':dict(green)}
    for k in ['specie_(species|taxon|genus)','altezza_height','chioma_diameter_crown','leaf_type']:
        pass
    out[z]['pct']={k:round(100*out[z][k]/n,1) if n else None for k in ['specie_(species|taxon|genus)','altezza_height','chioma_diameter_crown','leaf_type'] if k in out[z]} if False else {k:round(100*out[z][k]/n,1) for k in ['specie_(species|taxon|genus)','altezza_height','chioma_diameter_crown','leaf_type','circonferenza_tronco']} if n else {}
json.dump(out,open('campioni/osm_analisi.json','w'),ensure_ascii=False,indent=1); print(json.dumps(out,ensure_ascii=False,indent=1))
