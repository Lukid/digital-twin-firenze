"""Nucleo del servizio (T07, portato su Firenze in F10). CLI, API HTTP e server MCP chiamano solo run_tool(nome, argomenti).

Ogni input è validato contro contracts/schemas/mcp.schema.json prima di qualunque calcolo. I numeri vengono dalle
funzioni deterministiche di analysis/ (compute_walk_access). job_id = hash dell'input canonico (ADR-T02): se il manifest
esiste nella cache si restituisce quello, senza ricalcolare. Nessun SQL, nessun codice libero.
Risposta: sempre un dict, risultato oppure {"error": {code, message, ...}}."""
import hashlib, json, os, pathlib, re, shutil, sys, tempfile, unicodedata
from functools import lru_cache

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
# Area, baseline e cartelle vengono dal registro delle aree (stesso criterio dei motori: variabile DT_AOI, default Firenze Novoli).
AOI_ID = os.environ.get("DT_AOI", "aoi_firenze_novoli")
AREA = next(a for a in json.load(open(CONTRACTS / "aree.json"))["aree"] if a["aoi_id"] == AOI_ID)
SLUG = AOI_ID.removeprefix("aoi_")
BASELINE_ID = AREA["baseline_ids"][-1]
BASELINE = json.load(open(ROOT / "pipeline/baselines" / f"{BASELINE_ID}.json"))
NET = ROOT / "network" / SLUG
CACHE = pathlib.Path(os.environ.get("DT_CACHE_DIR") or ROOT / "service/cache" / SLUG)   # cache per area; deve stare sotto ROOT (i percorsi degli asset sono relativi a ROOT)
ID_DEST = re.compile(r"^dst_[a-z]{2,12}_[a-z0-9_]{2,60}$")
ENGINE_ORIGINS = "address_points"
TOOLS = ["list_approved_sources", "inspect_dataset", "list_destinations", "list_scenarios", "compute_walk_access", "get_job_status", "get_result_manifest", "compute_shadow", "create_local_scenario", "compare_scenarios", "get_source_card"]
# Fonti ammesse = solo quelle della baseline dell'area. Tema -> fonti candidate (le lacune nascono da fonti senza snapshot ok o senza uso permesso).
_BASE = {s["source_id"]: s["snapshot_id"] for s in BASELINE["snapshot"]}
_T = {"edifici": ["src_rt_uv_firenze_novoli", "src_osm_firenze"], "quote": ["src_fi_dsm2023", "src_fi_dtm2023"], "rete_pedonale": ["src_osm_firenze", "src_fi_barriere"],
      "verde": ["src_fi_alberi"], "trasporto": ["src_fi_tram_fermate", "src_gtfs_gest_firenze", "src_gtfs_at_firenze"],
      "destinazioni": ["src_fi_scuole_statali", "src_cm_edscol_firenze", "src_fi_rifugi_aree", "src_fi_rifugi_biblioteche", "src_osm_firenze", "src_fi_tram_fermate", "src_gtfs_gest_firenze", "src_gtfs_at_firenze"],
      "licenze": list(_BASE)}
THEMES = {t: [x for x in v if x in _BASE] for t, v in _T.items()}
GAPS_NOTI = {"verde": "Censimento alberi solo pubblico: chiome in parte stimate e imposta sempre stimata; vegetazione privata solo da LiDAR (prismi opachi, senza distinguere le specie).",
             "edifici": "Altezze LiDAR 2023 su unità volumetriche 2011; edifici nuovi solo dove li ha OSM; portici ignoti trattati come pieni.",
             "quote": "Datum verticale non confermato.",
             "rete_pedonale": "Rete solo OSM: lato del marciapiede, larghezze e pendenze ignoti."}

# Alias italiani delle destinazioni (chiave senza accenti, minuscola) -> id. Un alias con più id è ambiguo: il client chiede all'utente.
_DEST_ALIAS = {
    "polo": ["dst_university_w83537185"], "universita": ["dst_university_w83537185"], "ateneo": ["dst_university_w83537185"], "pandette": ["dst_university_w83537185"],
    "scienze sociali": ["dst_university_w83537185"], "polo scienze sociali": ["dst_university_w83537185"], "polo delle scienze sociali": ["dst_university_w83537185"],
    "scuola": ["dst_school_fiee86002g", "dst_school_fiaa86002a"], "vamba": ["dst_school_fiee86002g", "dst_school_fiaa86002a"], "scuola vamba": ["dst_school_fiee86002g", "dst_school_fiaa86002a"],
    "primaria vamba": ["dst_school_fiee86002g"], "scuola primaria": ["dst_school_fiee86002g"], "infanzia vamba": ["dst_school_fiaa86002a"], "scuola infanzia": ["dst_school_fiaa86002a"],
    "tram": ["dst_tram_fm9055", "dst_tram_fm9056", "dst_tram_fm9057"], "t2": ["dst_tram_fm9055", "dst_tram_fm9056", "dst_tram_fm9057"], "fermata": ["dst_tram_fm9055", "dst_tram_fm9056", "dst_tram_fm9057"], "fermata tram": ["dst_tram_fm9055", "dst_tram_fm9056", "dst_tram_fm9057"],
    "san donato": ["dst_tram_fm9055"], "fermata san donato": ["dst_tram_fm9055"], "san donato universita": ["dst_tram_fm9055"], "fermata universita": ["dst_tram_fm9055"], "fermata del polo": ["dst_tram_fm9055"],
    "fermata regione": ["dst_tram_fm9056"], "regione toscana": ["dst_tram_fm9056"], "regione": ["dst_tram_fm9056"],
    "torre degli agli": ["dst_tram_fm9057"], "fermata torre degli agli": ["dst_tram_fm9057"], "agli": ["dst_tram_fm9057"]}
CATEGORIA_CONTRATTO = {"tram": "stop"}   # il contratto ha school, university, stop, station, hospital: la fermata del tram è una fermata

canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
err = lambda code, msg, **k: {"error": {"code": code, "message": msg, **k}}
_load = lambda p: json.loads(pathlib.Path(p).read_text())
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn"))).strip()


# ---------- validazione ----------
@lru_cache(maxsize=1)
def _registry():
    from jsonschema import Draft202012Validator  # noqa: F401
    from referencing import Registry, Resource
    sch = {p.name: _load(p) for p in (CONTRACTS / "schemas").glob("*.schema.json")}
    return sch, Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in sch.values()])


def validator(defname):
    from jsonschema import Draft202012Validator
    sch, reg = _registry()
    return Draft202012Validator({"$ref": f"{sch['mcp.schema.json']['$id']}#/$defs/{defname}"}, registry=reg)


def validate(tool, direction, doc):
    """Lista di messaggi d'errore (vuota = valido)."""
    return [f"{'/'.join(map(str, e.path)) or '(radice)'}: {e.message[:160]}" for e in sorted(validator(f"{tool}.{direction}").iter_errors(doc), key=lambda e: list(e.path))]


def schema_for_client(tool):
    """JSON Schema dell'input del tool, con i $ref risolti (per l'elenco strumenti MCP)."""
    sch, _ = _registry()
    def res(n, cur="mcp.schema.json"):
        if isinstance(n, dict):
            if "$ref" in n:
                f, _, frag = n["$ref"].partition("#"); f = f or cur; doc = sch[f]
                for part in frag.strip("/").split("/"): doc = doc[part]
                return res(doc, f)
            return {k: res(v, cur) for k, v in n.items()}
        return [res(x, cur) for x in n] if isinstance(n, list) else n
    s = res(sch["mcp.schema.json"]["$defs"][f"{tool}.input"])
    if "oneOf" in s:   # inspect_dataset e compare_scenarios: una delle due forme; il controllo vero resta nel nucleo
        forme = {"inspect_dataset": "Indicare source_id oppure snapshot_id.", "compare_scenarios": "Indicare baseline_id e scenario_ids (confronto con la baseline) oppure manifest_ids e metric_ids (delta fra manifest di compute_shadow)."}
        s = {"type": "object", "additionalProperties": False, "properties": {k: v for o in s["oneOf"] for k, v in o["properties"].items()},
             "description": forme[tool]}
    if tool == "compute_walk_access":   # forma storica civici_sit_z2 (pilota precedente): resta valida per i contratti ma non si mostra al client
        o = s["properties"]["origins"]; o["oneOf"] = [x for x in o["oneOf"] if x["properties"]["kind"].get("const") != "civici_sit_z2"]
    s.pop("$schema", None)
    return s


# ---------- dati di progetto ----------
@lru_cache(maxsize=1)
def destinazioni():
    return _load(NET / "destinazioni.json")["destinazioni"]


def _ver(s): return {"verificato": "verified_on_site"}.get(s, "unverified")


def _dest_out(d):
    o = {"destination_id": d["destination_id"], "category": CATEGORIA_CONTRATTO.get(d["categoria"], d["categoria"]), "name": d["nome"], "verification": "verified_on_site" if d["stato_verifica"] == "verificato" else "desk_candidate",
         "entrances": [{"entrance_id": e["entrance_id"], "position": e["xy"], "verification": _ver(e["stato_verifica"])} for e in d["ingressi"]]}
    if d.get("condizioni_accesso"): o["access_conditions"] = d["condizioni_accesso"]
    return o


def _candidati(query=None):
    """Destinazioni che corrispondono al testo: alias italiani, poi nome, id e indirizzo (senza accenti né maiuscole)."""
    q = norm(query)
    if not q: return destinazioni()
    ids = _DEST_ALIAS.get(q)
    if ids: return [d for d in destinazioni() if d["destination_id"] in ids]
    return [d for d in destinazioni() if q in norm(d["nome"]) or q in norm(d["destination_id"]) or q in norm(d.get("indirizzo")) or q in norm(d.get("codice_mim"))]


def _snapshot_ok(source_id):
    """Snapshot della baseline per la fonte, se valido (status ok). Fuori baseline: None."""
    p = ROOT / "pipeline/snapshots" / f"{_BASE.get(source_id, 'x')}.json"
    if not p.exists(): return None
    s = _load(p); return s if s["status"] == "ok" else None


def _source(source_id):
    p = ROOT / "pipeline/sources" / f"{source_id}.json"
    return _load(p) if source_id in _BASE and p.exists() else None


# ---------- strumenti di sola lettura ----------
def list_approved_sources(a):
    if a["aoi_id"] != AOI_ID: return err("unknown_id", f"Area sconosciuta: {a['aoi_id']}. Disponibile: {AOI_ID}.", candidates=[AOI_ID])
    out, gaps = [], []
    for sid in THEMES[a["theme"]]:
        src, snap = _source(sid), _snapshot_ok(sid)
        if not src or not snap: gaps.append({"theme": a["theme"], "text": f"{sid}: nessuno snapshot valido."}); continue
        use = src["license"]["permitted_use"]
        if use == "none": gaps.append({"theme": a["theme"], "text": f"{sid}: uso non consentito dalla licenza."}); continue
        out.append({"source_id": sid, "snapshot_id": snap["snapshot_id"], "license_state": src["license"]["state"], "permitted_use": use,
                    "content_period": snap["content_period"] if "start" in snap["content_period"] else src["content_period"]})
    if a["theme"] in GAPS_NOTI: gaps.append({"theme": a["theme"], "text": GAPS_NOTI[a["theme"]]})
    return {"sources": out, "gaps": gaps}


def inspect_dataset(a):
    snap = None
    if "snapshot_id" in a:
        p = ROOT / "pipeline/snapshots" / f"{a['snapshot_id']}.json"
        if a["snapshot_id"] not in _BASE.values() or not p.exists(): return err("unknown_id", f"Snapshot fuori dalla baseline {BASELINE_ID}: {a['snapshot_id']}.", candidates=sorted(_BASE.values()))
        snap = _load(p); sid = snap["source_id"]
    else: sid = a["source_id"]
    src = _source(sid)
    if not src: return err("unknown_id", f"Fonte sconosciuta: {sid}.", candidates=sorted(_BASE))
    snap = snap or _snapshot_ok(sid)
    if not snap: return err("insufficient_data", f"{sid}: nessuno snapshot valido da ispezionare.")
    man = _load(NET / "rete_manifest.json"); u = src.get("units", {})
    lic = {k: v for k, v in src["license"].items() if k in ("state", "identifier", "evidence_url", "evidence_note", "reserve_note", "permitted_use")}
    return {"source_id": sid, "snapshot_id": snap["snapshot_id"],
            "fields": [{"name": f, "unit": u.get(f, "1"), "classification": "measured"} for f in src.get("schema_fields", [])],
            "extent": man["area_buffer_en"], "content_period": snap["content_period"] if "start" in snap["content_period"] else src["content_period"], "license": lic,
            "quality": [c["name"] + ": " + c["result"] + " (" + str(c["detail"]) + ")" for c in src.get("checks", [])] +
                       ["extent = riquadro del grafo dell'area pilota, non l'estensione della fonte", "unità '1' = non dichiarata dalla fonte; classificazione measured = valore grezzo di fonte"]}


SCHEDE = ROOT / "service/schede"   # generate da service/schede.py


def get_source_card(a):
    """Indice delle schede delle fonti, o la scheda di una fonte. Le schede coprono tutte le fonti dell'area, anche quelle fuori baseline."""
    ids = sorted(p.stem for p in SCHEDE.glob("src_*.md"))
    if "source_id" not in a: return {"index": (SCHEDE / "INDEX.md").read_text(), "source_ids": ids}
    if a["source_id"] not in ids: return err("unknown_id", f"Nessuna scheda per {a['source_id']}.", candidates=ids)
    return {"source_id": a["source_id"], "card": (SCHEDE / f"{a['source_id']}.md").read_text()}


def list_destinations(a):
    if a["aoi_id"] != AOI_ID: return err("unknown_id", f"Area sconosciuta: {a['aoi_id']}.", candidates=[AOI_ID])
    return {"destinations": [_dest_out(d) for d in _candidati(a.get("name_query")) if CATEGORIA_CONTRATTO.get(d["categoria"], d["categoria"]) == a["category"]]}


def list_scenarios(a):
    """Scenari salvati dell'area (versionati e creati dal client), con titolo, versione e riepilogo degli interventi."""
    if a.get("baseline_id", BASELINE_ID) != BASELINE_ID: return err("incompatible_baseline", f"Baseline disponibile: {BASELINE_ID}.", candidates=[BASELINE_ID])
    S, _ = _sc(); out = []
    for sid in sorted(S.elenco()):
        scn = S.carica(sid)
        out.append({"scenario_id": sid, "title": scn["title"], "version": scn["version"], "baseline_id": scn["baseline_id"], "interventions": S.riepilogo_interventi(scn)})
    return {"scenarios": out}


# ---------- job e cache ----------
CODICE_MOTORI = ["analysis/accessibilita.py", "network/rete_lib.py", "shadow/ombre.py", "scenarios/scenari.py", "scenarios/confronto.py", "service/core.py"]


@lru_cache(maxsize=1)
def _codice_e_dati():
    """Hash del codice dei motori (quello caricato all'avvio) e file di dati che i motori leggono."""
    for d in ("analysis", "shadow"): sys.path.insert(0, str(ROOT / d))
    import accessibilita as A, ombre as O
    return ({f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODICE_MOTORI},
            [O.GPKG, O.VEG_GPKG, A.RL.OUT / f"{A.RL.STEM}.pkl", A.RL.OUT / "origini_snap.gpkg"])


def _verifica_cache():
    """Gli job_id dipendono dalla richiesta, non dal codice né dai dati (R4): se cambia uno dei due, i risultati in cache non valgono più e si cancellano.
    Restano gli scenari creati dagli utenti."""
    codice, dati = _codice_e_dati()
    imp = hashlib.sha256(canon({"codice": codice, "dati": {str(p): [p.stat().st_size, p.stat().st_mtime_ns] if p.exists() else None for p in dati}}).encode()).hexdigest()[:16]
    f = CACHE / "impronta.txt"
    if f.exists() and f.read_text() == imp: return
    for p in [*CACHE.glob("job_*"), CACHE / "alias"]:   # job, manifest, sintesi, confronti, asset; alias delle ombre
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True); f.write_text(imp)   # senza lock: una richiesta in corso durante la pulizia può riscrivere un job vecchio; serve un lock se il servizio diventa multiutente


def _paths(job_id):
    return CACHE / f"{job_id}.job.json", CACHE / f"{job_id}.manifest.json"


def _read_job(job_id, what):
    """Cerca prima nella cache del servizio, poi tra i manifest versionati di analysis/<area>/, shadow/<area>/ e nl/<area>/."""
    for d in (CACHE, ROOT / "analysis" / SLUG / "manifest", ROOT / "shadow" / SLUG / "manifest", ROOT / "nl" / SLUG / "manifest"):
        p = d / f"{job_id}.{what}.json"
        if p.exists(): return _load(p)
    return None


def get_job_status(a):
    return _read_job(a["job_id"], "job") or err("unknown_id", f"Job sconosciuto: {a['job_id']}.")


def get_result_manifest(a):
    return _read_job(a["job_id"], "manifest") or err("unknown_id", f"Nessun manifest per il job {a['job_id']}.")


def _write(p, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=p.parent, suffix=".tmp", delete=False) as f:   # nome univoco: due richieste uguali non si pestano
        f.write(json.dumps(o, ensure_ascii=False, indent=1))
    try: os.replace(f.name, p)
    except OSError: os.unlink(f.name); raise


def _risposta(job, man, cached):
    return {"job_id": job["job_id"], "status": job["status"], "result_manifest_id": man["manifest_id"], "headline_metrics": man["metrics"], "cached": cached,
            "datasets": [{k: d[k] for k in ("snapshot_id", "source_id", "sha256", "license_state")} for d in man["datasets"]], "params": man["params"],
            "limits": man["limits"], "method": f"{man['method']['name']} {man['method']['version']}"}


def _risolvi_walk(a):
    """Argomenti validati -> argomenti di analysis.compute_walk_access, o errore. Nessun valore implicito oltre ai default dichiarati."""
    ids = sorted(set(a["destination_ids"]))   # più destinazioni = accessibilità verso almeno una (la più vicina)
    noti = {x["destination_id"]: x for x in destinazioni()}
    for i in ids:
        if i not in noti: return err("unknown_id", f"Destinazione sconosciuta: {i}.", candidates=[x["destination_id"] for x in _candidati(i.split("_", 2)[-1])][:10])
    if a["baseline_id"] != BASELINE_ID: return err("incompatible_baseline", f"Baseline disponibile: {BASELINE_ID}.", candidates=[BASELINE_ID])
    o = a["origins"]
    if o["kind"] != ENGINE_ORIGINS or o.get("aoi_id") != AOI_ID:
        return err("outside_capability", f"Il motore calcola solo con origini '{ENGINE_ORIGINS}' dell'area {AOI_ID} (civici come punti d'indirizzo); punti e griglia non sono ancora supportati.",
                   smaller_request={**a, "origins": {"kind": ENGINE_ORIGINS, "aoi_id": AOI_ID}})
    ents = {e["entrance_id"] for i in ids for e in noti[i]["ingressi"]}
    bad = [i for i in a.get("entrance_ids", []) if i not in ents]
    if bad: return err("invalid_params", f"Ingressi non appartenenti a {', '.join(ids)}: {bad}.", candidates=sorted(ents))
    p = a["profile"]
    return {"destination_id": ids[0] if len(ids) == 1 else ids, "profile": {"speed_m_s": p["speed_m_s"], "crossing_penalty_s": p.get("crossing_penalty_s", 0), "stairs": p.get("stairs", "allowed")},
            "snap_limit_m": p.get("snap_limit_m", 40), "thresholds_min": sorted(a["thresholds_min"]), "entrance_ids": sorted(a["entrance_ids"]) if a.get("entrance_ids") else None}


def _limiti(A, kw):
    """Limiti di area e di costo prima di eseguire. L'area è il riquadro delle origini; il costo è il numero di origini."""
    c = A.contesto(); x0, y0, x1, y1 = c["civ"].total_bounds; km2 = (x1 - x0) * (y1 - y0) / 1e6; n = len(c["civ"])
    if km2 > A.LIMITI["max_area_km2"]: return err("limit_exceeded", f"Area delle origini {km2:.1f} km2 oltre il limite di {A.LIMITI['max_area_km2']} km2.")
    if n > A.LIMITI["max_rows"]: return err("limit_exceeded", f"{n} origini oltre il limite di {A.LIMITI['max_rows']}.")


def _prevedi_job_id(A, kw):
    """job_id calcolato prima dell'esecuzione, con la stessa funzione che la libreria usa per il job."""
    return A.parametri_job(kw["destination_id"], ENGINE_ORIGINS, kw["profile"], kw["thresholds_min"], kw["snap_limit_m"], kw["entrance_ids"])[2]


def _esegui(kw, store=True, out_dir=None):
    sys.path.insert(0, str(ROOT / "analysis"))
    import accessibilita as A
    e = _limiti(A, kw)
    if e: return e
    try: jid = _prevedi_job_id(A, kw)
    except ValueError as ex: return err("invalid_params", str(ex))
    jp, mp = _paths(jid)
    if store and jp.exists() and mp.exists(): return _risposta(_load(jp), _load(mp), True)
    try:
        res = A.compute_walk_access(kw["destination_id"], profile=kw["profile"], thresholds_min=kw["thresholds_min"], snap_limit_m=kw["snap_limit_m"], entrance_ids=kw["entrance_ids"],
                                    out_dir=(CACHE / jid) if store else out_dir)
    except ValueError as ex: return err("invalid_params", str(ex))
    job, man = res["job"], res["manifest"]
    assert job["job_id"] == jid, f"job_id previsto {jid} diverso da quello calcolato {job['job_id']}"
    if man["timing"]["duration_s"] > job["limits"]["max_seconds"]: return err("limit_exceeded", "Tempo di calcolo oltre il limite.")
    if store: _write(mp, man); _write(jp, job)   # il job per ultimo: la sua presenza vale come cache completa
    return _risposta(job, man, False)


def compute_walk_access(a):
    kw = _risolvi_walk(a)
    return kw if "error" in kw else _esegui(kw)


SHADOW_MAX_COMBINAZIONI = 1500   # ricevitori x orari x casi: limite di costo del job (il calcolo è sincrono); i tempi veri sono nel REPORT-F10
OBST_VEG = "buildings_trees_and_lidar_vegetation"   # estensione del contratto: edifici, alberi censiti e vegetazione LiDAR (D14)
CASI_VEG = ["base", "base_h_min", "base_h_max", "alberi_min", "alberi_tipico", "alberi_max", "veg_lidar_min", "veg_lidar_tipico", "veg_lidar_max"]


def _percorso_campione(rid):
    import shapely.ops
    from pyproj import Transformer
    from shapely.geometry import mapping, shape
    from shapely import set_precision
    fs = {f["properties"]["id"]: f for f in _load(NET / "percorsi_campione.geojson")["features"] if f["properties"].get("stato") == "reachable" and "geometry" in f and f["geometry"]["type"] == "LineString"}
    if rid not in fs: return None, sorted(fs)
    to = Transformer.from_crs(4326, 7791, always_xy=True)
    g = shapely.ops.transform(lambda x, y, z=None: to.transform(x, y), shape(fs[rid]["geometry"]))
    return {"receiver_id": f"pth_fi_{rid}", "kind": "path", "geometry": mapping(set_precision(g, 0.01))}, sorted(fs)


def _risolvi_shadow(a):
    """Argomenti validati -> argomenti di ombre.compute_shadow (percorsi campione espansi), o errore."""
    if a["baseline_id"] != BASELINE_ID: return err("incompatible_baseline", f"Baseline disponibile: {BASELINE_ID}.", candidates=[BASELINE_ID])
    sid, ob = a.get("scenario_id"), a["method"]["obstacles"]
    if ob == "buildings_and_scenario" and not sid: return err("invalid_params", "buildings_and_scenario richiede scenario_id (creare lo scenario con create_local_scenario).")
    if sid and ob != "buildings_and_scenario":
        return err("invalid_params", "Con scenario_id usare obstacles=buildings_and_scenario: lo scenario si somma agli edifici documentati (nessun albero esistente).")
    if sid:
        S, _ = _sc()
        try: scn = S.carica(sid)
        except S.ScenarioError as e: return err(e.code, str(e), candidates=_cand_scn(e))
        if scn["baseline_id"] != a["baseline_id"]: return err("incompatible_baseline", f"Lo scenario {sid} parte dalla baseline {scn['baseline_id']}.", candidates=[scn["baseline_id"]])
    rec = []
    for r in a["receivers"]:
        if "route_id" in r:
            g, cand = _percorso_campione(r["route_id"])
            if not g: return err("unknown_id", f"Percorso campione sconosciuto: {r['route_id']}.", candidates=cand)
            rec.append(g)
        else: rec.append(r)
    ids = [r["receiver_id"] for r in rec]
    if len(set(ids)) != len(ids): return err("invalid_params", "receiver_id duplicati.")
    kw = {"baseline_id": a["baseline_id"], "receivers": rec, "when": a["when"], "method": a["method"], "walk_speed_m_s": a.get("walk_speed_m_s", 1.2)}
    if sid: kw.update(scenario_id=sid, scenario_sha256=S.sha_obj({k: v for k, v in scn.items() if k != "created_at"}))   # contenuto dello scenario nella chiave di cache
    return kw


def _alias_key(O, kw):
    g = O.GPKG.stat()
    return hashlib.sha256(canon({"kw": kw, "versione": O.VERSIONE, "gpkg": [g.st_size, g.st_mtime_ns]}).encode()).hexdigest()[:16]


def _risposta_shadow(job, man, extra, cached, casi):
    return {"job_id": job["job_id"], "status": job["status"], "result_manifest_id": man["manifest_id"], "headline_metrics": man["metrics"], "cached": cached,
            "datasets": [{k: d[k] for k in ("snapshot_id", "source_id", "sha256", "license_state")} for d in man["datasets"]], "params": man["params"], "limits": man["limits"],
            "method": f"{man['method']['name']} {man['method']['version']}", "cases": casi, **extra,
            **({"scenario_id": man["scenario_id"], "scenario_version": man["scenario_version"]} if "scenario_id" in man else {})}


def _esegui_shadow(kw, store=True):
    sys.path.insert(0, str(ROOT / "shadow"))
    import ombre as O
    ak = CACHE / "alias" / f"{_alias_key(O, kw)}.json"
    if store and ak.exists():
        jid = _load(ak)["job_id"]; jp, mp = _paths(jid)
        if jp.exists() and mp.exists(): return _risposta_shadow(_load(jp), _load(mp), _load(CACHE / f"{jid}.summary.json"), True, _load(ak)["cases"])
    method, casi_kw = kw["method"], kw.get("casi")
    if method["obstacles"] == OBST_VEG: method, casi_kw = {**method, "obstacles": "buildings_and_trees"}, CASI_VEG   # il motore chiede i casi veg_lidar_* con casi=[...]
    try:
        if kw.get("scenario_id"):   # baseline + interventi dello scenario (scenarios/scenari.py)
            S, _ = _sc(); cond = {"date": kw["when"]["date"], "times": kw["when"]["times"], "walk_speed_m_s": kw["walk_speed_m_s"], "fasce": [], "el_min_deg": O.EL_MIN_SUPPORTATA,
                                  "method": {k: kw["method"][k] for k in ("name", "space_step_m", "time_step_min")}}
            res = S.calcola_ombra(S.carica(kw["scenario_id"]), kw["receivers"], cond)
        else: res = O.compute_shadow(kw["baseline_id"], kw["receivers"], kw["when"], method, walk_speed_m_s=kw["walk_speed_m_s"], casi=casi_kw)
    except O.OraInesistente as e: return err("invalid_params", f"Ora inesistente: {str(e).split(' (')[0]} (salto dell'ora legale). Indicare un orario diverso.")
    except O.OraAmbigua as e: return err("invalid_params", f"Ora ambigua: {str(e).split(':')[0]} (fine ora legale). Chiedere all'utente se intende la prima (ora legale) o la seconda (ora solare), oppure scegliere un altro orario.")
    except ValueError as e: return err("invalid_params", str(e))
    job, man = json.loads(json.dumps(res["job"])), json.loads(json.dumps(res["manifest"])); rows = res["righe"]; casi = job["params"]["casi"]   # via JSON: stessa forma della cache (liste, non tuple)
    extra = {"sun_state_counts": {s: sum(1 for r in rows if r["stato"] == s) for s in sorted({r["stato"] for r in rows})}, "summary": res["sintesi"]}
    if store:
        jid = job["job_id"]; _write(CACHE / f"{jid}.summary.json", extra); _write(_paths(jid)[1], man); _write(_paths(jid)[0], job)
        _write(ak, {"job_id": jid, "cases": casi})
    return _risposta_shadow(job, man, extra, False, casi)


def _limite_shadow(a):
    """Costo = ricevitori x orari x casi. Oltre il limite: errore con la richiesta più piccola praticabile (stessi campi dell'input)."""
    sys.path.insert(0, str(ROOT / "shadow"))
    import ombre as O
    n_casi = len(CASI_VEG) if a["method"]["obstacles"] in (OBST_VEG, "buildings_and_scenario") else len(O.CASI_PER_OSTACOLI[a["method"]["obstacles"]]); times = a["when"]["times"]; recs = a["receivers"]
    comb = len(recs) * len(times) * n_casi
    if comb <= SHADOW_MAX_COMBINAZIONI: return None
    passo = -(-comb // SHADOW_MAX_COMBINAZIONI); small = {**a, "when": {**a["when"], "times": times[::passo]}}
    if len(recs) * len(small["when"]["times"]) * n_casi > SHADOW_MAX_COMBINAZIONI:
        small["receivers"] = recs[:max(1, SHADOW_MAX_COMBINAZIONI // (n_casi * len(small["when"]["times"])))]
    return err("limit_exceeded", f"{len(recs)} ricevitori x {len(times)} orari x {n_casi} casi = {comb} combinazioni, oltre il limite di {SHADOW_MAX_COMBINAZIONI}. "
               f"Ridurre gli orari (uno ogni {passo}) o i percorsi.", smaller_request=small)


def compute_shadow(a):
    e = _limite_shadow(a)
    if e: return e
    kw = _risolvi_shadow(a)
    return kw if "error" in kw else _esegui_shadow(kw)


def _fuori(msg): return err("outside_capability", msg + ". Nessun risultato numerico disponibile per questa richiesta.")


# ---------- scenari (chiamati in modo generico: le librerie sono in scenarios/, portate su Firenze a parte) ----------
def _sc():
    """Librerie di scenarios/ (scenari, confronto), caricate al primo uso."""
    for d in ("scenarios", "shadow"):
        if str(ROOT / d) not in sys.path: sys.path.insert(0, str(ROOT / d))
    import scenari, confronto
    return scenari, confronto


def _cand_scn(e):
    """Alternative proposte da scenarios/: solo gli scenari di Firenze (id scn_fi_*), mai quelli del pilota precedente."""
    return [c for c in (e.candidates or []) if str(c).startswith("scn_fi_")]


def create_local_scenario(a):
    """Crea e salva uno scenario versionato (id = hash del contenuto: stesso input, stesso scenario). Segnala, senza bloccare, gli interventi dentro edifici o su carreggiata."""
    S, _ = _sc()
    try:
        scn = S.crea_scenario(a["baseline_id"], a["scenario_title"], a["operations"], autore="client MCP")
        v = S.valida(scn); _, creato = S.salva(scn)
    except S.ScenarioError as e: return err(e.code, str(e), **({"candidates": _cand_scn(e)} if _cand_scn(e) else {}))
    return {"scenario_id": scn["scenario_id"], "version": scn["version"], "cached": not creato, "warnings": v["warnings"], "feasibility": v["feasibility"], "interventions": S.riepilogo_interventi(scn)}


def _dati_baseline(S):
    b = S.baseline(); return [{k: s[k] for k in ("snapshot_id", "source_id", "sha256", "license_state")} for s in b["snapshot"]]


def _metrica_delta(mid, label, d, unit, scope):
    m = {"metric_id": mid[:60], "label": label, "value": d["delta"], "unit": unit, "classification": "scenario", "scope": scope}
    m["uncertainty"] = {"kind": "interval", "low": min(d["intervallo"]), "high": max(d["intervallo"]), "basis": "delta accoppiato sui casi estremi del contesto (altezze degli edifici, chiome, vegetazione LiDAR); lato del marciapiede non modellato"}
    return m


CONTESTI_CMP = {"solo_edifici": "edifici", "con_alberi_esistenti": "alb", "con_vegetazione_lidar": "lidar"}   # contesto -> suffisso dei metric_id


def _contesti(ctx):
    """context dell'input -> contesti di scenarios/ ('entrambi' = tutti: nome storico del contratto)."""
    return list(CONTESTI_CMP) if ctx == "entrambi" else [ctx]


def _compatta(e, ctxs):
    """Riepilogo di uno scenario per la risposta, nei contesti chiesti: percorsi campione, area di attesa, archi più usati, accessibilità, robustezza.
    Il dettaglio per ora (per_ora) resta in scenarios/<area>/confronto.json."""
    out = {k: e[k] for k in ("titolo", "stato", "job_id", "manifest_id", "interventi", "segnalazioni", "fattibilita", "incompatibilita") if k in e}
    if e.get("stato") != "confrontato": return out
    out.update(percorsi={d: {c: t[c] for c in ctxs} for d, t in e["percorsi"].items()}, area_attesa_polo={d: {c: t[c] for c in ctxs} for d, t in e["area_attesa_polo"].items()},
               aree_attesa={rid: {d: {c: t[c] for c in ctxs} for d, t in v.items()} for rid, v in e.get("aree_attesa", {}).items()},   # pensiline S5 e S6
               archi_usati=e["archi_usati"], accessibilita={k: v for k, v in e["accessibilita"].items() if k != "ricalcolo"}, fasce_utili_R01=e["fasce_utili_R01"], robustezza=e.get("robustezza", {}))
    if "sovrapposizioni_alberi_esistenti" in e: out["sovrapposizioni_alberi_esistenti"] = e["sovrapposizioni_alberi_esistenti"]
    return out


def _compare_job(inputs, params, metrics, limits, payload, store, t0):
    import datetime
    jid = "job_" + hashlib.sha256(canon({"tool": "compare_scenarios", "inputs": inputs, "params": params}).encode()).hexdigest()[:16]
    t1 = datetime.datetime.now(datetime.timezone.utc); fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    man = {"manifest_id": "man_" + jid[4:], "job_id": jid, "tool": "compare_scenarios", "aoi_id": AOI_ID, "baseline_id": inputs["baseline_id"], "datasets": payload["datasets"], "params": params,
           "method": {"name": "scenario_comparison", "version": payload["method_version"], "description": "Delta accoppiati scenario meno baseline su condizioni comuni (stessi ricevitori, date, fasce, passi, geometrie), con intervalli da altezze e lato; nessun punteggio unico."},
           "crs": "EPSG:7791", "vertical_datum_status": "not_confirmed", "timezone": "Europe/Rome",
           "timing": {"started_at": fmt(t0), "finished_at": fmt(t1), "duration_s": round((t1 - t0).total_seconds(), 2)}, "metrics": metrics,
           "limits": limits, "validation_status": "not_validated_locally", "assets": []}
    job = {"job_id": jid, "tool": "compare_scenarios", "status": "succeeded", "created_at": fmt(t0), "started_at": fmt(t0), "finished_at": fmt(t1), "inputs": inputs, "params": params,
           "limits": {"max_area_km2": 4, "max_rows": 50000, "max_seconds": 3600, "max_memory_mb": 4096}, "progress": {"fraction": 1.0, "message": "completato"}, "result_manifest_id": man["manifest_id"]}
    return jid, job, man


def _compare_da_manifest(a):
    """Forma 1: delta fra manifest di compute_shadow già eseguiti (il primo è il riferimento, senza scenario)."""
    import datetime; t0 = datetime.datetime.now(datetime.timezone.utc); S, C = _sc()
    jobs, mans = [], []
    for mid in a["manifest_ids"]:
        j, m = _read_job("job_" + mid[4:], "job"), _read_job("job_" + mid[4:], "manifest")
        if not j or not m: return err("unknown_id", f"Manifest sconosciuto: {mid}.")
        if m["tool"] != "compute_shadow": return err("invalid_params", f"{mid}: il confronto per manifest vale per compute_shadow.")
        jobs.append(j); mans.append(m)
    ref_j, ref_m = jobs[0], mans[0]
    inputs = {"baseline_id": ref_j["inputs"]["baseline_id"], "snapshot_ids": ref_j["inputs"]["snapshot_ids"]}; params = {"manifest_ids": a["manifest_ids"], "metric_ids": a["metric_ids"]}
    jid = "job_" + hashlib.sha256(canon({"tool": "compare_scenarios", "inputs": inputs, "params": params}).encode()).hexdigest()[:16]; jp, mp = _paths(jid)
    if jp.exists() and mp.exists() and (CACHE / f"{jid}.compare.json").exists(): return {**_load(CACHE / f"{jid}.compare.json"), "cached": True}
    incomp, deltas = [], []
    ix_ref = {m["metric_id"]: m for m in ref_m["metrics"]}
    for j, m in zip(jobs[1:], mans[1:]):
        scope = m.get("scenario_id") or m["manifest_id"]
        inc = C.incompatibilita(ref_j, j)
        if inc: incomp += [{"code": i["code"], "text": f"{scope}: {i['text']}"} for i in inc]; continue
        for mid in a["metric_ids"]:
            cand = sorted(k for k in ix_ref if k == mid or k.endswith("_" + mid) or mid in k)
            if not cand: incomp.append({"code": "metrica_assente", "text": f"{mid}: nessuna metrica corrispondente nel manifest di riferimento."}); continue
            ix_s = {x["metric_id"]: x for x in m["metrics"]}
            for k in cand:
                if k not in ix_s: incomp.append({"code": "metrica_assente", "text": f"{k}: assente nel manifest {m['manifest_id']}."}); continue
                b_, s_ = ix_ref[k], ix_s[k]; d = round(s_["value"] - b_["value"], 6); ub, us = b_.get("uncertainty"), s_.get("uncertainty")
                lo, hi = (min(us["low"] - ub["low"], us["high"] - ub["high"], d), max(us["low"] - ub["low"], us["high"] - ub["high"], d)) if ub and us and ub["kind"] == us["kind"] == "interval" else (d, d)
                deltas.append({"metric_id": k, "baseline_value": b_["value"], "scenario_value": s_["value"], "delta": d, "delta_low": round(lo, 6), "delta_high": round(hi, 6), "unit": b_["unit"],
                               "classification": s_["classification"], "discriminates": bool(lo > C.TOL or hi < -C.TOL), "scope": f"{scope} - {b_.get('scope', '')}"})
    cc = {"baseline_id": ref_j["inputs"]["baseline_id"], "date": ref_j["params"]["when"]["date"], "times": ref_j["params"]["when"]["times"], "method": {k: v for k, v in ref_j["params"]["method"].items() if k != "obstacles"},
          "walk_speed_m_s": ref_j["params"]["walk_speed_m_s"], "receivers": [r["receiver_id"] for r in ref_j["params"]["receivers"]], "motore_ombre": ref_m["method"]["version"]}
    if not deltas and not incomp: incomp.append({"code": "nessun_delta", "text": "Nessuna metrica confrontabile."})
    if not deltas: return err("incompatible_baseline", "Confronto respinto: " + "; ".join(i["text"] for i in incomp)[:300])
    met = [_metrica_delta(f"d{n}_{d['metric_id']}", f"Delta {d['metric_id']}", {"delta": d["delta"], "intervallo": [d["delta_low"], d["delta_high"]]}, d["unit"], d["scope"]) for n, d in enumerate(deltas)]
    lim = [{"code": "confronto_per_manifest", "text": "Delta fra i valori dei manifest indicati; l'intervallo accoppia gli estremi di sensibilità dei due manifest."}, *ref_m["limits"][:3]]
    payload = {"datasets": ref_m["datasets"], "method_version": "0.1.0"}
    jid, job, man = _compare_job(inputs, params, met, lim, payload, True, t0)
    r = {"common_conditions": cc, "deltas": deltas, "incompatibilities": incomp, "job_id": jid, "result_manifest_id": man["manifest_id"], "status": "succeeded", "cached": False,
         "datasets": man["datasets"], "params": params, "limits": lim, "method": "scenario_comparison 0.1.0"}
    _write(CACHE / f"{jid}.compare.json", {k: v for k, v in r.items() if k != "cached"}); _write(_paths(jid)[1], man); _write(_paths(jid)[0], job)
    return r


def _compare_scenari(a):
    """Forma 2: confronto di scenari con la baseline S0 (scenarios/confronto.py), per data e contesto. Contesto principale: vegetazione LiDAR (D14).
    Le ombre degli scenari sono in cache (data/norm/<area>/scenarios/jobs): se mancano, il calcolo richiede alcuni minuti per scenario."""
    import datetime; t0 = datetime.datetime.now(datetime.timezone.utc); S, C = _sc()
    if a["baseline_id"] != BASELINE_ID: return err("incompatible_baseline", f"Baseline disponibile: {BASELINE_ID}.", candidates=[BASELINE_ID])
    if a.get("weights"): return err("outside_capability", "Nessun ordinamento con pesi: il confronto riporta indicatori separati, senza punteggio unico. Togliere weights.")
    try: scns = [S.carica(i) for i in a["scenario_ids"]]
    except S.ScenarioError as e: return err(e.code, str(e), candidates=_cand_scn(e))
    dif = S.verifica_baseline()
    if dif: return err("incompatible_baseline", "La baseline non coincide con il record congelato: " + "; ".join(dif)[:250])
    wv = a.get("with_variants", True); ctx = a.get("context", S.CONTESTO_PRINCIPALE); ctxs = _contesti(ctx)
    inputs = {"baseline_id": a["baseline_id"], "snapshot_ids": sorted(s["snapshot_id"] for s in S.baseline()["snapshot"])}
    params = {"scenario_ids": a["scenario_ids"], "scenario_sha256": [S.sha_obj({k: v for k, v in s.items() if k != "created_at"}) for s in scns], "with_variants": wv, "context": ctx, "method_version": C.VERSIONE,
              "ombre_version": S.O.VERSIONE, "baseline_record_sha256": S.stato_baseline()["record_sha256"]}
    jid = "job_" + hashlib.sha256(canon({"tool": "compare_scenarios", "inputs": inputs, "params": params}).encode()).hexdigest()[:16]; jp, mp = _paths(jid); cp = CACHE / f"{jid}.compare.json"
    if jp.exists() and mp.exists() and cp.exists(): return {**_load(cp), "cached": True}
    try: riep = C.confronta(a["scenario_ids"], con_varianti=wv, parallelo=False)   # senza processi figli: dal servizio il lancio in parallelo non è affidabile
    except S.ScenarioError as e: return err(e.code, str(e))
    inc = [{"code": i["code"], "text": f"{sid}: {i['text']}"} for sid, e in riep["scenari"].items() for i in e.get("incompatibilita", [])]
    deltas, met = [], []
    def aggiungi(mid, d, unit, sc, label):
        deltas.append({"metric_id": mid[:60], "baseline_value": d["baseline"], "scenario_value": d["scenario"], "delta": d["delta"], "delta_low": d["intervallo"][0], "delta_high": d["intervallo"][1],
                       "unit": unit, "classification": "scenario", "discriminates": d["discrimina"], "scope": sc}); met.append(_metrica_delta(mid, label, d, unit, sc))
    for n, (sid, e) in enumerate(riep["scenari"].items(), 1):
        if e.get("stato") != "confrontato": continue
        for data, perc in e["percorsi"].items():
            dd = data[5:].replace("-", "")
            for c in ctxs:
                for r, tab in perc[c].items():
                    for f, mm in tab.items():
                        for k, unit, nome in (("minuti_sole", "min", "sun_min"), ("frazione_ombra", "1", "shade")):
                            if mm[k]: aggiungi(f"sc{n}_{r.lower()}_{dd}_{f.split('_')[0]}_{nome}_{CONTESTI_CMP[c]}", mm[k], unit, f"{sid}, {r}, {data}, fascia {f}, contesto {c}", f"Delta {nome} {r}")
                for f, d in e["area_attesa_polo"][data][c].items():
                    if d: aggiungi(f"sc{n}_attesa_{dd}_{f.split('_')[0]}_shade_{CONTESTI_CMP[c]}", d, "1", f"{sid}, area di attesa Polo, {data}, fascia {f}, contesto {c}", "Delta ombra area di attesa")
                for rid, per_data in e.get("aree_attesa", {}).items():   # sfc_fi_attesa_s5 -> sc3_attesa_s5_...
                    for f, d in per_data[data][c].items():
                        if d: aggiungi(f"sc{n}_{rid.removeprefix('sfc_fi_')}_{dd}_{f.split('_')[0]}_shade_{CONTESTI_CMP[c]}", d, "1", f"{sid}, area di attesa {rid}, {data}, fascia {f}, contesto {c}", f"Delta ombra area di attesa {rid}")
    if not met: return err("incompatible_baseline", "Confronto respinto: " + "; ".join(i["text"] for i in inc)[:300])
    cc = {"baseline_id": riep["baseline_id"], "reference": riep["riferimento"]["scenario_id"], **{k: riep["condizioni_comuni"][k] for k in ("date", "fasce", "method", "walk_speed_m_s", "motore_ombre", "origini_e_percorsi", "contesto_principale")},
          "ricevitori": len(riep["condizioni_comuni"]["ricevitori"]), "contesti": {c: riep["condizioni_comuni"]["contesti"][c] for c in ctxs}}
    lim = [{"code": f"dichiarazione_{i + 1}", "text": t} for i, t in enumerate(riep["dichiarazioni"])]
    jid2, job, man = _compare_job(inputs, params, met, lim, {"datasets": _dati_baseline(S), "method_version": C.VERSIONE}, True, t0); assert jid2 == jid
    r = {"common_conditions": cc, "deltas": deltas, "incompatibilities": inc, "job_id": jid, "result_manifest_id": man["manifest_id"], "status": "succeeded", "datasets": man["datasets"], "params": params,
         "limits": lim, "method": f"scenario_comparison {C.VERSIONE}", "scenarios": {sid: _compatta(e, ctxs) for sid, e in riep["scenari"].items()}}
    _write(cp, r); _write(_paths(jid)[1], man); _write(_paths(jid)[0], job)
    return {**r, "cached": False}


def compare_scenarios(a):
    return _compare_da_manifest(a) if "manifest_ids" in a else _compare_scenari(a)


# ---------- punto d'ingresso unico ----------
def run_tool(name, args=None):
    args = args if isinstance(args, dict) else {}
    if name not in TOOLS: return err("unknown_id", f"Strumento sconosciuto: {name}.", candidates=TOOLS)
    if name == "compute_walk_access":   # destinazione mancante o data per nome: mai una scelta implicita
        ids = args.get("destination_ids")
        if not ids or not isinstance(ids, list) or any(not isinstance(i, str) or not ID_DEST.match(i) for i in ids):
            q = next((i for i in ids if isinstance(i, str) and not ID_DEST.match(i)), None) if isinstance(ids, list) else None
            cand = (_candidati(q) if q else []) or destinazioni()
            return err("ambiguous_destination", "Destinazione mancante o indicata per nome: scegliere un destination_id fra i candidati (list_destinations).",
                       candidates=[d["destination_id"] + " | " + d["nome"] for d in cand][:25])
    problemi = validate(name, "input", args)
    if problemi: return err("invalid_params", "; ".join(problemi[:5]))
    if name in ("compute_walk_access", "compute_shadow", "compare_scenarios"): _verifica_cache()
    return globals()[name](args)
