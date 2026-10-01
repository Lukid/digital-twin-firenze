"""T09: test del motore d'ombra e del sole. Uso: pipeline/.venv/bin/python shadow/test_ombre.py (asserzioni semplici, nessun framework)."""
import json, math, pathlib, sys, datetime as dt
import numpy as np, shapely
from shapely.geometry import box, Polygon, MultiPolygon, LineString, Point
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ombre as O

ROOT = O.ROOT; LAT, LON = 43.7228, 10.4017
ok = lambda nome: print("  ok", nome)


def test_sole_riferimenti():
    # Valori di riferimento calcolati offline con NREL SPA (implementazione numerica in pvlib 0.16.1, quota 4 m, altitudine non rilevante per la
    # geometria), latitudine/longitudine di Pisa. Nessun valore scaricato. Tolleranza 0,05 gradi (NOAA scarta meno di 0,02 gradi).
    ref = [("2026-06-21", "12:00", 134.424, 63.870), ("2026-06-21", "07:45", 76.508, 20.281), ("2026-09-15", "08:00", 95.872, 10.427),
           ("2026-10-01", "16:30", 238.013, 24.746), ("2026-10-25", "12:00", 179.270, 34.088), ("2026-12-21", "12:00", 175.912, 22.732)]
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


def _frazione_media(S, path, step, tipo="esatta", lat=43.715, lon=10.40, data="2026-09-15", t_da=8 * 60, t_a=18 * 60):
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
    t = O.locale_a_utc("2026-09-15", "10:00"); st, az, el, g = O.ombra_a_istante(S, t, 43.715, 10.40)
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
    # sui dati reali: gli intervalli sono annidati (h_min <= h <= h_max; base <= alberi min/tipico/max) e il cilindro supera l'ellissoide
    w = box(612500, 4840250, 613000, 4840700); t = O.locale_a_utc("2026-09-15", "10:00"); area = {}
    for c in O.CASI:
        st, az, el, g = O.ombra_a_istante(O.scena_caso(c), t, 43.715, 10.40, finestra=w); assert st == O.STATO_OK; area[c] = g.intersection(w)
    ar = {c: g.area for c, g in area.items()}
    assert ar["base_h_min"] < ar["base"] < ar["base_h_max"] and area["base_h_min"].difference(area["base"]).area < 1e-3
    for c in ("alberi_min", "alberi_tipico", "alberi_max", "alberi_tipico_cilindro"): assert area["base"].difference(area[c]).area < 1e-3 and ar[c] >= ar["base"], c
    assert ar["alberi_min"] <= ar["alberi_tipico"] <= ar["alberi_max"] and ar["alberi_tipico_cilindro"] > ar["alberi_tipico"]
    assert O.scena_caso("alberi_tipico_cilindro").chiome["forma"] == "cilindro" and O.scena_caso("alberi_tipico").chiome["forma"] == "ellissoide"
    ok("dati reali: casi annidati base <= alberi min <= tipico <= max, cilindro > ellissoide")


def test_contratti():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    sch = {p.name.split(".")[0]: json.loads(p.read_text()) for p in (ROOT / "contracts/schemas").glob("*.schema.json")}
    reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in sch.values()])
    rec = [{"receiver_id": "pth_t04_R01", "kind": "path", "geometry": {"type": "LineString", "coordinates": [[612600.0, 4840310.0], [612700.0, 4840330.0]]}}]
    w = {"date": "2026-09-15", "timezone": "Europe/Rome", "times": ["08:00", "13:00"]}; m = {"name": "geometric_ray", "space_step_m": 1, "time_step_min": 5, "obstacles": "buildings_and_trees"}
    r1 = O.compute_shadow("bas_z2_20261001", rec, w, m); r2 = O.compute_shadow("bas_z2_20261001", rec, w, m)
    assert r1["job"]["job_id"] == r2["job"]["job_id"] and r1["righe"] == r2["righe"]                     # deterministico
    h = O.hashlib.sha256(O.canon({"tool": "compute_shadow", "inputs": r1["job"]["inputs"], "params": r1["job"]["params"]}).encode()).hexdigest()[:16]
    assert r1["job"]["job_id"] == "job_" + h and r1["manifest"]["manifest_id"] == "man_" + h
    for nome, doc in (("job", r1["job"]), ("manifest", r1["manifest"])):
        errs = list(Draft202012Validator({"$ref": sch[nome]["$id"]}, registry=reg).iter_errors(doc)); assert not errs, (nome, errs[0].message)
    assert Draft202012Validator({"$ref": sch["mcp"]["$id"] + "#/$defs/compute_shadow.input"}, registry=reg).is_valid(
        {"baseline_id": "bas_z2_20261001", "receivers": rec, "when": w, "method": {**m, "obstacles": "documented_buildings_only"}})
    assert all(x["classification"] in ("derived", "estimated") and "unit" in x for x in r1["manifest"]["metrics"])
    # ora ambigua/inesistente respinta; sole sotto l'orizzonte: riga con stato esplicito e nessuna frazione
    for d, hh, esc in (("2026-10-25", "02:30", O.OraAmbigua), ("2026-03-29", "02:30", O.OraInesistente)):
        try: O.compute_shadow("bas_z2_20261001", rec, {**w, "date": d, "times": [hh]}, {**m, "obstacles": "documented_buildings_only"}); assert False
        except esc: pass
    rn = O.compute_shadow("bas_z2_20261001", rec, {**w, "date": "2026-10-25", "times": ["03:00", "12:00"]}, {**m, "obstacles": "documented_buildings_only"})
    notte = [x for x in rn["righe"] if x["time_local"] == "03:00"]; assert notte and all(x["stato"] == O.STATO_NOTTE and "shade_fraction" not in x for x in notte)
    assert any(x["stato"] == O.STATO_OK and 0 <= x["shade_fraction"] <= 1 for x in rn["righe"] if x["time_local"] == "12:00")
    ok("compute_shadow: deterministico, job_id = hash, job/manifest validi sugli schemi")


if __name__ == "__main__":
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"): print(nome); f()
    print("TUTTI I TEST OK")
