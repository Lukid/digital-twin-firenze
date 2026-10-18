#!/usr/bin/env python3
"""F4, compito 5: pagina stampabile per verificare sul posto l'ombra attesa su un percorso campione.
Legge shadow/<area>/esposizione_<data>.json (shadow/esposizione.py) e scrive, in questa cartella, <percorso>_<data>.html e <percorso>_<data>.json
(punti di osservazione e tratti in ombra attesi). Ombra attesa = solo edifici: d'inverno gli alberi della zona sono in buona parte spogli.

Uso: pipeline/.venv/bin/python shadow/esposizione.py --data 2026-12-12 --orari 11:00,13:00,14:30 --percorso R01
     pipeline/.venv/bin/python docs/verifica-posto/pagina.py --data 2026-12-12 --percorso R01"""
import argparse, html, json, pathlib, sys
import geopandas as gpd, numpy as np, shapely
from pyproj import Transformer
from shapely.geometry import shape

QUI = pathlib.Path(__file__).resolve().parent
ROOT = QUI.parents[1]
sys.path.insert(0, str(ROOT / "network"))
import rete_lib as RL  # noqa: E402

_da_ll = Transformer.from_crs(4326, 7791, always_xy=True).transform
UNISCI_M = 8   # bordi d'ombra di orari diversi più vicini di così: un solo punto di osservazione
CASO = "base"  # solo edifici


def m(g): return shapely.transform(shape(g), lambda c: np.column_stack(_da_ll(c[:, 0], c[:, 1])))


def intervalli(L, g):
    """Tratti in ombra come intervalli [da, a] in metri dall'inizio del percorso; buchi sotto 1 m uniti (giunzioni fra ombre di edifici vicini)."""
    if not g: return []
    out = []
    for p in sorted(shapely.get_parts(m(g)), key=lambda p: min(L.project(shapely.Point(p.coords[0])), L.project(shapely.Point(p.coords[-1])))):
        a, b = sorted((L.project(shapely.Point(p.coords[0])), L.project(shapely.Point(p.coords[-1]))))
        if b - a < 0.5: continue
        if out and a - out[-1][1] < 1: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return [(round(a, 1), round(b, 1)) for a, b in out]


def stato(iv, d):
    return "ombra" if any(a - 0.5 <= d <= b + 0.5 for a, b in iv) else "sole"


def strade(rid):
    """Nomi delle strade lungo il percorso, nell'ordine, dal grafo pedonale."""
    G, _ = RL.carica(); nome = {e["edge_id"]: e.get("name") or "vialetto pedonale" for _, _, e in G.edges(data=True)}
    archi = next(x for x in json.load(open(RL.RES / "percorsi_campione.json")) if x["id"] == rid)["archi"]
    out = []
    for a in archi:
        if nome.get(a) and (not out or out[-1] != nome[a]): out.append(nome[a])
    return out


def svg_mappa(L, punti, edifici, larghezza=640):
    x0, y0, x1, y1 = L.buffer(60).bounds; s = larghezza / (x1 - x0); h = (y1 - y0) * s
    P = lambda x, y: f"{(x - x0) * s:.1f},{(y1 - y) * s:.1f}"
    poli = []
    for g in edifici:
        for p in shapely.get_parts(g):
            poli.append(f'<polygon class="ed" points="{" ".join(P(x, y) for x, y in p.exterior.coords)}"/>')
    linea = f'<polyline class="perc" points="{" ".join(P(x, y) for x, y in L.coords)}"/>'
    pt = ""
    for q in punti:
        x, y = (float(v) for v in P(*L.interpolate(q["m"]).coords[0]).split(","))
        pt += f'<g><circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="9"/><text x="{x:.1f}" y="{y + 4:.1f}">{q["n"]}</text></g>'
    nord = f'<g transform="translate({larghezza - 30},30)"><path d="M0,-18 L7,8 L0,3 L-7,8 Z" class="nord"/><text y="22">N</text></g>'
    scala = f'<g transform="translate(16,{h - 16:.0f})"><line x1="0" y1="0" x2="{50 * s:.1f}" y2="0" class="scala"/><text x="{25 * s:.1f}" y="-6">50 m</text></g>'
    return (f'<svg viewBox="0 0 {larghezza} {h:.0f}" role="img" aria-label="Mappa del percorso con gli edifici e i punti di osservazione numerati">'
            + "".join(poli) + linea + pt + nord + scala + "</svg>")


def svg_striscia(L, iv, punti, larghezza=640):
    s = (larghezza - 20) / L.length; X = lambda d: 10 + d * s
    r = [f'<rect class="sole" x="10" y="14" width="{L.length * s:.1f}" height="18"/>']
    r += [f'<rect class="ombra" x="{X(a):.1f}" y="14" width="{(b - a) * s:.1f}" height="18"/>' for a, b in iv]
    r += [f'<line class="tick" x1="{X(q["m"]):.1f}" y1="8" x2="{X(q["m"]):.1f}" y2="38"/><text x="{X(q["m"]):.1f}" y="50">{q["n"]}</text>' for q in punti]
    return f'<svg viewBox="0 0 {larghezza} 56" role="img" aria-label="Tratti in ombra attesi lungo il percorso">' + "".join(r) + "</svg>"


def main():
    a = argparse.ArgumentParser(); a.add_argument("--data", required=True); a.add_argument("--percorso", default="R01"); a = a.parse_args()
    E = json.loads((ROOT / "shadow/firenze_novoli" / f"esposizione_{a.data}.json").read_text()); P = E["percorsi"][a.percorso]
    L = next(m(f["geometry"]) for f in json.load(open(RL.RES / "percorsi_campione.geojson"))["features"] if f["properties"]["id"] == a.percorso and f["geometry"]["type"] == "LineString")
    orari = {h: o for h, o in P["orari"].items() if o.get("geometrie")}
    iv = {h: intervalli(L, o["geometrie"][CASO]["ombra"]) for h, o in orari.items()}
    bordi = sorted({0.0, round(L.length, 1)} | {x for v in iv.values() for ab in v for x in ab if 1 < x < L.length - 1})
    tenuti = []
    for d in bordi:
        if not tenuti or d - tenuti[-1] >= UNISCI_M: tenuti.append(d)
    punti = [{"n": i + 1, "m": d, "atteso": {h: {"prima": stato(iv[h], max(d - 1.5, 0)), "dopo": stato(iv[h], min(d + 1.5, L.length))} for h in orari}} for i, d in enumerate(tenuti)]
    vol = gpd.read_file(ROOT / "data/norm/firenze_novoli/geometry/geometrie_firenze_novoli.gpkg", layer="volumi", bbox=L.buffer(60).bounds)
    edifici = [g for g in vol.geometry.clip(L.buffer(60).envelope) if not g.is_empty]
    nome = f"{a.percorso}_{a.data}"
    dati = {"percorso": a.percorso, "data": a.data, "job_id": P["job_id"], "caso": "solo edifici (base)", "lunghezza_m": round(L.length, 1), "strade": strade(a.percorso),
            "orari": {h: {"elevazione_deg": o["elevazione_deg"], "azimut_deg": o["azimut_deg"], "frazione_ombra_solo_edifici": o["solo_edifici"]["frazione_ombra"],
                          "frazione_ombra_con_vegetazione": o["frazione_ombra"], "tratti_ombra_m": iv[h]} for h, o in orari.items()},
            "punti": punti, "stato_verifica": "da_verificare"}
    (QUI / f"{nome}.json").write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n")
    lab = lambda x: {"ombra": "ombra", "sole": "sole"}[x]
    def cella(q, h):
        p, d = q["atteso"][h]["prima"], q["atteso"][h]["dopo"]
        return lab(p) if p == d else f"{lab(p)} → {lab(d)}"
    righe = "".join(f'<tr><th scope="row">{q["n"]}</th><td>{q["m"]:.0f} m</td>' + "".join(f"<td>{cella(q, h)}</td><td class='oss'></td>" for h in orari) + "</tr>" for q in punti)
    teste = "".join(f'<th scope="col">{h} atteso</th><th scope="col">{h} osservato</th>' for h in orari)
    strisce = "".join(f'<figure><figcaption><b>{h}</b>: sole a {o["elevazione_deg"]:.0f}° di altezza, da {o["azimut_deg"]:.0f}° (Nord = 0°). '
                      f'In ombra il {o["solo_edifici"]["frazione_ombra"] * 100:.0f}% del percorso (solo edifici; {o["frazione_ombra"] * 100:.0f}% con alberi e vegetazione).</figcaption>'
                      f'{svg_striscia(L, iv[h], punti)}</figure>' for h, o in orari.items())
    giorno = {"2026-12-12": "sabato 12 dicembre 2026"}.get(a.data, a.data)
    pagina = f"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verifica ombra {html.escape(a.percorso)}</title>
<style>
:root {{ --testo:#1a1a1a; --fondo:#fff; --linea:#888; --ombra:#3b4a6b; --sole:#f2c14e; --ed:#d9d9d9; }}
body {{ font: 11pt/1.4 system-ui, sans-serif; color: var(--testo); background: var(--fondo); max-width: 190mm; margin: 0 auto; padding: 16px; }}
h1 {{ font-size: 16pt; margin: 0 0 4px; }} h2 {{ font-size: 12.5pt; margin: 18px 0 6px; }}
svg {{ width: 100%; height: auto; display: block; }} figure {{ margin: 6px 0 10px; }} figcaption {{ font-size: 10pt; }}
.ed {{ fill: var(--ed); stroke: #b5b5b5; stroke-width: .5; }} .perc {{ fill: none; stroke: #c0392b; stroke-width: 4; }}
.pt {{ fill: #fff; stroke: #c0392b; stroke-width: 2; }} svg text {{ font: 10px system-ui, sans-serif; text-anchor: middle; }}
.nord {{ fill: var(--testo); }} .scala {{ stroke: var(--testo); stroke-width: 2; }}
.sole {{ fill: var(--sole); }} .ombra {{ fill: var(--ombra); }} .tick {{ stroke: var(--testo); stroke-width: 1; }}
.legenda span {{ display: inline-block; width: 14px; height: 10px; margin: 0 4px 0 12px; vertical-align: middle; }}
table {{ border-collapse: collapse; width: 100%; font-size: 9.5pt; }} th, td {{ border: 1px solid var(--linea); padding: 4px 5px; text-align: left; }}
td.oss {{ min-width: 22mm; }} ul, ol {{ padding-left: 20px; }} .nota {{ font-size: 9.5pt; }}
@media print {{ body {{ padding: 0; }} h2 {{ break-after: avoid; }} figure, table {{ break-inside: avoid; }} }}
</style></head><body>
<h1>Verifica dell'ombra sul posto: percorso {html.escape(a.percorso)}</h1>
<p>{html.escape(P["descrizione"])}. Lunghezza {L.length:.0f} m, circa {L.length / 1.2 / 60:.0f} minuti a piedi. Strade: {html.escape(", ".join(dati["strade"]))}.
Giorno: <b>{giorno}</b>. Orari: <b>{", ".join(orari)}</b> (ora di Roma). Calcolo: job <code>{P["job_id"]}</code>. Stato: da verificare.</p>
<p>Come arrivare: tram T2, fermata San Donato - Università. Il percorso parte dalla fermata e finisce all'ingresso dell'edificio D15 del Polo delle Scienze Sociali (Piazza Ugo di Toscana 5).</p>

<h2>Mappa e punti di osservazione</h2>
{svg_mappa(L, punti, edifici)}
<p class="nota">Linea rossa: percorso sull'asse della strada. Grigio: edifici del modello. Cerchi numerati: punti di osservazione, dove il calcolo prevede un bordo d'ombra in almeno uno degli orari, più inizio e fine.</p>

<h2>Ombra attesa per orario</h2>
<p class="legenda">Da sinistra (fermata) a destra (D15).<span style="background:var(--ombra)"></span>ombra<span style="background:var(--sole)"></span>sole</p>
{strisce}

<h2>Scheda da compilare</h2>
<table><thead><tr><th scope="col">Punto</th><th scope="col">Dalla fermata</th>{teste}</tr></thead><tbody>{righe}</tbody></table>
<p class="nota">"ombra → sole": camminando verso il D15, al punto l'ombra finisce. "sole → ombra": l'ombra comincia.</p>

<h2>Cosa annotare</h2>
<ol>
<li>A ogni orario, partire dalla fermata qualche minuto prima e percorrere tutto il percorso, sul marciapiede che si usa davvero (annotare quale lato).</li>
<li>In ogni punto: ombra o sole; se c'è un bordo d'ombra, la distanza fra il bordo e il punto in passi o metri, e verso dove (fermata o D15).</li>
<li>Bordi d'ombra non previsti: dove sono, rispetto al punto più vicino.</li>
<li>Ostacoli che il modello non ha: portici, impalcature, tende, alberi nuovi o abbattuti, chiome ancora con foglie, auto o furgoni alti, cantieri.</li>
<li>Foto: una per punto e per orario, verso il D15, con l'ora visibile.</li>
</ol>

<h2>Come confrontare osservato e calcolato</h2>
<ul>
<li>Per ogni punto e orario: concorda se lo stato osservato è quello atteso; per i bordi, scarto in metri fra il bordo osservato e il punto.</li>
<li>Scarti fino a 2-3 m sono attesi: il calcolo segue l'asse della strada, non il marciapiede, e le altezze degli edifici hanno un'incertezza di 0,5-2 m.</li>
<li>Scarti grandi o bordi mancanti: indicano un edificio con altezza sbagliata, un portico, un ostacolo nuovo o un tratto di rete diverso. Annotare cosa c'è.</li>
<li>Riportare le note in un file accanto a questa pagina (<code>{nome}_osservato.json</code> o una tabella), con data, ora vera dell'osservazione e lato del marciapiede.</li>
</ul>

<h2>Limiti del calcolo</h2>
<ul class="nota">
<li>Ombra geometrica degli edifici (unità volumetriche 2011 con altezze dal LiDAR 2023), sull'asse della strada; portici ignoti trattati come pieni.</li>
<li>D'inverno l'ombra attesa è quella dei soli edifici; con alberi e vegetazione del LiDAR la quota in ombra cambia al più di {max(abs(o["frazione_ombra"] - o["solo_edifici"]["frazione_ombra"]) for o in orari.values()) * 100:.1f} punti su questo percorso.</li>
<li>Sole calcolato senza rifrazione al centro dell'area; nuvole e foschia non contano.</li>
<li>Nessuna validazione sul posto finora: è lo scopo di questa scheda.</li>
</ul>
<p class="nota">Fonti: Regione Toscana (unità volumetriche), OpenStreetMap (ODbL), Comune di Firenze (DSM e DTM 2023, alberi, CC BY 4.0). Rifare con un'altra data:<br>
<code>pipeline/.venv/bin/python shadow/esposizione.py --data AAAA-MM-GG --orari 11:00,13:00,14:30 --percorso {html.escape(a.percorso)}</code><br>
<code>pipeline/.venv/bin/python docs/verifica-posto/pagina.py --data AAAA-MM-GG --percorso {html.escape(a.percorso)}</code></p>
</body></html>
"""
    (QUI / f"{nome}.html").write_text(pagina)
    print(nome, len(punti), "punti", {h: v for h, v in iv.items()})


if __name__ == "__main__":
    main()
