#!/usr/bin/env python3
"""Genera fieldwork/scheda.html (un solo file, nessuna dipendenza esterna) da punti.json, punti.geojson e dai dati di rete/edifici.
Uso: pipeline/.venv/bin/python fieldwork/genera_scheda.py"""
import json, html, collections
from pathlib import Path
import geopandas as gpd
from shapely.geometry import shape, box
import shapely.ops
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "fieldwork"
TO_M = Transformer.from_crs(4326, 7791, always_xy=True)
PJ = json.load(open(FW / "punti.json")); META = PJ["meta"]; PT = PJ["punti"]
GJ = json.load(open(FW / "punti.geojson"))
LINEE = {f["properties"]["id"][:-6]: shapely.ops.transform(lambda x, y, z=None: TO_M.transform(x, y), shape(f["geometry"])) for f in GJ["features"] if f["properties"]["gruppo"] == "percorso_linea"}
EA = gpd.read_file(ROOT / "data/norm/network/rete_z2.gpkg", layer="archi", engine="pyogrio")
BL = gpd.read_file(ROOT / "geometry/edifici_z2.geojson").set_crs(4326).to_crs(7791)
BID = {p["id_modello"] for p in PT if p["gruppo"] in ("edificio", "riferimento_altezza", "pensilina")}
esc = lambda s: html.escape(str(s), quote=True)
B_ = lambda: '<span class="b"></span>'
def opt(*xs): return " ".join(f'<span class="o">{B_()}{esc(x)}</span>' for x in xs)
BL_ = lambda lab, u="": f'<span class="o">{esc(lab)} <span class="ln"></span>{esc(u)}</span>'

CAMPI = {
    "esiste_oggetto": lambda p: "Esiste: " + opt("sì", "no", "diverso"),
    "posizione_oggetto": lambda p: BL_("GPS acc.", "m"),
    "altezza_edificio": lambda p: BL_("H gronda", "m") + " " + BL_("colmo", "m"),
    "portico": lambda p: "Portico: " + opt("sì", "no", "parziale"),
    "altezza_albero": lambda p: BL_("H", "m"),
    "chioma_diametro": lambda p: BL_("Chioma ø", "m") + " " + BL_("e", "m"),
    "altezza_imposta": lambda p: BL_("Imposta", "m"),
    "specie": lambda p: BL_("Specie") + " " + opt("rado", "medio", "denso"),
    "scala_gradini": lambda p: BL_("Gradini") + " Corrimano: " + opt("sì", "no") + " Rampa: " + opt("sì", "no") + " " + BL_("largh.", "m"),
    "cancello_passabile": lambda p: opt("passabile", "a orari", "chiuso", "non esiste", "aggirabile") + " " + BL_("largh.", "m"),
    "marciapiede_stato": lambda p: "Marciapiede: " + opt("entrambi", "un lato", "assente", "condivisa") + " " + BL_("largh. min.", "m"),
    "marciapiede_lato": lambda p: "Lato (verso la scuola): " + opt("sinistro", "destro", "entrambi", "nessuno"),
    "percorribile": lambda p: "Percorribile in sicurezza: " + opt("sì", "no"),
    "attraversamento_presente": lambda p: "Attraversamento: " + opt("strisce", "semaforo", "rialzato", "no"),
    "ingresso_in_uso": lambda p: "In uso: " + opt("sì", "no", "solo alunni", "solo personale", "altro"),
    "accesso_ingresso": lambda p: "Accesso: " + opt("sempre", "a orari", "su richiesta", "chiuso") + " " + BL_("orari:") + BL_("civico:"),
    "accesso_strada": lambda p: opt("privata", "pubblica", "con limitazioni", "non determinabile"),
    "accesso_negato": lambda p: "Dalla via pubblica: " + opt("negato", "consentito", "non determinabile"),
    "posizione_fermata": lambda p: BL_("GPS palo acc.", "m"),
    "lato_fermata_ok": lambda p: "Stesso lato della piattaforma OSM: " + opt("sì", "no"),
    "quota_imposta_pensilina": lambda p: BL_("Altezza libera", "m") + " " + BL_("soletta", "cm") + " " + opt("piena", "grigliata", "vetrata"),
    "altezza_assoluta_riferimento": lambda p: BL_("H metodo 1", "m") + " " + BL_("H metodo 2", "m") + " " + BL_("stazioni", "m"),
}
TITOLI = {"STAZ": "Tappa 1. Stazione", "PELL": "Tappa 2. Pellico e rotatoria", "R01": "Tappa 3. Passaggio A lungo R01 (Pellico verso la scuola)", "BATT": "Tappa 4. Scuola Battisti",
          "POE": "Tappa 5. Via Poerio e zona sud", "PCS": "Tappa 7. Percorsi campione a piedi", "EXTRA": "Facoltativo. Cancelli lontani"}

# ---------- mappe SVG ----------
def mappa(titolo, bbox, pts, W=720, linee=(), etichette=True, trees_dots_only=False, nota=""):
    x0, y0, x1, y1 = bbox; s = W / (x1 - x0); H = (y1 - y0) * s
    X = lambda x: round((x - x0) * s, 1); Y = lambda y: round((y1 - y) * s, 1)
    out = [f'<svg viewBox="0 0 {W} {H:.0f}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(titolo)}"><rect width="{W}" height="{H:.0f}" fill="#fff" stroke="#000" stroke-width="1"/>']
    bb = box(*bbox)
    for _, r in BL[BL.intersects(bb)].iterrows():
        tgt = r["id"] in BID
        for poly in (r.geometry.geoms if r.geometry.geom_type == "MultiPolygon" else [r.geometry]):
            d = "M" + "L".join(f"{X(a)},{Y(b)}" for a, b in poly.exterior.coords) + "Z"
            out.append(f'<path d="{d}" fill="{"#ccc" if tgt else "#efefef"}" stroke="{"#000" if tgt else "#999"}" stroke-width="{1.1 if tgt else 0.4}"/>')
    for _, r in EA[EA.intersects(bb)].iterrows():
        d = "M" + "L".join(f"{X(a)},{Y(b)}" for a, b in r.geometry.coords)
        st = ' stroke="#000" stroke-width="1.6" stroke-dasharray="1.5 1.5"' if r.highway == "steps" else (' stroke="#000" stroke-width="1.5" stroke-dasharray="4 2"' if r.tipo_arco == "attraversamento" else ' stroke="#777" stroke-width="0.9"')
        out.append(f'<path d="{d}" fill="none"{st}/>')
    for k, (lid, g) in enumerate(linee):
        d = "M" + "L".join(f"{X(a)},{Y(b)}" for a, b in g.coords)
        thick = lid == "R01"
        out.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{3.2 if thick else 1.6}" stroke-opacity="{0.55 if thick else 0.8}" stroke-dasharray="{"" if thick else "7 3"}"/>')
        m_ = g.interpolate(0.5, normalized=True); out.append(f'<text x="{X(m_.x)}" y="{Y(m_.y)}" class="lab" font-weight="bold">{lid}</text>')
    for p in pts:
        x, y = X(p["xy_m"][0]), Y(p["xy_m"][1])
        if not (0 <= x <= W and 0 <= y <= H): continue
        g_ = p["gruppo"]; pr = p["prio"]; r = 2.4 if g_ in ("albero",) else 4
        if g_ == "ombra": sym = f'<path d="M{x},{y-6}L{x+5},{y}L{x},{y+6}L{x-5},{y}Z" fill="#000"/>'
        elif g_ in ("edificio", "riferimento_altezza", "pensilina"): sym = f'<rect x="{x-3}" y="{y-3}" width="6" height="6" fill="{"#000" if pr == 1 else "#fff"}" stroke="#000" stroke-width="1.2"/>'
        elif pr == 3: sym = f'<path d="M{x},{y-4.5}L{x+4.5},{y+3.5}L{x-4.5},{y+3.5}Z" fill="#fff" stroke="#000" stroke-width="1.2"/>'
        else: sym = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{"#000" if pr == 1 else "#fff"}" stroke="#000" stroke-width="1.2"/>'
        out.append(sym)
        if etichette and not (trees_dots_only and g_ in ("albero", "edificio")):
            lab = p["id"].replace("PER-", "")
            out.append(f'<text x="{x+5}" y="{y-4}" class="lab">{esc(lab)}</text>')
    sb = 50 * s
    out.append(f'<g transform="translate(14,{H-14:.0f})"><path d="M0,0H{sb:.1f}" stroke="#000" stroke-width="2"/><path d="M0,-3V3M{sb:.1f},-3V3" stroke="#000"/><text x="{sb+4:.1f}" y="3" class="lab">50 m</text></g>')
    out.append(f'<g transform="translate({W-22},26)"><path d="M0,10V-14M-4,-8L0,-14L4,-8" fill="none" stroke="#000" stroke-width="1.5"/><text x="-3" y="22" class="lab">N</text></g></svg>')
    return f'<figure><figcaption>{esc(titolo)}</figcaption>{"".join(out)}{f"<p class=nota>{esc(nota)}</p>" if nota else ""}</figure>'

def bbox_di(pts, margin=40, minw=260):
    xs = [p["xy_m"][0] for p in pts]; ys = [p["xy_m"][1] for p in pts]
    x0, x1, y0, y1 = min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin
    if x1 - x0 < minw: c = (x0 + x1) / 2; x0, x1 = c - minw / 2, c + minw / 2
    if y1 - y0 < minw * 0.55: c = (y0 + y1) / 2; y0, y1 = c - minw * 0.275, c + minw * 0.275
    return (x0, y0, x1, y1)

# ---------- tabelle ----------
def riga_punto(p):
    campi = []
    for m_ in p["misure"]:
        if m_["grandezza"] in ("ombra_osservata", "offset_laterale", "lunghezza_percorso", "tempo_percorso", "n_attraversamenti"): continue
        campi.append(CAMPI[m_["grandezza"]](p))
    return (f'<tr class="p{p["prio"]}"><td class="id"><b>{esc(p["id"])}</b></td><td class="pr">{p["prio"]}</td>'
            f'<td class="cs"><b>{esc(p["nome"])}</b><br>{esc(p["cosa"])}<br><span class="cm">{esc(p["come"])}</span></td>'
            f'<td class="wr">{"<br>".join(campi)}</td><td class="ft"></td><td class="nt"></td></tr>')

def tabella(pts):
    return ('<table class="t"><thead><tr><th>ID</th><th>P</th><th>Cosa osservare e come</th><th>Valore / esito</th><th>Foto n.</th><th>Note</th></tr></thead><tbody>'
            + "".join(riga_punto(p) for p in pts if p["gruppo"] != "ombra" and p["gruppo"] != "percorso") + "</tbody></table>")

by = collections.defaultdict(list)
for p in PT: by[p["tappa"]].append(p)
for k in by: by[k].sort(key=lambda p: p["ordine"])
minuti = lambda pts, k: round(sum(p["min"] for p in pts if p["prio"] <= k))
n_pr = lambda pts, k: sum(1 for p in pts if p["prio"] == k)

# piano
ORARI = [("STAZ", "08:30", "Stazione: fermate, pensiline, piazza della Stazione. Poi 15 minuti a piedi verso Pellico."),
         ("PELL", "09:15", "Fermata Pellico e rotatoria. Alle 09:30 si parte lungo R01."),
         ("R01", "09:30", "Passaggio A: osservazioni d'ombra della mattina, alberi, edifici e altezze lungo R01. Arrivo alla scuola verso le 11:00."),
         ("BATT", "11:00", "Scuola: ingressi, scala, cancelli. Foto solo senza persone e mai ai momenti di entrata e uscita."),
         ("POE", "11:50", "Via Poerio e zona sud (circa 5 minuti dalla scuola), poi ritorno alla scuola."),
         ("--B", "12:30", "Passaggio B: osservazioni d'ombra di mezzogiorno, dalla scuola verso Pellico (solo ombra, nient'altro)."),
         ("--P", "13:00", "Pausa pranzo (45 minuti)."),
         ("PCS", "14:00", "Percorsi campione a piedi: R08 (stazione), R03, R04, R05, R09 (arriva a Pellico) e, se avanza tempo, R06 e R07. Dopo R09 si va al punto di partenza di R01."),
         ("--C", "15:30", "Passaggio C: partenza da Pellico, R01 cronometrato (tempo netto) con osservazioni d'ombra del pomeriggio. Fine verso le 16:00, lontano dalla scuola al momento dell'uscita.")]
def piano():
    rows = []
    for k, ora, desc in ORARI:
        if k.startswith("--"):
            rows.append(f"<tr><td>{ora}</td><td>{'Passaggio B' if k == '--B' else 'Pausa' if k == '--P' else 'Passaggio C'}</td><td colspan=4>{esc(desc)}</td></tr>"); continue
        pts = by[k]
        rows.append(f"<tr><td>{ora}</td><td>{esc(TITOLI[k].split('. ', 1)[1])}</td><td>{n_pr(pts,1)}</td><td>{n_pr(pts,2)}</td><td>{n_pr(pts,3)}</td><td>{esc(desc)}</td></tr>")
    return '<table class="t piano"><thead><tr><th>Ora</th><th>Tappa</th><th>P1</th><th>P2</th><th>P3</th><th>Cosa si fa</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>"

stima = {k: round((minuti(PT, k) * 1.25 + 45) / 60, 1) for k in (1, 2, 3)}

# tabella ombra
def tab_ombra():
    siti = sorted([p for p in PT if p["gruppo"] == "ombra"], key=lambda p: p["ch_r01_m"])
    rows = []
    for w, nome in (("A", "A. mattina (parte da Pellico)"), ("B", "B. mezzogiorno (parte dalla scuola)"), ("C", "C. pomeriggio (parte da Pellico)")):
        ordered = siti if w != "B" else siti[::-1]
        rows.append(f'<tr class="grp"><td colspan="10">Passaggio {esc(nome)}</td></tr>')
        for p in ordered:
            sl = next(m_ for m_ in p["misure"] if m_.get("slot") == w)
            rows.append(f'<tr class="p{p["prio"]}"><td class="id"><b>{esc(p["id"])}</b><br>{p["ch_r01_m"]} m</td><td class="pr">{p["prio"]}</td><td class="ora"><b>{esc(sl["ora_target"])}</b></td><td class="wr"></td>'
                        f'<td>{opt("ombra", "sole", "parziale")}</td><td>{opt("sì", "no")}</td><td>{opt("sereno", "velato", "coperto")}</td>'
                        f'<td class="wr">{opt("sx", "dx")} <span class="ln"></span> m</td><td class="wr"></td><td class="ft"></td></tr>')
    return ('<table class="t om"><thead><tr><th>Sito</th><th>P</th><th>Ora prevista (±5 min)</th><th>Ora reale hh:mm</th><th>Stato al suolo</th><th>Confine a meno di 1 m</th><th>Cielo</th><th>Lato e distanza dall\'asse</th><th>Oggetto che ombreggia</th><th>Foto n.</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>")

def tab_percorsi():
    rows = []
    for p in by["PCS"]:
        rows.append(f'<tr class="p{p["prio"]}"><td class="id"><b>{esc(p["id_modello"])}</b></td><td class="pr">{p["prio"]}</td><td class="cs">{esc(p["nome"].split(": ", 1)[1])}</td>'
                    f'<td class="wr">Partenza hh:mm<br><br>Arrivo hh:mm</td><td class="wr">Tempo netto (mm:ss)</td><td class="wr">Lunghezza (m)</td><td class="wr">Attraversamenti n.</td><td class="nt">Deviazioni, barriere, marciapiede mancante</td></tr>')
    return ('<table class="t pc"><thead><tr><th>Percorso</th><th>P</th><th>Da dove a dove</th><th>Orari</th><th>Cronometro</th><th>Ruota o traccia</th><th>Passaggi</th><th>Note</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")

# ---------- pagina ----------
CSS = """
@page{size:A4;margin:10mm}
*{box-sizing:border-box}
body{font:8.8pt/1.3 Arial,Helvetica,sans-serif;color:#000;background:#fff;margin:0 auto;max-width:200mm;padding:6mm}
h1{font-size:16pt;margin:0 0 2mm}h2{font-size:12pt;margin:6mm 0 2mm;border-bottom:1.5pt solid #000;padding-bottom:1mm;break-after:avoid}h3{font-size:10pt;margin:3mm 0 1mm}
p,li{margin:0 0 1.2mm}ul,ol{margin:0 0 2mm 5mm;padding:0}
.box{border:1.2pt solid #000;padding:2mm 3mm;margin:2mm 0;break-inside:avoid}.box.sic{border-width:2.5pt}
.hd{width:100%;border-collapse:collapse}.hd td{border:1pt solid #000;padding:2mm;height:9mm;vertical-align:top}
.t{width:100%;border-collapse:collapse;margin:1mm 0 3mm}.t th,.t td{border:.7pt solid #000;padding:1mm 1.5mm;vertical-align:top;text-align:left}.t th{background:#ddd;font-size:8pt}
.t tr{break-inside:avoid}.t td.id{white-space:nowrap;width:13mm}.t td.pr{text-align:center;width:6mm}.t td.cs{width:68mm}.t td.wr{width:50mm}.t td.ft{width:13mm}.t td.nt{width:30mm}
.t tr.grp td{background:#bbb;font-weight:bold;height:auto!important}.t td.ora{font-size:11pt;text-align:center}
.t.om td,.t.pc td{height:11mm}.t.piano td{height:auto}
tbody tr:not(.grp):not(.p1) td.id b::after{content:""}
.t tr.p1 td.pr{background:#000;color:#fff;font-weight:bold}.t tr.p2 td.pr{font-weight:bold}.t tr.p3 td.pr{font-style:italic;color:#444}
.cm{font-size:7.6pt;color:#333;font-style:italic}.nota{font-size:7.6pt;margin:.5mm 0 0}
.o{display:inline-block;margin-right:2mm;white-space:nowrap}.b{display:inline-block;width:2.8mm;height:2.8mm;border:.8pt solid #000;vertical-align:-.5mm;margin-right:.7mm}
.ln{display:inline-block;width:11mm;border-bottom:.8pt solid #000;vertical-align:baseline}
figure{margin:2mm 0 3mm;break-inside:avoid}figcaption{font-weight:bold;margin-bottom:1mm}svg{width:100%;height:auto;display:block}.lab{font:7.5px Arial,sans-serif;paint-order:stroke;stroke:#fff;stroke-width:2.4px;fill:#000}
.leg{font-size:8pt}.tools{background:#eee;border:1px solid #000;padding:3mm;margin-bottom:4mm}.tools button{font:inherit;padding:2mm 3mm;margin-right:2mm;border:1px solid #000;background:#fff;cursor:pointer}
.pb{break-before:page}
body.solo1 .p2,body.solo1 .p3,body.solo12 .p3{display:none}
@media print{body{padding:0;max-width:none;font-size:8.5pt}.tools{display:none}a{color:#000;text-decoration:none}}
"""
JS = """
function m(c){document.body.className=c;}
"""
def sezione_tappa(k):
    pts = by[k]
    s = [f'<h2 class="pb">{esc(TITOLI[k])}</h2>']
    if k == "R01":
        R = LINEE["PER-R01"]; L = R.length
        for i, (a, b) in enumerate(((0, 270), (240, 520), (490, L))):
            sub = shapely.ops.substring(R, a, b)
            sel = [p for p in PT if p["tappa"] in ("R01",) and a - 5 <= p["ch_r01_m"] <= b + 5] + [p for p in PT if p["gruppo"] in ("fermata", "marciapiede", "cancello") and a <= p["ch_r01_m"] <= b and p["d_r01_m"] < 80]
            bb = bbox_di(sel + [{"xy_m": [c[0], c[1]]} for c in sub.coords] if sel else [{"xy_m": [c[0], c[1]]} for c in sub.coords], margin=45)
            s.append(mappa(f"R01 tratto {i+1} di 3 (dal {int(a)} al {int(b)} m dalla fermata Pellico)", bb, [p for p in sel if p["tappa"] == "R01" or p["gruppo"] != "percorso"], linee=[("R01", R)], nota="Linea spessa: percorso R01 sull'asse della rete. Cerchio nero = priorità 1, cerchio vuoto = 2, triangolo = 3, quadrato = edificio, rombo = sito d'ombra."))
    else:
        sel = pts + ([p for p in by["PCS"] if False])
        sel = [p for p in sel if p["gruppo"] != "percorso"] or pts
        s.append(mappa(TITOLI[k].split(". ", 1)[1], bbox_di(sel, margin=50), sel, linee=[] if k != "POE" else [("V01", LINEE["PER-V01"])] if "PER-V01" in LINEE else []))
    if k == "R01": s.append("<p>Le righe d'ombra del passaggio A sono nella tabella delle osservazioni d'ombra (sezione dopo la tappa 5). Qui si fanno solo alberi, edifici e marciapiedi, in ordine lungo il percorso.</p>")
    s.append(tabella(pts))
    return "".join(s)

def build():
    ov_pts = [p for p in PT if p["prio"] <= 2 and p["tappa"] != "EXTRA" and p["gruppo"] != "percorso" and not (p["prio"] == 2 and p["gruppo"] in ("albero", "edificio"))]
    ov_bb = bbox_di(ov_pts, margin=60, minw=600)
    ov = mappa("Panoramica: punti di priorità 1 e 2 e percorsi campione", ov_bb, ov_pts, linee=[(k[4:], g) for k, g in LINEE.items()], trees_dots_only=True,
               nota="Alberi ed edifici sono senza etichetta in questa mappa: i numeri sono nelle mappe di dettaglio. Linee tratteggiate: percorsi campione. Strade con tratteggio a puntini: scale. Tratteggio lungo: attraversamenti.")
    H = []
    H.append(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Scheda di sopralluogo Z2</title><style>{CSS}</style></head><body class="tutto">')
    H.append('<div class="tools"><b>Prima di stampare</b> (questi pulsanti non si stampano). Scegli cosa stampare, poi Stampa del browser, formato A4, margini predefiniti, scala 100%, in bianco e nero. '
             '<br><button onclick="m(\'solo1\')">Solo priorità 1</button><button onclick="m(\'solo12\')">Priorità 1 e 2</button><button onclick="m(\'tutto\')">Tutto</button> <button onclick="window.print()">Stampa</button></div>')
    H.append("<h1>Scheda di sopralluogo Z2 (T11, validazione locale)</h1><p>Protocollo T11-Z2-v1. Un rilievo alla cieca: sulla scheda non ci sono i valori del modello. Scrivi cosa vedi e misuri.</p>")
    H.append('<table class="hd"><tr><td>Data</td><td>Rilevatore</td><td>Meteo e cielo all\'inizio</td><td>Ora inizio / fine</td></tr><tr><td>Ora del telefono corretta? '+B_()+' sì</td><td>Telefono e app usati</td><td>Fuso orario del telefono: Europe/Rome '+B_()+'</td><td>Fotocamera: data, ora e posizione attive '+B_()+'</td></tr></table>')
    H.append(f'<div class="box sic"><b>Sicurezza e privacy (vale sempre)</b><ul><li>Non entrare in aree private: cortili, cancelli chiusi, via Poerio. Si osserva dalla via pubblica.</li><li>Non fermarti sulla carreggiata. Misura dal marciapiede e attraversa solo sulle strisce. Niente laser verso il traffico né verso gli occhi di qualcuno.</li><li>Stazione: resta dietro la linea gialla e fuori dalle aree ferroviarie vietate.</li><li>Foto senza persone riconoscibili e senza minori. È una scuola primaria: niente foto di bambini, niente foto davanti alla scuola ai momenti di entrata e uscita. Targhe e finestre non leggibili.</li><li>Se qualcuno chiede cosa fai, spiega che è un rilievo del Comune e dei partner di progetto, senza raccogliere dati di persone.</li></ul></div>')
    H.append("<h2>Istruzioni brevi</h2><ol>"
             "<li>Una riga, un punto. Prima di ogni punto fotografa il suo ID scritto a mano sul foglio, poi le foto del punto. Scrivi il numero di foto nella colonna Foto.</li>"
             "<li>Posizione: smartphone fermo accanto all'oggetto per almeno 30 secondi, annota l'accuratezza dichiarata. Se supera 10 m, ripeti.</li>"
             "<li>Altezze: metro laser per la distanza orizzontale e clinometro o app inclinometro per gli angoli alla base e in alto, da due stazioni a distanze diverse. Scrivi la media. Chioma: due diametri perpendicolari a terra.</li>"
             "<li>Ombra: sul marciapiede nel punto indicato, entro 5 minuti dall'ora prevista. Scrivi l'ora reale, ombra, sole o parziale, se il confine è entro 1 m, cielo, lato e distanza dall'asse. Foto del suolo e dell'orizzonte verso il sole. Con cielo coperto non si osserva: ripeti nel passaggio successivo.</li>"
             "<li>Percorsi: segui esattamente l'itinerario sulla mappa. Cronometro con parziali: ferma alle soste, il tempo conta solo mentre cammini. Annota ogni deviazione.</li>"
             "<li>Se un oggetto non c'è o è diverso, scrivi \"no\" o \"diverso\" e descrivilo. Non cercare di far tornare i conti.</li>"
             "<li>Non correggere nulla in campo e non guardare il modello. Le correzioni si decidono dopo, secondo il protocollo.</li>"
             "<li>Priorità 1 per prima. Priorità 2 e 3 solo se avanza tempo. Dopo il rilievo, trascrivi in esiti_modello.csv e lancia importa_esiti.py.</li></ol>")
    H.append("<h2>Attrezzatura</h2><ul>" + "".join(f"<li>{B_()} {esc(x)}</li>" for x in [
        "Metro laser (o rotella metrica) per distanze e larghezze", "Rotella a ruota per le lunghezze dei percorsi (o traccia GPS calibrata su 50 m)", "Clinometro o app inclinometro",
        "Bussola (o app bussola)", "Cronometro con parziali", "Smartphone: foto con data, ora e posizione, posizione precisa attiva", "Batteria esterna di scorta", "Questa scheda stampata, cartellina rigida, matita e penna",
        "Gilet ad alta visibilità, acqua, cappello", "Scheda delle ore del sole: le ore previste del passaggio A, B, C sono nella tabella d'ombra"]) + "</ul>")
    H.append("<h2>Durata stimata e piano della giornata</h2>")
    H.append(f"<p>Tempo sui punti più trasferimenti (25%) e pausa di 45 minuti: priorità 1 circa {stima[1]} ore; priorità 1 e 2 circa {stima[2]} ore (due mezze giornate); tutto circa {stima[3]} ore. Con due persone i tempi sui punti si dimezzano, ma le osservazioni d'ombra restano agli orari fissi. Le ore sono indicative: si rispettano solo le tre partenze dei passaggi A, B e C.</p>")
    H.append(piano())
    H.append(f"<p class='leg'>Punti totali {META['n_punti']}: priorità 1 {META['per_priorita']['1']}, priorità 2 {META['per_priorita']['2']}, priorità 3 {META['per_priorita']['3']}. Minuti sui punti cumulati: P1 {minuti(PT,1)}, P1+P2 {minuti(PT,2)}, tutto {minuti(PT,3)}.</p>")
    H.append('<h2 class="pb">Mappe</h2>' + ov)
    for k in ("STAZ", "PELL", "R01", "BATT", "POE"):
        H.append(sezione_tappa(k))
    H.append('<h2 class="pb">Tappa 6. Osservazioni d\'ombra su R01 (passaggi A, B, C)</h2><p>Dodici osservazioni di priorità 1 (4 siti per 3 passaggi) e sei di priorità 2. Le ore previste partono da: A, Pellico alle 09:30; B, scuola alle 12:30; C, Pellico alle 15:30, a 1,2 m/s più 3 minuti per sito. Se sei in ritardo, scrivi l\'ora reale: conta quella.</p>' + tab_ombra())
    H.append(f'<h2 class="pb">{esc(TITOLI["PCS"])}</h2><p>Cronometro con parziali. Il tempo conta solo mentre cammini. Annota anche la tua velocità media (lunghezza diviso tempo). R01 si cronometra nel passaggio C. V01 (via Poerio) non si percorre: si guarda dalla via pubblica (tappa 5).</p>' + tab_percorsi())
    if by["EXTRA"]: H.append(f'<h2>{esc(TITOLI["EXTRA"])}</h2><p>Circa 700 m a ovest di Pellico, fuori dal giro. Solo se si passa di là.</p>' + tabella(by["EXTRA"]))
    H.append("<h2>Chiusura</h2><div class='box' style='height:35mm'><b>Anomalie, oggetti non trovati, cose da ricontrollare:</b></div><table class='hd'><tr><td>Fine rilievo (ora)</td><td>Foto totali</td><td>Punti non fatti (ID)</td><td>Firma</td></tr></table>")
    H.append(f"<script>{JS}</script></body></html>")
    return "".join(H)

if __name__ == "__main__":
    out = build(); (FW / "scheda.html").write_text(out, encoding="utf-8")
    print(len(out) // 1024, "KB", "stima ore", stima)
