"""Costruisce z2_campione.geojson dai campioni in docs/audit (sola lettura).
Uso: docs/audit/edifici/.venv/bin/python costruisci_campione.py   (serve pyproj, shapely)
Coordinate in EPSG:7791 (RDN2008 / UTM 32N, assi E,N). Le fonti consegnano lon/lat: si trattano
come equivalenti a RDN2008 geografico (differenza attesa sotto 1 m, non misurata qui)."""
import csv, hashlib, json, math, pathlib
from pyproj import Transformer
from shapely.geometry import Point, LineString, Polygon

A = pathlib.Path(__file__).resolve().parents[2] / "docs" / "audit"
T = Transformer.from_crs(4326, 7791, always_xy=True)
r2 = lambda v: round(v, 2)
def en(lon, lat): x, y = T.transform(lon, lat); return [r2(x), r2(y)]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

cand = json.load(open(A/"destinazioni/campioni/candidati_caso_A.json"))["Z2"]
school_lat, school_lon = cand["centro_osm"]
school = Point(*en(school_lon, school_lat))
feats = []
def add(geom, **props): feats.append({"type": "Feature", "geometry": geom, "properties": props})
pt = lambda c: {"type": "Point", "coordinates": c}

# scuola (destinazione) e ingressi OSM, non verificati
add(pt(en(school_lon, school_lat)), id="dst_school_piee82101p", layer="destination", source_id="src_osm_pisa",
    name="Scuola Primaria C. Battisti", category="school", mim_code="PIEE82101P", verification="desk_candidate",
    orig_wgs84=[school_lon, school_lat],
    cls={"name": "measured", "category": "derived", "mim_code": "measured", "verification": "derived", "orig_wgs84": "measured"})
for e in cand["ingressi_osm_nel_bbox"]:
    if e["id"] in (6532183886, 5101368983, 13804118745):
        add(pt(en(e["lon"], e["lat"])), id=f"ent_osm_n{e['id']}", layer="entrance", source_id="src_osm_pisa",
            destination_id="dst_school_piee82101p", osm_entrance=e["tag"]["entrance"], verification="unverified",
            orig_wgs84=[e["lon"], e["lat"]], cls={"osm_entrance": "measured", "verification": "derived", "orig_wgs84": "measured"})

# fermate GTFS
for row in csv.DictReader(open(A/"destinazioni/campioni/gtfs_fermate_zone.csv")):
    if row["stop_code"] in ("PI4390", "PI4389", "PI4074"):
        lon, lat = float(row["lon"]), float(row["lat"])
        add(pt(en(lon, lat)), id=f"dst_stop_{row['stop_code'].lower()}", layer="stop", source_id="src_gtfs_at_toscana",
            name=row["nome"], stop_code=row["stop_code"], trips_on_2026_10_01=int(row["corse_oggi"]), lines=row["linee_oggi"],
            wheelchair_boarding="unknown", orig_wgs84=[lon, lat],
            cls={"name": "measured", "stop_code": "measured", "trips_on_2026_10_01": "derived", "lines": "derived",
                 "wheelchair_boarding": "measured", "orig_wgs84": "measured"})

# tratti di rete e attraversamenti OSM entro 130 m dalla scuola
osm = json.load(open(A/"rete/campioni/osm_Z2.json"))["elements"]
ways = []
for w in osm:
    if w["type"] == "way" and "highway" in w.get("tags", {}) and "geometry" in w:
        ls = LineString([en(p["lon"], p["lat"]) for p in w["geometry"]])
        if ls.distance(school) <= 130 and ls.length <= 400:
            ways.append((ls.distance(school), w, ls))
ways.sort(key=lambda t: t[0])
for _, w, ls in ways[:8]:
    t = w["tags"]
    add({"type": "LineString", "coordinates": [list(map(r2, c)) for c in ls.coords]}, id=f"way_osm_{w['id']}", layer="network_edge",
        source_id="src_osm_pisa", highway=t["highway"], name=t.get("name", ""), sidewalk_tags=t.get("sidewalk", ""),
        length_m=r2(ls.length), cls={"highway": "measured", "name": "measured", "sidewalk_tags": "measured", "length_m": "derived"})
cr = []
for n in osm:
    if n["type"] == "node" and n.get("tags", {}).get("highway") == "crossing":
        p = Point(*en(n["lon"], n["lat"]))
        if p.distance(school) <= 150: cr.append((p.distance(school), n, p))
cr.sort(key=lambda t: t[0])
for _, n, p in cr[:3]:
    add(pt([r2(p.x), r2(p.y)]), id=f"nod_osm_{n['id']}", layer="crossing", source_id="src_osm_pisa",
        crossing=n["tags"].get("crossing", ""), tactile_paving=n["tags"].get("tactile_paving", ""),
        orig_wgs84=[n["lon"], n["lat"]], cls={"crossing": "measured", "tactile_paving": "measured", "orig_wgs84": "measured"})

# unità volumetriche regionali (volo 2010): le 8 più vicine alla scuola
uv = json.load(open(A/"edifici/campioni/rt_uv_Z2.json"))
cs = []
for u in uv:
    ring = [en(x, y) for x, y in u["polys"][0][0]]
    pg = Polygon(ring)
    cs.append((pg.distance(school), u, ring, pg))
cs.sort(key=lambda t: t[0])
for _, u, ring, pg in cs[:8]:
    add({"type": "Polygon", "coordinates": [[list(map(r2, c)) for c in ring]]}, id=f"bld_rt_{u['uv_id']}", layer="building_volume",
        source_id="src_rt_unita_volumetriche", edifc_id=u["edifc_id"], height_m=float(u["uv_av"]), ground_elev_m=float(u["uv_qs"]),
        roof_elev_m=float(u["uv_qe"]), area_m2=r2(pg.area), survey_year=int(u["anno"]),
        cls={"edifc_id": "measured", "height_m": "measured", "ground_elev_m": "measured", "roof_elev_m": "measured",
             "area_m2": "derived", "survey_year": "measured"})

fc = {"type": "FeatureCollection", "name": "z2_campione",
      "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::7791"}},
      "conventions": {"crs": "EPSG:7791", "axis_order": "E,N", "unit": "m", "vertical_datum": "not_confirmed", "timezone": "Europe/Rome"},
      "provenance": [{"source_id": s, "file": f, "sha256": sha(A/f)} for s, f in [
          ("src_osm_pisa", "rete/campioni/osm_Z2.json"), ("src_osm_pisa", "destinazioni/campioni/candidati_caso_A.json"),
          ("src_gtfs_at_toscana", "destinazioni/campioni/gtfs_fermate_zone.csv"), ("src_rt_unita_volumetriche", "edifici/campioni/rt_uv_Z2.json")]],
      "features": feats}
out = pathlib.Path(__file__).with_name("z2_campione.geojson")
out.write_text(json.dumps(fc, ensure_ascii=False, indent=1))
from collections import Counter
print(out.name, len(feats), dict(Counter(f["properties"]["layer"] for f in feats)))
