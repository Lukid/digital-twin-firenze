#!/usr/bin/env python3
"""F6, compito 1 (D56): ombra sui due lati della strada dei percorsi campione R01-R10 e RC1-RC5, accanto all'asse. Promosso dal prototipo F5 (solo R01).
Stato: prototipo, da verificare sul posto. Non scrive manifest né job: i risultati sull'asse (sintesi, esposizione, scenari) restano quelli di sempre.

Ogni segmento di strada del percorso va a sinistra e a destra nel verso di marcia, della distanza dal marciapiede mappato a parte in OSM (arco pedonale
parallelo entro 8 m, angolo sotto 30 gradi, dal punto medio del segmento); dove non c'è, del valore dichiarato MEZZA_DEFAULT_M. Raccordi e tratti già
pedonali (sentieri, piazze) restano sull'asse. Ombra all'istante, motore shadow/ombre.py, casi solo edifici e con vegetazione LiDAR (tipico).
Istanti: quelli dei risultati ufficiali di ogni percorso (sintesi: 15 luglio e 15 settembre, 8-19 ogni 30 minuti; esposizione: 14 del 15 luglio),
più gli orari della verifica del 12 dicembre per R01 (D50).

Uso: pipeline/.venv/bin/python shadow/lati_strada.py
Scrive: shadow/<area>/lati_strada.json"""
import json, math, os, sys, time
import numpy as np, shapely
from shapely.geometry import LineString, box, shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "network"))
import ombre as O, esposizione as ESP, run as RUN  # noqa: E402
import rete_lib as RL  # noqa: E402

GIORNATA = [(d, h) for d in RUN.DATE for h in RUN.ORARI]                    # sintesi.json, sintesi_rifugi_RCn.json (comprende le 14 del 15 luglio)
LUGLIO_14 = [("2026-07-15", "14:00")]                                       # esposizione_2026-07-15.json (D49)
VERIFICA = [("2026-12-12", h) for h in ("11:00", "13:00", "14:30")]          # esposizione_2026-12-12.json, verifica sul posto (D50)
ISTANTI = {"R01": GIORNATA + VERIFICA, "R02": GIORNATA, **{f"R{i:02d}": LUGLIO_14 for i in range(3, 11)}, **{f"RC{i}": GIORNATA for i in range(1, 6)}}
CASI = {"base": "edifici", "veg_lidar_tipico": "con_vegetazione"}           # principale: con vegetazione, come esposizione (D14)
MEZZA_DEFAULT_M = 3.0      # dichiarata: distanza del lato dove il marciapiede non è mappato a parte (D56)
RAGGIO_M, ANGOLO_MAX = 8.0, 30.0
TIPI_PEDONALI = ("sentiero", "marciapiede_disegnato")
PARI = 0.005               # sotto mezzo punto di differenza i due lati sono "pari"
LIMITI = [("prototipo_da_verificare", "Prototipo, da verificare sul posto: nessun lato della strada è stato osservato."),
          ("lato_scelto_da_chi_cammina", "Il lato lo sceglie chi cammina: sinistra e destra sono due linee intere, non un percorso che sceglie il lato più in ombra."),
          ("attraversamenti_non_modellati", "Attraversamenti non modellati: chi cambia lato attraversa, e il percorso più breve sul grafo non sa quale lato usa."),
          ("valore_dichiarato", f"Dove il marciapiede non è mappato a parte in OSM la distanza dall'asse è il valore dichiarato di {MEZZA_DEFAULT_M:g} m, non una larghezza misurata (metri per lato nel campo metri_valore_dichiarato)."),
          ("asse_nei_tratti_pedonali", "Raccordi e tratti pedonali (sentieri, piazze) restano sull'asse; ombra a un istante, non lungo il cammino."),
          ("vegetazione_prisma", "Vegetazione LiDAR come prisma opaco pieno: limite superiore dell'ombra; più i limiti del motore d'ombra sull'asse (altezze, portici ignoti).")]


def lati(L, G):
    """Per ogni segmento di L: (a, b, distanza a sinistra, distanza a destra, fonte). Raccordi (primo e ultimo segmento) e tratti pedonali sull'asse."""
    E = [d for _, _, d in G.edges(data=True)]; pedonali = [d for d in E if d["tipo_arco"] in TIPI_PEDONALI]
    gp = np.array([d["geom"] for d in pedonali], dtype=object); strade = np.array([d["geom"] for d in E if d["tipo_arco"] not in TIPI_PEDONALI], dtype=object)
    c = np.array(L.coords); out = []
    for i, (a, b) in enumerate(zip(c[:-1], c[1:])):
        if np.linalg.norm(b - a) == 0: continue
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


def ufficiale(rid, data, ora, caso):
    """Frazione d'ombra sull'asse dei risultati ufficiali: sintesi per ora (R01, R02, RC1-RC5), altrimenti esposizione all'istante. None se non c'è."""
    f = RUN.OUT / ("sintesi.json" if rid in ("R01", "R02") else f"sintesi_rifugi_{rid}.json")
    if f.exists():
        v = json.load(open(f))["frazione_per_ora"].get(data, {}).get(f"pth_fi_{rid}", {}).get(caso, {}).get(ora)
        if isinstance(v, float): return v
    f = RUN.OUT / f"esposizione_{data}.json"
    if not f.exists(): return None
    o = json.load(open(f))["percorsi"].get(rid, {}).get("orari", {}).get(ora)
    if not o or "frazione_ombra" not in o: return None
    return o["frazione_ombra"] if caso == "veg_lidar_tipico" else o["solo_edifici"]["frazione_ombra"]


def metri(seg, i, fonte): return round(sum(float(np.linalg.norm(b - a)) for a, b, *_, f in seg if f != "asse" and f.split("+")[i] == fonte), 1)


def percorso(rid, G, scene, istanti):
    RUN.PERCORSI = [rid]; rec = RUN.ricevitori()[0]; L = shape(rec["geometry"])
    seg = lati(L, G); fin = box(*L.bounds).buffer(10.0)
    linee = {nome: linea(seg, k) for nome, k in (("asse", 0), ("sinistra", 1), ("destra", -1))}
    P = {"descrizione": rec["_descrizione"], "verso": "sinistra e destra nel verso di marcia, dall'origine alla destinazione della descrizione",
         "lunghezza_asse_m": round(sum(la for _, _, la in linee["asse"]), 1),
         "metri_sull_asse": round(sum(float(np.linalg.norm(b - a)) for a, b, *_, f in seg if f == "asse"), 1),
         "metri_marciapiede_osm": {lato: metri(seg, i, "osm") for i, lato in enumerate(("sinistra", "destra"))},
         "metri_valore_dichiarato": {lato: metri(seg, i, "default") for i, lato in enumerate(("sinistra", "destra"))},
         "distanza_mediana_m": {lato: round(float(np.median([s[2 + i] for s in seg if s[4] != "asse"])), 2) if any(s[4] != "asse" for s in seg) else None
                                for i, lato in enumerate(("sinistra", "destra"))},
         "istanti": []}
    for data, ora in istanti:
        x = {"data": data, "ora": ora}
        for caso, nome in CASI.items():
            st, az, el, U = O.ombra_a_istante(scene[caso], O.locale_a_utc(data, ora), O.SOLE_LAT, O.SOLE_LON, finestra=fin)
            x["sole"] = {"stato": st, "azimut_deg": round(az, 1), "elevazione_deg": round(el, 1)}
            if st != O.STATO_OK: continue
            r = {}
            for lato, segs in linee.items():
                iv, m = tratti_ombra(segs, U); r[lato] = round(m / sum(g.length for g, _, _ in segs), 4)
                if rid == "R01" and data == VERIFICA[0][0] and caso == "base": x.setdefault("tratti_ombra_m", {})[lato] = iv   # per la verifica sul posto
            r["asse_ufficiale"] = ufficiale(rid, data, ora, caso); x[nome] = r
        if "con_vegetazione" in x:
            s, d = x["con_vegetazione"]["sinistra"], x["con_vegetazione"]["destra"]
            x["lato_piu_in_ombra"] = "pari" if abs(s - d) < PARI else "sinistra" if s > d else "destra"
        P["istanti"].append(x)
    return P


def main():
    t0 = time.time(); ESP.guardiano()
    G, _ = RL.carica(); scene = {c: O.scena_caso(c) for c in CASI}
    R = {"stato": "prototipo, da verificare sul posto", "versione_motore": O.VERSIONE, "baseline_id": O.BASELINE_ID,
         "ricevitore": "due linee parallele all'asse del percorso, a sinistra e a destra nel verso di marcia; l'asse accanto, calcolato allo stesso modo",
         "metodo": {"distanza": f"dal marciapiede mappato a parte in OSM (arco pedonale parallelo entro {RAGGIO_M:g} m, angolo sotto {ANGOLO_MAX:g} gradi, dal punto medio del segmento), altrimenti {MEZZA_DEFAULT_M:g} m dichiarati",
                    "asse": "raccordi e tratti pedonali restano sull'asse", "casi": CASI, "frazione": "metri in ombra della linea all'istante / lunghezza della linea",
                    "asse_ufficiale": "frazione sull'asse dei risultati ufficiali allo stesso istante (sintesi per ora o esposizione), per confronto",
                    "lato_piu_in_ombra": f"caso con vegetazione; 'pari' sotto {PARI * 100:g} punti di differenza", "unione_buchi_m": 1.0},
         "snapshot_ids": sorted(set(O.SNAPSHOT_IDS["edifici"]) | set(O.SNAPSHOT_IDS["alberi"])),
         "fonti": [{"source_id": "edifici, alberi, LiDAR e rete OSM della baseline", "licenza": "vedi get_source_card per ogni snapshot", "data_del_dato": "baseline 2026-10-09"}],
         "limits": [{"code": k, "text": t} for k, t in LIMITI], "percorsi": {}}
    for rid, ist in ISTANTI.items():
        tp = time.time(); R["percorsi"][rid] = P = percorso(rid, G, scene, ist)
        print(rid, len(ist), "istanti", round(time.time() - tp), "s", ESP.memoria_max_gb(), "GB", P["metri_valore_dichiarato"], flush=True)
    R["calcolo"] = {"secondi": round(time.time() - t0), "memoria_max_gb": ESP.memoria_max_gb()}
    (RUN.OUT / "lati_strada.json").write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n")
    print(R["calcolo"])


if __name__ == "__main__":
    main()
