#!/usr/bin/env python3
"""Schede delle fonti leggibili dagli agenti (F1, compito 2): una scheda Markdown per fonte di Firenze Novoli e un indice.
Uso: service/.venv/bin/python service/schede.py            scrive service/schede/INDEX.md e service/schede/<source_id>.md
     service/.venv/bin/python service/schede.py --verifica  esce con 1 se i file su disco non coincidono con quelli generati
     service/.venv/bin/python service/schede.py --tabella   stampa la tabella delle fonti del documento tecnico

Dati letti: pipeline/sources/*.json (record di fonte), pipeline/snapshots/*.json (scarichi), pipeline/t17_firenze.json (elenco delle fonti
di Firenze e rimando al catalogo), la baseline dell'area. Regola di provenienza: la data del dato è solo quella dichiarata nel periodo del
contenuto; la data di modifica della scheda del catalogo si riporta a parte e non è mai la data del dato."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "service/schede"
_load = lambda p: json.loads(pathlib.Path(p).read_text())
AREA = next(a for a in _load(ROOT / "contracts/aree.json")["aree"] if a["aoi_id"] == "aoi_firenze_novoli")
BASELINE = _load(ROOT / "pipeline/baselines" / f"{AREA['baseline_ids'][-1]}.json")
NELLA_BASELINE = {s["source_id"]: s["snapshot_id"] for s in BASELINE["snapshot"]}

STATO = {"clear": "verificata", "clear_with_reserve": "verificata con riserva", "unproven": "non verificata"}
USO = {"redistribution": "ridistribuzione consentita, con l'attribuzione richiesta dalla licenza", "internal_prototype": "solo prototipo interno: verificare prima di ridistribuire",
       "none": "uso non consentito"}
USO_BREVE = {"redistribution": "ridistribuzione", "internal_prototype": "solo prototipo interno", "none": "nessuno"}
ESITO = {"pass": "superato", "warn": "avviso", "fail": "fallito"}
# Limiti d'uso noti, da docs/STATO.md e docs/FONTI.md: si sommano agli avvisi dei controlli e alla riserva sulla licenza.
LIMITI = {
    "src_osm_firenze": ["Rete pedonale solo OSM: lato del marciapiede, larghezze e pendenze ignoti.",
                        "Estratto regionale del 2026-10-08, non più scaricabile da Geofabrik: la baseline non si ricostruisce identica da zero."],
    "src_fi_civici": ["Civici come punti d'indirizzo, non persone: le quote di accessibilità sono quote di civici."],
    "src_rt_uv_firenze_novoli": ["Unità volumetriche del 2011 con altezze dal LiDAR 2023: edifici nuovi solo dove li ha OSM; portici ignoti trattati come pieni."],
    "src_fi_dsm2023": ["Datum verticale non confermato.", "Vegetazione LiDAR trattata come prisma opaco pieno: limite superiore dell'ombra."],
    "src_fi_dtm2023": ["Datum verticale non confermato."],
    "src_fi_alberi": ["Solo alberi pubblici: chiome in parte stimate e imposta della chioma sempre stimata."],
    "src_gtfs_at_firenze": ["Finestra mobile di tre settimane: i calcoli usano solo le posizioni delle fermate, non gli orari."],
    "src_gtfs_gest_firenze": ["I calcoli usano solo le posizioni delle fermate, non gli orari."],
    "src_fi_rifugi_aree": ["Non ancora usata nei calcoli di accessibilità: destinazione candidata per il caso caldo (fase F2)."],
    "src_fi_rifugi_biblioteche": ["Non ancora usata nei calcoli di accessibilità: destinazione candidata per il caso caldo (fase F2)."],
    "src_fi_landsat_st": ["Temperatura delle superfici, non dell'aria; misura a 100 m distribuita a 30 m; solo passaggi di metà mattina."],
    "src_sir_termo_firenze": ["Una stazione a 1,3 km dal riquadro: temperatura dell'aria di stazione, non del riquadro. Licenza share-alike."],
    "src_fi_sezioni2011": ["Residenti del 2011: non entrano nei calcoli di accessibilità, che restano sui civici."],
    "src_rt_censimento2011": ["Dato di quindici anni fa; densità sulla superficie lorda della sezione."],
    "src_fi_catasto": ["Confini indicativi, non probatori; solo riquadro FP."],
    "src_fi_pericolosita_idraulica": ["Mappa di pianificazione, non previsione; classi senza legenda nel pacchetto."],
    "src_fi_allagate1966": ["Evento storico, non previsione."],
    "src_fi_pcca": ["Classi acustiche = limiti di legge, non rumore misurato."],
}


def fonti():
    """Fonti di Firenze nell'ordine del registro T17 (le fonti di Pisa restano fuori, D15)."""
    return [f["source_id"] for f in _load(ROOT / "pipeline/t17_firenze.json")["fonti"]]


def snapshot_ok(sid):
    """Scarichi validi della fonte, dal più vecchio."""
    ss = [_load(p) for p in sorted((ROOT / "pipeline/snapshots").glob("snp_*.json"))]
    return [s for s in ss if s.get("source_id") == sid and s["status"] == "ok"]


def periodo(cp):
    if not cp or not cp.get("start"): return "non dichiarata: vale lo stato alla data di scarico"
    s, e = cp["start"], cp.get("end")
    return s if not e or e == s else f"dal {s} al {e}"


def periodo_scarico(cp):
    cp = cp or {}
    if cp.get("start"): return periodo(cp)
    return f"non dichiarato ({cp['note']})" if cp.get("note") else "non dichiarato"


def licenza(lic):
    return lic.get("identifier") or "nessun identificativo dichiarato (vedere evidenza)"


def scheda(sid, t17):
    src, snaps = _load(ROOT / "pipeline/sources" / f"{sid}.json"), snapshot_ok(sid)
    lic, cp = src["license"], src.get("content_period") or {}
    r = [f"# {src['title']}", "", f"- Identificativo: `{sid}`", f"- Editore: {src['publisher']}"]
    if t17.get("dataset_catalogo"): r.append(f"- Scheda del catalogo: {t17['dataset_catalogo']}")
    else: r.append(f"- Scheda del catalogo: nessuna. {t17.get('lacuna') or ''}".rstrip())
    if src.get("dataset_url") and src["dataset_url"] != t17.get("dataset_catalogo"): r.append(f"- Pagina della fonte: {src['dataset_url']}")
    r += [f"- Risorsa scaricata: {src['resource_url']}",
          f"- Nella baseline congelata `{BASELINE['baseline_id']}`: " + (f"sì, snapshot `{NELLA_BASELINE[sid]}`" if sid in NELLA_BASELINE else "no, fonte aggiunta dopo (usata nella scena, non dai calcoli del servizio)"),
          "", "## Licenza", "", f"- Licenza: {licenza(lic)}", f"- Verifica: {STATO.get(lic['state'], lic['state'])}",
          f"- Uso consentito: {USO.get(lic['permitted_use'], lic['permitted_use'])}", f"- Evidenza: {lic['evidence_url']}", f"- Nota: {lic['evidence_note']}"]
    if lic.get("reserve_note"): r.append(f"- Riserva: {lic['reserve_note']}")
    r += ["", "## Date", "", f"- Data del dato: {periodo(cp)}"]
    if cp.get("note"): r.append(f"- Nota sul periodo: {cp['note']}")
    live = t17.get("catalogo_live") or {}
    if live.get("metadata_modified"): r.append(f"- Ultima modifica della scheda del catalogo: {live['metadata_modified']} (non è la data del dato)")
    r += ["", "Scarichi validi:", "", "| Snapshot | Scaricato il (UTC) | Periodo dichiarato nello scarico | sha256 (primi 12) | Baseline |", "|---|---|---|---|---|"]
    for s in snaps:
        r.append(f"| `{s['snapshot_id']}` | {s['retrieved_at']} | {periodo_scarico(s.get('content_period'))} | {s['sha256'][:12]} | {'sì' if NELLA_BASELINE.get(sid) == s['snapshot_id'] else 'no'} |")
    if not snaps: r.append("| nessuno | | | | |")
    r += ["", "## Campi usati", ""]
    r += [", ".join(f"`{f}`" for f in src["schema_fields"])] if src.get("schema_fields") else ["Non elencati nel record di fonte (raster, rete o file con più tabelle)."]
    if src.get("units"): r += ["", "Unità: " + ", ".join(f"`{k}` {v}" for k, v in src["units"].items())]
    crs = src.get("crs") or {}
    if crs: r += ["", f"Sistema di riferimento dichiarato: {crs.get('declared', 'non dichiarato')}" + (f" ({crs['note']})" if crs.get("note") else "")]
    r += ["", "## Controlli", ""] + [f"- {c['name']}: {ESITO.get(c['result'], c['result'])}" + (f". {c['detail']}" if c.get("detail") else "") for c in src["checks"]]
    lim = LIMITI.get(sid, []) + [f"{c['name']}: {c['detail']}" for c in src["checks"] if c["result"] != "pass" and c.get("detail")]
    if lic.get("reserve_note"): lim.append("Licenza con riserva: vedere sopra.")
    r += ["", "## Limiti", ""] + ([f"- {x}" for x in lim] or ["- Nessun limite specifico registrato oltre ai limiti generali del progetto."])
    r += ["", "Generata da `service/schede.py` a partire dai record di fonte e dagli snapshot del repository. Non modificare a mano.", ""]
    return "\n".join(r)


def indice(tutte):
    r = ["# Schede delle fonti: Firenze Novoli - Firenze Nova", "",
         f"Una scheda per fonte. Baseline congelata dei calcoli: `{BASELINE['baseline_id']}` ({len(NELLA_BASELINE)} fonti). Le altre fonti servono alla scena 3D.",
         "La data del dato è quella dichiarata dalla fonte; quando manca vale lo stato alla data di scarico. La data della scheda del catalogo non è mai la data del dato.", "",
         "| Fonte | Editore | Licenza | Uso consentito | Data del dato | Ultimo scarico | Baseline |", "|---|---|---|---|---|---|---|"]
    for sid, src, snaps in tutte:
        lic = src["license"]; ultimo = snaps[-1]["retrieved_at"][:10] if snaps else "nessuno"
        r.append(f"| [{src['title']}]({sid}.md) | {src['publisher']} | {licenza(lic)} ({STATO.get(lic['state'], lic['state'])}) | {USO_BREVE.get(lic['permitted_use'], lic['permitted_use'])} | {periodo(src.get('content_period'))} | {ultimo} | {'sì' if sid in NELLA_BASELINE else 'no'} |")
    r += ["", "Generato da `service/schede.py`. Non modificare a mano.", ""]
    return "\n".join(r)


# Nel documento tecnico niente nomi di prodotti software: si descrive la funzione.
EDITORE_DOC = {"src_fi_landsat_st": "U.S. Geological Survey (copia pubblica su un catalogo di dati satellitari in cloud)"}


def tabella():
    """Tabella delle fonti per docs/DOCUMENTO-TECNICO.md, fra i segnaposto <!-- tabella-fonti --> e <!-- /tabella-fonti -->."""
    r = ["| Fonte | Editore | Licenza | Uso consentito | Data del dato | Nella baseline dei calcoli |", "|---|---|---|---|---|---|"]
    for sid in fonti():
        src = _load(ROOT / "pipeline/sources" / f"{sid}.json"); lic = src["license"]
        r.append(f"| {src['title']} | {EDITORE_DOC.get(sid, src['publisher'])} | {licenza(lic)}, {STATO.get(lic['state'], lic['state'])} | {USO_BREVE.get(lic['permitted_use'], lic['permitted_use'])} | {periodo(src.get('content_period'))} | {'sì' if sid in NELLA_BASELINE else 'no'} |")
    return "\n".join(r)


def genera():
    """{nome file: testo} per l'indice e tutte le schede."""
    t17 = {f["source_id"]: f for f in _load(ROOT / "pipeline/t17_firenze.json")["fonti"]}
    tutte = [(sid, _load(ROOT / "pipeline/sources" / f"{sid}.json"), snapshot_ok(sid)) for sid in fonti()]
    out = {f"{sid}.md": scheda(sid, t17[sid]) for sid, _, _ in tutte}
    out["INDEX.md"] = indice(tutte)
    return out


if __name__ == "__main__":
    file = genera()
    if "--tabella" in sys.argv: print(tabella()); sys.exit(0)
    if "--verifica" in sys.argv:
        diversi = sorted(n for n, t in file.items() if not (OUT / n).exists() or (OUT / n).read_text() != t)
        extra = sorted(p.name for p in OUT.glob("*.md") if p.name not in file)
        if diversi or extra: print("schede da rigenerare:", diversi, "in più:", extra); sys.exit(1)
        print(f"OK {len(file)} file aggiornati"); sys.exit(0)
    OUT.mkdir(exist_ok=True)
    for n, t in file.items(): (OUT / n).write_text(t)
    print(f"{len(file) - 1} schede e INDEX.md in {OUT.relative_to(ROOT)}")
