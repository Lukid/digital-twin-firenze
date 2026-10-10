"""Test di F09. Uso: pipeline/.venv/bin/python scene/firenze_novoli/test_build.py (richiede assets/ già costruiti)."""
import gzip, hashlib, json, pathlib, tempfile
import build

A = pathlib.Path(__file__).resolve().parent / "assets"
IDX = json.load(open(A / "index.json"))
REP = json.load(open(build.ROOT / "geometry/firenze_novoli/report_firenze_novoli.json"))


def carica(nome):
    return json.loads(gzip.decompress((A / IDX["assets"][nome]["file"]).read_bytes()))


def test_indice_sha256_e_dimensioni():
    for nome, m in IDX["assets"].items():
        b = (A / m["file"]).read_bytes()
        assert hashlib.sha256(b).hexdigest() == m["sha256"], nome
        assert len(b) == m["byte"], nome


def test_conteggi_come_f05():
    assert IDX["assets"]["edifici"]["n"] == REP["edifici"]["fp"]["volumi"] == 1952
    assert IDX["assets"]["alberi"]["n"] == REP["alberi"]["fp"]["totale"] == 2917
    ed = carica("edifici")
    assert len(ed["edifici"]) == ed["n"] and sum(e["n"] for e in ed["edifici"]) * 12 == len(__import__("base64").b64decode(ed["posizioni"]))
    assert len(carica("alberi")["alberi"]) == 2917


def test_fonti_con_licenza():
    assert IDX["fonti"] and IDX["limiti"]
    ids = {f["id"] for f in IDX["fonti"]}
    for f in IDX["fonti"]:
        assert all(f[k] for k in ("titolo", "ente", "url", "licenza", "stato_licenza", "scaricato", "sha256_snapshot")), f["id"]
        assert f["url"].startswith("http")
    for k, L in IDX["livelli"].items():
        assert set(L["fonti"]) <= ids, k


def test_livelli_analitici_opzionali():
    with tempfile.TemporaryDirectory() as d:
        assert build.accessibilita(d) is None and build.ombra(d) is None  # assenti: saltati
        p = pathlib.Path(d)
        pt = lambda pr: {"type": "Feature", "geometry": {"type": "Point", "coordinates": [11.226, 43.798]}, "properties": pr}
        (p / "accessibilita_dst_tram_fm9056.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
            pt({"layer": "origine", "id": "a", "ind": "VIA X 1", "stato": "reachable", "t": 7.9}),
            pt({"id": "b", "civico": "VIA X 2", "minuti": None, "stato": "forbidden"}),
            pt({"layer": "arco_usato", "id": "c"})]}))
        (p / "ombra_percorsi_1700.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"id": "e", "frazione_ombra": 0.4, "istante": "2026-06-21T17:00"},
             "geometry": {"type": "LineString", "coordinates": [[11.22, 43.79], [11.23, 43.8]]}}]}))
        acc = build.accessibilita(d)
        assert acc["n"] == 2 and acc["destinazioni"][0]["id"] == "dst_tram_fm9056"
        assert [q["stato"] for q in acc["destinazioni"][0]["punti"]] == ["ok", "vietato"]
        assert build.ombra(d)["istanti"][0]["tratti"][0]["f"] == 0.4


def test_interventi_scenari():
    if "interventi" not in IDX["assets"]:  # opzionale: file degli scenari assente
        return
    d = carica("interventi")
    assert sum(len(s["alberi"]) for s in d["scenari"]) == 21 and sum(len(s["pensiline"]) for s in d["scenari"]) == 1
    assert IDX["assets"]["interventi"]["n"] == 22 and IDX["livelli_analitici"]["scenari"]["presente"]
    assert all(s["numeri"] and "ignota" in s["fattibilita"] for s in d["scenari"])
    s1 = next(s for s in d["scenari"] if s["id"] == "scn_fi_s1_filare_r01")
    assert s1["numeri"][0][1].startswith("minuti al sole da 4,25 a 3,89") and s1["numeri"][1][1] == "da 29,5% a 35,4%"   # R01 da San Donato - Università (D20)


def test_three_in_vendor():
    # la importmap e gli import di app.js e di three devono puntare a file presenti: altrimenti la scena resta bianca
    import re
    H = A.parent
    imp = json.loads(re.search(r'<script type="importmap">(.*?)</script>', (H / "index.html").read_text(), re.S).group(1))["imports"]
    for spec in re.findall(r"from '([^']+)'", (H / "app.js").read_text()):
        pref = max((k for k in imp if spec == k or (k.endswith("/") and spec.startswith(k))), key=len)
        f = H / (imp[pref] + spec[len(pref):])
        assert f.is_file(), f"{spec} -> {f} mancante"
        for rel in re.findall(r'from ?"(\./[^"]+)"', f.read_text()):
            assert (f.parent / rel).is_file(), f"{f.name} importa {rel}, mancante"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
