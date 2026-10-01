#!/usr/bin/env python3
"""T08: prepara scene/data/ dagli output versionati di geometry/, network/, analysis/out/ e analysis/manifest/.
Eseguire dalla radice: pipeline/.venv/bin/python scene/build.py
Dipendenze NON versionate (data/norm/): grafo rete_z2.gpkg (archi per lo stato del marciapiede, assenti negli output versionati)
e le tabelle origini per profilo di T06 (verificate con lo sha256 del manifest). Senza di esse il build si ferma."""
import csv, hashlib, json, math, os, shutil, statistics
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "scene", "data")
os.makedirs(OUT, exist_ok=True)
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
r6 = lambda v: round(v, 6)
def rnd(c): return [rnd(x) for x in c] if isinstance(c[0], list) else [r6(c[0]), r6(c[1])]
def dump(name, obj):
    p = os.path.join(OUT, name)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{name:28s} {os.path.getsize(p)//1024:5d} KB")
FC = lambda fs, **k: {"type": "FeatureCollection", **k, "features": fs}
F = lambda g, p: {"type": "Feature", "geometry": g, "properties": p}

# ---- ipotesi dichiarate (stesse nel legend e nelle schede)
SPESSORE_SOLETTA = (0.4, 0.2, 0.8)   # m, tipico/min/max: copertura OSM = soletta sottile, imposta = quota tetto - spessore
TRONCO_MIN_RESO = 0.6                # m, diametro minimo di resa del tronco (reale 0,3 m: sarebbe invisibile)
POLI_CHIOMA, POLI_TRONCO = 14, 8

# ---- edifici (T05)
ed = J("geometry/edifici_z2.geojson")["features"]
riep = J("analysis/out/riepilogo.json")
out = []
for f in ed:
    p = f["properties"]
    q = {k: p[k] for k in ("id", "tipo", "classe_h", "fonte", "z_base", "h", "h_min", "h_max", "area_m2", "anno", "flag", "portico", "sospeso")}
    if p["tipo"] == "copertura_osm":   # volume sospeso: base = tetto - spessore soletta (stima), h in scena = spessore
        q["sosp"] = 1
        q["imp"] = round(p["h"] - SPESSORE_SOLETTA[0], 2)
        q["imp_min"] = round(p["h_min"] - SPESSORE_SOLETTA[2], 2)
        q["imp_max"] = round(p["h_max"] - SPESSORE_SOLETTA[1], 2)
    else:
        q["imp"] = 0
    out.append(F({"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}, q))
dump("edifici.geojson", FC(out))
n_edifici, n_sosp = len(out), sum(1 for f in out if f["properties"].get("sosp"))

# ---- alberi (T05): tronco e chioma come prismi, dimensioni stimate
al = J("geometry/alberi_z2.geojson")["features"]
def poligono(lon, lat, d, n):
    kx, ky = 111320 * math.cos(math.radians(lat)), 110540
    return [[r6(lon + d / 2 * math.cos(2 * math.pi * i / n) / kx), r6(lat + d / 2 * math.sin(2 * math.pi * i / n) / ky)] for i in range(n)] + [None]
out = []
for f in al:
    p = f["properties"]; lon, lat = f["geometry"]["coordinates"]
    comune = {k: p[k] for k in ("id", "fonti", "h_cls", "z_base", "h", "h_min", "h_max", "chioma_d", "chioma_d_min", "chioma_d_max", "imposta", "imposta_min", "imposta_max", "tronco_d")}
    for parte, d, n in (("tronco", max(p["tronco_d"], TRONCO_MIN_RESO), POLI_TRONCO), ("chioma", p["chioma_d"], POLI_CHIOMA)):
        ring = poligono(lon, lat, d, n); ring[-1] = ring[0]
        out.append(F({"type": "Polygon", "coordinates": [ring]}, {**comune, "parte": parte}))
dump("alberi.geojson", FC(out))
n_alberi = len(out) // 2

# ---- grafo T04 per stato del marciapiede, percorsi campione, ingressi
import geopandas as gpd
gp = os.path.join(ROOT, "data/norm/network/rete_z2.gpkg")
assert os.path.exists(gp), "manca data/norm/network/rete_z2.gpkg: eseguire network/build.sh"
a = gpd.read_file(gp, layer="archi").to_crs(4326)
S, W, N, E = 90, 180, -90, -180
for f in ed:
    for ring in ([f["geometry"]["coordinates"][0]] if f["geometry"]["type"] == "Polygon" else [p[0] for p in f["geometry"]["coordinates"]]):
        for x, y in ring: S, W, N, E = min(S, y), min(W, x), max(N, y), max(E, x)
from shapely.geometry import box
a = a[a.intersects(box(W, S, E, N))]
dump("rete.geojson", FC([F({"type": "LineString", "coordinates": [[r6(x), r6(y)] for x, y in g.coords]},
    {"id": x.edge_id, "tipo": x.tipo_arco, "hw": x.highway, "nome": x["name"] if isinstance(x["name"], str) else "", "mc": x.marciapiede_stato, "m": round(x.length_m, 1)})
    for _, x in a.iterrows() for g in [x.geometry] if g.geom_type == "LineString"]))
perc = J("network/percorsi_campione.geojson")
dump("percorsi.geojson", FC([F({"type": "LineString", "coordinates": rnd(f["geometry"]["coordinates"])}, {k: v for k, v in f["properties"].items()}) for f in perc["features"]]))
ing = J("network/destinazioni_ingressi.geojson")
dump("ingressi.geojson", FC([F({"type": "Point", "coordinates": rnd(f["geometry"]["coordinates"])}, f["properties"]) for f in ing["features"]
    if f["geometry"]["type"] == "Point" and f["properties"]["classe"] != "ingresso_fermata"]))

# ---- risultati T06: civici, tempi per profilo, dettagli
PROF = [("base_1_2", 1.2, "allowed"), ("lento_0_8", 0.8, "allowed"), ("rapido_1_4", 1.4, "allowed"), ("ridotta_0_8_senza_scale", 0.8, "excluded")]
DEST = {"b": ("battisti", "dst_school_piee82101p"), "p": ("pellico", "dst_stop_pi4390")}
manifests = {}
for fn in sorted(os.listdir(os.path.join(ROOT, "analysis/manifest"))):
    if fn.endswith(".manifest.json"):
        m = J("analysis/manifest/" + fn); manifests[m["job_id"]] = m
os.makedirs(os.path.join(OUT, "manifest"), exist_ok=True)
meta = {"dest": {}, "soglie_min": riep["soglie_min"], "profili": [], "riepilogo": {}, "limiti": [], "ipotesi": {
    "spessore_soletta_m": SPESSORE_SOLETTA, "tronco_min_reso_m": TRONCO_MIN_RESO}}
civici, det, tempo = {}, {}, {}
archi = []
for dk, (dname, dst) in DEST.items():
    gj = J(f"analysis/out/accessibilita_{dname}.geojson")
    meta["dest"][dk] = {"nome": dname, "destination_id": dst, "jobs": []}
    jobs = []
    for i, (pk, speed, stairs) in enumerate(PROF):
        jid = riep["destinazioni"][dname][pk]["job_id"]
        m = manifests[jid]; pr = m["params"]["profile"]
        assert dst in m["params"]["destination_ids"] and pr["speed_m_s"] == speed and pr["stairs"] == stairs, (jid, pk)
        shutil.copy(os.path.join(ROOT, f"analysis/manifest/{jid}.manifest.json"), os.path.join(OUT, "manifest", f"{jid}.manifest.json"))
        meta["dest"][dk]["jobs"].append({"job_id": jid, "manifest_id": m["manifest_id"], "validation": m["validation_status"], "finished_at": m["timing"]["finished_at"],
            "speed": speed, "stairs": stairs, "crossing_penalty_s": pr["crossing_penalty_s"], "snap_limit_m": pr["snap_limit_m"], "entrance_ids": m["params"]["entrance_ids"],
            "method": m["method"]["name"] + " " + m["method"]["version"], "graph": m["params"]["graph"]["graph_id"], "datasets": m["datasets"]})
        if not meta["limiti"]: meta["limiti"] = m["limits"]
        csvp = next(x["path"] for x in m["assets"] if x["asset_id"] == "ast_origini_csv")
        raw = open(os.path.join(ROOT, csvp), "rb").read()
        assert hashlib.sha256(raw).hexdigest() == next(x["sha256"] for x in m["assets"] if x["asset_id"] == "ast_origini_csv"), "sha256 CSV non coincide con il manifest " + csvp
        for row in csv.DictReader(raw.decode().splitlines()):
            if row["stato"] == "reachable":
                det.setdefault(row["origin_id"], {}).setdefault(dk, [None] * 4)[i] = [round(float(row["totale_m"])), int(row["attraversamenti"]), round(float(row["m_marciapiede_ignoto"])), int(row["scale"]), int(row["sottopassi"]), float(row["deviazione"])]
                tempo.setdefault(row["origin_id"], {}).setdefault(dk, [None] * 4)[i] = round(float(row["tempo_s"]) / 60, 4)
        rr = riep["destinazioni"][dname][pk]
        meta["riepilogo"][f"{dk}{i}"] = {"conteggi": rr["conteggi"], "quote": rr["quote"], "tempo": rr["tempo_min"], "ign": rr["quota_ignoto"], "att_med": rr["attraversamenti_mediana"],
            "rete_p50": rr["rete_m_p50"], "dev": rr["deviazione"], "dev_alta": rr["deviazione_alta"], "barriere": rr["origini_con_barriera"], "scale": rr["origini_con_scale"], "job_id": rr["job_id"]}
    for f in gj["features"]:
        p = f["properties"]
        if p.get("layer") == "origine":
            c = civici.setdefault(p["id"], {"g": f["geometry"]["coordinates"], "p": {"id": p["id"], "a": p["ind"] if isinstance(p["ind"], str) else "(indirizzo assente nel SIT)"}})
            c["p"]["s" + dk] = p["stato"]
            if p["stato"] != "reachable": c["p"]["m" + dk] = p["motivo"]
        elif p.get("layer") == "arco_usato":
            archi.append(F({"type": "LineString", "coordinates": f["geometry"]["coordinates"]}, {**{k: p[k] for k in ("id", "gruppo", "n_origini", "marciapiede", "nome", "tipo")}, "d": dk}))
        elif p.get("layer") == "destinazione":
            meta["dest"][dk]["xy"] = f["geometry"]["coordinates"]; meta["dest"][dk]["ingresso"] = p["ingresso"]; meta["dest"][dk]["nome_dest"] = p["nome"]
    # coerenza: tempo del geojson (profilo base) = tempo della tabella T06
    for f in gj["features"]:
        p = f["properties"]
        if p.get("layer") == "origine" and p["stato"] == "reachable":
            assert abs(p["t"] - tempo[p["id"]][dk][0]) < 0.06, p["id"]
feats = []
for oid, c in civici.items():
    p = dict(c["p"])
    for dk in DEST:
        if oid in tempo and dk in tempo[oid]:
            for i, t in enumerate(tempo[oid][dk]): p[f"t{dk}{i}"] = t
    feats.append(F({"type": "Point", "coordinates": c["g"]}, p))
dump("civici.geojson", FC(feats))
dump("civici_dettaglio.json", {k: v for k, v in det.items()})
dump("archi_usati.geojson", FC(archi))
meta["bbox"] = [r6(W), r6(S), r6(E), r6(N)]
meta["z2_riferimento"] = {"crs_modello": "EPSG:7791", "crs_web": "EPSG:4326 derivato, coordinate arrotondate a 6 decimali (circa 0,1 m)"}

# ---- controlli di coerenza con i conteggi di riepilogo.json
assert len(civici) == 2224 and len(feats) == 2224
for dk, (dname, _) in DEST.items():
    cnt = {}
    for f in feats: cnt[f["properties"]["s" + dk]] = cnt.get(f["properties"]["s" + dk], 0) + 1
    for pk, _, _ in PROF:
        want = {k: v for k, v in riep["destinazioni"][dname][pk]["conteggi"].items() if v}
        assert cnt == want, (dname, cnt, want)
assert (n_edifici, n_sosp, n_alberi) == (1069, 12, 453), (n_edifici, n_sosp, n_alberi)
dump("meta.json", meta)

# ---- layer ombre T09: vuoto, con il formato atteso
os.makedirs(os.path.join(OUT, "ombre"), exist_ok=True)
dump("ombre/index.json", {"stato": "non_calcolate", "messaggio": "Ombre non ancora calcolate (T09).", "job_id": None, "istanti": [],
    "formato_atteso": {"file": "FeatureCollection GeoJSON EPSG:4326 (derivato dal modello in EPSG:7791), un file per istante, elencato in 'istanti'",
        "istanti": [{"istante": "2026-07-21T14:00:00+02:00 (RFC 3339, Europe/Rome)", "url": "ombre/<job_id>_<AAAAMMGGThhmm>.geojson"}],
        "feature": "Polygon/MultiPolygon: unione delle ombre al suolo a quell'istante",
        "properties": {"job_id": "job_<16 hex>", "istante": "RFC 3339 con offset", "elevazione_solare_gradi": "numero", "classificazione": "derived|estimated|scenario", "ostacoli": "baseline_edifici|edifici_e_alberi_stimati|scenario"}}})
print("OK", meta["bbox"])
