"""F08: scenari locali e baseline congelata (caso C) su Firenze Novoli (area da DT_AOI, default aoi_firenze_novoli). Libreria deterministica: CLI, API e MCP la chiamano uguale.

    b = baseline()                      # record congelato (scenarios/baseline.json)
    verifica_baseline()                 # ricalcola gli hash dei file citati: deve coincidere
    s = crea_scenario(bas, titolo, operazioni)   # validato sullo schema, id = hash del contenuto, mai modifica la baseline
    r = calcola_ombra(s, ricevitori(), condizioni())   # ombre.compute_shadow con gli interventi

Interventi ammessi: nuovo albero (punto, altezza, diametro chioma, altezza d'imposta) e pensilina (poligono, quota d'imposta e tetto), tutti
classe `scenario`, senza modello di crescita né anni. Rimozioni, modifiche, volumi edilizi: fuori capacità. La fattibilità è sempre ignota."""
import datetime as dt, hashlib, json, math, os, pathlib, sys
from functools import lru_cache
import numpy as np, shapely
from shapely.geometry import Point, Polygon, mapping, shape

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shadow")); sys.path.insert(0, str(ROOT / "network")); sys.path.insert(0, str(ROOT / "analysis"))
import ombre as O  # noqa: E402
from coordinate import arrotonda  # noqa: E402
SLUG = O.SLUG
SC = ROOT / "scenarios" / SLUG            # file piccoli versionati: baseline, scenari, confronto, interventi
GRANDI = ROOT / "data/norm" / SLUG / "scenarios"   # dati grandi non versionati: cache dei job e asset
DATA = pathlib.Path(os.environ.get("DT_SCENARIOS_DIR") or GRANDI)   # scenari creati dagli strumenti (non versionati)
JOBS, OUT = GRANDI / "jobs", GRANDI / "out"   # cache dei job di ombra degli scenari (chiave = contenuto, versione del motore e geometrie)

BASELINE_ID, AOI_ID = O.BASELINE_ID, O.AOI_ID
VERSIONE = "0.2.0"
PREFISSO = "scn_fi_"
PASSAGGIO_SEMILARGHEZZA_M = 1.0   # ipotesi: spazio libero da tenere attorno all'asse di un arco pedonale molto usato (pensiline)
SEMILARGHEZZA_CARREGGIATA_M = 3.0   # ipotesi: la rete ha solo l'asse, la larghezza della carreggiata non è nei dati
AREE_PEDONALI = ROOT / "data/norm" / SLUG / "fi_aree_pedonali.gpkg"   # aree di circolazione pedonale del Comune: dove si cammina (non carreggiata, binari, aiuole)
DIM_ALBERO = ("height_m", "crown_diameter_m", "crown_base_m")
DIM_PENSILINA = ("roof_height_m", "canopy_base_m")
FATTIBILITA = {"sottoservizi": "ignota", "spazio_radicale": "ignota", "permessi": "ignota", "proprieta_suolo": "ignota", "manutenzione_e_specie": "ignota"}

canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
sha_file = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
sha_obj = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()
now_z = lambda: dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rel = lambda p: str(pathlib.Path(p).resolve().relative_to(ROOT))


class ScenarioError(ValueError):
    """code: invalid_params | outside_capability | incompatible_baseline | unknown_id (stessi codici di tool_error)."""
    def __init__(self, code, message, candidates=None):
        super().__init__(message); self.code, self.candidates = code, candidates


# ---------------------------------------------------------------- schema
@lru_cache(maxsize=1)
def _validatore():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    sch = {p.name: json.loads(p.read_text()) for p in (ROOT / "contracts/schemas").glob("*.schema.json")}
    reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in sch.values()])
    return Draft202012Validator(sch["scenario.schema.json"], registry=reg)


def errori_schema(scn):
    return [f"{'/'.join(map(str, e.path)) or '(radice)'}: {e.message[:160]}" for e in sorted(_validatore().iter_errors(scn), key=lambda e: list(e.path))]


# ---------------------------------------------------------------- baseline congelata
def baseline():
    return json.loads((SC / "baseline.json").read_text())


def _hash_riferimenti(b):
    """Hash correnti di tutti i file citati dal record, nello stesso ordine del record."""
    h = {"geometrie": sha_file(ROOT / b["geometrie"]["file"]), "parametri_chiome": sha_file(ROOT / b["geometrie"]["parametri_chiome"]),
         "grafo": sha_file(ROOT / b["grafo"]["file"]), "regole": sha_file(ROOT / b["grafo"]["regole"]), "origini": sha_file(ROOT / b["origini"]["file"]), "vegetazione_lidar": (O.vegetazione_lidar(), O.dati()["veg_sha256"])[1],
         "percorsi": sha_file(ROOT / b["ricevitori"]["percorsi_file"]), "archi_usati": {k: sha_file(ROOT / v["file"]) for k, v in b["ricevitori"]["archi_usati"].items()},
         "motore_ombre": sha_file(ROOT / b["motori"]["ombre"]["file"]), "motore_accessibilita": sha_file(ROOT / b["motori"]["accessibilita"]["file"]),
         "snapshot": {s["snapshot_id"]: json.loads((ROOT / "pipeline/snapshots" / f"{s['snapshot_id']}.json").read_text())["sha256"] for s in b["snapshot"]}}
    return h


def verifica_baseline():
    """Lista di scostamenti fra il record e lo stato corrente dei file e delle versioni (vuota = baseline invariata)."""
    b = baseline(); h = _hash_riferimenti(b); d = []
    for k, rec in (("geometrie", b["geometrie"]["sha256"]), ("parametri_chiome", b["geometrie"]["parametri_chiome_sha256"]), ("grafo", b["grafo"]["sha256"]),
                   ("regole", b["grafo"]["regole_sha256"]), ("origini", b["origini"]["sha256"]), ("vegetazione_lidar", b["vegetazione_lidar"]["poligoni_sha256"]), ("percorsi", b["ricevitori"]["percorsi_sha256"]),
                   ("motore_ombre", b["motori"]["ombre"]["file_sha256"]), ("motore_accessibilita", b["motori"]["accessibilita"]["file_sha256"])):
        if h[k] != rec: d.append(f"{k}: hash cambiato")
    for k, v in b["ricevitori"]["archi_usati"].items():
        if h["archi_usati"][k] != v["sha256"]: d.append(f"archi_usati {k}: hash cambiato")
    for s in b["snapshot"]:
        if h["snapshot"][s["snapshot_id"]] != s["sha256"]: d.append(f"snapshot {s['snapshot_id']}: hash cambiato")
    import accessibilita as A
    if O.VERSIONE != b["motori"]["ombre"]["version"]: d.append(f"versione ombre {O.VERSIONE} != {b['motori']['ombre']['version']}")
    if A.VERSIONE != b["motori"]["accessibilita"]["version"]: d.append(f"versione accessibilità {A.VERSIONE} != {b['motori']['accessibilita']['version']}")
    return d


def stato_baseline():
    """Impronta della baseline: hash del record e di tutti i riferimenti (per verificare che uno scenario non la tocchi)."""
    b = baseline(); return {"record_sha256": sha_file(SC / "baseline.json"), "riferimenti": _hash_riferimenti(b), "versioni": [O.VERSIONE, b["motori"]["accessibilita"]["version"]]}


def condizioni():
    """Condizioni comuni a baseline e scenari: data, orari, fasce, metodo, velocità, quota minima del sole."""
    return baseline()["condizioni"]


# ---------------------------------------------------------------- ricevitori
@lru_cache(maxsize=1)
def _grafo():
    import rete_lib as RL
    G, _ = RL.carica(); return G


def linea_percorso(rid):
    """Percorso campione `rid` (asse della rete, network/<area>/percorsi_campione.geojson) in EPSG:7791, precisione 1 cm. None se non raggiungibile."""
    import shapely.ops
    from pyproj import Transformer
    to = Transformer.from_crs(4326, 7791, always_xy=True)
    for f in json.loads((ROOT / f"network/{SLUG}/percorsi_campione.geojson").read_text())["features"]:
        if f["properties"]["id"] == rid and f["properties"].get("stato") == "reachable":
            return shapely.set_precision(shapely.ops.transform(lambda x, y, z=None: to.transform(x, y), shape(f["geometry"])), 0.01)
    return None


def ricevitori():
    """Percorsi campione (asse della rete, come F07), aree di attesa (superfici) e archi più usati di F06, tutti in EPSG:7791.
    Gli stessi per baseline e scenari: sono la condizione comune del confronto."""
    b = baseline(); rec = []
    assert b["ricevitori"]["percorsi_file"] == f"network/{SLUG}/percorsi_campione.geojson"
    for i in b["ricevitori"]["route_ids"]:
        g = linea_percorso(i)
        if g is not None: rec.append({"receiver_id": f"pth_fi_{i}", "kind": "path", "geometry": mapping(g)})
    for a in [b["ricevitori"]["area_attesa"]] + b["ricevitori"].get("aree_attesa_altre", []):
        rec.append({"receiver_id": a["receiver_id"], "kind": "surface", "geometry": a["geometry"]})
    G = _grafo(); geom = {e["edge_id"]: e["geom"] for _, _, e in G.edges(data=True)}
    for r in b["ricevitori"]["archi"]:
        rec.append({"receiver_id": r["receiver_id"], "kind": "path", "geometry": mapping(shapely.set_precision(geom[r["edge_id"]], 0.01))})
    return rec


# ---------------------------------------------------------------- scenari
def _dim(op, chiavi):
    d = op["dimensions"]; mancanti = [k for k in chiavi if k not in d]
    if mancanti: raise ScenarioError("invalid_params", f"{op['op_id']}: dimensioni mancanti per {op['target_type']}: {mancanti}. Richieste: {list(chiavi)}.")
    for k in chiavi:
        if d[k]["unit"] != "m": raise ScenarioError("invalid_params", f"{op['op_id']}: {k} deve essere in metri.")
    return {k: float(d[k]["value"]) for k in chiavi}


def _rettangolo_pensilina(op):
    g = shape(op["geometry"])
    if g.geom_type != "Polygon": raise ScenarioError("invalid_params", f"{op['op_id']}: la pensilina richiede un poligono.")
    return g


def valida(scn, geometrie=True):
    """Controlla uno scenario. Errori (rifiuto): schema, baseline, tipi e dimensioni. Segnalazioni (non bloccano): interventi dentro edifici,
    fuori dalle aree di circolazione pedonale del Comune, su carreggiata di strada carrabile senza marciapiede, fuori dal riquadro dell'area, su un arco molto usato. Fattibilità sempre ignota.
    Ritorna {warnings: [{code, op_id, text, severity}], feasibility: {...}}."""
    e = errori_schema(scn)
    if e: raise ScenarioError("invalid_params", "; ".join(e[:5]))
    if scn["baseline_id"] != BASELINE_ID: raise ScenarioError("incompatible_baseline", f"Baseline disponibile: {BASELINE_ID}.", [BASELINE_ID])
    ids = [o["op_id"] for o in scn["operations"]]
    if len(set(ids)) != len(ids): raise ScenarioError("invalid_params", "op_id duplicati.")
    for op in scn["operations"]:
        if op["op"] != "add": raise ScenarioError("outside_capability", f"{op['op_id']}: '{op['op']}' non è supportato; solo 'add' (nuovi alberi e pensiline).")
        if op["target_type"] not in ("tree", "shelter"):
            raise ScenarioError("outside_capability", f"{op['op_id']}: target_type '{op['target_type']}' non supportato; ammessi tree e shelter.")
        if op["hypothesis_status"] == "feasibility_checked":
            raise ScenarioError("invalid_params", f"{op['op_id']}: la fattibilità non può risultare verificata in questo ambiente; usare feasibility_unknown o hypothesis.")
        if op["target_type"] == "tree":
            if op["geometry"]["type"] != "Point": raise ScenarioError("invalid_params", f"{op['op_id']}: l'albero richiede un punto.")
            d = _dim(op, DIM_ALBERO)
            if not (0 <= d["crown_base_m"] < d["height_m"]) or d["crown_diameter_m"] <= 0 or d["height_m"] > 40:
                raise ScenarioError("invalid_params", f"{op['op_id']}: servono 0 <= crown_base_m < height_m <= 40 e crown_diameter_m > 0.")
            if d["crown_base_m"] > 0.5 * d["height_m"]: raise ScenarioError("invalid_params", f"{op['op_id']}: l'imposta non può superare metà altezza (stessa regola della chioma di F07).")
        else:
            _rettangolo_pensilina(op); d = _dim(op, DIM_PENSILINA)
            if not (0 <= d["canopy_base_m"] < d["roof_height_m"] <= 12): raise ScenarioError("invalid_params", f"{op['op_id']}: servono 0 <= canopy_base_m < roof_height_m <= 12.")
    return {"warnings": _segnalazioni(scn) if geometrie else [], "feasibility": dict(FATTIBILITA)}


@lru_cache(maxsize=1)
def _contesto_geo():
    from shapely.strtree import STRtree
    v = O.dati()["v"]; v = v[v.tipo != "copertura_osm"]
    bld = list(v.geometry); G = _grafo()
    strade = [(e["geom"], e["marciapiede_stato"], e["edge_id"], e.get("name")) for _, _, e in G.edges(data=True) if e["tipo_arco"] == "strada"]
    b = baseline(); usati = {a["edge_id"]: a for a in b["ricevitori"]["archi"]}
    pass_ = [(e["geom"], e["edge_id"]) for _, _, e in G.edges(data=True) if e["edge_id"] in usati]
    z2 = list(O.RIQUADRO_EN)
    import pyogrio
    ped = shapely.union_all(pyogrio.read_dataframe(AREE_PEDONALI).geometry.values); shapely.prepare(ped)
    return {"ped": ped, "bld": bld, "bld_tree": STRtree(bld), "strade": strade, "strade_tree": STRtree([s[0] for s in strade]), "usati": pass_, "usati_info": usati, "riquadro": z2}


def _impronta(op):
    return shape(op["geometry"])   # albero: il punto (tronco); la chioma non è un ostacolo di passaggio


def _segnalazioni(scn):
    c = _contesto_geo(); w = []
    for op in scn["operations"]:
        g = _impronta(op); t = op["target_type"]
        for j in c["bld_tree"].query(g):
            ov = c["bld"][int(j)].intersection(g)
            if (t == "tree" and c["bld"][int(j)].contains(g)) or (t == "shelter" and ov.area > 0.5):
                w.append({"code": "dentro_edificio", "op_id": op["op_id"], "severity": "warning", "text": "L'intervento cade dentro l'impronta di un edificio documentato."}); break
        if (t == "tree" and not c["ped"].contains(g)) or (t == "shelter" and c["ped"].intersection(g).area < 0.5 * g.area):
            w.append({"code": "fuori_area_pedonale", "op_id": op["op_id"], "severity": "warning",
                      "text": "Fuori dalle aree di circolazione pedonale del Comune: può cadere su carreggiata, binari del tram, aiuola o area privata; da verificare."})
        gx = g.buffer(SEMILARGHEZZA_CARREGGIATA_M)
        ass, ign = [], []
        for j in c["strade_tree"].query(gx):
            geom, st, eid, nome = c["strade"][int(j)]
            if geom.distance(g) <= SEMILARGHEZZA_CARREGGIATA_M: (ass if st == "assente" else ign if st == "ignoto" else []).append(eid)
        if ass: w.append({"code": "su_carreggiata_senza_marciapiede", "op_id": op["op_id"], "severity": "warning",
                          "text": f"Entro {SEMILARGHEZZA_CARREGGIATA_M:g} m dall'asse di una strada carrabile senza marciapiede (ipotesi sulla semilarghezza della carreggiata): {ass[:3]}."})
        elif ign: w.append({"code": "marciapiede_ignoto", "op_id": op["op_id"], "severity": "info",
                            "text": "Vicino a una strada carrabile con marciapiede ignoto: il lato e la carreggiata non sono verificabili dai dati."})
        usati = [eid for geom, eid in c["usati"] if geom.distance(g) <= (0.5 if t == "tree" else PASSAGGIO_SEMILARGHEZZA_M)]
        if usati: w.append({"code": "su_arco_molto_usato", "op_id": op["op_id"], "severity": "warning",
                            "text": f"L'impronta tocca un arco fra i più usati da F06 ({usati[:2]}): passaggio libero e larghezza non modellati, da verificare."})
        if t == "tree" and any(o["op_id"] == op["op_id"] and o["n_tipica"] for o in sovrapposizioni_alberi_esistenti(scn)):
            w.append({"code": "chioma_su_chioma_esistente", "op_id": op["op_id"], "severity": "info", "text": "La chioma in proiezione si sovrappone a quella di un albero esistente (F05, chioma tipica): il beneficio marginale nel contesto con alberi esistenti è minore."})
        x0, y0, x1, y1 = c["riquadro"]
        px, py = g.centroid.x, g.centroid.y
        if not (x0 <= px <= x1 and y0 <= py <= y1): w.append({"code": "fuori_riquadro", "op_id": op["op_id"], "severity": "warning", "text": "Fuori dal riquadro dell'area pilota."})
    return w


def crea_scenario(baseline_id, titolo, operazioni, autore="prototipo digital twin Firenze", created_at=None):
    """Scenario versionato (versione 1) validato sullo schema. scenario_id = scn_fi_ + 16 esadecimali dello sha256 di (baseline, titolo, operazioni):
    stesso input, stesso id; un contenuto diverso è un altro scenario. Non scrive nulla: usare salva()."""
    sid = PREFISSO + sha_obj({"baseline_id": baseline_id, "title": titolo, "operations": operazioni})[:16]
    return {"scenario_id": sid, "version": 1, "baseline_id": baseline_id, "title": titolo, "author": autore, "created_at": created_at or now_z(), "operations": operazioni}


def salva(scn, cartella=DATA):
    """Scrive lo scenario (immutabile: se esiste con lo stesso contenuto lo lascia, con contenuto diverso rifiuta). Ritorna (percorso, creato)."""
    cartella = pathlib.Path(cartella); cartella.mkdir(parents=True, exist_ok=True)
    p = cartella / f"{scn['scenario_id']}.json"
    if p.exists():
        old = json.loads(p.read_text())
        if {k: v for k, v in old.items() if k != "created_at"} != {k: v for k, v in scn.items() if k != "created_at"}:
            raise ScenarioError("invalid_params", f"{scn['scenario_id']} esiste già con contenuto diverso: gli scenari sono immutabili, creare un nuovo scenario.")
        return p, False
    p.write_text(json.dumps(scn, ensure_ascii=False, indent=1)); return p, True


def elenco():
    out = {}
    for d in (SC, DATA):
        for p in sorted(d.glob(PREFISSO + "*.json")): out[p.stem] = p
    return out


def carica(scenario_id):
    p = elenco().get(scenario_id)
    if not p: raise ScenarioError("unknown_id", f"Scenario sconosciuto: {scenario_id}.", sorted(elenco()))
    return json.loads(p.read_text())


def sovrapposizioni_alberi_esistenti(scn):
    """Per ogni albero di scenario, gli alberi esistenti (F05) la cui chioma in proiezione si sovrappone: distanza fra i centri < somma dei raggi,
    con chioma esistente tipica e massima. Ritorna lista di {op_id, vicino_m, n_tipica, n_max, ids_tipica}."""
    a = O.dati()["a"]; out = []
    if a.empty: return out
    x, y, r_t, r_m = a.geometry.x.values, a.geometry.y.values, a["chioma_d"].values / 2, a["chioma_d_max"].values / 2
    for op in scn["operations"]:
        if op["target_type"] != "tree": continue
        p = shape(op["geometry"]); r = op["dimensions"]["crown_diameter_m"]["value"] / 2; d = np.hypot(x - p.x, y - p.y)
        t, m = d < r + r_t, d < r + r_m
        out.append({"op_id": op["op_id"], "vicino_m": round(float(d.min()), 2), "n_tipica": int(t.sum()), "n_max": int(m.sum()), "ids_tipica": [str(i) for i in a["id"].values[t]][:5]})
    return out


def riepilogo_interventi(scn):
    n = {"tree": 0, "shelter": 0}; area = {"tree": 0.0, "shelter": 0.0}
    for op in scn["operations"]:
        n[op["target_type"]] += 1
        if op["target_type"] == "tree": area["tree"] += math.pi * (op["dimensions"]["crown_diameter_m"]["value"] / 2) ** 2
        else: area["shelter"] += shape(op["geometry"]).area
    return {"alberi": n["tree"], "pensiline": n["shelter"], "area_proiezione_chiome_m2": round(area["tree"], 1), "area_pensiline_m2": round(area["shelter"], 1)}


# ---------------------------------------------------------------- ombra con gli interventi
def volumi_scenario(scn):
    """Interventi -> (prismi, alberi) per ombre.compute_shadow. Prismi: pensiline [{id 'shelter:<op>', geometry, z_lo, z_hi}]. Alberi: chiome
    ellissoidali [{id 'tree:<op>', x, y, a, z_lo, z_hi}] con quota d'imposta e cima. Il descrittore identifica l'intervento per intero (entra nell'hash del job)."""
    prismi, alberi = [], []
    for op in scn["operations"]:
        if op["target_type"] == "tree":
            d = _dim(op, DIM_ALBERO); p = shape(op["geometry"])
            alberi.append({"id": f"tree:{op['op_id']}", "x": p.x, "y": p.y, "a": d["crown_diameter_m"] / 2, "z_lo": d["crown_base_m"], "z_hi": d["height_m"]})
        else:
            d = _dim(op, DIM_PENSILINA); prismi.append({"id": f"shelter:{op['op_id']}", "geometry": op["geometry"], "z_lo": d["canopy_base_m"], "z_hi": d["roof_height_m"]})
    return prismi, alberi


CONTESTI = ("solo_edifici", "con_alberi_esistenti", "con_vegetazione_lidar")
CASI_CONTESTO = {"solo_edifici": ("base", "base_h_min", "base_h_max"), "con_alberi_esistenti": ("alberi_tipico", "alberi_min", "alberi_max"),
                 "con_vegetazione_lidar": ("veg_lidar_tipico", "veg_lidar_min", "veg_lidar_max")}   # centrale, estremi
CASI = [c for v in CONTESTI for c in CASI_CONTESTO[v]]   # i 9 casi del motore calcolati in un solo job
CONTESTO_PRINCIPALE = "con_vegetazione_lidar"   # base di confronto principale (D14): edifici, alberi censiti e vegetazione LiDAR


def calcola_ombra(scn, rec, cond, casi=None, fasce=None, asset_times=(), asset_casi=("base",), asset_bbox=None, out_dir=None, walk_speed_m_s=None):
    """Ombra della baseline più gli interventi dello scenario, su tutti i casi del motore (edifici; con alberi censiti; con vegetazione LiDAR). cond["date"] = giorno.
    Senza interventi: le stesse righe del motore senza scenario (delta nullo). Gli interventi entrano in ogni caso come ostacoli aggiuntivi."""
    vol, alb = volumi_scenario(scn)
    method = {**cond["method"], "obstacles": "buildings_and_trees"}; casi = casi or CASI
    when = {"date": cond["date"], "timezone": "Europe/Rome", "times": cond["times"]}
    r = O.compute_shadow(scn["baseline_id"], rec, when, method, scenario_id=scn["scenario_id"], scenario_volumes=vol or None, scenario_trees=alb or None,
                         walk_speed_m_s=walk_speed_m_s or cond["walk_speed_m_s"], casi=casi, fasce=fasce if fasce is not None else cond["fasce"],
                         el_min=cond["el_min_deg"], asset_times=asset_times, asset_casi=asset_casi, asset_bbox=asset_bbox, out_dir=out_dir, scenario_version=scn["version"])
    man = r["manifest"]; man["scenario_id"], man["scenario_version"] = scn["scenario_id"], scn["version"]
    man["limits"] += [{"code": "scenario_ipotesi", "text": "Interventi ipotetici di classe scenario: dimensioni dichiarate, non da progetto; nessun modello di crescita né anni."},
                      {"code": "fattibilita_ignota", "text": "Fattibilità ignota: sottoservizi, spazio radicale, proprietà del suolo, permessi e specie non verificati."},
                      {"code": "chioma_scenario_ellissoide", "text": "Alberi di scenario come chiome ellissoidali opache, come gli alberi esistenti di F07; tronco trascurato; la vegetazione esistente è presente solo nei casi con alberi censiti e con vegetazione LiDAR."}]
    return r


def _chiave_cache(scn, rec, cond, casi, fasce, asset_times, asset_casi, asset_bbox):
    g = O.dati()["gpkg_sha256"]
    return sha_obj({"scn": {k: v for k, v in scn.items() if k != "created_at"}, "rec": [(r["receiver_id"], r["geometry"]) for r in rec], "cond": cond, "casi": casi, "fasce": fasce,
                    "assets": [list(asset_times), list(asset_casi), asset_bbox], "ombre": O.VERSIONE, "gpkg": g, "veg": (O.vegetazione_lidar(), O.dati()["veg_sha256"])[1], "f08": VERSIONE})[:20]


def ombra_con_cache(scn, rec=None, cond=None, casi=None, asset_times=(), asset_casi=("base",), asset_bbox=None, asset=False):
    """calcola_ombra con cache in data/norm/<area>/scenarios/jobs. Ritorna {job, manifest, sintesi, cached}. Con asset=True scrive i GeoJSON 4326 delle ombre in data/norm/<area>/scenarios/out
    (nome ombre_<scenario>_<data>_<hhmm>.geojson, con scenario_id nelle proprietà)."""
    rec = rec or ricevitori(); cond = cond or condizioni(); k = _chiave_cache(scn, rec, cond, casi, cond["fasce"], asset_times, asset_casi, asset_bbox)
    p = JOBS / f"{k}.json"
    if p.exists():
        c = json.loads(p.read_text())
        if all((ROOT / a["path"]).exists() for a in c["manifest"]["assets"] if a["role"] == "result_geometry"): return {**c, "cached": True}
    r = calcola_ombra(scn, rec, cond, casi=casi, asset_times=asset_times if asset else (), asset_casi=asset_casi, asset_bbox=asset_bbox, out_dir=OUT if asset else None)
    man = r["manifest"]
    for a in man["assets"]:   # nomi per scenario invece che per job; scenario_id nelle proprietà
        if a["role"] != "result_geometry": continue
        src = ROOT / a["path"]; hhmm = src.stem.rsplit("_", 1)[1]; dst = OUT / f"ombre_{scn['scenario_id']}_{cond['date']}_{hhmm}.geojson"
        fc = json.loads(src.read_text())
        for f in fc["features"]: f["properties"]["scenario_id"] = scn["scenario_id"]
        dst.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":"))); src.unlink()
        b = dst.read_bytes(); a.update(path=rel(dst), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    slim = ("receiver_id", "time_local", "caso", "stato", "shade_fraction", "walk_sun_min", "walk_stato")   # per-ora nel confronto
    c = {"job": r["job"], "manifest": man, "sintesi": r["sintesi"], "righe": [{k: x[k] for k in slim if k in x} for x in r["righe"]]}
    JOBS.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(c, ensure_ascii=False))
    return {**c, "cached": False}


def geojson_interventi(scn):
    """Interventi in EPSG:4326 per la scena: punto e cerchio della chioma per gli alberi, poligono per le pensiline; dimensioni e stato di ipotesi."""
    import shapely.ops
    from pyproj import Transformer
    tr = Transformer.from_crs(7791, 4326, always_xy=True).transform; feats = []
    ll = lambda g: arrotonda(mapping(shapely.transform(g, lambda a: np.column_stack(tr(a[:, 0], a[:, 1])))))
    for op in scn["operations"]:
        dims = {k: v["value"] for k, v in op["dimensions"].items()}
        base = {"scenario_id": scn["scenario_id"], "op_id": op["op_id"], "target_type": op["target_type"], "dimensions_m": dims, "classification": "scenario",
                "hypothesis_status": op["hypothesis_status"], "feasibility": "ignota", "dimension_source": next(iter(op["dimensions"].values()))["dimension_source"]}
        g = shape(op["geometry"])
        feats.append({"type": "Feature", "geometry": ll(g), "properties": {**base, "layer": "intervento"}})
        if op["target_type"] == "tree":
            feats.append({"type": "Feature", "geometry": ll(g.buffer(dims["crown_diameter_m"] / 2, quad_segs=16)), "properties": {**base, "layer": "chioma_proiezione"}})
    return {"type": "FeatureCollection", "name": scn["scenario_id"], "crs_note": "EPSG:4326; classe scenario, ipotesi, fattibilità ignota", "features": feats}
