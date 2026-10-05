#!/usr/bin/env python3
"""F01 destinazioni, Firenze. Adattato da ../../audit/destinazioni/analizza.py (T01 Pisa).
Legge i dati grezzi in data/raw/fi_audit_20261001/ e i riquadri in ../RIQUADRO.json.
Scrive CSV/JSON in campioni/. Tutte le distanze sono calcolate in EPSG:7791 (RDN2008 / UTM 32N).
uso: analizza_fi.py   (nessun argomento)"""
import csv, json, os, re, collections, datetime, sys
import geopandas as gpd
from shapely.geometry import box, Point, Polygon, shape
from shapely.ops import unary_union, linemerge, polygonize
from shapely import wkt
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.abspath(HERE + '/../../../data/raw/fi_audit_20261001')
OUT = HERE + '/campioni/'
DATA_SERVIZIO = '20261007'  # mercoledì: il GTFS di Autolinee Toscane vale 20261005-20261025
SOGLIA_BORDO = 700  # m, 10 min a 1,2 m/s (arrotondato)
MATCH_M = 150  # m, soglia per dire che due fonti indicano la stessa scuola

T = Transformer.from_crs(4326, 7791, always_xy=True)
Ti = Transformer.from_crs(7791, 4326, always_xy=True)


def prj(lon, lat):
    return T.transform(lon, lat)


def gprj(geom):
    from shapely.ops import transform
    return transform(lambda x, y, z=None: T.transform(x, y), geom)


RQ = json.load(open(HERE + '/../RIQUADRO.json'))
BOX = {}
for k, v in {**RQ['zone'], 'CTX': RQ['contesto']}.items():
    s, w, n, e = v['bbox']
    BOX[k] = gprj(box(w, s, e, n))  # S,W,N,E -> box(minx=W, miny=S, maxx=E, maxy=N)
ZK = ['FA', 'FB']


def dist_bordo(g, b):
    """metri dal bordo del riquadro b: positivo se g (punto) è dentro, negativo se fuori"""
    return b.exterior.distance(g) if b.contains(g) else -b.distance(g)


def inside(g, b):
    return b.contains(g)


# ---------------- sorgenti scuole ----------------
def load_osm():
    d = json.load(open(RAW + '/osm_fi.json'))['elements']
    feats = []
    for e in d:
        t = e.get('tags', {})
        if e['type'] == 'node':
            g = Point(prj(e['lon'], e['lat']))
        elif e['type'] == 'way':
            c = [prj(p['lon'], p['lat']) for p in e.get('geometry', [])]
            if len(c) < 2:
                continue
            g = Polygon(c) if c[0] == c[-1] and len(c) >= 4 else None
            if g is None:
                from shapely.geometry import LineString
                g = LineString(c)
        else:  # relation: unisce i lati outer
            from shapely.geometry import LineString
            lines = [LineString([prj(p['lon'], p['lat']) for p in m['geometry']]) for m in e.get('members', []) if m.get('role') == 'outer' and m.get('geometry')]
            polys = list(polygonize(unary_union(lines))) if lines else []
            if not polys:
                continue
            g = unary_union(polys)
        feats.append({'oid': f"{e['type'][0]}{e['id']}", 'tags': t, 'g': g})
    return feats


OSM = load_osm()


def is_scuola(t):
    return t.get('amenity') in ('school', 'kindergarten', 'college') or (t.get('amenity') == 'childcare' and t.get('building') == 'kindergarten')


def is_univ(t):
    return t.get('amenity') == 'university' or t.get('building') == 'university'


osm_scuole_am = [f for f in OSM if is_scuola(f['tags'])]
am_poly = unary_union([f['g'] for f in osm_scuole_am if f['g'].geom_type in ('Polygon', 'MultiPolygon')])
osm_build_orfani = [f for f in OSM if f['tags'].get('building') in ('school', 'kindergarten') and not is_scuola(f['tags']) and f['g'].geom_type in ('Polygon', 'MultiPolygon') and not f['g'].intersects(am_poly)]
osm_univ = [f for f in OSM if is_univ(f['tags'])]
osm_ent = [f for f in OSM if 'entrance' in f['tags'] and f['g'].geom_type == 'Point']

mim = []
for r in csv.DictReader(open(RAW + '/fi_scuole2627.csv')):
    lon, lat = wkt.loads(r['geom']).coords[0]
    mim.append({'src': 'MIM_statale', 'cod': r['codicescuo'], 'nome': r['nome'], 'ind': r['indirizzo'], 'tip': r['tipologia'], 'g': Point(prj(lon, lat))})
for f in json.load(open(RAW + '/cf_paritarie.geojson'))['features']:
    p = f['properties']; lon, lat = f['geometry']['coordinates']
    mim.append({'src': 'Comune_paritaria', 'cod': p['codicescuo'], 'nome': p['nome'].strip('"'), 'ind': p['indirizzo'], 'tip': p['tipologia'], 'g': Point(prj(lon, lat))})
cm_acc = gpd.read_file(RAW + '/cm_form_ed_scolastici_accessi/form_ed_scolastici_accessi.shp').to_crs(7791)
cm_ed = gpd.read_file(RAW + '/cm_form_ed_scolastici/form_ed_scolastici.shp').to_crs(7791)

# ---------------- 1. scuole: conteggi per riquadro e per fonte ----------------
conteggi = collections.OrderedDict()


def zone_of(g):
    return [k for k in ZK + ['CTX'] if inside(g.representative_point() if g.geom_type != 'Point' else g, BOX[k])]


def cnt(items, getg):
    return {k: sum(1 for i in items if inside((lambda g: g if g.geom_type == 'Point' else g.representative_point())(getg(i)), BOX[k])) for k in ZK + ['CTX']}


conteggi['scuole_MIM_statali'] = cnt([m for m in mim if m['src'] == 'MIM_statale'], lambda m: m['g'])
conteggi['scuole_Comune_paritarie'] = cnt([m for m in mim if m['src'] == 'Comune_paritaria'], lambda m: m['g'])
conteggi['CM_edifici_scolastici_poligoni'] = cnt(list(cm_ed.geometry), lambda g: g)
conteggi['CM_accessi_scolastici_punti'] = cnt(list(cm_acc.geometry), lambda g: g)
conteggi['OSM_scuole_amenity(school|kindergarten|college)'] = cnt(osm_scuole_am, lambda f: f['g'])
conteggi['OSM_scuole_amenity_con_nome'] = cnt([f for f in osm_scuole_am if f['tags'].get('name')], lambda f: f['g'])
conteggi['OSM_building=school_senza_amenity_orfani'] = cnt(osm_build_orfani, lambda f: f['g'])
conteggi['OSM_entrance=*_totali'] = cnt(osm_ent, lambda f: f['g'])

def sedi_distinte(items, tol=30):
    """codici meccanografici diversi allo stesso indirizzo condividono il punto: si contano le sedi (cluster entro tol metri)"""
    cl = []
    for m in items:
        for c in cl:
            if c.distance(m['g']) <= tol:
                break
        else:
            cl.append(m['g'])
    return cl


mim_stat = [m for m in mim if m['src'] == 'MIM_statale']
sedi_stat = sedi_distinte(mim_stat)
sedi_par = sedi_distinte([m for m in mim if m['src'] == 'Comune_paritaria'])
conteggi['sedi_distinte_MIM_statali_(codici_entro_30m_uniti)'] = {k: sum(1 for g in sedi_stat if inside(g, BOX[k])) for k in ZK + ['CTX']}
conteggi['sedi_distinte_paritarie'] = {k: sum(1 for g in sedi_par if inside(g, BOX[k])) for k in ZK + ['CTX']}


def parole(a):
    return {w for w in re.findall(r'[a-zà-ù]{4,}', a.lower()) if w not in ('via', 'viale', 'piazza', 'largo')}


sospette = []
for i, a in enumerate(mim_stat):
    for b in mim_stat[i + 1:]:
        if a['g'].distance(b['g']) < 5 and not (parole(a['ind']) & parole(b['ind'])) and inside(a['g'], BOX['CTX']):
            sospette.append({'codice_a': a['cod'], 'nome_a': a['nome'], 'indirizzo_a': a['ind'], 'codice_b': b['cod'], 'nome_b': b['nome'], 'indirizzo_b': b['ind']})

# ---------------- 2. concordanza MIM/paritarie con OSM e con CM ----------------
rows = []
osm_named_pts = [(f, f['g']) for f in osm_scuole_am]
for m in mim:
    z = zone_of(m['g'])
    if 'CTX' not in z:
        continue
    # OSM più vicina (distanza al poligono)
    best = min(osm_scuole_am, key=lambda f: f['g'].distance(m['g'])) if osm_scuole_am else None
    do = best['g'].distance(m['g']) if best else None
    # CM accessi con lo stesso codice meccanografico
    acc = cm_acc[cm_acc['CODICE'] == m['cod']]
    dacc = min((a.distance(m['g']) for a in acc.geometry), default=None)
    # CM edifici: codice in uno dei cod_csa*
    cols = [c for c in cm_ed.columns if c.startswith('cod_csa')]
    ed = cm_ed[cm_ed[cols].apply(lambda r: m['cod'] in set(r.dropna().astype(str)), axis=1)]
    ded = min((e.distance(m['g']) for e in ed.geometry), default=None)
    # ingressi OSM entro 15 m dal poligono OSM più vicino se entro MATCH_M
    nent = None
    if best is not None and do <= MATCH_M and best['g'].geom_type != 'Point':
        nent = sum(1 for e in osm_ent if best['g'].distance(e['g']) <= 15)
    rows.append({'fonte': m['src'], 'codice': m['cod'], 'nome': m['nome'], 'indirizzo': m['ind'], 'tipologia': m['tip'],
                 'in_FA': int('FA' in z), 'in_FB': int('FB' in z), 'dist_bordo_FA_m': round(dist_bordo(m['g'], BOX['FA'])), 'dist_bordo_FB_m': round(dist_bordo(m['g'], BOX['FB'])),
                 'osm_piu_vicina': (best['tags'].get('name') or best['oid']) if best else '', 'osm_dist_m': round(do) if do is not None else '',
                 'osm_concorda_entro_150m': int(do is not None and do <= MATCH_M),
                 'cm_accessi_stesso_codice': len(acc), 'cm_accesso_dist_m': round(dacc) if dacc is not None else '',
                 'cm_edificio_dist_m': round(ded) if ded is not None else '',
                 'osm_ingressi_entro_15m_poligono': nent if nent is not None else ''})
rows.sort(key=lambda r: (-(r['in_FA'] + r['in_FB']), r['nome']))
with open(OUT + 'scuole_concordanza_fonti.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)

# OSM con nome senza scuola MIM/paritaria entro MATCH_M
solo_osm = []
for f in osm_scuole_am:
    if not inside(f['g'].representative_point(), BOX['CTX']):
        continue
    dm = min(m['g'].distance(f['g']) for m in mim)
    if dm > MATCH_M:
        z = zone_of(f['g'])
        solo_osm.append({'osm': f['oid'], 'nome': f['tags'].get('name', ''), 'amenity': f['tags'].get('amenity'), 'in_FA': int('FA' in z), 'in_FB': int('FB' in z), 'mim_piu_vicina_m': round(dm)})
with open(OUT + 'scuole_solo_osm.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, ['osm', 'nome', 'amenity', 'in_FA', 'in_FB', 'mim_piu_vicina_m']); w.writeheader(); w.writerows(solo_osm)

conc = {}
for k in ZK + ['CTX']:
    sel = [r for r in rows if (r['in_' + k] if k != 'CTX' else 1)]
    conc[k] = {'scuole_MIM_o_paritarie': len(sel), 'con_osm_entro_150m': sum(r['osm_concorda_entro_150m'] for r in sel),
               'con_cm_accesso_stesso_codice': sum(1 for r in sel if r['cm_accessi_stesso_codice'] > 0),
               'senza_alcuna_corrispondenza_osm_cm': sum(1 for r in sel if not r['osm_concorda_entro_150m'] and r['cm_accessi_stesso_codice'] == 0)}
    conc[k]['osm_senza_mim'] = sum(1 for s in solo_osm if (s['in_' + k] if k != 'CTX' else 1))

# ---------------- 3. università: Polo delle Scienze Sociali ----------------
polo = [f for f in osm_univ if 'Polo delle Scienze Sociali' in (f['tags'].get('name') or '') and f['g'].geom_type in ('Polygon', 'MultiPolygon')]
polo_u = unary_union([f['g'] for f in polo])
univ_rows = []
for f in sorted(osm_univ, key=lambda f: f['tags'].get('name', '')):
    if f['g'].geom_type == 'Point':
        gg = f['g']
    else:
        gg = f['g'].representative_point()
    if not inside(gg, BOX['CTX']):
        continue
    nent = sum(1 for e in osm_ent if f['g'].distance(e['g']) <= 15) if f['g'].geom_type != 'Point' else ''
    univ_rows.append({'osm': f['oid'], 'nome': f['tags'].get('name', ''), 'amenity': f['tags'].get('amenity', ''), 'building': f['tags'].get('building', ''),
                      'tipo_geom': f['g'].geom_type, 'area_m2': round(f['g'].area) if f['g'].geom_type != 'Point' else '',
                      'polo_scienze_sociali': int(f in polo), 'in_FA': int(inside(gg, BOX['FA'])), 'in_FB': int(inside(gg, BOX['FB'])),
                      'dist_bordo_FA_m': round(dist_bordo(gg, BOX['FA'])), 'dist_bordo_FB_m': round(dist_bordo(gg, BOX['FB'])), 'ingressi_osm_entro_15m': nent})
with open(OUT + 'universita_osm.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, univ_rows[0].keys()); w.writeheader(); w.writerows(univ_rows)
polo_c = polo_u.centroid
polo_ent = [e for e in osm_ent if polo_u.distance(e['g']) <= 15]
polo_info = {'poligoni_osm': [f['oid'] + ' ' + (f['tags'].get('name') or '') for f in polo], 'area_m2': round(polo_u.area),
             'centroide_lonlat': [round(x, 6) for x in Ti.transform(polo_c.x, polo_c.y)],
             'ingressi_osm_entro_15m': len(polo_ent),
             'ingressi_tipi': dict(collections.Counter(e['tags']['entrance'] for e in polo_ent)),
             'ingressi_con_accessibilita_wheelchair': sum(1 for e in polo_ent if 'wheelchair' in e['tags'])}
for k in ZK + ['CTX']:
    polo_info['centroide_dist_bordo_' + k + '_m'] = round(dist_bordo(polo_c, BOX[k])) if k != 'CTX' else round(dist_bordo(polo_c, BOX['CTX']))
    polo_info['ingressi_dentro_' + k] = sum(1 for e in polo_ent if inside(e['g'], BOX[k]))
    polo_info['quota_area_polo_dentro_' + k] = round(polo_u.intersection(BOX[k]).area / polo_u.area, 2)

# ---------------- 4. fermate ----------------
def gtfs_active(gd):
    cal = {}
    if os.path.exists(gd + '/calendar.txt'):
        wd = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][datetime.datetime.strptime(DATA_SERVIZIO, '%Y%m%d').weekday()]
        for r in csv.DictReader(open(gd + '/calendar.txt')):
            if r['start_date'] <= DATA_SERVIZIO <= r['end_date'] and r[wd] == '1':
                cal[r['service_id']] = True
    for r in csv.DictReader(open(gd + '/calendar_dates.txt')):
        if r['date'] == DATA_SERVIZIO:
            if r['exception_type'] == '1':
                cal[r['service_id']] = True
            else:
                cal.pop(r['service_id'], None)
    return set(cal)


def gtfs_analysis(gd, nome):
    stops = {r['stop_id']: r for r in csv.DictReader(open(gd + '/stops.txt', encoding='utf-8-sig'))}
    sg = {}
    for sid, r in stops.items():
        try:
            g = Point(prj(float(r['stop_lon']), float(r['stop_lat'])))
        except ValueError:
            continue
        if inside(g, BOX['CTX']):
            sg[sid] = g
    routes = {r['route_id']: r for r in csv.DictReader(open(gd + '/routes.txt', encoding='utf-8-sig'))}
    act = gtfs_active(gd)
    trips = {}
    for r in csv.DictReader(open(gd + '/trips.txt', encoding='utf-8-sig')):
        if r['service_id'] in act:
            trips[r['trip_id']] = r['route_id']
    dep = collections.Counter(); rts = collections.defaultdict(set)
    for r in csv.DictReader(open(gd + '/stop_times.txt', encoding='utf-8-sig')):
        if r['stop_id'] in sg and r['trip_id'] in trips:
            dep[r['stop_id']] += 1
            rt = routes[trips[r['trip_id']]]
            rts[r['stop_id']].add(rt.get('route_short_name') or rt['route_id'])
    rows = []
    for sid, g in sg.items():
        rows.append({'feed': nome, 'stop_id': sid, 'nome': stops[sid]['stop_name'], 'lon': stops[sid]['stop_lon'], 'lat': stops[sid]['stop_lat'],
                     'in_FA': int(inside(g, BOX['FA'])), 'in_FB': int(inside(g, BOX['FB'])),
                     'dist_bordo_FA_m': round(dist_bordo(g, BOX['FA'])), 'dist_bordo_FB_m': round(dist_bordo(g, BOX['FB'])),
                     'partenze_giorno': dep[sid], 'linee': ' '.join(sorted(rts[sid]))})
    return rows, len(act), len(trips)


g_rows, g_act, g_trips = gtfs_analysis(RAW + '/gest', 'GEST_tram')
a_rows, a_act, a_trips = gtfs_analysis(RAW + '/gtfs_at', 'AT_bus')
fer_rows = g_rows + a_rows
fer_rows.sort(key=lambda r: (r['feed'], r['nome']))
with open(OUT + 'fermate_gtfs_contesto.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fer_rows[0].keys()); w.writeheader(); w.writerows(fer_rows)
feed_info = open(RAW + '/gtfs_at/feed_info.txt').read().splitlines()[1]
gest_dates = sorted({r['date'] for r in csv.DictReader(open(RAW + '/gest/calendar_dates.txt'))})

fermate = {}
for feed in ('GEST_tram', 'AT_bus'):
    for k in ZK + ['CTX']:
        sel = [r for r in fer_rows if r['feed'] == feed and (r['in_' + k] if k != 'CTX' else 1)]
        att = [r for r in sel if r['partenze_giorno'] > 0]
        linee = set(l for r in att for l in r['linee'].split())
        fermate[f'{feed}_{k}'] = {'fermate_nel_feed': len(sel), 'fermate_con_servizio_il_giorno': len(att), 'linee_con_servizio': sorted(linee), 'n_linee': len(linee)}

# OSM fermate (nodi: tram_stop / bus_stop). Le piattaforme/posizioni sono dello stesso palo: si contano i nodi con tag principale.
osm_tram = [f for f in OSM if f['g'].geom_type == 'Point' and f['tags'].get('railway') == 'tram_stop']
osm_bus = [f for f in OSM if f['g'].geom_type == 'Point' and f['tags'].get('highway') == 'bus_stop']
osm_ferm = {}
for nome, L in (('OSM_tram_stop', osm_tram), ('OSM_bus_stop', osm_bus)):
    for k in ZK + ['CTX']:
        sel = [f for f in L if inside(f['g'], BOX[k])]
        osm_ferm[f'{nome}_{k}'] = {'nodi': len(sel), 'nomi_distinti': len({f['tags'].get('name', '') for f in sel})}

# candidata tram: fermate GEST nel contesto, con elementi OSM entro 40 m
tram_cand = []
for r in g_rows:
    g = Point(prj(float(r['lon']), float(r['lat'])))
    near = [f for f in OSM if f['g'].distance(g) <= 40 and (f['tags'].get('railway') in ('tram_stop', 'platform') or f['tags'].get('public_transport') in ('platform', 'stop_position')) and (f['tags'].get('tram') == 'yes' or f['tags'].get('railway') in ('tram_stop', 'platform'))]
    tram_cand.append({**{k: r[k] for k in ('stop_id', 'nome', 'lon', 'lat', 'partenze_giorno', 'linee', 'in_FA', 'in_FB', 'dist_bordo_FA_m', 'dist_bordo_FB_m')},
                      'osm_elementi_entro_40m': len(near)})
with open(OUT + 'tram_candidate.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, tram_cand[0].keys()); w.writeheader(); w.writerows(tram_cand)

# ---------------- 5. Careggi ----------------
ho = json.load(open(RAW + '/osm_careggi.json'))['elements']
hosp = {}
for e in ho:
    if e['type'] == 'way' and e.get('geometry'):
        c = [prj(p['lon'], p['lat']) for p in e['geometry']]
        if len(c) >= 4 and c[0] == c[-1]:
            hosp[e['tags'].get('name', str(e['id']))] = (f"w{e['id']}", Polygon(c))
careggi = {}
for nome, (oid, pg) in hosp.items():
    if 'Careggi' in nome or 'Traumatologico' in nome or 'Meyer' in nome:
        careggi[nome] = {'osm': oid, 'area_m2': round(pg.area), **{f'dist_{k}_m': round(BOX[k].distance(pg)) for k in ZK},
                         'bordo_riquadro_dentro_poligono': {k: bool(BOX[k].intersects(pg)) for k in ZK},
                         'centroide_dist_centro_FA_m': round(pg.centroid.distance(BOX['FA'].centroid)), 'centroide_dist_centro_FB_m': round(pg.centroid.distance(BOX['FB'].centroid))}

# ---------------- 6. candidati e riquadro corretto ----------------
cand = []
for r in rows:
    if r['fonte'] == 'MIM_statale':
        cand.append({'tipo': 'scuola', 'nome': r['nome'], 'codice': r['codice'], 'FA': r['dist_bordo_FA_m'], 'FB': r['dist_bordo_FB_m']})
cand.append({'tipo': 'università', 'nome': 'Polo delle Scienze Sociali (centroide)', 'codice': 'OSM', 'FA': polo_info['centroide_dist_bordo_FA_m'], 'FB': polo_info['centroide_dist_bordo_FB_m']})
for r in tram_cand:
    cand.append({'tipo': 'tram', 'nome': f"{r['nome']} ({r['linee']})", 'codice': r['stop_id'], 'FA': r['dist_bordo_FA_m'], 'FB': r['dist_bordo_FB_m']})
top = {}
for k in ZK:
    for tipo in ('scuola', 'università', 'tram'):
        L = sorted([c for c in cand if c['tipo'] == tipo and c[k] > 0], key=lambda c: -c[k])[:5]
        top[f'{k}_{tipo}'] = L

geom_riquadri = {}
for k in ZK + ['CTX']:
    b = BOX[k]; x0, y0, x1, y1 = b.bounds
    geom_riquadri[k] = {'area_km2': round(b.area / 1e6, 3), 'larghezza_m': round(x1 - x0), 'altezza_m': round(y1 - y0), 'semilato_minimo_m': round(min(x1 - x0, y1 - y0) / 2)}


def riquadro_centrato(lon, lat, semilato=710):
    x, y = prj(lon, lat)
    lo0, la0 = Ti.transform(x - semilato, y - semilato); lo1, la1 = Ti.transform(x + semilato, y + semilato)
    return [round(la0, 5), round(lo0, 5), round(la1, 5), round(lo1, 5)]  # S,W,N,E


def contenuto_riquadro(bb):
    s, w, n, e = bb; b = gprj(box(w, s, e, n))
    return {'area_km2': round(b.area / 1e6, 2),
            'scuole_MIM_statali': sum(1 for m in mim if m['src'] == 'MIM_statale' and inside(m['g'], b)),
            'scuole_paritarie': sum(1 for m in mim if m['src'] == 'Comune_paritaria' and inside(m['g'], b)),
            'fermate_tram_GEST': sum(1 for r in g_rows if r['partenze_giorno'] > 0 and inside(Point(prj(float(r['lon']), float(r['lat']))), b)),
            'fermate_bus_AT_con_servizio': sum(1 for r in a_rows if r['partenze_giorno'] > 0 and inside(Point(prj(float(r['lon']), float(r['lat']))), b)),
            'polo_scienze_sociali_quota_area_dentro': round(polo_u.intersection(b).area / polo_u.area, 2),
            'careggi_dist_m': round(b.distance(hosp['Azienda Ospedaliera Universitaria di Careggi'][1]))}


proposte = {}
nome_sede = {}
for m in mim_stat:
    nome_sede.setdefault((round(m['g'].x), round(m['g'].y)), []).append(m)
centri_scan = [('scuola ' + ' / '.join(sorted({x['nome'].strip('\"') for x in v})), v[0]['g']) for v in nome_sede.values() if inside(v[0]['g'], BOX['CTX'])]
centri_scan.append(('università Polo Scienze Sociali', polo_c))
centri_scan += [('tram ' + r['nome'] + ' ' + r['linee'], Point(prj(float(r['lon']), float(r['lat'])))) for r in g_rows]
with open(OUT + 'scansione_riquadri_centrati.csv', 'w', newline='') as fh:
    out = []
    for nome, g in centri_scan:
        lon, lat = Ti.transform(g.x, g.y)
        bb = riquadro_centrato(lon, lat)
        c = contenuto_riquadro(bb)
        sedi = sum(1 for q in sedi_stat if inside(q, gprj(box(bb[1], bb[0], bb[3], bb[2]))))
        out.append({'centro': nome, 'lon': round(lon, 6), 'lat': round(lat, 6), 'bbox_SWNE': ' '.join(map(str, bb)), 'sedi_scolastiche_statali': sedi, **c})
    out.sort(key=lambda r: (-r['sedi_scolastiche_statali'], -r['fermate_tram_GEST']))
    w = csv.DictWriter(fh, out[0].keys()); w.writeheader(); w.writerows(out)
# centri candidati: scelti dopo aver letto top{} (vedi REPORT.md); sono parametri, non risultati
CENTRI = json.load(open(HERE + '/centri_proposta.json')) if os.path.exists(HERE + '/centri_proposta.json') else {}
for nome, (lon, lat) in CENTRI.items():
    bb = riquadro_centrato(lon, lat)
    proposte[nome] = {'centro_lonlat': [lon, lat], 'bbox_SWNE': bb, **contenuto_riquadro(bb)}

res = {'data_servizio_gtfs': DATA_SERVIZIO, 'feed_info_AT': feed_info, 'gest_date_calendar_dates': [gest_dates[0], gest_dates[-1], len(gest_dates)],
       'gtfs_attivi': {'GEST_servizi': g_act, 'GEST_corse': g_trips, 'AT_servizi': a_act, 'AT_corse': a_trips},
       'geometria_riquadri': geom_riquadri, 'conteggi_scuole': conteggi, 'coordinate_mim_sospette': sospette, 'concordanza_scuole': conc, 'universita_polo': polo_info,
       'fermate_gtfs': fermate, 'fermate_osm': osm_ferm, 'careggi': careggi, 'candidati_top5_distanza_dal_bordo': top, 'proposte_riquadro_2km2': proposte}
json.dump(res, open(OUT + 'risultati.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
