#!/usr/bin/env python3
"""Ispezione destinazioni caso A per Z1-Z4. Solo lettura dei campioni, scrive CSV/JSON in campioni/.
uso: analizza.py <cartella GTFS decompressa> <csv MIM statali> <csv MIM paritarie> <csv Provincia edifici>"""
import csv, json, math, re, sys, datetime, collections, os

GT, MIMS, MIMP, PROV = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
C = HERE + '/campioni/'
ZONE = json.load(open(HERE + '/zone.json'))
ZK = ['Z1', 'Z2', 'Z3', 'Z4']
TODAY = '20261001'


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(x))


def zona(lat, lon, extra=0):
    """zona il cui cerchio (+extra m) contiene il punto; la più vicina al centro se più d'una"""
    best = None
    for k in ZK:
        z = ZONE[k]
        d = hav(z['lat'], z['lon'], lat, lon)
        if d <= z['raggio_m'] + extra and (best is None or d < best[1]):
            best = (k, d)
    return best[0] if best else None


def centro(g):
    t = g['type']
    if t == 'Point':
        return g['coordinates'][1], g['coordinates'][0]
    ring = g['coordinates'][0] if t == 'Polygon' else g['coordinates'][0][0]
    return sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)


STOP = {'via', 'viale', 'piazza', 'largo', 'lungarno', 'piazzale', 'vicolo', 'corso', 'di', 'del', 'della', 'dei', 'delle', 'dello', 'degli', 'da', 'd', 'l', 'n', 'snc', 'fraz', 'localita'}


def toks(s):
    s = re.sub(r"[^a-z0-9àèéìòù ]", ' ', (s or '').lower().replace("'", ' '))
    return {t for t in s.split() if t not in STOP and not t.isdigit() and len(t) > 1}


def civ(s):
    m = re.findall(r'\b(\d+)\b', s or '')
    return m[-1] if m else ''


# ---------------- GTFS ----------------
stops = list(csv.DictReader(open(GT + '/stops.txt', encoding='utf-8-sig')))
trips = {r['trip_id']: r for r in csv.DictReader(open(GT + '/trips.txt'))}
routes = {r['route_id']: r for r in csv.DictReader(open(GT + '/routes.txt'))}
cal = {r['service_id']: r for r in csv.DictReader(open(GT + '/calendar.txt'))}
cd = collections.defaultdict(dict)
for r in csv.DictReader(open(GT + '/calendar_dates.txt')):
    cd[r['service_id']][r['date']] = r['exception_type']
wd = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][datetime.datetime.strptime(TODAY, '%Y%m%d').weekday()]
act = set()
for sid in set(cal) | set(cd):
    on = sid in cal and cal[sid]['start_date'] <= TODAY <= cal[sid]['end_date'] and cal[sid][wd] == '1'
    e = cd.get(sid, {}).get(TODAY)
    on = True if e == '1' else False if e == '2' else on
    if on:
        act.add(sid)
act_trips = {t for t, r in trips.items() if r['service_id'] in act}
szone = {}
for s in stops:
    z = zona(float(s['stop_lat']), float(s['stop_lon']), 250)  # 250 m di contesto
    if z:
        szone[s['stop_id']] = z
dep = collections.Counter(); rts = collections.defaultdict(set)
for r in csv.DictReader(open(GT + '/stop_times.txt')):
    if r['stop_id'] in szone and r['trip_id'] in act_trips:
        dep[r['stop_id']] += 1; rts[r['stop_id']].add(routes[trips[r['trip_id']]['route_id']]['route_short_name'])
gt_rows = []
for s in stops:
    if s['stop_id'] in szone:
        la, lo = float(s['stop_lat']), float(s['stop_lon'])
        z = ZONE[szone[s['stop_id']]]
        gt_rows.append(dict(zona=szone[s['stop_id']], stop_id=s['stop_id'], stop_code=s['stop_code'], nome=s['stop_name'], lat=la, lon=lo,
                            dentro_cerchio=hav(z['lat'], z['lon'], la, lo) <= z['raggio_m'], corse_oggi=dep[s['stop_id']],
                            linee_oggi=' '.join(sorted(rts[s['stop_id']])), wheelchair_boarding=s['wheelchair_boarding']))
gt_rows.sort(key=lambda r: (r['zona'], -r['corse_oggi']))
with open(C + 'gtfs_fermate_zone.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(gt_rows[0].keys())); w.writeheader(); w.writerows(gt_rows)

# ---------------- OSM ----------------
osm = {}
for k in ZK:
    p = C + f'osm_{k}.json'
    osm[k] = json.load(open(p))['elements'] if os.path.exists(p) else []


def ell(e):
    if 'bounds' in e:  # con "out center bb" Overpass restituisce solo i limiti
        b = e['bounds']; return (b['minlat'] + b['maxlat']) / 2, (b['minlon'] + b['maxlon']) / 2
    c = e.get('center') or {'lat': e.get('lat'), 'lon': e.get('lon')}
    return c['lat'], c['lon']


edu_osm = []
for k in ZK:
    seen = set()
    ent = [e for e in osm[k] if 'entrance' in e['tags'] and e['type'] == 'node']
    for e in osm[k]:
        t = e['tags']
        if t.get('amenity') in ('school', 'university', 'college', 'kindergarten') or t.get('building') in ('school', 'university', 'college', 'kindergarten'):
            la, lo = ell(e)
            if (e['type'], e['id']) in seen:
                continue
            seen.add((e['type'], e['id']))
            if 'bounds' in e:
                b = e['bounds']; m = 0.00012
                near = [n for n in ent if b['minlat'] - m <= n['lat'] <= b['maxlat'] + m and b['minlon'] - m * 1.4 <= n['lon'] <= b['maxlon'] + m * 1.4]
            else:
                near = [n for n in ent if hav(la, lo, n['lat'], n['lon']) <= 25]
            edu_osm.append(dict(zona_osm_query=k, osm=f"{e['type']}/{e['id']}", tipo=t.get('amenity') or 'building=' + t.get('building', ''), nome=t.get('name', ''),
                                lat=la, lon=lo, zona=zona(la, lo, 0), entrate_osm_vicine=len(near),
                                entrate_wheelchair=sum(1 for n in near if n['tags'].get('wheelchair')), entrate_tag=' '.join(sorted({n['tags']['entrance'] for n in near})),
                                access=t.get('access', ''), operator=t.get('operator', ''), check_date=t.get('check_date', ''), addr=(t.get('addr:street', '') + ' ' + t.get('addr:housenumber', '')).strip()))
# dedup per id osm tra query di zone sovrapposte
d = {}
for r in edu_osm:
    d.setdefault(r['osm'], r)
edu_osm = [r for r in d.values() if r['zona']]
edu_osm.sort(key=lambda r: (r['zona'], r['tipo'], r['nome']))
with open(C + 'osm_istruzione_zone.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(edu_osm[0].keys())); w.writeheader(); w.writerows(edu_osm)
# fermate osm
osm_stops = []
for k in ZK:
    for e in osm[k]:
        t = e['tags']
        if t.get('highway') == 'bus_stop' or t.get('public_transport') == 'platform':
            osm_stops.append(ell(e) + (t.get('name', ''),))
osm_stops = list(set(osm_stops))
conc_stops = {}
for k in ZK:
    g = [r for r in gt_rows if r['zona'] == k and r['dentro_cerchio']]
    n40 = sum(1 for r in g if any(hav(r['lat'], r['lon'], a, b) <= 40 for a, b, _ in osm_stops))
    conc_stops[k] = dict(gtfs_fermate_nel_cerchio=len(g), con_osm_entro_40m=n40, con_servizio_oggi=sum(1 for r in g if r['corse_oggi'] > 0))

# ---------------- SIT, MIM, Provincia ----------------
sit = json.load(open(C + 'sit_scuole.geojson'))['features']
ed = json.load(open(C + 'sit_edifici.geojson'))['features']
mim = [r for r in csv.DictReader(open(MIMS, encoding='utf-8-sig')) if r['DESCRIZIONECOMUNE'].upper() == 'PISA']
mimp = [r for r in csv.DictReader(open(MIMP, encoding='utf-8-sig')) if r['DESCRIZIONECOMUNE'].upper() == 'PISA']
prov = [r for r in csv.DictReader(open(PROV, encoding='cp1252', errors='replace')) if r['comune'] == 'Pisa']
for r in mim: r['_t'] = toks(r['INDIRIZZOSCUOLA']); r['_c'] = civ(r['INDIRIZZOSCUOLA']); r['_src'] = 'statale'
for r in mimp: r['_t'] = toks(r['INDIRIZZOSCUOLA']); r['_c'] = civ(r['INDIRIZZOSCUOLA']); r['_src'] = 'paritaria'
mimall = mim + mimp

conc = []
for f in sit:
    la, lo = centro(f['geometry'])
    z = zona(la, lo, 400)
    if not z:
        continue
    p = f['properties']
    addr = p.get('indirizzo') or p.get('via') or ''
    tk, cv = toks(addr), civ(addr)
    # corrispondenza MIM per via (+ civico se presente in entrambi)
    m = [r for r in mimall if tk and (tk & r['_t']) and (not cv or not r['_c'] or cv == r['_c'])]
    # corrispondenza per nome (token del nome SIT nella denominazione MIM)
    nt = toks(p.get('nomi', ''))
    mn = [r for r in mimall if nt and nt <= toks(r['DENOMINAZIONESCUOLA'])]
    o = [(hav(la, lo, r['lat'], r['lon']), r) for r in edu_osm if r['tipo'] in ('school', 'kindergarten', 'building=school', 'building=kindergarten')]
    o = sorted(o, key=lambda x: x[0])
    on = o[0] if o and o[0][0] <= 120 else None
    conc.append(dict(zona=z, fid=p['fid'], nome_sit=p.get('nomi', ''), tipo_sit=p.get('tiposcuola', ''), istituto_sit=p.get('istit_scol', ''), indirizzo_sit=addr, nota_sit=(p.get('nota_1') or '').strip(),
                     lat=round(la, 6), lon=round(lo, 6), mim_per_via=' | '.join(f"{r['CODICESCUOLA']} {r['DENOMINAZIONESCUOLA']} ({r['INDIRIZZOSCUOLA']})" for r in m[:3]),
                     mim_per_nome=' | '.join(f"{r['CODICESCUOLA']} ({r['INDIRIZZOSCUOLA']})" for r in mn[:2]),
                     osm_piu_vicino_entro_120m=(f"{on[1]['osm']} {on[1]['nome']} {on[0]:.0f}m entrate={on[1]['entrate_osm_vicine']}" if on else '')))
with open(C + 'concordanza_scuole_sit_mim_osm.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(conc[0].keys())); w.writeheader(); w.writerows(sorted(conc, key=lambda r: (r['zona'], r['tipo_sit'])))

# edifici SIT (poligoni, solo via/civico) e Provincia (superiori, 2017)
edr = []
for f in ed:
    la, lo = centro(f['geometry']); z = zona(la, lo, 400)
    if z:
        p = f['properties']; edr.append(dict(zona=z, fid=p['fid'], via=p['via'], civico=p['civico'], stato=p['stato'], proprieta=p['proprieta'], lat=round(la, 6), lon=round(lo, 6)))
with open(C + 'sit_edifici_scolastici_zone.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(edr[0].keys())); w.writeheader(); w.writerows(sorted(edr, key=lambda r: r['zona']))

kb = [k for k in prov[0] if 'barriere' in k][0]; kr = [k for k in prov[0] if 'rampe' in k][0]
kas = [k for k in prov[0] if 'ascensore' in k][0]
prow = [dict(codice_edificio=r['codice edificio'], plesso=r['Plesso'], via=r['tipologia strada'] + ' ' + r['denominazione strada'], civico=r['numero'], barriere_accorgimenti=r[kb], rampe=r[kr], ascensore=r[kas],
             percorsi_esterni=r.get([k for k in r if 'percorsi esterni' in k][0], '')) for r in prov]
with open(C + 'provincia_edifici_superiori_pisa.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(prow[0].keys())); w.writeheader(); w.writerows(prow)
with open(C + 'mim_pisa_2026_27.csv', 'w', newline='') as f:
    cols = ['_src', 'CODICESCUOLA', 'DENOMINAZIONESCUOLA', 'INDIRIZZOSCUOLA', 'CAPSCUOLA', 'DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA']
    w = csv.writer(f); w.writerow(['fonte'] + cols[1:])
    for r in mimall: w.writerow([r['_src']] + [r[c] for c in cols[1:]])

# civici per zona
civs = {}
for k in ZK:
    fs = json.load(open(C + f'sit_civici_{k}.geojson'))['features']
    sez = collections.Counter(f['properties']['sezione_censuaria_istat'] for f in fs)
    civs[k] = dict(civici=len(fs), sezioni_distinte=len(sez), ambito=dict(collections.Counter(f['properties']['ambito'] for f in fs)), dt_agg_max=datetime.datetime.fromtimestamp(max((f['properties']['dt_agg'] or 0) for f in fs) / 1000, datetime.timezone.utc).strftime('%Y-%m-%d'))

summary = dict(conc_fermate=conc_stops, civici=civs, n_sit_scuole_zone=collections.Counter(r['zona'] for r in conc), n_osm_istruzione=collections.Counter(r['zona'] for r in edu_osm),
               n_mim_pisa=dict(statali=len(mim), paritarie=len(mimp)), n_provincia_pisa=len(prow), n_sit_edifici=collections.Counter(r['zona'] for r in edr))

# ---------------- candidati caso A (scelti a mano dopo la lettura delle tabelle sopra; ingressi da verificare) ----------------
CAND = {'Z1': ('way/232482921', 'Liceo Artistico F. Russoli (via San Frediano 13)'), 'Z2': ('way/695634299', 'Scuola primaria C. Battisti (via Corridoni 42)'),
        'Z3': ('way/211388929', 'Scuola primaria L. Gereschi (via U. Viale 16)'), 'Z4': ('way/128401172', 'Scuola secondaria I grado L. Fibonacci (via Lalli 4)')}
cand_out = {}
for k, (oid, label) in CAND.items():
    typ, i = oid.split('/')
    e = next(x for x in osm[k] if x['type'] == typ and str(x['id']) == i)
    b = e['bounds']; m = 0.00012
    ents = [n for n in osm[k] if n['type'] == 'node' and 'entrance' in n['tags'] and b['minlat'] - m <= n['lat'] <= b['maxlat'] + m and b['minlon'] - m * 1.4 <= n['lon'] <= b['maxlon'] + m * 1.4]
    la, lo = ell(e)
    fer = sorted(((hav(la, lo, r['lat'], r['lon']), r) for r in gt_rows if hav(la, lo, r['lat'], r['lon']) <= 300), key=lambda x: x[0])
    cand_out[k] = dict(etichetta=label, osm=oid, nome_osm=e['tags'].get('name', ''), centro_osm=[round(la, 6), round(lo, 6)], tag_osm={a: v for a, v in e['tags'].items() if a in ('name', 'amenity', 'building', 'check_date', 'addr:street', 'addr:housenumber', 'wheelchair')},
                       ingressi_osm_nel_bbox=[dict(id=n['id'], lat=n['lat'], lon=n['lon'], tag=n['tags']) for n in ents],
                       fermate_gtfs_entro_300m=[dict(codice=r['stop_code'], nome=r['nome'], dist_m=round(d), corse_oggi=r['corse_oggi'], linee=r['linee_oggi']) for d, r in fer])
json.dump(cand_out, open(C + 'candidati_caso_A.json', 'w'), ensure_ascii=False, indent=1)
for k, v in cand_out.items():
    print(k, v['etichetta'], 'ingressi', len(v['ingressi_osm_nel_bbox']), 'fermate<=300m', len(v['fermate_gtfs_entro_300m']), 'corse oggi sulle fermate', sum(f['corse_oggi'] for f in v['fermate_gtfs_entro_300m']))

json.dump(summary, open(C + 'riepilogo_zone.json', 'w'), ensure_ascii=False, indent=1, default=dict)
print(json.dumps(summary, ensure_ascii=False, indent=1, default=dict))
