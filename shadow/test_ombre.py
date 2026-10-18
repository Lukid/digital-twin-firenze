"""F07: test del motore d'ombra e del sole (area da DT_AOI, default Firenze Novoli). Uso: pipeline/.venv/bin/python shadow/test_ombre.py (asserzioni semplici, nessun framework)."""
import json, math, pathlib, sys, datetime as dt
import numpy as np, shapely
from shapely.geometry import box, Polygon, MultiPolygon, LineString, Point
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ombre as O

ROOT = O.ROOT; LAT, LON = O.SOLE_LAT, O.SOLE_LON; E0, N0, E1, N1 = O.RIQUADRO_EN; CE, CN = (E0 + E1) / 2, (N0 + N1) / 2
ok = lambda nome: print("  ok", nome)


def test_sole_riferimenti():
    # Valori di riferimento calcolati offline con NREL SPA (implementazione numerica in pvlib 0.16.1, quota 4 m, altitudine non rilevante per la
    # geometria), latitudine/longitudine del centro del riquadro (Firenze Novoli). Nessun valore scaricato. Tolleranza 0,05 gradi (NOAA scarta meno di 0,02 gradi).
    ref = [("2026-07-15", "12:00", 136.497, 62.068), ("2026-07-15", "08:00", 80.353, 21.546), ("2026-09-15", "08:00", 96.469, 11.011),
           ("2026-09-15", "19:00", 270.271, 3.801), ("2026-10-25", "12:00", 180.242, 34.015), ("2026-12-21", "12:00", 176.733, 22.695)]
    for d, h, az, el in ref:
        a, e = O.sole(O.locale_a_utc(d, h), LAT, LON)
        assert abs(a - az) < 0.05 and abs(e - el) < 0.05, (d, h, a, e, az, el)
    # controllo analitico indipendente: elevazione massima del giorno = 90 - lat + declinazione, azimut 180 al massimo
    for d, dec in (("2026-06-21", 23.44), ("2026-09-23", 0.0), ("2026-12-21", -23.44)):
        ist = O.istanti_giorno(d, 1); az, el = O.sole([t for t in ist], LAT, LON); k = int(np.argmax(el))
        assert abs(el[k] - (90 - LAT + dec)) < 0.35, (d, el[k]); assert abs(az[k] - 180) < 2, (d, az[k])
    ok("sole: 6 riferimenti SPA e 3 massimi giornalieri analitici")


def test_cambio_ora():
    assert O.locale_a_utc("2026-03-29", "01:30").isoformat() == "2026-03-29T00:30:00+00:00"    # CET, UTC+1
    assert O.locale_a_utc("2026-03-29", "03:30").isoformat() == "2026-03-29T01:30:00+00:00"    # CEST, UTC+2
    assert O.locale_a_utc("2026-10-25", "01:30").isoformat() == "2026-10-24T23:30:00+00:00"    # CEST
    assert O.locale_a_utc("2026-10-25", "03:30").isoformat() == "2026-10-25T02:30:00+00:00"    # CET
    for f, esc in ((lambda: O.locale_a_utc("2026-03-29", "02:30"), O.OraInesistente), (lambda: O.locale_a_utc("2026-10-25", "02:30"), O.OraAmbigua)):
        try: f(); assert False, "doveva fallire"
        except esc: pass
    assert O.locale_a_utc("2026-10-25", "02:30", fold=0).isoformat() == "2026-10-25T00:30:00+00:00"
    assert O.locale_a_utc("2026-10-25", "02:30", fold=1).isoformat() == "2026-10-25T01:30:00+00:00"
    assert [O.locale_a_utc("2026-10-25", "02:30", O.FOLD[k]).isoformat() for k in ("daylight_saving", "standard")] == ["2026-10-25T00:30:00+00:00", "2026-10-25T01:30:00+00:00"]   # when["ambiguous_time"] (F5)
    assert len(O.istanti_giorno("2026-03-29", 15)) == 92 and len(O.istanti_giorno("2026-10-25", 15)) == 100 and len(O.istanti_giorno("2026-09-15", 15)) == 96
    # 12:00 locale del 29/3 (UTC+2) è lo stesso istante UTC di 11:00 locale del 28/3 (UTC+1), a meno di un giorno di moto del sole (< 1 grado)
    a29, e29 = O.sole(O.locale_a_utc("2026-03-29", "12:00"), LAT, LON); a28, e28 = O.sole(O.locale_a_utc("2026-03-28", "11:00"), LAT, LON)
    assert abs(a29 - a28) < 1 and abs(e29 - e28) < 1, (a28, a29)
    a28b, _ = O.sole(O.locale_a_utc("2026-03-28", "12:00"), LAT, LON); assert abs(a28b - a29) > 15       # senza il salto l'azimut sarebbe sbagliato di 15+ gradi
    # culminazione: l'istante UTC di massima elevazione resta (quasi) fisso nei giorni vicini, l'ora locale salta di 1 h
    def culm(d):
        ist = O.istanti_giorno(d, 1); az, el = O.sole(ist, LAT, LON); return ist[int(np.argmax(el))].astimezone(O.ROMA)
    c28, c29 = culm("2026-03-28"), culm("2026-03-29"); salto = (c29.hour * 60 + c29.minute) - (c28.hour * 60 + c28.minute)
    assert 55 < salto < 65, salto
    c24, c25 = culm("2026-10-24"), culm("2026-10-25"); salto = (c25.hour * 60 + c25.minute) - (c24.hour * 60 + c24.minute)
    assert -65 < salto < -55, salto
    ok("cambio ora 29/3 e 25/10/2026: offset, ore inesistenti/ambigue, 92/100 passi, culminazione")


def test_cubo_analitico():
    a, h = 10.0, 10.0
    u = O.ombra_prisma(box(0, 0, a, a), 0, h, 180, 45)            # sole a sud, ombra verso nord lunga 10 m
    assert abs(u.area - 200) < 1e-6 and abs(u.bounds[3] - 20) < 1e-9
    assert abs(u.difference(box(0, 0, a, a)).area - 100) < 1e-6
    az, el = 45, 30                                                   # sole a nord-est: ombra verso sud-ovest
    D = h / math.tan(math.radians(el)); dx = dy = D * math.sin(math.radians(45))
    u = O.ombra_prisma(box(0, 0, a, a), 0, h, az, el)
    assert abs(u.area - (a * a + a * (dx + dy))) < 1e-6, u.area      # somma di Minkowski quadrato + segmento
    assert u.bounds[0] < -dx + 1e-6 and u.bounds[1] < -dy + 1e-6
    # lunghezza dell'ombra = h / tan(elevazione), per elevazioni diverse
    for el in (15, 30, 60, 80):
        u = O.ombra_prisma(box(0, 0, 1, 1), 0, 7, 180, el)
        assert abs((u.bounds[3] - 1) - 7 / math.tan(math.radians(el))) < 1e-9
    # un volume più alto contiene l'ombra di uno più basso (anche con footprint concavo e buchi)
    L = Polygon([(0, 0), (20, 0), (20, 6), (6, 6), (6, 20), (0, 20)])
    c = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)], [[(10, 10), (20, 10), (20, 20), (10, 20)]])   # corte interna
    for g in (L, c):
        for az in (30, 140, 250):
            a_, b_ = O.ombra_prisma(g, 0, 8, az, 22), O.ombra_prisma(g, 0, 12, az, 22)
            assert a_.difference(b_).area < 1e-6
    # corte interna: con sole alto la corte resta in parte al sole, con sole basso è tutta in ombra
    assert not O.ombra_prisma(c, 0, 12, 180, 80).contains(Point(15, 15))      # corte: sole alto, centro al sole (ombra solo 2 m oltre il lato sud)
    assert O.ombra_prisma(c, 0, 12, 180, 80).contains(Point(15, 11))
    assert O.ombra_prisma(c, 0, 12, 180, 10).contains(Point(15, 15))
    ok("cubo: area e lunghezza analitiche, monotonia con l'altezza, corte interna")


def test_volume_sospeso():
    p = box(0, 0, 10, 10)                                             # pensilina 10x10 da 4 a 5 m
    u = O.ombra_prisma(p, 4, 5, 180, 45)
    assert abs(u.area - 110) < 1e-6 and abs(u.bounds[1] - 4) < 1e-9 and abs(u.bounds[3] - 15) < 1e-9
    assert not u.contains(Point(5, 2)) and not u.intersects(Point(5, 3.5)) and u.contains(Point(5, 6))   # suolo sotto: non ombreggiato dal pieno
    pieno = O.ombra_prisma(p, 0, 5, 180, 45)
    assert pieno.contains(Point(5, 2)) and u.difference(pieno).area < 1e-6 and pieno.area > u.area
    z = O.ombra_prisma(p, 4, 5, 180, 89.9)                            # sole allo zenit: il suolo sotto è all'ombra
    assert z.contains(Point(5, 5)) and abs(z.area - 100) < 1.0
    ok("volume sospeso: ombra spostata, suolo sotto libero, zenit = footprint")


def test_unione():
    a, b = box(0, 0, 10, 10), box(5, 0, 15, 10)                      # footprint sovrapposti
    S = O.Scena([a, b], [0, 0], [10, 10]); u = O.ombra_scena(S, 180, 45)
    ua, ub = O.ombra_prisma(a, 0, 10, 180, 45), O.ombra_prisma(b, 0, 10, 180, 45)
    assert abs(u.area - (ua.area + ub.area - ua.intersection(ub).area)) < 1e-6 and abs(u.area - 300) < 1e-6    # 15 x 20, nessun doppio conteggio
    assert abs(O.ombra_scena(O.Scena([a, a, a], [0] * 3, [10] * 3), 180, 45).area - ua.area) < 1e-6              # duplicati: stessa area
    # frazione di percorso con ombre sovrapposte: la lunghezza ombreggiata non supera quella del percorso
    path = LineString([(-2, 14), (17, 14)]); sh = path.intersection(u).length
    assert abs(sh - 15) < 1e-6 and sh <= path.length
    ok("unione: due volumi sovrapposti, duplicati, frazione di percorso")


def test_sole_sotto_orizzonte():
    S = O.Scena([box(0, 0, 10, 10)], [0], [10])
    for d, h in (("2026-06-21", "23:00"), ("2026-10-01", "03:00"), ("2026-12-21", "06:00")):
        st, az, el, g = O.ombra_a_istante(S, O.locale_a_utc(d, h), LAT, LON)
        assert st == O.STATO_NOTTE and g is None and el <= 0, (d, h, st, el)
    try: O.ombra_scena(S, 90, -3); assert False
    except ValueError: pass
    st, az, el, g = O.ombra_a_istante(S, O.locale_a_utc("2026-12-21", "07:45"), LAT, LON)    # alba: sole sotto l'orizzonte o sotto il limite di supporto
    assert st != O.STATO_OK and g is None, (st, el)
    st, az, el, g = O.ombra_a_istante(S, O.locale_a_utc("2026-06-21", "13:00"), LAT, LON)
    assert st == O.STATO_OK and g is not None and el > 60
    ok("sole sotto l'orizzonte e sole troppo basso: stato esplicito, nessuna geometria")


def _canyon():
    # via est-ovest larga 12 m fra due edifici alti 18 m e 14 m (lunghi 80 m), percorso lungo la via e trasversale
    S = O.Scena([box(0, 0, 80, 20), box(0, 32, 80, 52)], [0, 0], [18, 14])
    return S, LineString([(-10, 26), (90, 26)]), LineString([(40, 22), (40, 30)])


def _frazione_media(S, path, step, tipo="esatta", lat=LAT, lon=LON, data="2026-09-15", t_da=8 * 60, t_a=18 * 60):
    fr = []
    for m in range(t_da, t_a + 1, step):
        t = O.locale_a_utc(data, f"{m // 60:02d}:{m % 60:02d}"); st, az, el, g = O.ombra_a_istante(S, t, lat, lon)
        if st == O.STATO_OK: fr.append(path.intersection(g).length / path.length)
    return float(np.mean(fr))


def test_convergenza():
    S, path, _ = _canyon()
    f1, f5, f15 = (_frazione_media(S, path, s) for s in (1, 5, 15))
    assert abs(f15 - f1) < 0.01 and abs(f5 - f1) <= abs(f15 - f1) + 1e-9, (f1, f5, f15)    # passo temporale 15/5/1 min: convergenza sotto 1 punto
    # passo spaziale: campionamento del percorso a 2/1/0,5 m contro l'intersezione esatta, a un istante fisso
    t = O.locale_a_utc("2026-09-15", "10:00"); st, az, el, g = O.ombra_a_istante(S, t, LAT, LON)
    ex = path.intersection(g).length / path.length; err = []
    for ds in (2.0, 1.0, 0.5):
        n = int(math.ceil(path.length / ds)); s = (np.arange(n) + 0.5) * path.length / n; p = shapely.line_interpolate_point(path, s)
        err.append(abs(float(shapely.contains_xy(g, shapely.get_x(p), shapely.get_y(p)).mean()) - ex))
    assert err[0] <= 2 * ds / path.length + 1e-9 and err[2] <= err[0] + 1e-9 and err[2] < 0.5 / path.length * 2 + 1e-9, err
    print(f"     passo temporale 15/5/1 min: media giornaliera {f15:.4f}/{f5:.4f}/{f1:.4f}; passo spaziale 2/1/0,5 m: scarto {err[0]:.4f}/{err[1]:.4f}/{err[2]:.4f}")
    ok("convergenza temporale e spaziale su canyon sintetico")


def test_chioma():
    r, zc, el, az = 3.0, 8.0, 30.0, 90.0                                # sfera: area = pi r^2 / sin(el), centro spostato di zc / tan(el) verso ovest
    p = O.ellisse_chioma(0, 0, r, zc - r, zc + r, az, el)
    assert abs(p.area - math.pi * r * r / math.sin(math.radians(el))) < 0.01 * p.area
    assert abs(p.centroid.x + zc / math.tan(math.radians(el))) < 1e-6 and abs(p.centroid.y) < 1e-6
    a, c, el = 3.0, 4.0, 35.0                                           # ellissoide a,a,c: area = pi a sqrt(c^2 cos^2 + a^2 sin^2) / sin
    p = O.ellisse_chioma(5, 5, a, 6 - c, 6 + c, 200, el); e = math.radians(el)
    assert abs(p.area - math.pi * a * math.sqrt(c * c * math.cos(e) ** 2 + a * a * math.sin(e) ** 2) / math.sin(e)) < 0.01 * p.area
    # chioma sollevata: il suolo sotto la chioma con sole allo zenit è in ombra, con sole basso l'ombra cade lontano dal tronco
    S = O.Scena(chiome={"x": np.array([0.0]), "y": np.array([0.0]), "a": np.array([3.0]), "z_lo": np.array([3.0]), "z_hi": np.array([11.0]), "forma": "ellissoide"})
    z = O.ombra_scena(S, 100, 89.0); assert z.contains(Point(0, 0)) and abs(z.area - math.pi * 9) < 0.5
    b = O.ombra_scena(S, 180, 20.0); assert not b.contains(Point(0, 0)) and b.centroid.y > 15
    Sc = O.Scena(chiome={**S.chiome, "forma": "cilindro"}); cil = O.ombra_scena(Sc, 180, 20.0)     # cilindro: limite superiore dell'ellissoide
    assert cil.area > b.area and cil.contains(b.buffer(-0.01).representative_point())
    ok("chioma: ellisse analitica, chioma sollevata, cilindro come limite superiore")


def test_casi_dati():
    # sui dati reali: aree ordinate h_min < h < h_max; base <= alberi min/tipico/max) e il cilindro supera l'ellissoide
    w = box(CE - 250, CN - 250, CE + 250, CN + 250); t = O.locale_a_utc("2026-09-15", "10:00"); area = {}
    for c in O.CASI:
        st, az, el, g = O.ombra_a_istante(O.scena_caso(c), t, LAT, LON, finestra=w); assert st == O.STATO_OK; area[c] = g.intersection(w)
    ar = {c: g.area for c, g in area.items()}
    assert ar["base_h_min"] < ar["base"] < ar["base_h_max"]    # non annidati in senso stretto: le coperture sospese cambiano anche la base
    for c in ("alberi_min", "alberi_tipico", "alberi_max", "alberi_tipico_cilindro"): assert area["base"].difference(area[c]).area < 1e-3 and ar[c] >= ar["base"], c
    assert ar["alberi_min"] <= ar["alberi_tipico"] <= ar["alberi_max"] and ar["alberi_tipico_cilindro"] > ar["alberi_tipico"]
    assert O.scena_caso("alberi_tipico_cilindro").chiome["forma"] == "cilindro" and O.scena_caso("alberi_tipico").chiome["forma"] == "ellissoide"
    # vegetazione LiDAR: aggiunge ombra e non ne toglie, a parità di caso degli alberi; ordine min <= tipico <= max
    for k in ("min", "tipico", "max"): assert area["alberi_" + k].difference(area["veg_lidar_" + k]).area < 1e-3 and ar["veg_lidar_" + k] >= ar["alberi_" + k], k
    assert ar["veg_lidar_tipico"] > ar["alberi_tipico"] and ar["veg_lidar_min"] <= ar["veg_lidar_tipico"] <= ar["veg_lidar_max"]
    ok("dati reali: casi annidati base <= alberi min <= tipico <= max, cilindro > ellissoide, vegetazione LiDAR >= alberi")


def test_vegetazione_lidar():
    g = O.vegetazione_lidar(); D = O.dati()
    assert len(g) > 0 and not g.liscia.any() and (g.h95 >= 2.5).all() and D["n_veg_lisce"] > 0     # cluster liscia (probabili tetti) esclusi
    S = O.scena_vegetazione("tipico")
    assert len(S.geoms) == len(g) and np.allclose(S.z_hi, g.h95) and np.allclose(S.z_lo, 0.25 * g.h95) and (S.z_lo < S.z_hi).all()
    assert (O.scena_vegetazione("min").z_lo > S.z_lo).all() and (O.scena_vegetazione("max").z_lo < S.z_lo).all()
    # le poligonazioni non toccano gli edifici (maschera di F05): sovrapposizione trascurabile
    v = D["v"]; ug = shapely.union_all(g.geometry.values)
    assert shapely.union_all(v.geometry.values).intersection(ug).area < 0.01 * ug.area
    assert D["n_volumi_demoliti"] > 0 and v.presente_2023.all()      # nessun edificio demolito (LiDAR 2023) nella scena
    ok("vegetazione LiDAR: solo cluster non liscia, z_lo/z_hi dichiarati, fuori dagli edifici; demolizioni escluse")


def test_copertura_osm_sospesa():
    # la copertura OSM più grande (building=roof) è sospesa: z_lo = tetto - 0,4 m; il suolo sotto con sole alto resta libero
    v = O.dati()["v"]; cp = v[(v.tipo == "copertura_osm") & (v.h >= 2.0)]; assert len(cp), "nessuna copertura OSM"; r = cp.loc[cp.geometry.area.idxmax()]; S = O.scena_edifici("h")
    i = S.ids.index(r.id); assert abs(S.z_hi[i] - r.h) < 1e-9 and abs(S.z_lo[i] - (r.h - 0.4)) < 1e-9
    assert abs(O.scena_edifici("h_min").z_lo[i] - (r.h_min - 0.8)) < 1e-9 and abs(O.scena_edifici("h_max").z_lo[i] - (r.h_max - 0.2)) < 1e-9
    assert (S.z_lo[[k for k, x in enumerate(v.id) if v.tipo.values[k] != "copertura_osm"]] == 0).all()    # portici/volumi pieni restano pieni
    c = r.geometry.representative_point(); az, el = 180.0, 85.0
    sosp = O.ombra_prisma(r.geometry, r.h - 0.4, r.h, az, el); pieno = O.ombra_prisma(r.geometry, 0, r.h, az, el)
    assert pieno.contains(c) and pieno.area > sosp.area and sosp.difference(pieno).area < 1e-6
    assert sosp.area < r.geometry.area + 2 * r.geometry.length * 0.4 / math.tan(math.radians(el)) + r.geometry.length * r.h / math.tan(math.radians(el)) and sosp.area > 0
    ok("copertura OSM reale sospesa (regola della scena), portici pieni, ombra sospesa contenuta nella piena")


def test_contratti():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    sch = {p.name.split(".")[0]: json.loads(p.read_text()) for p in (ROOT / "contracts/schemas").glob("*.schema.json")}
    reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in sch.values()])
    rec = [{"receiver_id": "pth_fi_prova", "kind": "path", "geometry": {"type": "LineString", "coordinates": [[round(CE, 2), round(CN, 2)], [round(CE + 100, 2), round(CN + 20, 2)]]}}]
    w = {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ["08:00", "13:00"]}; m = {"name": "geometric_ray", "space_step_m": 1, "time_step_min": 5, "obstacles": "buildings_and_trees"}
    r1 = O.compute_shadow(O.BASELINE_ID, rec, w, m); r2 = O.compute_shadow(O.BASELINE_ID, rec, w, m)
    assert r1["job"]["job_id"] == r2["job"]["job_id"] and r1["righe"] == r2["righe"]                     # deterministico
    h = O.hashlib.sha256(O.canon({"tool": "compute_shadow", "inputs": r1["job"]["inputs"], "params": r1["job"]["params"]}).encode()).hexdigest()[:16]
    assert r1["job"]["job_id"] == "job_" + h and r1["manifest"]["manifest_id"] == "man_" + h
    for nome, doc in (("job", r1["job"]), ("manifest", r1["manifest"])):
        errs = list(Draft202012Validator({"$ref": sch[nome]["$id"]}, registry=reg).iter_errors(doc)); assert not errs, (nome, errs[0].message)
    assert Draft202012Validator({"$ref": sch["mcp"]["$id"] + "#/$defs/compute_shadow.input"}, registry=reg).is_valid(
        {"baseline_id": O.BASELINE_ID, "receivers": rec, "when": w, "method": {**m, "obstacles": "documented_buildings_only"}})
    assert all(x["classification"] in ("derived", "estimated") and "unit" in x for x in r1["manifest"]["metrics"])
    # ora ambigua/inesistente respinta; sole sotto l'orizzonte: riga con stato esplicito e nessuna frazione
    for d, hh, esc in (("2026-10-25", "02:30", O.OraAmbigua), ("2026-03-29", "02:30", O.OraInesistente)):
        try: O.compute_shadow(O.BASELINE_ID, rec, {**w, "date": d, "times": [hh]}, {**m, "obstacles": "documented_buildings_only"}); assert False
        except esc: pass
    rn = O.compute_shadow(O.BASELINE_ID, rec, {**w, "date": "2026-10-25", "times": ["03:00", "12:00"]}, {**m, "obstacles": "documented_buildings_only"})
    notte = [x for x in rn["righe"] if x["time_local"] == "03:00"]; assert notte and all(x["stato"] == O.STATO_NOTTE and "shade_fraction" not in x for x in notte)
    assert any(x["stato"] == O.STATO_OK and 0 <= x["shade_fraction"] <= 1 for x in rn["righe"] if x["time_local"] == "12:00")
    ok("compute_shadow: deterministico, job_id = hash, job/manifest validi sugli schemi")


def _percorsi_firenze():
    import run
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in run.ricevitori()]


def test_firenze_vegetazione_e_determinismo():
    # percorso reale fermata T2 -> Polo: con la vegetazione LiDAR l'ombra aumenta o resta uguale, a parità di caso degli alberi; stesso input = stessi numeri
    rec = _percorsi_firenze(); assert [r["receiver_id"] for r in rec] == ["pth_fi_R01", "pth_fi_R02"]
    w = {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ["09:00", "12:30", "16:00"]}; m = {"name": "geometric_ray", "space_step_m": 1, "time_step_min": 5, "obstacles": "buildings_and_trees"}
    casi = ["base", "alberi_tipico", "veg_lidar_tipico", "alberi_min", "veg_lidar_min", "alberi_max", "veg_lidar_max"]
    r1 = O.compute_shadow(O.BASELINE_ID, rec, w, m, casi=casi, tratti_casi=["base"]); r2 = O.compute_shadow(O.BASELINE_ID, rec, w, m, casi=casi, tratti_casi=["base"])
    assert r1["job"]["job_id"] == r2["job"]["job_id"] and r1["righe"] == r2["righe"] and r1["tratti"] == r2["tratti"]
    fr = {(x["receiver_id"], x["time_local"], x["caso"]): x["shade_fraction"] for x in r1["righe"] if x["stato"] == O.STATO_OK}
    assert fr, "nessun istante calcolato"
    for (rid, t, c), f in fr.items():
        assert 0 <= f <= 1
        if c.startswith("alberi_"): assert f >= fr[(rid, t, "base")] - 1e-9 and fr[(rid, t, "veg_lidar_" + c[7:])] >= f - 1e-9, (rid, t, c)
    assert any(fr[(rid, t, "veg_lidar_tipico")] > fr[(rid, t, "alberi_tipico")] for (rid, t, c) in fr if c == "base"), "la vegetazione LiDAR non pesa mai?"
    # tratti: un Feature per ricevitore/ora calcolati del caso base, metri in ombra uguali a quelli delle righe
    tr = {(f["properties"]["receiver_id"], f["properties"]["time_local"]): f for f in r1["tratti"]["features"]}
    assert len(tr) == sum(1 for k in fr if k[2] == "base") and all(f["properties"]["caso"] == "base" for f in tr.values())
    for (rid, t), f in tr.items(): assert abs(f["properties"]["shade_fraction"] - fr[(rid, t, "base")]) < 1e-9
    ok("percorsi Firenze: vegetazione LiDAR >= alberi >= edifici, determinismo, tratti")


def test_nessun_riferimento_a_pisa():
    rec = _percorsi_firenze()[:1]; w = {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ["12:30"]}
    m = {"name": "geometric_ray", "space_step_m": 2, "time_step_min": 10, "obstacles": "buildings_and_trees"}
    r = O.compute_shadow(O.BASELINE_ID, rec, w, m, casi=["base", "veg_lidar_tipico"])
    docs = [json.dumps(r["manifest"], ensure_ascii=False), json.dumps(r["job"], ensure_ascii=False)]
    docs += [p.read_text() for p in (ROOT / "shadow" / O.SLUG / "manifest").glob("*.json")] if (ROOT / "shadow" / O.SLUG / "manifest").exists() else []
    for d in docs:
        low = d.lower(); assert "pisa" not in low and "z2" not in low and "aoi_z2" not in low, "riferimento a Pisa"
    assert r["manifest"]["aoi_id"] == "aoi_firenze_novoli" and r["manifest"]["baseline_id"] == "bas_firenze_novoli_20261009"
    ok("manifest e job senza riferimenti a Pisa, area e baseline di Firenze")


def test_risultati_versionati():
    f = ROOT / "shadow" / O.SLUG / "sintesi.json"
    if not f.exists(): print("  (sintesi.json assente: eseguire shadow/run.py)"); return
    S = json.load(open(f)); assert set(S["date"]) == {"2026-07-15", "2026-09-15"} and len(S["percorsi"]) == 2
    for data, righe in S["date"].items():
        for r in righe:
            e, a, v = (r[k].get("frazione") for k in ("edifici", "edifici_e_alberi", "edifici_alberi_e_vegetazione_lidar"))
            if e is None: continue
            assert 0 <= e["min"] <= e["valore"] <= e["max"] <= 1
            assert e["valore"] <= a["valore"] + 1e-9 <= v["valore"] + 2e-9, (data, r["receiver_id"], r["fascia"])       # più ostacoli, non meno ombra
            assert a["min"] <= a["valore"] <= a["max"] and v["min"] <= v["valore"] <= v["max"]
        assert {r["fascia"] for r in righe} == {"punta_12_30_13_30", "giornata_8_19"}
    for data in S["date"]:
        g = json.load(open(ROOT / "shadow" / O.SLUG / f"tratti_ombra_{data}.geojson")); assert g["type"] == "FeatureCollection" and g["features"]
        for ft in g["features"]:
            if ft["geometry"]: assert all(8 < c[0] < 14 and 40 < c[1] < 46 for ln in (ft["geometry"]["coordinates"] if ft["geometry"]["type"] == "MultiLineString" else [ft["geometry"]["coordinates"]]) for c in ln)   # lon/lat
    ok("sintesi e GeoJSON versionati coerenti: intervalli ordinati, edifici <= alberi <= vegetazione, EPSG:4326")


def test_memoria_misurata():
    # D46: ru_maxrss è in KB su Linux e in byte su macOS; il massimo non può stare sotto la memoria residente di adesso né sopra quella della macchina
    import esposizione, psutil
    m = esposizione.memoria_max_gb() * 2**30; rss = psutil.Process().memory_info().rss
    assert 0.9 * rss <= m + 0.01 * 2**30 and m <= psutil.virtual_memory().total, (m, rss)
    ok(f"memoria massima {m / 2**30:.2f} GB, residente {rss / 2**30:.2f} GB")



TOL_ASSE = 1e-4   # quarta cifra: stesso motore e stessa linea, l'asse deve uscire uguale


def test_lati_strada():
    # F6 (D56): i due lati stanno accanto all'asse, non al posto: sull'asse, calcolata allo stesso modo, escono i numeri di sempre (sintesi per ora, esposizione)
    import lati_strada as LS, rete_lib as RL
    f = ROOT / "shadow" / O.SLUG / "lati_strada.json"
    if not f.exists(): print("  (lati_strada.json assente: eseguire shadow/lati_strada.py)"); return
    R = json.load(open(f)); E = json.load(open(ROOT / "shadow" / O.SLUG / "esposizione_2026-07-15.json")); n = 0; peggiore = 0.0
    assert set(R["percorsi"]) == set(LS.ISTANTI) and R["stato"].startswith("prototipo")
    for rid, P in R["percorsi"].items():
        assert [(x["data"], x["ora"]) for x in P["istanti"]] == LS.ISTANTI[rid], rid
        assert abs(P["lunghezza_asse_m"] - E["percorsi"][rid]["lunghezza_m"]) < 0.2, rid
        for x in P["istanti"]:
            for caso, nome in LS.CASI.items():
                if nome not in x: continue
                v = x[nome]; assert v["asse_ufficiale"] == LS.ufficiale(rid, x["data"], x["ora"], caso) is not None, (rid, x)
                d = abs(v["asse"] - v["asse_ufficiale"]); peggiore = max(peggiore, d); n += 1
                assert d <= TOL_ASSE, (rid, x["data"], x["ora"], nome, v)
    # rifatto adesso: R01 alle 14 del 15 luglio deve ridare il file
    G, _ = RL.carica(); x = LS.percorso("R01", G, {c: O.scena_caso(c) for c in LS.CASI}, [("2026-07-15", "14:00")])["istanti"][0]
    y = next(y for y in R["percorsi"]["R01"]["istanti"] if (y["data"], y["ora"]) == ("2026-07-15", "14:00"))
    assert {k: x[k] for k in ("edifici", "con_vegetazione", "lato_piu_in_ombra")} == {k: y[k] for k in ("edifici", "con_vegetazione", "lato_piu_in_ombra")}, (x, y)
    ok(f"lati della strada: {n} quote sull'asse uguali ai risultati ufficiali entro {TOL_ASSE * 100:g} punti (scarto massimo {peggiore * 100:.2f}); R01 alle 14 rifatto identico")


if __name__ == "__main__":
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"): print(nome); f()
    print("TUTTI I TEST OK")
