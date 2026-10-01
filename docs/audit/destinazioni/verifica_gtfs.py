#!/usr/bin/env python3
"""Controlli di integrità di base sul feed GTFS decompresso. uso: verifica_gtfs.py <cartella>"""
import csv, sys, collections, datetime
D = sys.argv[1] + '/'
print(open(D + 'feed_info.txt').read())
stops = list(csv.DictReader(open(D + 'stops.txt', encoding='utf-8-sig')))
ids = {s['stop_id'] for s in stops}
print('fermate', len(stops), 'id duplicati', len(stops) - len(ids), 'senza coordinate', sum(1 for s in stops if not s['stop_lat'] or not s['stop_lon']))
print('location_type', dict(collections.Counter(s['location_type'] for s in stops)), 'wheelchair_boarding', dict(collections.Counter(s['wheelchair_boarding'] for s in stops)))
routes = {r['route_id']: r for r in csv.DictReader(open(D + 'routes.txt'))}
print('linee', len(routes), 'route_type', dict(collections.Counter(r['route_type'] for r in routes.values())))
trips = {r['trip_id']: r for r in csv.DictReader(open(D + 'trips.txt'))}
cal = {r['service_id']: r for r in csv.DictReader(open(D + 'calendar.txt'))}
days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
print('corse', len(trips), 'wheelchair_accessible', dict(collections.Counter(t['wheelchair_accessible'] for t in trips.values())))
print('calendar.txt: servizi', len(cal), 'con almeno un giorno settimanale a 1:', sum(1 for r in cal.values() if any(r[d] == '1' for d in days)))
cd = collections.defaultdict(set); exc = collections.Counter()
for r in csv.DictReader(open(D + 'calendar_dates.txt')):
    exc[r['exception_type']] += 1
    if r['exception_type'] == '1': cd[r['date']].add(r['service_id'])
print('calendar_dates eccezioni', dict(exc))
sc = collections.Counter(t['service_id'] for t in trips.values())
for d in sorted(cd):
    print(d, datetime.datetime.strptime(d, '%Y%m%d').strftime('%a'), 'servizi', len(cd[d]), 'corse', sum(sc[s] for s in cd[d]))
print('corse con servizio inesistente', sum(1 for t in trips.values() if t['service_id'] not in cal and t['service_id'] not in cd.keys() and not any(t['service_id'] in v for v in cd.values())))
print('corse con linea inesistente', sum(1 for t in trips.values() if t['route_id'] not in routes))
sh = set()
with open(D + 'shapes.txt') as f:
    next(f)
    for l in f: sh.add(l.split(',', 1)[0])
print('shape', len(sh), 'corse senza shape', sum(1 for t in trips.values() if not t['shape_id']), 'shape referenziate ma mancanti', len({t['shape_id'] for t in trips.values()} - sh))
n = orf_t = orf_s = 0; mx = 0
for r in csv.DictReader(open(D + 'stop_times.txt')):
    n += 1; orf_t += r['trip_id'] not in trips; orf_s += r['stop_id'] not in ids; mx = max(mx, int(r['arrival_time'].split(':')[0]))
print('stop_times', n, 'corse orfane', orf_t, 'fermate orfane', orf_s, 'ora massima', mx)
