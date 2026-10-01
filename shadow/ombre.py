"""T09: ombra geometrica (caso B). Libreria deterministica, indipendente dal renderer e dall'interfaccia (CLI, API, MCP la chiamano uguale).

    r = compute_shadow("bas_z2_20261001", receivers, when, method, walk_speed_m_s=1.2, out_dir=...)
    r["job"], r["manifest"], r["righe"] (una riga per ricevitore/ora/caso), r["sintesi"]

Metodo (versione in VERSIONE):
 1. Sole: algoritmo NOAA (Meeus), azimut orario da Nord, elevazione geometrica (senza rifrazione). Tempo locale Europe/Rome convertito
    in UTC col database tz (passaggi ora legale/solare gestiti dal database; ore inesistenti o ambigue respinte con errore esplicito).
 2. Ombra di un volume prismatico fra quota z_lo e z_hi (sopra il piano del suolo) = somma di Minkowski del footprint con il segmento
    [d*z_lo, d*z_hi], d = spostamento orizzontale per metro di altezza = 1/tan(elevazione), verso opposto al sole. Esatta per prismi
    con footprint qualsiasi (concavo, con buchi). Un volume sospeso (z_lo > 0) non ombreggia il suolo sotto di sé, salvo sole allo zenit.
 3. Chioma = ellissoide opaco fra altezza d'imposta e altezza totale (proiezione parallela esatta: un'ellisse); tronco trascurato
    (diametro 0,1-0,9 m, dichiarato). Opzione "cilindro" come limite superiore.
 4. Unione di tutte le ombre in un solo poligono (nessun doppio conteggio); frazione = lunghezza(L ∩ unione) / lunghezza(L).
Terreno: quasi piano, dichiarato. Ogni oggetto è riferito al proprio piede (quota base di fonte, altezze relative): il ricevitore si
assume alla quota del piede degli oggetti vicini. Nessuna conversione in gradi o comfort."""
import datetime as dt, hashlib, json, math, pathlib
from zoneinfo import ZoneInfo
import numpy as np
import shapely
from shapely.geometry import LineString, MultiPolygon, Polygon, Point, box, mapping
from shapely import affinity

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSIONE = "0.1.0"
ROMA = ZoneInfo("Europe/Rome")
UTC = dt.timezone.utc
EL_MIN_SUPPORTATA = 5.0   # gradi: sotto, il contesto dei dati (margine 450 m dal bordo Z2) non copre ombre di edifici da 38 m
STATO_OK, STATO_NOTTE, STATO_BASSO = "ok", "sole_sotto_orizzonte", "sole_basso_fuori_supporto"
LIMITI = {"max_area_km2": 4, "max_rows": 50000, "max_seconds": 3600, "max_memory_mb": 4096}


# ---------------------------------------------------------------- tempo e sole
class OraInesistente(ValueError): pass
class OraAmbigua(ValueError): pass


def locale_a_utc(data, hhmm, fold=None):
    """Data 'AAAA-MM-GG' (o date) e ora locale 'HH:MM' in Europe/Rome -> datetime UTC. 02:30 del 29/3/2026 non esiste (OraInesistente);
    02:30 del 25/10/2026 compare due volte (OraAmbigua, salvo fold=0 per la prima, ora legale, o fold=1 per la seconda)."""
    d = dt.date.fromisoformat(data) if isinstance(data, str) else data
    h, m = (int(x) for x in hhmm.split(":"))
    n = dt.datetime(d.year, d.month, d.day, h, m)
    a, b = n.replace(tzinfo=ROMA, fold=0), n.replace(tzinfo=ROMA, fold=1)
    if a.astimezone(UTC).astimezone(ROMA).replace(tzinfo=None) != n:
        raise OraInesistente(f"{data} {hhmm} non esiste in Europe/Rome (salto dell'ora legale)")
    if a.utcoffset() != b.utcoffset():
        if fold is None: raise OraAmbigua(f"{data} {hhmm} compare due volte in Europe/Rome (fine ora legale): indicare fold=0 o 1")
        return (a if fold == 0 else b).astimezone(UTC)
    return a.astimezone(UTC)


def istanti_giorno(data, step_min):
    """Tutti gli istanti UTC del giorno locale, a passo costante: 92 passi da 15 min il 29/3/2026, 100 il 25/10/2026, 96 gli altri giorni."""
    d = dt.date.fromisoformat(data) if isinstance(data, str) else data
    t0 = dt.datetime(d.year, d.month, d.day, tzinfo=ROMA).astimezone(UTC)
    t1 = dt.datetime.combine(d + dt.timedelta(days=1), dt.time(), tzinfo=ROMA).astimezone(UTC)
    n = int(round((t1 - t0).total_seconds() / 60 / step_min))
    return [t0 + dt.timedelta(minutes=step_min * k) for k in range(n)]


def sole(utc, lat, lon):
    """Posizione del sole (azimut deg da Nord in senso orario, elevazione geometrica deg). utc: datetime aware o array di secondi unix.
    Algoritmo NOAA General Solar Position (Meeus, Astronomical Algorithms): precisione attesa ~0,01-0,05 deg per il 2026."""
    t = np.atleast_1d(np.asarray([x.timestamp() for x in utc] if isinstance(utc, (list, tuple)) else
                                 (utc.timestamp() if isinstance(utc, dt.datetime) else utc), float))
    jc = (t / 86400.0 + 2440587.5 - 2451545.0) / 36525.0
    r = np.radians
    l0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    C = (np.sin(r(M)) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + np.sin(r(2 * M)) * (0.019993 - 0.000101 * jc) + np.sin(r(3 * M)) * 0.000289)
    lam = l0 + C - 0.00569 - 0.00478 * np.sin(r(125.04 - 1934.136 * jc))
    eps = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60 + 0.00256 * np.cos(r(125.04 - 1934.136 * jc))
    dec = np.arcsin(np.sin(r(eps)) * np.sin(r(lam)))
    y = np.tan(r(eps) / 2) ** 2
    eqt = 4 * np.degrees(y * np.sin(2 * r(l0)) - 2 * e * np.sin(r(M)) + 4 * e * y * np.sin(r(M)) * np.cos(2 * r(l0))
                         - 0.5 * y * y * np.sin(4 * r(l0)) - 1.25 * e * e * np.sin(2 * r(M)))
    tst = (((t % 86400.0) / 60.0) + eqt + 4 * lon) % 1440
    ha = r(tst / 4 - 180)
    la = r(lat)
    el = np.degrees(np.arcsin(np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)))
    az = (np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(la) - np.tan(dec) * np.cos(la))) + 180) % 360
    return (float(az[0]), float(el[0])) if np.ndim(utc) == 0 or isinstance(utc, dt.datetime) else (az, el)


def stato_sole(el, el_min=EL_MIN_SUPPORTATA):
    return STATO_NOTTE if el <= 0 else STATO_BASSO if el < el_min else STATO_OK


# ---------------------------------------------------------------- motore vettoriale
class Scena:
    """Insieme di ostacoli: prismi (footprint, z_lo, z_hi) e chiome (ellissoidi o cilindri). Altezze in m sopra il piano del suolo.
    ponytail: unione con union_all su tutti i pezzi; per l'intero buffer Z2 resta nell'ordine di secondi per istante, vedi finestra in compute_shadow."""
    def __init__(self, geoms=(), z_lo=(), z_hi=(), ids=(), chiome=None):
        self.geoms = np.array(list(geoms), dtype=object); self.z_lo = np.asarray(z_lo, float); self.z_hi = np.asarray(z_hi, float)
        self.ids = list(ids)
        # chiome: dict con array x, y, a (raggio orizzontale), z_lo, z_hi (imposta e cima), forma
        self.chiome = chiome or {"x": np.zeros(0), "y": np.zeros(0), "a": np.zeros(0), "z_lo": np.zeros(0), "z_hi": np.zeros(0), "forma": "ellissoide"}
        if len(self.geoms):
            parts, pi = shapely.get_parts(self.geoms, return_index=True)   # MultiPolygon -> Polygon (get_rings non scende nei multi)
            rings, gi = shapely.get_rings(parts, return_index=True)
            co, ri = shapely.get_coordinates(rings, return_index=True)
            same = ri[:-1] == ri[1:]
            self.A, self.B, self.owner = co[:-1][same], co[1:][same], pi[gi[ri[:-1][same]]]
            self.bounds = shapely.bounds(self.geoms)
        else:
            self.A = self.B = np.zeros((0, 2)); self.owner = np.zeros(0, int); self.bounds = np.zeros((0, 4))

    def n(self): return len(self.geoms) + len(self.chiome["x"])

    def aggiungi(self, altra):
        """Nuova scena = questa + altra (es. pensiline di scenario)."""
        c = {k: np.concatenate([self.chiome[k], altra.chiome[k]]) if k != "forma" else self.chiome["forma"] for k in self.chiome}
        return Scena(list(self.geoms) + list(altra.geoms), np.concatenate([self.z_lo, altra.z_lo]), np.concatenate([self.z_hi, altra.z_hi]),
                     self.ids + altra.ids, c)


def _dir(az, el):
    """Spostamento orizzontale (E, N) per metro di altezza: verso opposto al sole."""
    k = 1.0 / math.tan(math.radians(el)); a = math.radians(az)
    return np.array([-math.sin(a) * k, -math.cos(a) * k])


def ombra_prisma(geom, z_lo, z_hi, az, el):
    """Ombra su suolo piano (z=0) di un prisma con footprint geom fra z_lo e z_hi. Somma di Minkowski footprint + segmento."""
    return ombra_scena(Scena([geom], [z_lo], [z_hi]), az, el)


def ellisse_chioma(x, y, a, z_lo, z_hi, az, el, n=64, forma="ellissoide"):
    """Ombra su suolo piano di un ellissoide (semiassi a, a, c; centro a quota (z_lo+z_hi)/2) con proiezione parallela: sagoma esatta
    (ellisse), con n vertici e raggio corretto in modo che l'area poligonale uguagli quella dell'ellisse."""
    c = (z_hi - z_lo) / 2.0; zc = (z_hi + z_lo) / 2.0
    ae, ee = math.radians(az), math.radians(el)
    s = np.array([math.cos(ee) * math.sin(ae), math.cos(ee) * math.cos(ae), math.sin(ee)])
    k = a / c; sp = np.array([s[0], s[1], s[2] * k]); sp /= np.linalg.norm(sp)
    u = np.cross(sp, [0, 0, 1.0]); u = np.array([1.0, 0, 0]) if np.linalg.norm(u) < 1e-9 else u / np.linalg.norm(u)
    v = np.cross(sp, u)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ar = a * math.sqrt((2 * math.pi / n) / math.sin(2 * math.pi / n))
    q = np.array([x, y, zc * k]) + ar * (np.outer(np.cos(th), u) + np.outer(np.sin(th), v))
    q[:, 2] /= k
    p = q[:, :2] - np.outer(q[:, 2] / s[2], s[:2])
    return Polygon(p)


def pezzi_scena(S, az, el, attivi=None, chiome_idx=None):
    """Elenco di poligoni la cui unione è l'ombra della scena. attivi: indici dei prismi da considerare (None = tutti)."""
    d = _dir(az, el); out = []
    if len(S.geoms):
        att = np.arange(len(S.geoms)) if attivi is None else np.asarray(attivi, int)
        m = np.zeros(len(S.geoms), bool); m[att] = True
        em = m[S.owner]; A, B, o = S.A[em], S.B[em], S.owner[em]
        dlo = np.outer(S.z_lo[o], d); dhi = np.outer(S.z_hi[o], d)
        area = np.abs((B - A)[:, 0] * d[1] - (B - A)[:, 1] * d[0]) * (S.z_hi[o] - S.z_lo[o])
        k = area > 1e-9
        if k.any():
            P = np.stack([A + dlo, B + dlo, B + dhi, A + dhi, A + dlo], axis=1)[k]
            out.append(shapely.polygons(P))
        g = S.geoms[att]; zl, zh = S.z_lo[att], S.z_hi[att]
        z0 = zl == 0
        out.append(g[z0])
        if (~z0).any(): out.append(np.array([affinity.translate(x, *(d * z)) for x, z in zip(g[~z0], zl[~z0])], dtype=object))
        out.append(np.array([affinity.translate(x, *(d * z)) for x, z in zip(g, zh)], dtype=object))
    C = S.chiome
    for i in (range(len(C["x"])) if chiome_idx is None else chiome_idx):
        if C["forma"] == "cilindro":
            f = Point(C["x"][i], C["y"][i]).buffer(C["a"][i], quad_segs=16)
            out.append(np.array([affinity.translate(f, *(d * C["z_lo"][i])), affinity.translate(f, *(d * C["z_hi"][i]))], dtype=object))
            A = np.array(f.exterior.coords)[:-1]; B = np.roll(A, -1, axis=0); dl, dh = d * C["z_lo"][i], d * C["z_hi"][i]
            out.append(shapely.polygons(np.stack([A + dl, B + dl, B + dh, A + dh, A + dl], axis=1)))
        else:
            out.append(np.array([ellisse_chioma(C["x"][i], C["y"][i], C["a"][i], C["z_lo"][i], C["z_hi"][i], az, el)], dtype=object))
    return np.concatenate([np.asarray(x, dtype=object) for x in out]) if out else np.zeros(0, dtype=object)


def ombra_scena(S, az, el, attivi=None, chiome_idx=None):
    """Unione delle ombre di tutti gli ostacoli. Sole sotto l'orizzonte: eccezione (usare ombra_a_istante per lo stato esplicito)."""
    if el <= 0: raise ValueError("sole sotto l'orizzonte: nessuna ombra da calcolare")
    p = pezzi_scena(S, az, el, attivi, chiome_idx)
    if not len(p): return Polygon()
    try: return shapely.union_all(p)
    except shapely.errors.GEOSException:     # robustezza: pezzi quasi coincidenti; si riprova su griglia di 1 mm (errore massimo 1 mm sull'ombra)
        return shapely.union_all(shapely.make_valid(shapely.set_precision(p, 0.001)))


def ombra_a_istante(S, utc, lat, lon, el_min=EL_MIN_SUPPORTATA, finestra=None):
    """Ritorna (stato, az, el, geometria). Fuori dallo stato 'ok' la geometria è None e nessuna unione viene tentata.
    finestra: shapely box (ricevitori); considera solo i volumi la cui ombra può raggiungerla (distanza <= z_hi/tan(el))."""
    az, el = sole(utc, lat, lon); st = stato_sole(el, el_min)
    if st != STATO_OK: return st, az, el, None
    att = ci = None
    if finestra is not None:
        t = math.tan(math.radians(el))
        if len(S.geoms): att = np.nonzero(shapely.distance(S.geoms, finestra) <= S.z_hi / t + 1.0)[0]
        C = S.chiome
        if len(C["x"]): ci = np.nonzero(shapely.distance(shapely.points(C["x"], C["y"]), finestra) <= C["z_hi"] / t + C["a"] + 1.0)[0]
    return st, az, el, ombra_scena(S, az, el, att, ci)


# ---------------------------------------------------------------- dati e scene
GPKG = ROOT / "data/norm/geometry/geometrie_z2.gpkg"
SNAPSHOT_IDS = {"edifici": ["snp_rt_unita_volumetriche_20261001", "snp_osm_pisa_20261001", "snp_rt_dsm2021_20261001", "snp_rt_dtm10_20261001"],
                "alberi": ["snp_rt_dbt10k_pisa_20261001"]}
BASELINE_ID, AOI_ID = "bas_z2_20261001", "aoi_z2"
# caso -> (colonna altezza edifici, caso chiome o None, forma chioma). Intervalli h_min/h_max di T05: ±0,5 m measured, ±1,36 m derived
# (×1,5 con alberi entro 2 m): sono quelli usati nella sensibilità.
CASI = {"base": ("h", None, None), "base_h_min": ("h_min", None, None), "base_h_max": ("h_max", None, None),
        "alberi_min": ("h", "min", "ellissoide"), "alberi_tipico": ("h", "tipico", "ellissoide"), "alberi_max": ("h", "max", "ellissoide"),
        "alberi_tipico_cilindro": ("h", "tipico", "cilindro")}
CASI_PER_OSTACOLI = {"documented_buildings_only": ["base", "base_h_min", "base_h_max"],
                     "buildings_and_scenario": ["base", "base_h_min", "base_h_max"],
                     "buildings_and_trees": ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max"]}
_cache = {}


def dati():
    if "v" not in _cache:
        import geopandas as gpd
        v = gpd.read_file(GPKG, layer="volumi"); a = gpd.read_file(GPKG, layer="alberi")
        _cache["n_volumi_totali"] = len(v); _cache["n_volumi_scartati"] = int(v[["h", "z_base"]].isna().any(axis=1).sum())
        v = v.dropna(subset=["h", "z_base"]); v["geometry"] = shapely.make_valid(v.geometry.values)
        _cache["n_alberi_totali"] = len(a)
        _cache["n_alberi_in_edificio"] = int(a.in_edificio.sum())
        a = a[~a.in_edificio].dropna(subset=["h", "h_min", "h_max", "chioma_d", "imposta"])
        _cache["v"], _cache["a"] = v.reset_index(drop=True), a.reset_index(drop=True)
        _cache["gpkg_sha256"] = hashlib.sha256(GPKG.read_bytes()).hexdigest()
    return _cache


def scena_edifici(col="h"):
    """Tutti i volumi del buffer (non solo Z2: le ombre entrano in Z2 da fuori). Volumi tutti pieni (z_lo = 0): il campo 'sospeso' della fonte è
    'ignoto' ovunque, quindi le coperture OSM sono trattate come volumi pieni, limite superiore dell'ombra al suolo."""
    v = dati()["v"]
    return Scena(v.geometry.values, np.zeros(len(v)), np.clip(v[col].values.astype(float), 0.3, None), v.id.tolist())


def scena_alberi(caso, forma="ellissoide"):
    """Chiome per il caso min/tipico/max. min = chioma piccola e alta d'imposta; max = chioma grande e bassa d'imposta.
    L'imposta è limitata a metà altezza (la fonte dà imposta massima >= altezza minima in 463 alberi)."""
    a = dati()["a"]
    col = {"min": ("h_min", "chioma_d_min", "imposta_max"), "tipico": ("h", "chioma_d", "imposta"), "max": ("h_max", "chioma_d_max", "imposta_min")}[caso]
    H, D, imp = (a[c].values.astype(float) for c in col)
    imp_eff = np.minimum(imp, 0.5 * H)
    _cache.setdefault("imposta_limitata", {})[caso] = int((imp_eff < imp - 1e-9).sum())
    return Scena(chiome={"x": a.geometry.x.values, "y": a.geometry.y.values, "a": D / 2, "z_lo": imp_eff, "z_hi": H, "forma": forma})


def scena_caso(caso, extra=None):
    col, tc, forma = CASI[caso]
    S = scena_edifici(col)
    if tc: S = S.aggiungi(scena_alberi(tc, forma))
    return S.aggiungi(extra) if extra is not None else S


def scena_da_volumi(volumi):
    """Volumi di scenario (pensiline, coperture...): [{id, geometry (GeoJSON 7791 o shapely), z_lo, z_hi}], quote in m sopra il suolo, classe scenario."""
    g = [shapely.geometry.shape(v["geometry"]) if isinstance(v["geometry"], dict) else v["geometry"] for v in volumi]
    return Scena(g, [v.get("z_lo", 0.0) for v in volumi], [v["z_hi"] for v in volumi], [v["id"] for v in volumi])


# ---------------------------------------------------------------- calcolo
canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
_hash_job = lambda tool, inputs, params: "job_" + hashlib.sha256(canon({"tool": tool, "inputs": inputs, "params": params}).encode()).hexdigest()[:16]


def _snap_ids(obstacles): return SNAPSHOT_IDS["edifici"] + (SNAPSHOT_IDS["alberi"] if obstacles == "buildings_and_trees" else [])


def _validate(receivers, when, method, walk_speed_m_s):
    if when.get("timezone") != "Europe/Rome": raise ValueError("timezone ammessa: Europe/Rome")
    if method.get("name") != "geometric_ray": raise ValueError("metodo ammesso: geometric_ray")
    if not 0.25 <= method["space_step_m"] <= 5 or not 1 <= method["time_step_min"] <= 30: raise ValueError("passi fuori dai limiti (0,25-5 m; 1-30 min)")
    if method["obstacles"] not in CASI_PER_OSTACOLI: raise ValueError(f"ostacoli ammessi: {sorted(CASI_PER_OSTACOLI)}")
    if not 0.3 <= walk_speed_m_s <= 2.5: raise ValueError("velocità di cammino fuori da 0,3-2,5 m/s")
    if not 1 <= len(receivers) <= 50 or not 1 <= len(when["times"]) <= 96: raise ValueError("ricevitori 1-50, orari 1-96")
    for r in receivers:
        if r["kind"] not in ("path", "surface"): raise ValueError("kind ammesso: path, surface")


def _sample(L, step):
    n = max(1, int(math.ceil(L.length / step))); ds = L.length / n
    s = (np.arange(n) + 0.5) * ds; p = shapely.line_interpolate_point(L, s)
    return s, ds, shapely.get_x(p), shapely.get_y(p)


def compute_shadow(baseline_id, receivers, when, method, scenario_id=None, scenario_volumes=None, walk_speed_m_s=1.2, *,
                   casi=None, fasce=None, el_min=EL_MIN_SUPPORTATA, asset_times=(), asset_casi=("base",), asset_bbox=None, out_dir=None, scenario_version=1):
    """Ombra su ricevitori. Parametri come compute_shadow.input di mcp.schema.json (baseline_id, receivers, when, method, scenario_id, walk_speed_m_s).
    receivers: [{receiver_id, kind: path|surface, geometry (GeoJSON in EPSG:7791, [E, N])}]. when: {date, timezone, times: ['HH:MM']}.
    method: {name:'geometric_ray', space_step_m, time_step_min, obstacles}. obstacles: documented_buildings_only | buildings_and_scenario |
    buildings_and_trees (estensione: aggiunge le chiome degli alberi in 3 casi min/tipico/max, da inserire nell'enum del contratto).
    scenario_volumes: volumi di scenario [{id, geometry, z_lo, z_hi}]. casi: sottoinsieme di CASI (default da obstacles). fasce: [{id, from, to}] per
    le metriche del manifest. asset_*: GeoJSON 4326 delle ombre unite per orari e casi, ritagliato su asset_bbox (E0, N0, E1, N1 in 7791).
    Ritorna {job, manifest, righe, sintesi, assets}. Stesso input = stesso job_id e stessi numeri. Ora inesistente/ambigua: OraInesistente/OraAmbigua."""
    t_start = dt.datetime.now(UTC)
    _validate(receivers, when, method, walk_speed_m_s)
    ob = method["obstacles"]
    if ob == "buildings_and_scenario" and not (scenario_id and scenario_volumes): raise ValueError("buildings_and_scenario richiede scenario_id e scenario_volumes")
    casi = list(casi or CASI_PER_OSTACOLI[ob]); fasce = list(fasce or [])
    D = dati()
    extra = scena_da_volumi(scenario_volumes) if scenario_volumes else None
    scene = {c: scena_caso(c, extra) for c in casi}
    geoms = {r["receiver_id"]: (shapely.geometry.shape(r["geometry"]) if isinstance(r["geometry"], dict) else r["geometry"]) for r in receivers}
    kind = {r["receiver_id"]: r["kind"] for r in receivers}
    from pyproj import Transformer
    allg = shapely.union_all(list(geoms.values())); cx, cy = allg.centroid.x, allg.centroid.y
    lon, lat = Transformer.from_crs(7791, 4326, always_xy=True).transform(cx, cy); lon, lat = round(lon, 4), round(lat, 4)
    finestra = box(*allg.bounds).buffer(1.0)
    step_t = method["time_step_min"] * 60.0
    cache = {}

    def ombra(caso, epoch):
        k = (caso, epoch)
        if k not in cache:
            cache[k] = ombra_a_istante(scene[caso], dt.datetime.fromtimestamp(epoch, UTC), lat, lon, el_min, finestra)
        return cache[k]

    campioni = {rid: _sample(g, method["space_step_m"]) for rid, g in geoms.items() if kind[rid] == "path"}
    righe = []
    for hhmm in when["times"]:
        t_utc = locale_a_utc(when["date"], hhmm); t0 = t_utc.timestamp()
        for rid, g in geoms.items():
            for caso in casi:
                st, az, el, U = ombra(caso, t0)
                r = {"receiver_id": rid, "kind": kind[rid], "time_local": hhmm, "utc": t_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "azimuth_deg": round(az, 2),
                     "elevation_deg": round(el, 2), "stato": st, "caso": caso}
                if kind[rid] == "path":
                    r["length_m"] = round(g.length, 2)
                    if st == STATO_OK:
                        sh = g.intersection(U).length if not U.is_empty else 0.0
                        s, ds, x, y = campioni[rid]
                        r.update(shaded_m=round(sh, 2), shade_fraction=round(sh / g.length, 4),
                                 sampled_fraction=round(float(shapely.contains_xy(U, x, y).mean()) if not U.is_empty else 0.0, 4))
                        ep = np.round((t0 + s / walk_speed_m_s) / step_t) * step_t; ok = np.zeros(len(s), bool); wst = STATO_OK
                        for e in np.unique(ep):
                            stw, _, _, Uw = ombra(caso, float(e))
                            if stw != STATO_OK: wst = stw; break
                            m = ep == e
                            ok[m] = shapely.contains_xy(Uw, x[m], y[m]) if not Uw.is_empty else False
                        if wst == STATO_OK:
                            r.update(walk_stato=wst, walk_shade_m=round(float(ok.sum() * ds), 2), walk_sun_min=round(float((~ok).sum() * ds / walk_speed_m_s / 60), 3),
                                     walk_total_min=round(g.length / walk_speed_m_s / 60, 3))
                        else: r["walk_stato"] = wst
                else:
                    r["area_m2"] = round(g.area, 2)
                    if st == STATO_OK:
                        sh = g.intersection(U).area if not U.is_empty else 0.0
                        r.update(shaded_m2=round(sh, 2), shade_fraction=round(sh / g.area, 4))
                righe.append(r)
    sintesi = _sintesi(righe, fasce, when["times"])
    # --- asset GeoJSON 4326
    assets_geo = []
    if asset_times:
        from pyproj import Transformer as T
        tr = T.from_crs(7791, 4326, always_xy=True).transform
        win = box(*(asset_bbox or allg.buffer(100).bounds))
        for hhmm in asset_times:
            t_utc = locale_a_utc(when["date"], hhmm); feats = []
            for caso in asset_casi:
                if caso not in scene: scene[caso] = scena_caso(caso, extra)
                st, az, el, U = ombra_a_istante(scene[caso], t_utc, lat, lon, el_min, win)
                f = {"type": "Feature", "geometry": None, "properties": {
                    "time_local": hhmm, "date": when["date"], "utc": t_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "azimuth_deg": round(az, 2), "elevation_deg": round(el, 2),
                    "stato": st, "caso": caso, "classification": "derived" if CASI[caso][1] is None else "estimated",
                    "obstacles": "edifici documentati" if CASI[caso][1] is None else f"edifici documentati + chiome ({CASI[caso][1]}, {CASI[caso][2]})"}}
                if U is not None and not U.is_empty:
                    c = shapely.simplify(shapely.clip_by_rect(U, *win.bounds), 0.25)
                    f["properties"]["area_m2"] = round(c.area, 1)
                    c = shapely.transform(c, lambda a: np.round(np.column_stack(tr(a[:, 0], a[:, 1])), 6))
                    f["geometry"] = mapping(c)
                feats.append(f)
            assets_geo.append((hhmm, {"type": "FeatureCollection", "features": feats}))
    # --- job, manifest
    inputs = {"baseline_id": baseline_id, "snapshot_ids": sorted(_snap_ids(ob))}
    if scenario_id: inputs.update(scenario_id=scenario_id, scenario_version=scenario_version)
    rec_canon = [{"receiver_id": r["receiver_id"], "kind": r["kind"], "geometry": json.loads(canon(shapely.geometry.mapping(
        shapely.set_precision(geoms[r["receiver_id"]], 0.01))))} for r in receivers]
    params = {"receivers": rec_canon, "when": when, "method": method, "walk_speed_m_s": walk_speed_m_s, "casi": casi, "fasce": fasce,
              "el_min_deg": el_min, "sun_reference_lonlat": [lon, lat], "geometrie_sha256": D["gpkg_sha256"],
              "chiome": {"forma": "ellissoide", "tronco": "trascurato", "parametri": "geometry/parametri_chiome.json"},
              "sospesi": "nessuno: campo sospeso ignoto nella fonte, volumi trattati come pieni", "method_version": VERSIONE}
    if scenario_volumes: params["scenario_volumes"] = [{"id": v["id"], "z_lo": v.get("z_lo", 0.0), "z_hi": v["z_hi"],
                                                         "geometry": mapping(shapely.set_precision(shapely.geometry.shape(v["geometry"]) if isinstance(v["geometry"], dict) else v["geometry"], 0.01))} for v in scenario_volumes]
    if asset_times: params["assets"] = {"times": list(asset_times), "casi": list(asset_casi), "bbox": list(asset_bbox) if asset_bbox else None}
    job_id = _hash_job("compute_shadow", inputs, params)
    t_end = dt.datetime.now(UTC); fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    man = _manifest(job_id, inputs, params, ob, sintesi, righe, casi, t_start, t_end, fasce, when, geoms, kind)
    assets = []
    if out_dir is not None:
        assets = _scrivi_assets(job_id, when["date"], righe, assets_geo, out_dir)
        man["assets"] = assets
    job = {"job_id": job_id, "tool": "compute_shadow", "status": "succeeded", "created_at": fmt(t_start), "started_at": fmt(t_start), "finished_at": fmt(t_end),
           "inputs": inputs, "params": params, "limits": LIMITI, "progress": {"fraction": 1.0, "message": "completato"}, "result_manifest_id": man["manifest_id"]}
    return {"job": job, "manifest": man, "righe": righe, "sintesi": sintesi, "assets": assets}


def _sintesi(righe, fasce, times):
    """Medie per ricevitore, caso e finestra oraria (solo istanti con sole supportato). Una riga per combinazione."""
    out = []; wins = [{"id": f["id"], "from": f["from"], "to": f["to"]} for f in fasce] or [{"id": "tutti", "from": min(times), "to": max(times)}]
    chiavi = sorted({(r["receiver_id"], r["caso"]) for r in righe})
    for w in wins:
        for rid, caso in chiavi:
            rr = [r for r in righe if r["receiver_id"] == rid and r["caso"] == caso and w["from"] <= r["time_local"] <= w["to"]]
            ok = [r for r in rr if r.get("shade_fraction") is not None]
            s = {"receiver_id": rid, "caso": caso, "fascia": w["id"], "n_orari": len(rr), "n_orari_calcolati": len(ok)}
            if ok:
                f = [r["shade_fraction"] for r in ok]
                s.update(shade_fraction_mean=round(float(np.mean(f)), 4), shade_fraction_min=min(f), shade_fraction_max=max(f),
                         el_min_deg=min(r["elevation_deg"] for r in ok), el_max_deg=max(r["elevation_deg"] for r in ok))
                if "shaded_m" in ok[0]: s["shaded_m_mean"] = round(float(np.mean([r["shaded_m"] for r in ok])), 1); s["length_m"] = ok[0]["length_m"]
                wk = [r for r in ok if r.get("walk_sun_min") is not None]
                if wk:
                    s.update(walk_sun_min_mean=round(float(np.mean([r["walk_sun_min"] for r in wk])), 3), walk_sun_min_min=min(r["walk_sun_min"] for r in wk),
                             walk_sun_min_max=max(r["walk_sun_min"] for r in wk), walk_total_min=wk[0]["walk_total_min"], n_orari_walk=len(wk),
                             walk_shade_m_mean=round(float(np.mean([r["walk_shade_m"] for r in wk])), 1))
            s["stati"] = sorted({r["stato"] for r in rr})
            out.append(s)
    return out


def _metrica(mid, label, value, unit, cls, scope, unc=None):
    m = {"metric_id": mid[:60], "label": label, "value": value, "unit": unit, "classification": cls, "scope": scope}
    if unc: m["uncertainty"] = unc
    return m


def _manifest(job_id, inputs, params, ob, sintesi, righe, casi, t0, t1, fasce, when, geoms, kind):
    D = dati(); ds = []
    for sid in inputs["snapshot_ids"]:
        s = json.load(open(ROOT / "pipeline/snapshots" / f"{sid}.json")); ds.append({"snapshot_id": sid, "source_id": s["source_id"], "sha256": s["sha256"], "license_state": s["license_state"]})
    ix = {(s["receiver_id"], s["caso"], s["fascia"]): s for s in sintesi}
    met = []
    for rid in geoms:
        for f in sorted({s["fascia"] for s in sintesi}):
            tag = f"{rid.lower()}_{f}"
            def val(caso, key): return (ix.get((rid, caso, f)) or {}).get(key)
            for key, nome, unit in (("shade_fraction_mean", "shade_fraction", "1"), ("walk_sun_min_mean", "walk_sun_min", "min")):
                if kind[rid] != "path" and key.startswith("walk"): continue
                sc = f"{rid}, {when['date']}, fascia {f}"
                b = [val(c, key) for c in ("base", "base_h_min", "base_h_max") if val(c, key) is not None]
                if val("base", key) is not None:
                    lab = "Frazione ombreggiata, edifici documentati" if nome == "shade_fraction" else "Minuti al sole camminando, edifici documentati"
                    met.append(_metrica(f"{tag}_{nome}_base", lab, val("base", key), unit, "derived", sc + ", centerline",
                                        {"kind": "interval", "low": min(b), "high": max(b), "basis": "sensibilità altezze: intervallo h_min/h_max di T05 (±0,5 m measured, ±1,36 m derived)"}))
                t = [val(c, key) for c in ("alberi_min", "alberi_tipico", "alberi_max") if val(c, key) is not None]
                if val("alberi_tipico", key) is not None:
                    lab = "Frazione ombreggiata, edifici + chiome idealizzate" if nome == "shade_fraction" else "Minuti al sole camminando, edifici + chiome idealizzate"
                    met.append(_metrica(f"{tag}_{nome}_alberi", lab, val("alberi_tipico", key), unit, "estimated", sc + ", centerline, chioma tipica",
                                        {"kind": "interval", "low": min(t), "high": max(t), "basis": "chiome min/tipico/max da parametri_chiome.json: classi stimate, non misurate"}))
    if not met: met.append(_metrica("shade_none", "Nessun istante con sole supportato", 0, "count", "derived", "tutti gli orari"))
    n_ok = sum(1 for r in righe if r["stato"] == STATO_OK); stati = {s: sum(1 for r in righe if r["stato"] == s) for s in sorted({r["stato"] for r in righe})}
    limits = [("terreno_piano", "Terreno quasi piano dichiarato: ogni volume riferito al proprio piede (quota base di fonte), ricevitore alla quota dei piedi vicini; dislivelli locali non modellati."),
              ("centerline", "Percorsi sull'asse della rete OSM, non sul lato del marciapiede: lato e portici non noti (marciapiede ignoto), l'effetto del lato non è nel risultato."),
              ("volumi_sospesi_ignoti", "Il campo sospeso è ignoto in tutta la fonte: portici e pensiline trattati come volumi pieni (limite superiore dell'ombra al suolo); il motore gestisce volumi sospesi se forniti."),
              ("alberi_solo_stimati", "Chiome idealizzate opache (ellissoide) con parametri stimati per classe; tronco trascurato; inventario incompleto (462 gruppi di vegetazione DSM senza albero puntuale): non è l'ombra reale degli alberi."),
              ("ombra_binaria", "Ombra geometrica binaria: nessuna trasmissività, nessuna conversione in temperatura, comfort o domanda pedonale."),
              ("altezze_non_indipendenti", "Altezze delle unità volumetriche 2010 e DSM 2021 non indipendenti; datum verticale non confermato; edifici post-2010 solo da OSM più DSM."),
              ("sole_geometrico", f"Sole NOAA senza rifrazione; sotto {params['el_min_deg']} gradi di elevazione il contesto dei dati non copre le ombre lunghe: istanti esclusi con stato esplicito."),
              ("non_validato", "Nessuna osservazione di campo: risultato non validato localmente."),
              ("camminata_velocita", f"Minuti al sole a velocità costante {params['walk_speed_m_s']} m/s (ipotesi, nessun attraversamento o attesa); istante di ogni punto = partenza + distanza/velocità, agganciato al passo temporale.")]
    if inputs["snapshot_ids"] and ob == "buildings_and_trees":
        limits.append(("alberi_esclusi", f"Esclusi {D['n_alberi_in_edificio']} alberi con posizione dentro un edificio; {D['n_volumi_scartati']} volumi senza altezza o quota base scartati."))
    return {"manifest_id": "man_" + job_id[4:], "job_id": job_id, "tool": "compute_shadow", "aoi_id": AOI_ID, "baseline_id": inputs["baseline_id"], "datasets": ds, "params": params,
            "method": {"name": "geometric_ray", "version": VERSIONE,
                       "description": "Sole con algoritmo astronomico NOAA in Europe/Rome; ombra di ogni volume come somma di Minkowski del footprint con il segmento fra quota di base e di tetto; chiome come ellissoidi opachi; unione di tutte le ombre e intersezione con il ricevitore."},
            "crs": "EPSG:7791", "vertical_datum_status": "not_confirmed", "timezone": "Europe/Rome",
            "timing": {"started_at": t0.strftime("%Y-%m-%dT%H:%M:%SZ"), "finished_at": t1.strftime("%Y-%m-%dT%H:%M:%SZ"), "duration_s": round((t1 - t0).total_seconds(), 2)},
            "metrics": met, "coverage": {"note": f"Calcoli {n_ok} di {len(righe)} (ricevitore, ora, caso); stati del sole: {stati}. Volumi {len(D['v'])}, alberi {len(D['a'])}."},
            "limits": [{"code": a, "text": b} for a, b in limits], "validation_status": "not_validated_locally", "assets": []}


def _scrivi_assets(job_id, data, righe, assets_geo, out_dir):
    import csv
    out = []
    def reg(p, aid, media, role):
        b = pathlib.Path(p).read_bytes()
        out.append({"asset_id": aid, "path": str(pathlib.Path(p).resolve().relative_to(ROOT)), "media_type": media, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "role": role})
    bulk = ROOT / "data/norm/shadow"; bulk.mkdir(parents=True, exist_ok=True)
    cols = sorted({k for r in righe for k in r}, key=lambda k: (k not in ("receiver_id", "kind", "caso", "time_local", "utc"), k))
    p = bulk / f"{job_id}_righe.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, cols, lineterminator="\n"); w.writeheader(); [w.writerow(r) for r in righe]
    reg(p, "ast_shadow_righe_csv", "text/csv", "result_table")
    od = pathlib.Path(out_dir); od.mkdir(parents=True, exist_ok=True)
    for hhmm, fc in assets_geo:
        p = od / f"{job_id}_{data}_{hhmm.replace(':', '')}.geojson"
        p.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")))
        reg(p, f"ast_ombra_{data.replace('-', '')}_{hhmm.replace(':', '')}", "application/geo+json", "result_geometry")
    return out
