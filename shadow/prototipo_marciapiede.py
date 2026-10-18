#!/usr/bin/env python3
"""F5, compito 5: prototipo dell'ombra sul marciapiede, solo su R01. Fuori dai risultati ufficiali: non scrive manifest né job.

Oggi l'ombra si misura sull'asse della rete. Qui R01 si sposta ai due lati della strada: ogni segmento del percorso va a sinistra e a destra
della distanza dal marciapiede mappato a parte in OSM (arco pedonale parallelo entro 8 m, distanza dal punto medio del segmento); dove
non c'è un marciapiede mappato, della mezza larghezza dichiarata MEZZA_DEFAULT_M. Sui tratti già pedonali (sentieri, piazze) e sui
raccordi il percorso resta dov'è. Ombra all'istante, motore shadow/ombre.py, casi solo edifici e con vegetazione LiDAR (tipico).

Uso: pipeline/.venv/bin/python shadow/prototipo_marciapiede.py
Scrive: shadow/<area>/prototipo_marciapiede_R01.json (quote d'ombra per lato e per orario, spostamento dei bordi rispetto all'asse)."""
import json, math, os, sys, time
import numpy as np, shapely
from shapely.geometry import LineString, box, shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "network"))
import ombre as O, esposizione as ESP, run as RUN  # noqa: E402
import rete_lib as RL  # noqa: E402

ISTANTI = [("2026-07-15", "14:00"), ("2026-12-12", "11:00"), ("2026-12-12", "13:00"), ("2026-12-12", "14:30")]   # D49 e verifica sul posto (D50)
CASI = ["base", "veg_lidar_tipico"]
MEZZA_DEFAULT_M = 3.0      # dichiarata: mezza carreggiata di una strada residenziale senza marciapiede mappato
RAGGIO_M, ANGOLO_MAX = 8.0, 30.0
TIPI_PEDONALI = ("sentiero", "marciapiede_disegnato")


def lati(L, G):
    """Per ogni segmento di L: (a, b, distanza a sinistra, distanza a destra, fonte). Raccordi (primo e ultimo segmento) e tratti pedonali sull'asse."""
    E = [d for _, _, d in G.edges(data=True)]; pedonali = [d for d in E if d["tipo_arco"] in TIPI_PEDONALI]
    gp = np.array([d["geom"] for d in pedonali], dtype=object); strade = np.array([d["geom"] for d in E if d["tipo_arco"] not in TIPI_PEDONALI], dtype=object)
    c = np.array(L.coords); out = []
    for i, (a, b) in enumerate(zip(c[:-1], c[1:])):
        m = shapely.Point((a + b) / 2); v = (b - a) / np.linalg.norm(b - a)
        if i in (0, len(c) - 2) or shapely.distance(strade, m).min() > 0.5:   # raccordo, o segmento non su una strada
            out.append((a, b, 0.0, 0.0, "asse")); continue
        d = {+1: None, -1: None}
        for g in gp[shapely.distance(gp, m) <= RAGGIO_M]:
            p = np.array(shapely.line_interpolate_point(g, shapely.line_locate_point(g, m)).coords[0]); s = shapely.line_locate_point(g, m)
            q = np.array(shapely.line_interpolate_point(g, min(s + 1.0, g.length)).coords[0]) - np.array(shapely.line_interpolate_point(g, max(s - 1.0, 0)).coords[0])
            if np.linalg.norm(q) == 0 or abs(np.dot(q / np.linalg.norm(q), v)) < math.cos(math.radians(ANGOLO_MAX)): continue   # non parallelo
            w = p - np.array(m.coords[0]); lato = 1 if v[0] * w[1] - v[1] * w[0] > 0 else -1; dist = float(np.linalg.norm(w))
            if dist > 0.5 and (d[lato] is None or dist < d[lato]): d[lato] = dist
        out.append((a, b, d[1] if d[1] is not None else MEZZA_DEFAULT_M, d[-1] if d[-1] is not None else MEZZA_DEFAULT_M,
                    "+".join("osm" if d[k] is not None else "default" for k in (1, -1))))
    return out


def linea(seg, lato):
    """Segmenti spostati di lato (+1 sinistra, -1 destra, 0 asse) e posizione d'inizio di ognuno lungo l'asse."""
    s0, out = 0.0, []
    for a, b, ds, dd, _ in seg:
        v = (b - a) / np.linalg.norm(b - a); n = np.array([-v[1], v[0]]) * {1: ds, -1: -dd, 0: 0.0}[lato]
        out.append((LineString([a + n, b + n]), s0, float(np.linalg.norm(b - a)))); s0 += float(np.linalg.norm(b - a))
    return out


def tratti_ombra(segs, U):
    """Intervalli in ombra (metri dall'inizio, misurati sull'asse) e metri in ombra della linea spostata."""
    iv, m = [], 0.0
    for g, s0, la in segs:
        k = la / g.length
        for p in shapely.get_parts(g.intersection(U)):
            if p.geom_type != "LineString" or p.length == 0: continue
            t = sorted(shapely.line_locate_point(g, shapely.points(np.array(p.coords)[[0, -1]]))); iv.append([s0 + t[0] * k, s0 + t[1] * k]); m += p.length
    iv.sort(); fusi = []
    for a, b in iv:
        if fusi and a - fusi[-1][1] < 1.0: fusi[-1][1] = max(fusi[-1][1], b)   # buchi sotto 1 m uniti, come la pagina di verifica
        else: fusi.append([a, b])
    return [[round(a, 1), round(b, 1)] for a, b in fusi], m


def bordi(iv, L): return [x for a, b in iv for x in (a, b) if 0.5 < x < L - 0.5]


def main():
    t0 = time.time(); ESP.guardiano()
    RUN.PERCORSI = ["R01"]; L = shape(RUN.ricevitori()[0]["geometry"]); G, _ = RL.carica()
    seg = lati(L, G); fin = box(*L.bounds).buffer(10.0); Lax = sum(np.linalg.norm(b - a) for a, b, *_ in seg)
    linee = {nome: linea(seg, k) for nome, k in (("asse", 0), ("sinistra", 1), ("destra", -1))}
    R = {"percorso": "R01", "stato": "prototipo, fuori dai risultati ufficiali", "lunghezza_asse_m": round(Lax, 1),
         "metodo": {"lati": "sinistra e destra nel verso di marcia (fermata T2 San Donato - Università -> ingresso D15 del Polo)",
                    "distanza": f"dal marciapiede mappato a parte in OSM (arco pedonale parallelo entro {RAGGIO_M:g} m, angolo sotto {ANGOLO_MAX:g} gradi), altrimenti {MEZZA_DEFAULT_M:g} m dichiarati",
                    "asse": "raccordi e tratti pedonali restano sull'asse", "casi": CASI, "unione_buchi_m": 1.0},
         "segmenti": {"totali": len(seg), "sull_asse": sum(s[4] == "asse" for s in seg),
                      "metri_con_marciapiede_osm": {lato: round(sum(np.linalg.norm(b - a) for a, b, ds, dd, f in seg if f != "asse" and f.split("+")[i] == "osm"), 1) for i, lato in enumerate(("sinistra", "destra"))},
                      "metri_con_valore_dichiarato": {lato: round(sum(np.linalg.norm(b - a) for a, b, ds, dd, f in seg if f != "asse" and f.split("+")[i] == "default"), 1) for i, lato in enumerate(("sinistra", "destra"))},
                      "distanza_mediana_m": {lato: round(float(np.median([s[2 + i] for s in seg if s[4] != "asse"])), 2) for i, lato in enumerate(("sinistra", "destra"))}},
         "istanti": []}
    for data, ora in ISTANTI:
        for caso in CASI:
            st, az, el, U = O.ombra_a_istante(O.scena_caso(caso), O.locale_a_utc(data, ora), O.SOLE_LAT, O.SOLE_LON, finestra=fin)
            x = {"data": data, "ora": ora, "caso": caso, "sole": {"azimut_deg": round(az, 1), "elevazione_deg": round(el, 1)}, "lati": {}}
            for nome, segs in linee.items():
                iv, m = tratti_ombra(segs, U); lung = sum(g.length for g, _, _ in segs)
                x["lati"][nome] = {"lunghezza_m": round(lung, 1), "frazione_ombra": round(m / lung, 4), "tratti_ombra_m": iv}
            ba = bordi(x["lati"]["asse"]["tratti_ombra_m"], Lax)
            for nome in ("sinistra", "destra"):
                bl = bordi(x["lati"][nome]["tratti_ombra_m"], Lax)
                sp = [min(abs(b - c) for c in bl) for b in ba] if bl else []
                x["lati"][nome]["bordi"] = len(bl); x["lati"][nome]["spostamento_bordi_m"] = {"bordi_asse": len(ba), "mediana": round(float(np.median(sp)), 1) if sp else None,
                                                                                            "massimo": round(max(sp), 1) if sp else None, "oltre_10_m": int(sum(s > 10 for s in sp))}
            R["istanti"].append(x); print(data, ora, caso, {k: v["frazione_ombra"] for k, v in x["lati"].items()}, flush=True)
    R["calcolo"] = {"secondi": round(time.time() - t0), "memoria_max_gb": ESP.memoria_max_gb()}
    (ESP.OUT / "prototipo_marciapiede_R01.json").write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n")
    print(R["segmenti"], R["calcolo"])


if __name__ == "__main__":
    main()
