#!/usr/bin/env python3
"""Ricalcolo sui riquadri canonici (../ZONE.json). uso: ricalcolo.py <GTFS dir> <MIM statali csv> <MIM paritarie csv>
Scrive campioni/ricalcolo_zone_canoniche.json. I candidati stanno in CAND (scelti a mano dopo aver letto l'elenco stampato)."""
import csv, json, math, sys, os, re, datetime, collections, subprocess
sys.argv_ = sys.argv
GT, MIMS, MIMP = sys.argv[1:4]
H = os.path.dirname(os.path.abspath(__file__)); C = H + '/campioni/'
Z = json.load(open(H + '/../ZONE.json'))['zone']
CAND = json.load(open(H + '/candidati_canonici.json')) if os.path.exists(H + '/candidati_canonici.json') else {}
def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(x))
def inb(k, la, lo):
    s, w, n, e = Z[k]['bbox']; return s <= la <= n and w <= lo <= e
def cen(g):
    if g['type'] == 'Point': return g['coordinates'][1], g['coordinates'][0]
    r = g['coordinates'][0] if g['type'] == 'Polygon' else g['coordinates'][0][0]
    return sum(p[1] for p in r) / len(r), sum(p[0] for p in r) / len(r)
STOP = {'via','viale','piazza','largo','lungarno','piazzale','di','del','della','dei','delle','dello','degli','da','d','l','n','snc'}
def toks(s):
    s = re.sub(r"[^a-z0-9 ]", ' ', (s or '').lower().replace("'", ' ')); return {t for t in s.split() if t not in STOP and not t.isdigit() and len(t) > 1}
# GTFS
stops = list(csv.DictReader(open(GT + '/stops.txt', encoding='utf-8-sig')))
trips = {r['trip_id']: r for r in csv.DictReader(open(GT + '/trips.txt'))}
routes = {r['route_id']: r for r in csv.DictReader(open(GT + '/routes.txt'))}
on = {r['service_id'] for r in csv.DictReader(open(GT + '/calendar_dates.txt')) if r['date'] == '20261001' and r['exception_type'] == '1'}
act = {t for t, r in trips.items() if r['service_id'] in on}
near = [s for s in stops if any(inb(k, float(s['stop_lat']) , float(s['stop_lon'])) or True for k in Z) and any(Z[k]['bbox'][0] - .004 <= float(s['stop_lat']) <= Z[k]['bbox'][2] + .004 and Z[k]['bbox'][1] - .006 <= float(s['stop_lon']) <= Z[k]['bbox'][3] + .006 for k in Z)]
ids = {s['stop_id'] for s in near}; dep = collections.Counter(); rts = collections.defaultdict(set)
for r in csv.DictReader(open(GT + '/stop_times.txt')):
    if r['stop_id'] in ids and r['trip_id'] in act:
        dep[r['stop_id']] += 1; rts[r['stop_id']].add(routes[trips[r['trip_id']]['route_id']]['route_short_name'])
def civici_count(lat, lon, dist):
    a = subprocess.check_output(['curl','-sS','-m','60','-G','https://sit.comune.pisa.it/arcgis/rest/services/Hosted/Civici_puntuali_View/FeatureServer/0/query','--data-urlencode',f'geometry={lon},{lat}','--data-urlencode','geometryType=esriGeometryPoint','--data-urlencode','inSR=4326','--data-urlencode',f'distance={dist}','--data-urlencode','units=esriSRUnit_Meter','--data-urlencode','where=1=1','--data-urlencode','returnCountOnly=true','--data-urlencode','f=json'])
    return json.loads(a)['count']
sit = json.load(open(C + 'sit_scuole.geojson'))['features']
mim = [r for r in csv.DictReader(open(MIMS, encoding='utf-8-sig')) if r['DESCRIZIONECOMUNE'].upper() == 'PISA'] + [r for r in csv.DictReader(open(MIMP, encoding='utf-8-sig')) if r['DESCRIZIONECOMUNE'].upper() == 'PISA']
out = {'riquadri': {k: v['bbox'] for k, v in Z.items()}, 'zone': {}}
for k in Z:
    s, w, n, e = Z[k]['bbox']
    r = {}
    fs = [x for x in near if inb(k, float(x['stop_lat']), float(x['stop_lon']))]
    r['gtfs'] = dict(fermate=len(fs), servite_oggi=sum(1 for x in fs if dep[x['stop_id']] > 0), linee_oggi=len({l for x in fs for l in rts[x['stop_id']]}), corse_oggi_somma_sulle_fermate=sum(dep[x['stop_id']] for x in fs))
    ss = [(x, cen(x['geometry'])) for x in sit if inb(k, *cen(x['geometry']))]
    r['scuole_sit'] = dict(totale=len(ss), per_tipo=dict(collections.Counter(x['properties']['tiposcuola'].strip() for x, _ in ss)))
    r['elenco_sit'] = [dict(nome=x['properties'].get('nomi'), indirizzo=x['properties'].get('indirizzo'), lat=round(c[0], 6), lon=round(c[1], 6)) for x, c in ss]
    # MIM: per via contenuta tra gli indirizzi SIT dentro il riquadro (corrispondenza grezza), conteggio sedi uniche
    mm = set()
    for x, c in ss:
        t = toks(x['properties'].get('indirizzo') or x['properties'].get('via'))
        for m in mim:
            if t and t & toks(m['INDIRIZZOSCUOLA']): mm.add(m['CODICESCUOLA'])
    r['mim_sedi_con_via_di_una_scuola_SIT_nel_riquadro'] = len(mm)
    p = C + f'osmc_{k}.json'
    if os.path.exists(p):
        el = json.load(open(p))['elements']; ent = [x for x in el if x['type'] == 'node' and 'entrance' in x['tags']]
        edu = []
        for x in el:
            t = x['tags']
            if t.get('amenity') in ('school','university','college','kindergarten') or t.get('building') in ('school','university','college','kindergarten'):
                if 'bounds' in x:
                    b = x['bounds']; la, lo = (b['minlat']+b['maxlat'])/2, (b['minlon']+b['maxlon'])/2; m_ = .00012
                    ne = [q for q in ent if b['minlat']-m_ <= q['lat'] <= b['maxlat']+m_ and b['minlon']-m_*1.4 <= q['lon'] <= b['maxlon']+m_*1.4]
                else:
                    la, lo = x.get('lat'), x.get('lon'); ne = [q for q in ent if hav(la, lo, q['lat'], q['lon']) <= 25]
                if inb(k, la, lo): edu.append(dict(osm=f"{x['type']}/{x['id']}", tipo=t.get('amenity') or 'building=' + t.get('building',''), nome=t.get('name',''), lat=round(la,6), lon=round(lo,6), ingressi=len(ne), check_date=t.get('check_date','')))
        r['osm'] = dict(scuole_infanzia=sum(1 for d in edu if 'school' in d['tipo'] or 'kinder' in d['tipo']), universita=sum(1 for d in edu if 'univ' in d['tipo'] or 'college' in d['tipo']), con_ingressi=sum(1 for d in edu if d['ingressi']), base_osm=json.load(open(p))['osm3s']['timestamp_osm_base'])
        r['elenco_osm'] = sorted(edu, key=lambda d: (d['tipo'], d['nome']))
    # civici nel riquadro (envelope)
    a = subprocess.check_output(['curl','-sS','-m','60','-G','https://sit.comune.pisa.it/arcgis/rest/services/Hosted/Civici_puntuali_View/FeatureServer/0/query','--data-urlencode',f'geometry={w},{s},{e},{n}','--data-urlencode','geometryType=esriGeometryEnvelope','--data-urlencode','inSR=4326','--data-urlencode','where=1=1','--data-urlencode','returnCountOnly=true','--data-urlencode','f=json'])
    r['civici_sit_nel_riquadro'] = json.loads(a)['count']
    c = CAND.get(k)
    if c:
        la, lo = c['lat'], c['lon']
        assert inb(k, la, lo), k
        fer = sorted(((hav(la, lo, float(x['stop_lat']), float(x['stop_lon'])), x) for x in near), key=lambda t: t[0])
        r['candidato'] = dict(c, dentro_riquadro=True, fermate_gtfs_entro_300m=[dict(codice=x['stop_code'], nome=x['stop_name'], dist_m=round(d), corse_oggi=dep[x['stop_id']], linee=' '.join(sorted(rts[x['stop_id']]))) for d, x in fer if d <= 300],
                              civici_entro_500m=civici_count(la, lo, 500), civici_entro_1000m=civici_count(la, lo, 1000))
    out['zone'][k] = r
json.dump(out, open(C + 'ricalcolo_zone_canoniche.json', 'w'), ensure_ascii=False, indent=1)
for k, r in out['zone'].items(): print(k, {a: b for a, b in r.items() if not a.startswith('elenco') and a != 'candidato'})
