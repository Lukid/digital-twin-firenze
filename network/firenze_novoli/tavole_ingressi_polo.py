#!/usr/bin/env python3
"""Tavole per il controllo degli ingressi del Polo sull'ortofoto regionale 2024/2025 (layer rt_ofc.5k24.32bit).
Ogni tavola è un SVG: l'ortofoto è richiamata dal WMS della Regione al momento della visualizzazione (non scaricata né versionata),
sopra ci sono edifici e rete OSM, i punti OSM con entrance/barrier, gli ingressi del Polo e i civici del Comune di Via delle Pandette,
Via Miele e Largo Frezza. Uso: pipeline/.venv/bin/python network/firenze_novoli/tavole_ingressi_polo.py [cartella di uscita]
(default data/norm/firenze_novoli/network/tavole_polo/, fuori da git)."""
import json, pathlib, sys, urllib.parse
from xml.sax.saxutils import escape
import geopandas as gpd

ROOT = pathlib.Path(__file__).resolve().parents[2]
NORM = ROOT / "data/norm/firenze_novoli"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else NORM / "network/tavole_polo"
WMS = "https://www502.regione.toscana.it/ows_ofc/com.rt.wms.RTmap/wms?map=owsofc_rt&"
FONTE = "Ortofoto 2024/2025 Regione Toscana (rt_ofc.5k24.32bit), solo consultazione WMS. Vettori: OSM (ODbL), civici Comune di Firenze."
TAVOLE = {   # nome: (x0, y0, x1, y1) EPSG:7791, metri per pixel
    "insieme": ((679200, 4851050, 679850, 4851520), 0.5),
    "asse_pandette": ((679395, 4851195, 679585, 4851400), 0.2),
    "E1_n11152998932": ((679383, 4851182, 679483, 4851282), 0.125),
    "E2_n11152998933": ((679485, 4851256, 679585, 4851356), 0.125),
}
COL = {"strada": "#ff7800", "sentiero": "#00ffff", "attraversamento": "#ffffff", "marciapiede_disegnato": "#00ff00"}


def dati():
    B = (679150, 4851000, 679900, 4851550)
    archi = gpd.read_file(NORM / "network/rete_firenze_novoli.gpkg", layer="archi", bbox=B)
    punti = gpd.read_file(NORM / "osm_firenze.gpkg", layer="points", bbox=B)
    edifici = gpd.read_file(NORM / "osm_firenze.gpkg", layer="buildings", bbox=B)
    civ = gpd.read_file(NORM / "fi_civici.gpkg", bbox=B)
    civ = civ[civ.STRADA.str.contains("PANDETTE|MIELE|FREZZA", na=False)]
    tag = lambda t: json.loads(t) if isinstance(t, str) else {}
    punti = [(r.geometry, tag(r.tags)) for r in punti.itertuples()]
    dst = json.loads((ROOT / "network/firenze_novoli/destinazioni.json").read_text())["destinazioni"]
    ingressi = [i for d in dst if d["destination_id"] == "dst_university_w83537185" for i in d["ingressi"]]
    return archi, [(g, t) for g, t in punti if {"entrance", "barrier"} & set(t)], edifici, civ, ingressi


def tavola(nome, bbox, res, archi, punti, edifici, civ, ingressi):
    x0, y0, x1, y1 = bbox; w, h = round((x1 - x0) / res), round((y1 - y0) / res)
    P = lambda cs: " ".join(f"{(x - x0) / res:.1f},{(y1 - y) / res:.1f}" for x, y, *_ in cs)
    q = dict(SERVICE="WMS", VERSION="1.3.0", REQUEST="GetMap", LAYERS="rt_ofc.5k24.32bit", STYLES="", CRS="EPSG:7791",
             BBOX=f"{x0},{y0},{x1},{y1}", WIDTH=w, HEIGHT=h, FORMAT="image/jpeg")
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h + 24}" font-family="sans-serif" font-size="11">',
         f'<image href="{escape(WMS + urllib.parse.urlencode(q))}" width="{w}" height="{h}"/>', '<g fill="none">']
    for g in edifici.geometry:
        for p in getattr(g, "geoms", [g]): s.append(f'<polyline points="{P(p.exterior.coords)}" stroke="#ffff00"/>')
    for r in archi.itertuples():
        c = "#888888" if "no" in (r.access, r.foot) or "private" in (r.access, r.foot) else COL.get(r.tipo_arco, "#ff00ff")
        s.append(f'<polyline points="{P(r.geometry.coords)}" stroke="{c}" stroke-width="2"><title>{escape(f"{r.edge_id} {r.tipo_arco}")}</title></polyline>')
    s.append("</g>")
    for g, t in punti:
        x, y = (g.x - x0) / res, (y1 - g.y) / res
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="none" stroke="#0000ff" stroke-width="2"/><text x="{x + 6:.1f}" y="{y:.1f}" fill="#0000ff">{escape(t.get("barrier", "entrance"))}</text>')
    for r in civ.itertuples():
        x, y = (r.geometry.x - x0) / res, (y1 - r.geometry.y) / res
        s.append(f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="none" stroke="#ff00ff" stroke-width="2"/><text x="{x + 6:.1f}" y="{y + 4:.1f}" fill="#ffffff">{escape(f"{r.STRADA.split()[-1].title()} {r.NUMEROCIVI}")}</text>')
    for i in ingressi:
        x, y = (i["xy"][0] - x0) / res, (y1 - i["xy"][1]) / res
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="none" stroke="#ff0000" stroke-width="3"/><text x="{x + 10:.1f}" y="{y:.1f}" fill="#ff0000" font-weight="bold">{i["entrance_id"]}</text>')
    s += [f'<text x="4" y="{h + 16}" fill="#000">{escape(FONTE)}</text>', "</svg>"]
    (OUT / f"{nome}.svg").write_text("\n".join(s))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True); d = dati()
    for nome, (bbox, res) in TAVOLE.items(): tavola(nome, bbox, res, *d); print(OUT / f"{nome}.svg")
