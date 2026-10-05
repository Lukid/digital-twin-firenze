#!/usr/bin/env python3
"""Prova ogni URL di risorsa dei dataset di layers.py con GET parziale (Range 0-65535, segue i redirect).
Registra codice, URL finale, tipo, dimensione dichiarata e primi byte. Dedup degli URL WMS. Scarica intero solo il GTFS del tram (circa 1 MB)."""
import json, os, urllib.request, urllib.error, hashlib, datetime, zipfile, io, csv
from concurrent.futures import ThreadPoolExecutor
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "..", "..", "research")
UA = {"User-Agent": "Mozilla/5.0 (audit)", "Range": "bytes=0-65535"}
pk = json.load(open(os.path.join(R, "ckan-toscana-fi-pacchetti.json")))
EXTRA = {  # fonti fuori da CKAN o richiamate dalle schede
 "OSM, estratto Geofabrik Italia centro": "https://download.geofabrik.de/europe/italy/centro-latest.osm.pbf",
 "OSM, copyright": "https://www.openstreetmap.org/copyright",
 "MIM, portale dati scuola (home)": "https://dati.istruzione.it/opendata/",
 "Geoscopio, WMS CTR": "http://www502.regione.toscana.it/geoscopio/servizi/wms/CTR.htm",
}
def sniff(b):
    if b[:2] == b"PK": return "zip"
    if b[:1] in (b"{", b"["): return "json"
    t = b[:600].lower()
    if b"pagina di errore" in t or b"<html" in t or b"<!doctype html" in t: return "html"
    if b[:5] == b"<?xml" or b[:1] == b"<": return "xml"
    return "binario/testo"
def probe(item):
    lab, url = item
    q = url
    if "request=GetCapabilities" in url or "wms" in url.lower() and "?" in url: pass
    t0 = datetime.datetime.now(datetime.timezone.utc)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            b = r.read(65536); h = r.headers
            cr = h.get("Content-Range"); cl = h.get("Content-Length")
            tot = int(cr.split("/")[-1]) if cr and "/" in cr and cr.split("/")[-1].isdigit() else (int(cl) if cl and r.status == 200 else None)
            return {"label": lab, "url": url, "code": r.status, "final_url": r.geturl(), "content_type": h.get("Content-Type"),
                    "dimensione_byte": tot, "range_rispettato": r.status == 206, "primi_byte": sniff(b), "letti": len(b),
                    "last_modified": h.get("Last-Modified"), "disposition": h.get("Content-Disposition"), "ts": t0.isoformat()}
    except urllib.error.HTTPError as e:
        return {"label": lab, "url": url, "code": e.code, "errore": str(e), "ts": t0.isoformat()}
    except Exception as e:
        return {"label": lab, "url": url, "code": None, "errore": str(e)[:200], "ts": t0.isoformat()}
items, seen = [], set()
for n, p in pk["packages"].items():
    for r in p["resources"]:
        u = r["url"]
        if not u or u in seen: continue
        seen.add(u); items.append((n + " | " + (r.get("format") or "?"), u))
for k, u in EXTRA.items():
    if u not in seen: seen.add(u); items.append((k, u))
with ThreadPoolExecutor(6) as ex: res = list(ex.map(probe, items))
json.dump({"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "metodo": "GET con Range 0-65535, redirect seguiti",
           "risultati": res}, open(os.path.join(R, "ckan-toscana-fi-url.json"), "w"), ensure_ascii=False, indent=1)
# GTFS tram completo (circa 1 MB): contenuto e fermate nel riquadro di contesto
gu = next(r["url"] for r in pk["packages"]["rt-oraritb"]["resources"] if r["url"].endswith("gest.gtfs"))
b = urllib.request.urlopen(urllib.request.Request(gu, headers={"User-Agent": "Mozilla/5.0 (audit)"}), timeout=120).read()
open(os.path.join(H, "campioni", "gest.gtfs.zip"), "wb").write(b)
z = zipfile.ZipFile(io.BytesIO(b)); rd = lambda n: list(csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig")))
routes, stops = rd("routes.txt"), rd("stops.txt")
ctx = json.load(open(os.path.join(H, "..", "RIQUADRO.json")))["contesto"]["bbox"]
ins = [s for s in stops if ctx[0] <= float(s["stop_lat"]) <= ctx[2] and ctx[1] <= float(s["stop_lon"]) <= ctx[3]]
cal = rd("calendar.txt") if "calendar.txt" in z.namelist() else []
cd = rd("calendar_dates.txt") if "calendar_dates.txt" in z.namelist() else []
feed = rd("feed_info.txt") if "feed_info.txt" in z.namelist() else []
out = {"file": z.namelist(), "route_type": sorted({r["route_type"] for r in routes}), "routes": [(r["route_short_name"], r["route_long_name"]) for r in routes],
       "fermate_totali": len(stops), "fermate_nel_riquadro_contesto": [(s["stop_name"], s["stop_lat"], s["stop_lon"]) for s in ins],
       "calendar_start_min": min([c["start_date"] for c in cal] + [c["date"] for c in cd], default=None), "calendar_end_max": max([c["end_date"] for c in cal] + [c["date"] for c in cd], default=None),
       "feed_info": feed, "sha256": hashlib.sha256(b).hexdigest(), "byte": len(b), "url": gu}
json.dump(out, open(os.path.join(R, "ckan-toscana-fi-gtfs-tram.json"), "w"), ensure_ascii=False, indent=1)
print(len(res), "URL provati; tram:", out["route_type"], out["fermate_totali"], "fermate,", len(ins), "nel contesto")

# GTFS autolinee (circa 170 MB, ignora Range): scarico intero in GTFS_DIR (default: cartella temporanea), analizzo stops, routes, trips, stop_times
import tempfile, sys
gd = os.environ.get("GTFS_DIR", tempfile.gettempdir()); p = os.path.join(gd, "at.gtfs.zip")
au = next(r["url"] for r in pk["packages"]["rt-oraritb"]["resources"] if "smartregion" in r["url"])
if not os.path.exists(p):
    with urllib.request.urlopen(urllib.request.Request(au, headers={"User-Agent": "Mozilla/5.0 (audit)"}), timeout=600) as r, open(p, "wb") as f:
        while True:
            c = r.read(1 << 20)
            if not c: break
            f.write(c)
h = hashlib.sha256()
with open(p, "rb") as f:
    for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
z = zipfile.ZipFile(p); rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))
stops = list(rd("stops.txt")); routes = {r["route_id"]: r for r in rd("routes.txt")}
sid = {s["stop_id"]: s for s in stops if s["stop_lat"] and ctx[0] <= float(s["stop_lat"]) <= ctx[2] and ctx[1] <= float(s["stop_lon"]) <= ctx[3]}
trips = {t["trip_id"]: t["route_id"] for t in rd("trips.txt")}
rts = {}
for st in rd("stop_times.txt"):
    if st["stop_id"] in sid: rts.setdefault(trips.get(st["trip_id"]), set()).add(st["stop_id"])
cal = list(rd("calendar.txt")); cd = list(rd("calendar_dates.txt")); fi = list(rd("feed_info.txt")); ag = list(rd("agency.txt"))
bus = {"url": au, "byte": os.path.getsize(p), "sha256": h.hexdigest(), "agenzie": sorted({a["agency_name"] for a in ag}), "route_type_conteggio": {},
       "fermate_totali": len(stops), "fermate_nel_riquadro_contesto": len(sid), "linee_che_servono_il_riquadro": len(rts),
       "linee_riquadro_per_tipo": {}, "linee_riquadro_esempi": sorted({(routes[r]["route_short_name"], routes[r]["route_type"]) for r in rts if r in routes})[:40],
       "calendar_start_min": min([c["start_date"] for c in cal] + [c["date"] for c in cd]), "calendar_end_max": max([c["end_date"] for c in cal] + [c["date"] for c in cd]), "feed_info": fi}
for r in routes.values(): bus["route_type_conteggio"][r["route_type"]] = bus["route_type_conteggio"].get(r["route_type"], 0) + 1
for r in rts:
    if r in routes: t = routes[r]["route_type"]; bus["linee_riquadro_per_tipo"][t] = bus["linee_riquadro_per_tipo"].get(t, 0) + 1
json.dump(bus, open(os.path.join(R, "ckan-toscana-fi-gtfs-autolinee.json"), "w"), ensure_ascii=False, indent=1)
print("autolinee:", bus["byte"], "byte;", bus["fermate_nel_riquadro_contesto"], "fermate nel contesto;", bus["linee_che_servono_il_riquadro"], "linee")
