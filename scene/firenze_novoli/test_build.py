"""Test di F09. Uso: pipeline/.venv/bin/python scene/firenze_novoli/test_build.py (richiede assets/ già costruiti)."""
import gzip, hashlib, json, pathlib, re, tempfile
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
    assert sum(len(s["alberi"]) for s in d["scenari"]) == 21 and sum(len(s["pensiline"]) for s in d["scenari"]) == 3   # S2, S5, S6
    assert IDX["assets"]["interventi"]["n"] == 24 and IDX["livelli_analitici"]["scenari"]["presente"]
    assert all(s["numeri"] and "ignota" in s["fattibilita"] for s in d["scenari"])
    s1 = next(s for s in d["scenari"] if s["id"] == "scn_fi_s1_filare_r01")
    assert s1["numeri"][0][1].startswith("minuti al sole da 4,25 a 3,89") and s1["numeri"][1][1] == "da 29,5% a 35,4%"   # R01 da San Donato - Università (D20)


def test_fermate_tram():
    t = [p["id"] for p in carica("punti")["punti"] if p["livello"] == "tram"]
    assert "ent_gtfs_fm9055" in t and len(t) == 3   # San Donato - Università dal GTFS (D20), le altre due dal Comune


def test_ombra_percorsi_interi():
    if "ombra" not in IDX["assets"]:  # opzionale: uscita del motore ombre assente
        return
    d = carica("ombra")
    assert [q["id"] for q in d["percorsi"]] == ["pth_fi_R01", "pth_fi_R02"]   # il giallo sotto i tratti in ombra
    assert all(0 <= v <= 1 for i in d["istanti"] for v in i["quota"].values())
    assert d["istanti"][0]["quota"]["pth_fi_R01"] == 0.808


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


def test_mappa_ed_etichette():
    m, e = carica("mappa"), carica("etichette")
    assert m["verde"] and m["strade"] and all(len(s["p"]) >= 4 for s in m["strade"])
    t = [q["t"] for q in e["etichette"]]
    assert {"Palazzo di Giustizia", "Polo delle Scienze Sociali", "Via di Novoli"} <= set(t) and len(t) == len(set(t))
    assert "src_osm_firenze" in IDX["livelli"]["etichette"]["fonti"]


def test_catasto():
    c = carica("catasto")
    assert c["n"] == len(c["particelle"]) == 1631 and len(c["fogli"]) == 21   # riquadro FP, scarico del 2026-10-10
    assert all(q["rif"] == f"foglio {q['f']} particella {q['p']}" and q["t"] in ("particella", "strada", "acqua") and q["a"] and len(q["a"][0][0]) >= 6
               for q in c["particelle"])
    assert {q["f"] for q in c["particelle"]} <= {f["f"] for f in c["fogli"]}
    ed = carica("edifici")["edifici"]
    assert all(isinstance(e["cat"], list) and len(e["cat"]) <= 1 for e in ed)   # soglia 50%: al massimo una particella
    assert sum(len(e["cat"]) == 1 for e in ed) > 0.9 * len(ed)
    assert "src_fi_catasto" in IDX["livelli"]["catasto"]["fonti"] and any("non probatori" in t for t in IDX["limiti"])


def test_temperature_e_meteo():
    if "temperature" not in IDX["assets"]:  # opzionale: serve data/norm con Landsat
        return
    t, ter = carica("temperature"), carica("terreno")
    nc = t["nx"] * t["ny"]
    # stesso spigolo sud-ovest del terreno (FP - MARGINE), passo 30 m invece di 10 m
    bordo = lambda g: (g["x0"] - g["passo"] / 2, g["z0"] + (g["ny"] - 0.5) * g["passo"])
    assert t["passo"] == 30 and all(abs(a - b) < 0.01 for a, b in zip(bordo(t), bordo(ter)))
    assert t["nodata"] == build.NODATA_T and t["n"] == len(t["date"]) > 0
    d = [q["data"] for q in t["date"]]
    assert d == sorted(set(d)) and all(q["validi_pct"] >= t["soglia_validi_pct"] == 80 and q["ora_utc"].startswith("09:5") for q in t["date"])
    assert all(len(q["t"]) == nc for q in t["date"]) and len(t["media"]) == len(t["sopra_40"]) == len(t["validi_per_cella"]) == nc
    v = [x for q in t["date"] for x in q["t"] if x != t["nodata"]]
    assert 150 < min(v) and max(v) < 800   # tra 15 e 80 °C d'estate
    assert all(0 <= k <= n <= t["n"] for k, n in zip(t["sopra_40"], t["validi_per_cella"]))
    assert "src_fi_landsat_st" in IDX["livelli"]["temperature"]["fonti"] and any("non dell'aria" in x for x in IDX["limiti"])
    m = carica("meteo")
    assert m["stazione"]["id"] == "TOS01001096" and m["stazione"]["distanza_fp_m"] < 3000 and set(m["date_landsat"]) == set(d)
    g = {q[0]: q for q in m["giorni"]}
    assert all(q[1] is None or q[2] is None or q[1] >= q[2] for q in m["giorni"]) and sum(x in g for x in d) >= 0.9 * len(d)
    assert next(f for f in IDX["fonti"] if f["id"] == "src_sir_termo_firenze")["licenza"] == "CC-BY-SA-4.0"


def test_aria():
    if "aria" not in IDX["assets"]:  # opzionale: serve data/norm con i dati ARPAT
        return
    a = carica("aria")
    st = {q["codice"]: q for q in a["stazioni"]}
    assert a["n"] == len(st) == 6 and a["anno"] == 2025 and set(st) == {"FI-MOSSE", "FI-LAVAGNINI", "FI-BOBOLI", "FI-GRAMSCI", "FI-BASSI", "FI-SETTIGNANO"}
    assert all(q["fuori_riquadro"] and q["distanza_m"] > 0 for q in st.values())   # nessuna stazione nel riquadro FP
    m = st["FI-MOSSE"]
    assert m["tipo"] == "traffico" and 700 < m["distanza_m"] < 800 and m["distanza_m"] == min(q["distanza_m"] for q in st.values())
    for q in st.values():
        assert q["inquinanti"]
        for p in q["inquinanti"]:
            assert "(D.Lgs. 155/2010)" in p["limite"]
            assert 0 <= p["validi_pct"] <= 100 and p["ultimo"]["data"].startswith("2025-") and p["unita"] in ("µg/m³", "mg/m³")
            assert ("soglia" in p) == (p["superamenti"] is not None)
    no2 = next(p for p in m["inquinanti"] if p["parametro"] == "NO2")
    assert no2["soglia"] == 200 and no2["ammessi"] == 18 and no2["conta"] == "ore" and no2["base"] == "oraria"
    assert next(p for p in st["FI-SETTIGNANO"]["inquinanti"] if p["parametro"] == "O3")["soglia_su"].endswith("8 ore")
    assert not all(p["copertura_ok"] for p in st["FI-GRAMSCI"]["inquinanti"])   # disattivata da marzo 2025 (lavori della tramvia)
    assert IDX["livelli"]["aria"]["fonti"] == ["src_arpat_aria"] and any("ARPAT" in x and "non una mappa" in x for x in IDX["limiti"])
    f = next(f for f in IDX["fonti"] if f["id"] == "src_arpat_aria")
    assert f["stato_licenza"] == "clear_with_reserve" and "D21" in f["riserva"] and f.get("fuori_baseline")


def test_protezione_civile():
    pt = {p["id"]: p for p in carica("punti")["punti"] if p["livello"] in ("attesa", "assistenza")}
    assert set(pt) == {"pcv_att_fi_18", "pcv_ass_fi_AA13", "pcv_ass_fi_AA14", "pcv_ass_fi_AA15"}
    assert {k for k, p in pt.items() if p.get("fuori")} == {"pcv_att_fi_18", "pcv_ass_fi_AA14", "pcv_ass_fi_AA15"} and pt["pcv_att_fi_18"]["distanza_m"] == 235   # oltre il terreno: elenco, come ARPAT
    assert "?" not in pt["pcv_ass_fi_AA13"]["attr"]["Accessi"]   # apostrofi e "può" ripristinati
    assert {f["id"] for f in IDX["fonti"]} >= {"src_fi_aree_attesa", "src_fi_aree_assistenza"}


def test_ricognizione_catalogo():
    import collections
    c = collections.Counter(p["livello"] for p in carica("punti")["punti"])
    assert {k: c[k] for k in ("farmacie", "sosta_disabili", "bike_sharing", "car_sharing", "scudo_verde", "giochi", "cani", "sport")} == \
        {"farmacie": 6, "sosta_disabili": 154, "bike_sharing": 15, "car_sharing": 6, "scudo_verde": 5, "giochi": 12, "cani": 3, "sport": 7}   # sul terreno disegnato
    T = carica("tematismi")["livelli"]
    assert {k: len(v["poligoni"]) for k, v in T.items()} == {"verde": 103, "idraulica": 30, "alluvione1966": 1, "acustica": 9, "zone30": 179, "residenti": 126}
    assert all(q["c"] < len(v["classi"]) for v in T.values() for q in v["poligoni"]) and set(T) <= set(IDX["livelli"])
    nuove = {"src_fi_farmacie", "src_fi_sosta_disabili", "src_fi_pericolosita_idraulica", "src_fi_pcca", "src_fi_sezioni2011", "src_rt_censimento2011"}
    f = {x["id"]: x for x in IDX["fonti"]}
    assert nuove <= set(f) and all(f[k].get("fuori_baseline") for k in nuove) and f["src_rt_censimento2011"]["stato_licenza"] == "clear_with_reserve"



def test_costruzione_fallita_lascia_la_scena():
    import sys
    def guasto(): raise RuntimeError("input mancante")
    vero, argv = build.terreno, sys.argv
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d) / "assets"; out.mkdir()
        (out / "edifici.json.gz").write_bytes(b"vecchio"); (out / "index.json").write_text("{}")
        build.terreno, sys.argv = guasto, ["build.py", "--out", str(out)]
        try:
            build.main(); assert False, "doveva fallire"
        except RuntimeError: pass
        finally: build.terreno, sys.argv = vero, argv
        assert (out / "edifici.json.gz").read_bytes() == b"vecchio" and (out / "index.json").exists()
        assert [f.name for f in pathlib.Path(d).iterdir()] == ["assets"]   # temporaneo rimosso

def test_pagina_di_metodo():
    """F1: metodo.html aggiornata rispetto a schede e indice, raggiungibile dalla scena, con un'ancora per ogni fonte."""
    import metodo
    H = pathlib.Path(__file__).resolve().parent
    pag = (H / "metodo.html").read_text()
    assert pag == metodo.pagina(), "metodo.html da rigenerare: pipeline/.venv/bin/python scene/firenze_novoli/metodo.py"
    assert 'href="metodo.html"' in (H / "index.html").read_text()
    ancore = set(re.findall(r'<details id="(src_[a-z0-9_]+)"', pag))
    assert {f["id"] for f in IDX["fonti"]} <= ancore and set(metodo.schede.fonti()) == ancore
    assert set(re.findall(r'href="#(src_[a-z0-9_]+)"', pag)) <= ancore   # nessun rimando a schede che non ci sono
    assert pag.count("<h1>") == 1 and 'lang="it"' in pag and "<caption" in pag



def test_arrivo_al_rifugio_all_ombra():
    """F6: civici entro 15 minuti dal rifugio più vicino per classe d'ombra; la soglia del 50% separa le classi e torna con il risultato; metodo collegato."""
    with tempfile.TemporaryDirectory() as d:
        assert build.ombra_rifugi(d) is None
    O = carica("ombra_rifugi"); R = json.load(open(build.ROOT / "shadow/firenze_novoli/ombra_rifugi_2026-07-15.json"))
    assert O["n"] == len(O["punti"]) == sum(c["civici"] for c in O["classi"]) == R["civici_entro_15_min"]
    sopra = [c for c in O["classi"] if "soprattutto" in c["t"]]
    assert O["soglia"] == 0.5 and [L for L, _, _ in build.CLASSI_OMBRA].index(0.5) == len(O["classi"]) - len(sopra) - 1
    assert sum(c["civici"] for c in sopra) == sum(p["o"] >= O["soglia"] for p in O["punti"]) == R["soglie"][1]["soprattutto_ombra"]["civici"]
    assert all(s["riserva"] for s in O["soglie"]) and all(c["c"].startswith("#") for c in O["classi"])
    H = pathlib.Path(__file__).resolve().parent
    assert 'id="ombra_rifugi"' in (H / "metodo.html").read_text() and "metodo.html#ombra_rifugi" in (H / "app.js").read_text()


def test_civico_a_pari_distanza():
    """D58: due civici dentro l'edificio (distanza 0): vince il CODICECIVI minore, in qualunque ordine li dia l'indice spaziale."""
    import geopandas as gpd
    from shapely.geometry import Point, box
    civ = gpd.GeoDataFrame({"CODICECIVI": ["B10", "B08", "A99R", "C01"], "rosso": [False, False, True, False]},
                           geometry=[Point(1, 1), Point(2, 2), Point(1.5, 1.5), Point(20, 20)])
    ed = box(0, 0, 3, 3)
    assert {build.civico_vicino(civ, v, ed) for v in ([0, 1, 2, 3], [3, 2, 1, 0], [1, 0])} == {1}
    assert build.civico_vicino(civ, [2, 3], ed) == 3 and build.civico_vicino(civ, [], ed) is None   # i neri prima dei rossi
    bis = [e["ind"] for e in carica("edifici")["edifici"] if e["id"] == "bld_rt_RT0201010201432041"]
    assert bis == ["Via Bisenzio 6"], bis   # dentro ci sono il 6, l'8 e il 10: sul Mac usciva il 10, sul worker l'8


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
