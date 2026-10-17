"""T06/F06: accessibilità pedonale (caso A), per l'area scelta con DT_AOI. Libreria deterministica, senza dipendenze dall'interfaccia (CLI, API, MCP la chiamano uguale).

    r = compute_walk_access("dst_university_w83537185", profile=PROFILI["base_1_2"], snap_limit_m=40, out_dir=...)
    r["job"], r["manifest"], r["origini"] (una riga per origine), r["aggregati"], r["archi_usati"]

Metodo: cammino minimo per tempo (lunghezza / velocità + penalità di attraversamento) sul grafo pedonale T04/F04, con le origini
agganciate come nodi che spezzano gli archi (rete_lib.con_agganci) e un'unica Dijkstra dalla destinazione. Stati: vedi ADR-T02.
Stesso input canonico = stesso job_id e stessi numeri."""
import csv, datetime, hashlib, json, pathlib, statistics, sys
from functools import lru_cache
import geopandas as gpd, networkx as nx
from pyproj import Transformer
from shapely.geometry import Point, mapping
import shapely.ops

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "network")); sys.path.insert(0, str(ROOT / "pipeline"))
import rete_lib as RL  # noqa: E402
from coordinate import arrotonda  # noqa: E402

VERSIONE = "0.1.0"
# Area, grafo, file e snapshot vengono dall'area scelta con DT_AOI (network/rete_lib.py), dal registro contracts/aree.json e dalla baseline.
AOI_ID = RL.AOI_ID
AREA = next(a for a in json.load(open(ROOT / "contracts/aree.json"))["aree"] if a["aoi_id"] == AOI_ID)
BASELINE_ID = AREA["baseline_ids"][-1]
BASELINE = json.load(open(ROOT / "pipeline/baselines" / f"{BASELINE_ID}.json"))
GRAPH_ID = json.load(open(RL.RES / "rete_manifest.json"))["graph_id"]
SLUG = AOI_ID.removeprefix("aoi_")
OUT_DATI = RL.OUT.parent / "analysis"          # dati grandi, non versionati
OUT_VERS = ROOT / "analysis" / SLUG             # file piccoli versionati: manifest, riepilogo, asset per la mappa
LIMITI = {"max_area_km2": 4, "max_rows": 50000, "max_seconds": 600, "max_memory_mb": 4096}

# Profili: ipotesi di esperimento, non misure sul posto e non attribuite a gruppi demografici (SPEC_ANALISI, caso A).
# Le tre velocità sono quelle della SPEC (0,8 / 1,2 / 1,4 m/s). Il quarto profilo è un'ipotesi nostra: passo lento, scale escluse,
# 10 s di attesa per attraversamento. Mancano pendenze, larghezze, rampe e gradini di marciapiede: non certifica accessibilità universale.
PROFILI = {
    "base_1_2": {"speed_m_s": 1.2, "crossing_penalty_s": 0, "stairs": "allowed"},
    "lento_0_8": {"speed_m_s": 0.8, "crossing_penalty_s": 0, "stairs": "allowed"},
    "rapido_1_4": {"speed_m_s": 1.4, "crossing_penalty_s": 0, "stairs": "allowed"},
    "ridotta_0_8_senza_scale": {"speed_m_s": 0.8, "crossing_penalty_s": 10, "stairs": "excluded"},
}
DEVIAZIONE_ALTA = {"ratio": 1.5, "min_diretta_m": 100}   # ipotesi: percorso 50% più lungo della linea d'aria, solo oltre 100 m
SENS_VELOCITA = (0.8, 1.4)                                  # intervallo di incertezza dichiarato sui tempi

_sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
_to_ll = Transformer.from_crs(7791, 4326, always_xy=True)


def _ll(g): return shapely.ops.transform(lambda x, y, z=None: _to_ll.transform(x, y), g)


@lru_cache(maxsize=1)
def contesto():
    """Grafo, regole, snapper, destinazioni e origini di T04, caricati una volta."""
    G, D = RL.carica(); P = RL.permissivo(G, D["esclusi"])
    bld = gpd.read_file(RL.OSM_GPKG, layer="buildings")
    dest = {d["destination_id"]: d for d in json.load(open(RL.RES / "destinazioni.json"))["destinazioni"]}
    man = json.load(open(RL.RES / "rete_manifest.json"))
    civ = gpd.read_file(RL.OUT / "origini_snap.gpkg", layer="origini").set_index("id").sort_index()
    return {"G": G, "D": D, "P": P, "SN": RL.Snapper(G, D["esclusi"], D["bloccati"], bld), "dest": dest, "man": man, "civ": civ,
            "orig_len": {e["edge_id"]: e["length_m"] for _, _, e in G.edges(data=True)},
            "graph_sha256": _sha(RL.OUT / f"{RL.STEM}.pkl"), "regole_sha256": _sha(RL.NET / "regole.json")}


@lru_cache(maxsize=8)
def agganci_origini(family, snap_limit_m):
    """Agganci delle origini al limite dato: {id: (Point, snap)}. Origini fuori dal riquadro del grafo: stato outside_model."""
    if family != "address_points": raise ValueError(f"famiglia di origini non supportata: {family}")
    c = contesto(); R = RL.REGOLE["snapping"]["origini"]; x0, y0, x1, y1 = c["man"]["area_buffer_en"]; out = {}
    for oid, row in c["civ"].iterrows():
        p = row.geometry
        if not (x0 <= p.x <= x1 and y0 <= p.y <= y1): out[oid] = (p, {"stato": "outside_model", "motivo": "fuori dal riquadro del grafo"})
        else: out[oid] = (p, c["SN"].snap(p, snap_limit_m, R["candidati"], tuple(R["tipi_arco_esclusi"])))
    return out


con_agganci = RL.con_agganci   # unica implementazione, in network/rete_lib.py


def _costo(e, prof, orig_len):
    if e.get("scala") and prof["stairs"] == "excluded": return None
    t = e["length_m"] / prof["speed_m_s"]
    if e["tipo_arco"] == "attraversamento": t += prof["crossing_penalty_s"] * e["length_m"] / orig_len[e.get("parte_di", e["edge_id"])]
    return t


def _inf(x): return float('inf') if x is None else x


def _peso(prof, orig_len):
    def w(u, v, dd):
        cs = [c for c in (_costo(e, prof, orig_len) for e in dd.values()) if c is not None]
        return min(cs) if cs else None
    return w


def _riassunto(H, nodi, archi):
    ids = lambda f: {e.get("parte_di", e["edge_id"]) for e in archi if f(e)}
    L = lambda f: sum(e["length_m"] for e in archi if f(e))
    return {"rete_m": round(L(lambda e: True), 1), "attraversamenti": len(ids(lambda e: e["tipo_arco"] == "attraversamento")),
            "m_marciapiede_ignoto": round(L(lambda e: e["marciapiede_stato"] == "ignoto"), 1),
            "m_marciapiede_assente": round(L(lambda e: e["marciapiede_stato"] == "assente"), 1),
            "scale": len(ids(lambda e: e["scala"])), "sottopassi": len(ids(lambda e: e["tipo_arco"] == "sottopasso" or e["tunnel"])),
            "barriere_passate": [H.nodes[n].get("barriera") for n in nodi if H.nodes[n].get("barriera")],
            "restrizioni": [e["restrizione"] for e in archi if e.get("restrizione")]}


def calcola(entrate, origini, prof):
    """Nucleo: entrate = {entrance_id: (Point, snap)}, origini = {nome: (Point, snap)}, prof = profilo. Ritorna ({nome: riga}, {arco: n_origini}, Htree)."""
    c = contesto(); G, P = c["G"], c["P"]; w = _peso(prof, c["orig_len"])
    ent = {k: (p, s) for k, (p, s) in sorted(entrate.items())}
    ok = {n: (p, s) for n, (p, s) in sorted(origini.items()) if s["stato"] == "agganciato"}
    sn = {f"E{i}": s for i, (p, s) in enumerate(ent.values())}; eid = {f"snp_E{i}": k for i, k in enumerate(ent)}
    H = con_agganci(G, {**sn, **{"o_" + n: s for n, (p, s) in ok.items()}})
    H.add_node("SRC", x=0, y=0, bordo_buffer=False, in_z2=True, componente=None)
    for i, (k, (p, s)) in enumerate(ent.items()):
        H.add_edge("SRC", f"snp_E{i}", key=f"virt_{i}", length_m=s["dist_m"], tipo_arco="virtuale", scala=False, edge_id=f"virt_{i}")
    dist, path = nx.single_source_dijkstra(H, "SRC", weight=w)
    comp_dest = {s.get("componente") or G.nodes[s["u"]]["componente"] for p, s in ent.values()}
    righe, uso, da_permissivo = {}, {}, []
    for nome, (p, s) in sorted(origini.items()):
        r = {"origin_id": nome, "stato": None, "motivo": None}
        if s["stato"] != "agganciato":
            r.update(stato=s["stato"], motivo=s.get("motivo")); righe[nome] = r; continue
        r["raccordo_origine_m"] = s["dist_m"]; r["componente"] = G.nodes[s["u"]]["componente"]; n = "snp_o_" + nome
        if n in dist:
            pn = path[n]; nodi = pn[1:]
            archi = [min(H[a][b].values(), key=lambda e: (_inf(_costo(e, prof, c["orig_len"])), e["edge_id"])) for a, b in zip(nodi, nodi[1:])]
            ent_k = eid[nodi[0]]; rd = ent[ent_k][1]["dist_m"]; rs = _riassunto(H, nodi, archi)
            tot = rs["rete_m"] + s["dist_m"] + rd; dirett = p.distance(ent[ent_k][0])
            r.update(stato="reachable", entrance_id=ent_k, **rs, raccordo_destinazione_m=rd, totale_m=round(tot, 1), diretta_m=round(dirett, 1),
                     deviazione=round(tot / max(dirett, 1.0), 2), tempo_s=round(dist[n] + s["dist_m"] / prof["speed_m_s"], 1),
                     attesa_s=round(sum(_costo(e, prof, c["orig_len"]) - e["length_m"] / prof["speed_m_s"] for e in archi), 1))   # penalità accumulata, come nel costo
            for e in {e.get("parte_di", e["edge_id"]) for e in archi}: uso[e] = uso.get(e, 0) + 1
        elif r["componente"] in comp_dest:
            r.update(stato="isolated", motivo="profilo: ogni percorso passa da tratti esclusi dal profilo (scale)")
        else:
            r.update(stato="isolated", motivo=f"componente isolata {r['componente']} sul grafo verificato"); da_permissivo.append(nome)
        righe[nome] = r
    if da_permissivo:   # collegata solo attraverso una restrizione documentata? allora forbidden, non isolated
        Hp = con_agganci(P, {**sn, **{"o_" + n: ok[n][1] for n in da_permissivo}}); Hp.add_node("SRC")
        rac_d = [s["dist_m"] for p, s in ent.values()]   # raccordo di ogni ingresso, contato nella distanza come nel caso raggiungibile
        for i in range(len(ent)): Hp.add_edge("SRC", f"snp_E{i}", key=f"virt_{i}", length_m=rac_d[i], tipo_arco="virtuale", scala=False, edge_id=f"virt_{i}", marciapiede_stato="n/a", tunnel=None)
        dp, pp = nx.single_source_dijkstra(Hp, "SRC", weight=lambda u, v, dd: min(e["length_m"] for e in dd.values()))
        for nome in da_permissivo:
            n = "snp_o_" + nome
            if n not in dp: continue
            nodi = pp[n][1:]; archi = [min(Hp[a][b].values(), key=lambda e: e["length_m"]) for a, b in zip(nodi, nodi[1:])]
            rs = _riassunto(Hp, nodi, archi)
            righe[nome].update(stato="forbidden", motivo="nessun percorso sul grafo verificato; collegata solo da tratti con restrizione documentata",
                               restrizioni=sorted(set(rs["restrizioni"])), permissivo_m=round(rs["rete_m"] + ok[nome][1]["dist_m"] + rac_d[int(pp[n][1][5:])], 1))
    return righe, uso


def _quantili(v, qs=(0.1, 0.5, 0.9)):
    v = sorted(v)
    if not v: return {f"p{int(q*100)}": None for q in qs}
    return {f"p{int(q*100)}": round(v[min(len(v) - 1, int(q * (len(v) - 1) + 0.5))], 2) for q in qs}


def _aggrega(righe, uso, prof, soglie, dev, n_top=30):
    c = contesto(); ok = [r for r in righe.values() if r["stato"] == "reachable"]; n = len(righe)
    conteggi = {s: sum(1 for r in righe.values() if r["stato"] == s) for s in ("reachable", "isolated", "insufficient_data", "forbidden", "outside_model")}
    t_min = [r["tempo_s"] / 60 for r in ok]
    def tempo_a(r, v): return (r["totale_m"] / v + r["attesa_s"]) / 60   # stesso percorso, attese invariate
    quote = {}
    for T in soglie:
        quote[f"{T:g}"] = {"servite": sum(1 for t in t_min if t <= T), "quota": round(sum(1 for t in t_min if t <= T) / n, 4),
                         "quota_sui_raggiungibili": round(sum(1 for t in t_min if t <= T) / max(len(ok), 1), 4),
                         "intervallo_velocita": [round(sum(1 for r in ok if tempo_a(r, v) <= T) / n, 4) for v in SENS_VELOCITA]}
    alte = [r for r in ok if r["diretta_m"] >= dev["min_diretta_m"] and r["deviazione"] >= dev["ratio"]]
    metri = sum(r["totale_m"] for r in ok)
    # archi più usati
    info = {e["edge_id"]: (e, u, v) for u, v, e in c["G"].edges(data=True)}
    def riga_arco(k, nn):
        e = info[k][0]; return {"edge_id": k, "n_origini": nn, "quota_raggiungibili": round(nn / max(len(ok), 1), 3), "tipo_arco": e["tipo_arco"], "marciapiede_stato": e["marciapiede_stato"],
                                "nome": e.get("name"), "length_m": e["length_m"], "highway": e["highway"], "geom": e["geom"]}
    ordine = sorted(uso.items(), key=lambda kv: (-kv[1], kv[0]))
    top = [riga_arco(k, nn) for k, nn in ordine[:n_top]]
    ign = [riga_arco(k, nn) for k, nn in ordine if info[k][0]["marciapiede_stato"] == "ignoto"][:n_top]
    return {"origini_totali": n, "conteggi": conteggi, "quote_soglie": quote, "tempo_min_velocita": [_quantili([tempo_a(r, v) for r in ok]) for v in SENS_VELOCITA], "tempo_min": {**_quantili(t_min), "max": round(max(t_min), 2) if t_min else None, "media": round(statistics.fmean(t_min), 2) if t_min else None},
            "istogramma_tempo_min": {f"{a}-{b}": sum(1 for t in t_min if a <= t < b) for a, b in [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 999)]},
            "rete_m": _quantili([r["totale_m"] for r in ok]), "deviazione": _quantili([r["deviazione"] for r in ok if r["diretta_m"] >= dev["min_diretta_m"]]),
            "deviazione_alta": {"regola": dev, "n": len(alte), "quota_raggiungibili": round(len(alte) / max(len(ok), 1), 4), "origin_ids": sorted(r["origin_id"] for r in alte)},
            "quota_metri_marciapiede_ignoto": round(sum(r["m_marciapiede_ignoto"] for r in ok) / max(metri - sum(r["raccordo_origine_m"] + r["raccordo_destinazione_m"] for r in ok), 1), 4),
            "attraversamenti_mediana": statistics.median([r["attraversamenti"] for r in ok]) if ok else None,
            "origini_con_scale": sum(1 for r in ok if r["scale"]), "origini_con_barriera": sum(1 for r in ok if r["barriere_passate"]),
            "archi_piu_usati": top, "archi_ignoti_piu_usati": ign}


def _hash_job(tool, inputs, params): return "job_" + hashlib.sha256(canon({"tool": tool, "inputs": inputs, "params": params}).encode()).hexdigest()[:16]


# fonti della destinazione per categoria (sottostringhe del source_id nella baseline); osm e civici valgono sempre
FONTI_DEST = {"school": ("scuole_statali", "cm_edscol"), "tram": ("gtfs_gest",), "stop": ("gtfs",), "cooling_refuge": ("rifugi_aree", "rifugi_biblioteche")}


def _snapshot_ids(destination_ids):
    ids = [destination_ids] if isinstance(destination_ids, str) else destination_ids
    chiavi = ("civici",) + tuple(k for i in ids for k in FONTI_DEST.get(contesto()["dest"][i]["categoria"], ()))
    ids = {RL.OSM_SNAP["snapshot_id"]} | {s["snapshot_id"] for s in BASELINE["snapshot"] if any(k in s["source_id"] for k in chiavi)}
    return sorted(ids)


def _metrica(mid, label, value, unit, cls, scope=None, unc=None):
    m = {"metric_id": mid, "label": label, "value": value, "unit": unit, "classification": cls}
    if scope: m["scope"] = scope
    if unc: m["uncertainty"] = unc
    return m


def _scrivi_assets(job_id, righe, agg, soglie, out_dir):
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); assets = []
    def reg(nome, aid, media, role):
        p = out_dir / nome; b = p.read_bytes()
        assets.append({"asset_id": aid, "path": str(p.relative_to(ROOT)), "media_type": media, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "role": role})
    cols = ["origin_id", "stato", "motivo", "entrance_id", "rete_m", "raccordo_origine_m", "raccordo_destinazione_m", "totale_m", "diretta_m", "deviazione", "tempo_s",
            "attraversamenti", "m_marciapiede_ignoto", "m_marciapiede_assente", "scale", "sottopassi", "componente"]
    with open(out_dir / f"{job_id}_origini.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore", lineterminator="\n"); w.writeheader()
        for k in sorted(righe): w.writerow({c: righe[k].get(c, "") for c in cols})
    reg(f"{job_id}_origini.csv", "ast_origini_csv", "text/csv", "result_table")
    feats = [{"type": "Feature", "geometry": arrotonda(mapping(_ll(a["geom"]))),
              "properties": {k: v for k, v in a.items() if k != "geom"} | {"gruppo": g}} for g, lst in (("piu_usati", agg["archi_piu_usati"]), ("ignoti_piu_usati", agg["archi_ignoti_piu_usati"])) for a in lst]
    (out_dir / f"{job_id}_archi_usati.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")))
    reg(f"{job_id}_archi_usati.geojson", "ast_archi_usati", "application/geo+json", "result_geometry")
    rep = {k: v for k, v in agg.items() if k not in ("archi_piu_usati", "archi_ignoti_piu_usati")}
    (out_dir / f"{job_id}_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True))
    reg(f"{job_id}_report.json", "ast_report", "application/json", "report")
    return assets


def _ingressi(dest_ids, entrance_ids=None):
    """Ingressi da usare: quelli indicati o i predefiniti di ogni destinazione (il Polo ne ha 7, D19). Con più destinazioni l'unione: il più vicino vince."""
    c = contesto(); ents = {e["entrance_id"]: e for i in dest_ids for e in c["dest"][i]["ingressi"]}
    ids = sorted(entrance_ids or [x for i in dest_ids for x in (c["dest"][i].get("ingressi_predefiniti") or [c["dest"][i]["ingresso_predefinito"]])])
    if any(i not in ents for i in ids): raise ValueError(f"ingresso non appartenente a {', '.join(dest_ids)}")
    return ids, ents


def parametri_job(destination_id, origin_family="address_points", profile=None, thresholds_min=(5, 10, 15), snap_limit_m=40, entrance_ids=None, deviazione_alta=None):
    """(inputs, params, job_id) di compute_walk_access senza calcolare: il servizio lo usa per la cache. destination_id: un id o una lista (accessibilità verso almeno una)."""
    c = contesto(); prof = dict(profile or PROFILI["base_1_2"]); dev = dict(deviazione_alta or DEVIAZIONE_ALTA)
    if set(prof) != {"speed_m_s", "crossing_penalty_s", "stairs"} or prof["stairs"] not in ("allowed", "excluded") or not 0.3 <= prof["speed_m_s"] <= 2.5:
        raise ValueError("profilo non valido: servono speed_m_s (0,3-2,5), crossing_penalty_s, stairs (allowed|excluded)")
    dest_ids = sorted({destination_id} if isinstance(destination_id, str) else set(destination_id))
    for i in dest_ids:
        if i not in c["dest"]: raise ValueError(f"destinazione sconosciuta: {i}")
    ids, _ = _ingressi(dest_ids, entrance_ids)
    inputs = {"baseline_id": BASELINE_ID, "snapshot_ids": _snapshot_ids(dest_ids)}
    params = {"destination_ids": dest_ids, "entrance_ids": ids, "origins": {"kind": origin_family, "aoi_id": AOI_ID, "count": len(agganci_origini(origin_family, float(snap_limit_m)))},
              "profile": {**prof, "snap_limit_m": float(snap_limit_m)}, "thresholds_min": sorted(float(t) for t in thresholds_min), "deviazione_alta": dev, "method_version": VERSIONE,
              "graph": {"graph_id": c["man"]["graph_id"], "graph_sha256": c["graph_sha256"], "regole_sha256": c["regole_sha256"]}}
    return inputs, params, _hash_job("compute_walk_access", inputs, params)


def compute_walk_access(destination_id, origin_family="address_points", profile=None, thresholds_min=(5, 10, 15), snap_limit_m=40,
                        entrance_ids=None, deviazione_alta=None, out_dir=None):
    """Accessibilità verso una destinazione, o verso almeno una di più destinazioni (lista di id: tutti gli ingressi insieme, il più vicino per tempo vince).
    entrance_ids: ingressi da considerare; None = ingressi predefiniti (o l'ingresso predefinito) di ogni destinazione.
    Ritorna dict con job, manifest, origini (righe), aggregati, archi_usati. Con out_dir scrive gli asset e li registra nel manifest."""
    t0 = datetime.datetime.now(datetime.timezone.utc)
    inputs, params, job_id = parametri_job(destination_id, origin_family, profile, thresholds_min, snap_limit_m, entrance_ids, deviazione_alta)
    prof = {k: v for k, v in params["profile"].items() if k != "snap_limit_m"}; dev = params["deviazione_alta"]; soglie = params["thresholds_min"]; dest_ids = params["destination_ids"]
    ids, ents = _ingressi(dest_ids, entrance_ids)
    snaps = {i: (Point(ents[i]["xy"]), {**ents[i]["aggancio"], "proj": tuple(ents[i]["aggancio"]["proj"])}) for i in ids}
    if any(s["stato"] != "agganciato" for _, s in snaps.values()): raise ValueError("ingresso non agganciato alla rete")
    orig = agganci_origini(origin_family, float(snap_limit_m))
    righe, uso = calcola(snaps, orig, prof)
    agg = _aggrega(righe, uso, prof, soglie, dev)
    t1 = datetime.datetime.now(datetime.timezone.utc); fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    sc = f"{' + '.join(dest_ids)}, {prof['speed_m_s']} m/s, snapping {snap_limit_m:g} m" + (", almeno una destinazione (la più vicina)" if len(dest_ids) > 1 else "")
    unc_v = lambda lo, hi: {"kind": "interval", "low": lo, "high": hi, "basis": "sensibilità velocità 0,8-1,4 m/s a parità di percorso"}
    met = [_metrica("origins_total", f"Origini (civici di {AREA['comune']})", agg["origini_totali"], "count", "derived")]
    met += [_metrica(f"origins_{s}", f"Origini in stato {s}", n, "count", "derived") for s, n in agg["conteggi"].items()]
    for T in soglie:
        q = agg["quote_soglie"][f"{T:g}"]; k = f"{T:g}".replace(".", "_")
        met.append(_metrica(f"served_count_{k}min", f"Origini raggiunte entro {T:g} minuti", q["servite"], "count", "estimated", sc + f", soglia {T:g} min",
                            unc_v(*(round(x * agg["origini_totali"]) for x in q["intervallo_velocita"]))))
        met.append(_metrica(f"served_share_{k}min", f"Quota di origini (tutte) raggiunte entro {T:g} minuti", q["quota"], "1", "estimated", sc + f", soglia {T:g} min", unc_v(*q["intervallo_velocita"])))
    tm = agg["tempo_min"]
    for key, lab in (("p50", "mediano"), ("p90", "90° percentile")):
        if tm[key] is not None:
            lento, rapido = agg["tempo_min_velocita"]; met.append(_metrica(f"travel_time_{key}", f"Tempo {lab} delle origini raggiungibili", tm[key], "min", "estimated", sc,
                                                                    unc_v(rapido[key], lento[key])))
    met += [_metrica("network_distance_p50", "Distanza di cammino mediana (rete più raccordi)", agg["rete_m"]["p50"], "m", "derived", sc),
            _metrica("deviation_p50", "Deviazione mediana rispetto alla linea d'aria", agg["deviazione"]["p50"], "1", "derived", sc + ", origini oltre 100 m"),
            _metrica("high_deviation_count", "Origini con deviazione alta (rapporto 1,5 o più, oltre 100 m)", agg["deviazione_alta"]["n"], "count", "derived", sc),
            _metrica("unknown_sidewalk_share", "Quota dei metri di rete a marciapiede ignoto", agg["quota_metri_marciapiede_ignoto"], "1", "derived", sc)]
    ds = []
    for sid in inputs["snapshot_ids"]:
        s = next(x for x in BASELINE["snapshot"] if x["snapshot_id"] == sid) if sid != RL.OSM_SNAP["snapshot_id"] else RL.OSM_SNAP; ds.append({"snapshot_id": sid, "source_id": s["source_id"], "sha256": s["sha256"], "license_state": s["license_state"]})
    limits = [("grafo_osm_non_verificato", "Rete da OSM congelato, non verificata sul posto; percorsi, ingressi e restrizioni da controllare al sopralluogo."),
              ("marciapiede_ignoto", "Dove il marciapiede non è taggato lo stato è ignoto: il tratto è percorribile ma non certificato."),
              ("civici_non_residenti", f"I civici del Comune di {AREA['comune']} (CC BY 4.0) sono punti d'indirizzo, non residenti: le quote sono quote di civici, non di popolazione."),
              ("velocita_ipotesi", "Velocità e penalità sono ipotesi di esperimento, non misure sul posto e non attribuite a gruppi di persone."),
              ("snapping_parametro", "Il limite di snapping e il raccordo non attraversano edifici; i civici non agganciati restano insufficient_data."),
              ("no_certificazione_accessibilita", "Mancano pendenze, larghezze, rampe e gradini di marciapiede: nessuna certificazione di accessibilità universale."),
              ("ingresso_da_verificare", "Ingresso e orari della destinazione non verificati; cambiare ingresso può cambiare lunghezze e attraversamenti.")] + ([("almeno_una_destinazione", f"Più destinazioni ({len(dest_ids)}): per ogni origine conta la più vicina (ingresso più vicino per tempo fra tutti); la quota è di civici che ne raggiungono almeno una.")] if len(dest_ids) > 1 else [])
    man = {"manifest_id": "man_" + job_id[4:], "job_id": job_id, "tool": "compute_walk_access", "aoi_id": AOI_ID, "baseline_id": BASELINE_ID, "datasets": ds, "params": params,
           "method": {"name": "shortest_path_walk_time", "version": VERSIONE, "description": "Cammino minimo pesato per tempo (lunghezza su velocità più penalità di attraversamento) sul grafo pedonale OSM congelato, con raccordo registrato dall'origine alla rete."},
           "crs": "EPSG:7791", "vertical_datum_status": "not_confirmed", "timezone": "Europe/Rome",
           "timing": {"started_at": fmt(t0), "finished_at": fmt(t1), "duration_s": round((t1 - t0).total_seconds(), 2)}, "metrics": met,
           "coverage": {"accessibility_counts": agg["conteggi"], "note": "Le componenti isolate restano nei conteggi."},
           "limits": [{"code": a, "text": b} for a, b in limits], "validation_status": "not_validated_locally", "assets": []}
    if out_dir: man["assets"] = _scrivi_assets(job_id, righe, agg, soglie, out_dir)
    job = {"job_id": job_id, "tool": "compute_walk_access", "status": "succeeded", "created_at": fmt(t0), "started_at": fmt(t0), "finished_at": fmt(t1), "inputs": inputs,
           "params": params, "limits": LIMITI, "progress": {"fraction": 1.0, "message": "completato"}, "result_manifest_id": man["manifest_id"]}
    return {"job": job, "manifest": man, "origini": righe, "aggregati": agg, "archi_usati": uso}
