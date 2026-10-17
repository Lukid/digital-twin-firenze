#!/usr/bin/env python3
"""Test delle schede delle fonti (F1, compito 2). Uso: service/.venv/bin/python service/test_schede.py (non richiede data/).
Le schede su disco coincidono con quelle generate; ogni fonte della baseline ha la sua; nessun campo di licenza vuoto;
le date degli scarichi coincidono con gli snapshot; la data del dato viene solo dal periodo dichiarato, mai dalla scheda del catalogo."""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import core, schede as S  # noqa: E402

file = S.genera()
diversi = sorted(n for n, t in file.items() if not (S.OUT / n).exists() or (S.OUT / n).read_text() != t)
assert not diversi, f"schede da rigenerare con service/schede.py: {diversi}"
assert sorted(p.name for p in S.OUT.glob("*.md")) == sorted(file), "schede in più o in meno su disco"

# tutte le fonti della baseline, e solo fonti di Firenze
fonti = S.fonti()
assert set(S.NELLA_BASELINE) <= set(fonti), set(S.NELLA_BASELINE) - set(fonti)
assert not any("pisa" in f or f.startswith("src_sit_") for f in fonti), fonti

for sid in fonti:
    t, src = file[f"{sid}.md"], json.loads((S.ROOT / "pipeline/sources" / f"{sid}.json").read_text())
    campo = lambda nome: (re.search(rf"^- {nome}: (.*)$", t, re.M) or [None, ""])[1].strip()
    # licenza: nessun campo vuoto
    for nome in ("Licenza", "Verifica", "Uso consentito", "Evidenza", "Nota"):
        assert campo(nome), f"{sid}: campo '{nome}' vuoto"
    assert campo("Evidenza").startswith("http"), sid
    # data del dato: solo dal periodo dichiarato nel record di fonte
    assert campo("Data del dato") == S.periodo(src.get("content_period")), sid
    # scarichi: uno per snapshot valido, con la data dello snapshot
    snaps = S.snapshot_ok(sid); assert snaps, f"{sid}: nessuno snapshot valido"
    for s in snaps:
        riga = next((r for r in t.splitlines() if r.startswith(f"| `{s['snapshot_id']}` |")), None)
        assert riga and f"| {s['retrieved_at']} |" in riga and s["sha256"][:12] in riga, (sid, s["snapshot_id"])
    if sid in S.NELLA_BASELINE:
        b = next(x for x in S.BASELINE["snapshot"] if x["source_id"] == sid)
        assert f"`{b['snapshot_id']}`" in campo("Nella baseline congelata `" + S.BASELINE["baseline_id"] + "`") and b["sha256"][:12] in t, sid
    # la data di modifica della scheda del catalogo, se c'è, è dichiarata come tale
    for r in t.splitlines():
        if "scheda del catalogo:" in r.lower() and re.search(r"\d{4}-\d\d-\d\d", r): assert "non è la data del dato" in r, (sid, r)

# tabella delle fonti del documento tecnico, generata dalle stesse schede
doc = (S.ROOT / "docs/DOCUMENTO-TECNICO.md").read_text()
blocco = re.search(r"<!-- tabella-fonti -->\n(.*?)\n<!-- /tabella-fonti -->", doc, re.S)
assert blocco and blocco[1] == S.tabella(), "tabella delle fonti del documento tecnico da rigenerare: service/schede.py --tabella"

# strumento MCP
r = core.run_tool("get_source_card", {})
assert core.validate("get_source_card", "output", r) == [] and r["source_ids"] == sorted(fonti) and r["index"] == file["INDEX.md"]
r = core.run_tool("get_source_card", {"source_id": "src_fi_civici"})
assert core.validate("get_source_card", "output", r) == [] and r["card"] == file["src_fi_civici.md"]
r = core.run_tool("get_source_card", {"source_id": "src_inesistente"})
assert r["error"]["code"] == "unknown_id" and core.validate("get_source_card", "output", r) == []
assert core.run_tool("get_source_card", {"source_id": "../INDEX"})["error"]["code"] == "invalid_params"
print(f"OK schede: {len(fonti)} fonti, {len(S.NELLA_BASELINE)} nella baseline")
