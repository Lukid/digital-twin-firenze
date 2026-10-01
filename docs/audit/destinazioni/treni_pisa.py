#!/usr/bin/env python3
"""Estratto GTFS Trenitalia: stazioni di Pisa e passaggi del 2026-10-01. uso: treni_pisa.py <cartella GTFS> <file di uscita>"""
import csv, sys, collections
D, OUT = sys.argv[1] + '/', sys.argv[2]
TODAY = '20261001'
tr = {r['trip_id']: r for r in csv.DictReader(open(D + 'trips.txt'))}
dates = set(); on = set()
for r in csv.DictReader(open(D + 'calendar_dates.txt')):
    dates.add(r['date'])
    if r['date'] == TODAY and r['exception_type'] == '1': on.add(r['service_id'])
act = {t for t, r in tr.items() if r['service_id'] in on}
st = [r for r in csv.DictReader(open(D + 'stops.txt')) if r['stop_name'].startswith('Pisa')]
ids = {r['stop_id']: r for r in st}; n = collections.Counter()
for r in csv.DictReader(open(D + 'stop_times.txt')):
    if r['stop_id'] in ids and r['trip_id'] in act: n[r['stop_id']] += 1
w = csv.writer(open(OUT, 'w', newline='')); w.writerow(['stop_id', 'nome', 'lat', 'lon', 'passaggi_2026-10-01', 'calendar_dates_da', 'calendar_dates_a', 'calendar.txt_presente'])
import os
for i, r in ids.items(): w.writerow([i, r['stop_name'], r['stop_lat'], r['stop_lon'], n[i], min(dates), max(dates), os.path.exists(D + 'calendar.txt')])
