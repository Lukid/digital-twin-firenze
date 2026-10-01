"""T07: nucleo del servizio. CLI, API HTTP e server MCP chiamano solo run_tool(nome, argomenti).

Ogni input è validato contro contracts/schemas/mcp.schema.json prima di qualunque calcolo. I numeri vengono dalle
funzioni deterministiche di analysis/ (compute_walk_access). job_id = hash dell'input canonico (ADR-T02): se il manifest
esiste nella cache si restituisce quello, senza ricalcolare. Nessun SQL, nessun codice libero.
Risposta: sempre un dict, risultato oppure {"error": {code, message, ...}}."""
import json, os, pathlib, re, sys, tempfile
from functools import lru_cache

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
CACHE = pathlib.Path(os.environ.get("DT_CACHE_DIR") or ROOT / "service/cache")   # deve stare sotto ROOT (i percorsi degli asset sono relativi a ROOT)
BASELINE_ID, AOI_ID = "bas_z2_20261001", "aoi_z2"
ID_DEST = re.compile(r"^dst_[a-z]{2,12}_[a-z0-9_]{2,60}$")
ENGINE_ORIGINS = "civici_sit_z2"
TOOLS_FUTURI = {"compute_shadow": "il motore d'ombra (T09) non è ancora disponibile",
                "create_local_scenario": "gli scenari locali (T10) non sono ancora disponibili",
                "compare_scenarios": "il confronto fra scenari (T10) non è ancora disponibile"}
TOOLS = ["list_approved_sources", "inspect_dataset", "list_destinations", "compute_walk_access", "get_job_status", "get_result_manifest", *TOOLS_FUTURI]
THEMES = {  # tema -> fonti candidate (le lacune nascono da fonti senza snapshot ok o senza uso permesso)
    "edifici": ["src_rt_unita_volumetriche", "src_rt_dbt10k_pisa", "src_sit_edifici_scolastici", "src_osm_pisa"],
    "quote": ["src_rt_dsm2021", "src_rt_dtm10"], "rete_pedonale": ["src_osm_pisa", "src_rt_iternet"],
    "verde": [], "destinazioni": ["src_sit_scuole", "src_sit_edifici_scolastici", "src_osm_pisa", "src_gtfs_at_toscana", "src_gtfs_trenitalia"],
    "trasporto": ["src_gtfs_at_toscana", "src_gtfs_trenitalia"],
    "licenze": ["src_gtfs_at_toscana", "src_gtfs_trenitalia", "src_osm_pisa", "src_rt_dbt10k_pisa", "src_rt_dsm2021", "src_rt_dtm10", "src_rt_iternet",
                "src_rt_unita_volumetriche", "src_sit_civici", "src_sit_edifici_scolastici", "src_sit_scuole"]}
GAPS_NOTI = {"verde": "Nessun censimento di alberi o chiome tra le fonti ammesse: serve rilievo locale o fonte da acquisire.",
             "edifici": "Edifici posteriori al 2010 senza altezza misurata (da DSM 2021 o rilievo); portici e volumi sospesi non rilevati.",
             "quote": "Datum verticale non confermato; DTM 10 m con epoca non dichiarata."}

canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
err = lambda code, msg, **k: {"error": {"code": code, "message": msg, **k}}
_load = lambda p: json.loads(pathlib.Path(p).read_text())


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
    if "oneOf" in s:   # inspect_dataset: uno tra source_id e snapshot_id; il controllo vero resta nel nucleo
        s = {"type": "object", "additionalProperties": False, "properties": {k: v for o in s["oneOf"] for k, v in o["properties"].items()},
             "description": "Indicare source_id oppure snapshot_id."}
    s.pop("$schema", None)
    return s


# ---------- dati di progetto ----------
@lru_cache(maxsize=1)
def destinazioni():
    return _load(ROOT / "network/destinazioni.json")["destinazioni"]


def _ver(s): return {"verificato": "verified_on_site"}.get(s, "unverified")


def _dest_out(d):
    o = {"destination_id": d["destination_id"], "category": d["categoria"], "name": d["nome"], "verification": "verified_on_site" if d["stato_verifica"] == "verificato" else "desk_candidate",
         "entrances": [{"entrance_id": e["entrance_id"], "position": e["xy"], "verification": _ver(e["stato_verifica"])} for e in d["ingressi"]]}
    if d.get("condizioni_accesso"): o["access_conditions"] = d["condizioni_accesso"]
    return o


def _candidati(query=None):
    q = (query or "").lower().strip()
    return [d for d in destinazioni() if not q or q in d["nome"].lower() or q in d["destination_id"] or q in (d.get("indirizzo") or "").lower()]


def _snapshot_ok(source_id):
    ss = [s for s in (_load(p) for p in sorted((ROOT / "pipeline/snapshots").glob("*.json"))) if s["source_id"] == source_id and s["status"] == "ok"]
    return ss[-1] if ss else None


def _source(source_id):
    p = ROOT / "pipeline/sources" / f"{source_id}.json"
    return _load(p) if p.exists() else None


# ---------- strumenti di sola lettura ----------
def list_approved_sources(a):
    out, gaps = [], []
    if a["aoi_id"] != AOI_ID: return err("unknown_id", f"Area sconosciuta: {a['aoi_id']}. Disponibile: {AOI_ID}.", candidates=[AOI_ID])
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
        if not p.exists(): return err("unknown_id", f"Snapshot sconosciuto: {a['snapshot_id']}.")
        snap = _load(p); sid = snap["source_id"]
    else: sid = a["source_id"]
    src = _source(sid)
    if not src: return err("unknown_id", f"Fonte sconosciuta: {sid}.", candidates=sorted(p.stem for p in (ROOT / "pipeline/sources").glob("src_*.json")))
    snap = snap or _snapshot_ok(sid)
    if not snap: return err("insufficient_data", f"{sid}: nessuno snapshot valido da ispezionare.")
    man = _load(ROOT / "network/rete_manifest.json"); u = src.get("units", {})
    lic = {k: v for k, v in src["license"].items() if k in ("state", "identifier", "evidence_url", "evidence_note", "reserve_note", "permitted_use")}
    return {"source_id": sid, "snapshot_id": snap["snapshot_id"],
            "fields": [{"name": f, "unit": u.get(f, "1"), "classification": "measured"} for f in src["schema_fields"]],
            "extent": man["area_buffer_en"], "content_period": snap["content_period"] if "start" in snap["content_period"] else src["content_period"], "license": lic,
            "quality": [c["name"] + ": " + c["result"] + " (" + str(c["detail"]) + ")" for c in src.get("checks", [])] +
                       ["extent = riquadro del grafo pilota Z2, non l'estensione della fonte", "unità '1' = non dichiarata dalla fonte; classificazione measured = valore grezzo di fonte"]}


def list_destinations(a):
    if a["aoi_id"] != AOI_ID: return err("unknown_id", f"Area sconosciuta: {a['aoi_id']}.", candidates=[AOI_ID])
    return {"destinations": [_dest_out(d) for d in _candidati(a.get("name_query")) if d["categoria"] == a["category"]]}


# ---------- job e cache ----------
def _paths(job_id):
    return CACHE / f"{job_id}.job.json", CACHE / f"{job_id}.manifest.json"


def _read_job(job_id, what):
    """Cerca prima nella cache del servizio, poi tra i manifest già prodotti da analysis/ (T06)."""
    for d in (CACHE, ROOT / "analysis/manifest"):
        p = d / f"{job_id}.{what}.json"
        if p.exists(): return _load(p)
    return None


def get_job_status(a):
    return _read_job(a["job_id"], "job") or err("unknown_id", f"Job sconosciuto: {a['job_id']}.")


def get_result_manifest(a):
    return _read_job(a["job_id"], "manifest") or err("unknown_id", f"Nessun manifest per il job {a['job_id']}.")


def _write(p, o):
    p.parent.mkdir(parents=True, exist_ok=True); t = p.with_suffix(".tmp"); t.write_text(json.dumps(o, ensure_ascii=False, indent=1)); t.replace(p)


def _risposta(job, man, cached):
    return {"job_id": job["job_id"], "status": job["status"], "result_manifest_id": man["manifest_id"], "headline_metrics": man["metrics"], "cached": cached,
            "datasets": [{k: d[k] for k in ("snapshot_id", "source_id", "sha256", "license_state")} for d in man["datasets"]], "params": man["params"],
            "limits": man["limits"], "method": f"{man['method']['name']} {man['method']['version']}"}


def _risolvi_walk(a):
    """Argomenti validati -> argomenti di analysis.compute_walk_access, o errore. Nessun valore implicito oltre ai default dichiarati."""
    ids = a["destination_ids"]
    if len(ids) > 1:
        return err("limit_exceeded", "Il motore calcola una destinazione per job: ripetere la richiesta per ciascuna.", candidates=ids, smaller_request={**a, "destination_ids": ids[:1]})
    d = next((x for x in destinazioni() if x["destination_id"] == ids[0]), None)
    if not d: return err("unknown_id", f"Destinazione sconosciuta: {ids[0]}.", candidates=[x["destination_id"] for x in _candidati(ids[0].split("_", 2)[-1])][:10])
    if a["baseline_id"] != BASELINE_ID: return err("incompatible_baseline", f"Baseline disponibile: {BASELINE_ID}.", candidates=[BASELINE_ID])
    if a["origins"]["kind"] != ENGINE_ORIGINS:
        return err("outside_capability", f"Il motore calcola solo con origini '{ENGINE_ORIGINS}' (civici SIT di Z2); punti e griglia non sono ancora supportati.", smaller_request={**a, "origins": {"kind": ENGINE_ORIGINS}})
    ents = {e["entrance_id"] for e in d["ingressi"]}
    bad = [i for i in a.get("entrance_ids", []) if i not in ents]
    if bad: return err("invalid_params", f"Ingressi non appartenenti a {ids[0]}: {bad}.", candidates=sorted(ents))
    p = a["profile"]
    return {"destination_id": ids[0], "profile": {"speed_m_s": p["speed_m_s"], "crossing_penalty_s": p.get("crossing_penalty_s", 0), "stairs": p.get("stairs", "allowed")},
            "snap_limit_m": p.get("snap_limit_m", 40), "thresholds_min": sorted(a["thresholds_min"]), "entrance_ids": sorted(a["entrance_ids"]) if a.get("entrance_ids") else None}


def _limiti(A, kw):
    """Limiti di area e di costo prima di eseguire. L'area è il riquadro delle origini; il costo è il numero di origini."""
    c = A.contesto(); x0, y0, x1, y1 = c["civ"].total_bounds; km2 = (x1 - x0) * (y1 - y0) / 1e6; n = len(c["civ"])
    if km2 > A.LIMITI["max_area_km2"]: return err("limit_exceeded", f"Area delle origini {km2:.1f} km2 oltre il limite di {A.LIMITI['max_area_km2']} km2.")
    if n > A.LIMITI["max_rows"]: return err("limit_exceeded", f"{n} origini oltre il limite di {A.LIMITI['max_rows']}.")


def _prevedi_job_id(A, kw):
    """job_id calcolato prima dell'esecuzione con gli stessi parametri che la libreria mette nel job."""
    c = A.contesto(); d = c["dest"][kw["destination_id"]]; ids = kw["entrance_ids"] or [d["ingresso_predefinito"]]
    params = {"destination_ids": [kw["destination_id"]], "entrance_ids": sorted(ids), "origins": {"kind": ENGINE_ORIGINS, "count": len(c["civ"])},
              "profile": {**kw["profile"], "snap_limit_m": float(kw["snap_limit_m"])}, "thresholds_min": sorted(float(t) for t in kw["thresholds_min"]),
              "deviazione_alta": dict(A.DEVIAZIONE_ALTA), "method_version": A.VERSIONE,
              "graph": {"graph_id": c["man"]["graph_id"], "graph_sha256": c["graph_sha256"], "regole_sha256": c["regole_sha256"]}}
    return A._hash_job("compute_walk_access", {"baseline_id": A.BASELINE_ID, "snapshot_ids": A._snapshot_ids(kw["destination_id"])}, params)


def _esegui(kw, store=True, out_dir=None):
    sys.path.insert(0, str(ROOT / "analysis"))
    import accessibilita as A
    e = _limiti(A, kw)
    if e: return e
    jid = _prevedi_job_id(A, kw); jp, mp = _paths(jid)
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


def _fuori(msg): return err("outside_capability", msg + ". Nessun risultato numerico disponibile per questa richiesta.")


# ---------- punto d'ingresso unico ----------
def run_tool(name, args=None):
    args = args if isinstance(args, dict) else {}
    if name not in TOOLS: return err("unknown_id", f"Strumento sconosciuto: {name}.", candidates=TOOLS)
    if name in TOOLS_FUTURI: return _fuori(TOOLS_FUTURI[name][0].upper() + TOOLS_FUTURI[name][1:])
    if name == "compute_walk_access":   # destinazione mancante o data per nome: mai una scelta implicita
        ids = args.get("destination_ids")
        if not ids or not isinstance(ids, list) or any(not isinstance(i, str) or not ID_DEST.match(i) for i in ids):
            q = next((i for i in ids if isinstance(i, str) and not ID_DEST.match(i)), None) if isinstance(ids, list) else None
            cand = (_candidati(q) if q else []) or destinazioni()
            return err("ambiguous_destination", "Destinazione mancante o indicata per nome: scegliere un destination_id fra i candidati (list_destinations).",
                       candidates=[d["destination_id"] + " | " + d["nome"] for d in cand][:25])
    problemi = validate(name, "input", args)
    if problemi: return err("invalid_params", "; ".join(problemi[:5]))
    return globals()[name](args)
