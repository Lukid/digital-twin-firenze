#!/usr/bin/env python3
"""Pagina di metodo della scena (F1, compito 4): da dove viene ogni numero, cosa calcola ogni livello, cosa non sappiamo, schede delle fonti.
Uso: pipeline/.venv/bin/python scene/firenze_novoli/metodo.py   scrive scene/firenze_novoli/metodo.html (non richiede data/)
Legge assets/index.json (livelli, fonti e limiti della scena) e le schede delle fonti generate da service/schede.py. Pagina statica, senza script."""
import html, json, pathlib, re, sys

QUI = pathlib.Path(__file__).resolve().parent
ROOT = QUI.parents[1]
sys.path.insert(0, str(ROOT / "service"))
import schede  # noqa: E402

IDX = json.loads((QUI / "assets/index.json").read_text())
e = html.escape

# Livelli che portano numeri calcolati dal progetto: cosa calcolano, con quale motore, da quali file.
CALCOLI = [
    ("accessibilita", "Accessibilità (minuti a piedi)",
     "Per ogni civico (punto d'indirizzo) il tempo a piedi fino all'ingresso più vicino della destinazione, sulla rete pedonale. Quote di civici entro 5, 10 e 15 minuti.",
     "Rete pedonale da OpenStreetMap costruita in F04 (marciapiedi, attraversamenti, scale); civico agganciato alla rete entro 40 m; velocità 1,2 m/s con intervallo 0,8-1,4; nessuna penalità agli attraversamenti nel profilo base.",
     "analysis/accessibilita.py (F06)", "analysis/firenze_novoli/riepilogo.json e un manifest per job in analysis/firenze_novoli/manifest/", "analysis/REPORT-F06.md",
     ["src_osm_firenze", "src_fi_civici", "src_fi_scuole_statali", "src_cm_edscol_firenze", "src_gtfs_gest_firenze", "src_fi_tram_fermate"]),
    ("ombra", "Ombra sui percorsi",
     "Frazione di un percorso campione in ombra e minuti passati al sole camminando, per data e ora, dalle fermate del tram al Polo.",
     "Raggio geometrico dal punto del percorso verso il sole (posizione con l'algoritmo SPA al centro del riquadro), passo di 1 m e di 5 minuti; ostacoli: edifici con altezza LiDAR, alberi censiti con chioma misurata o stimata e, in un caso separato, vegetazione LiDAR. Il punto è sull'asse della rete.",
     "shadow/ombre.py (F07)", "shadow/firenze_novoli/sintesi.json, tratti_ombra_*.geojson e manifest", "shadow/REPORT-F07.md",
     ["src_rt_uv_firenze_novoli", "src_fi_dsm2023", "src_fi_dtm2023", "src_fi_alberi", "src_osm_firenze"]),
    ("scenari", "Scenari (interventi ipotetici)",
     "Effetto di un filare o di una pensilina ipotetici sull'ombra di un percorso o di un'area di attesa: differenza rispetto alla baseline, a parità di condizioni.",
     "Stesso motore dell'ombra con gli interventi aggiunti agli ostacoli; dimensioni dell'albero per classe, con le varianti di chioma minima e massima. La fattibilità (sottoservizi, proprietà, norme) non è valutata.",
     "scenarios/scenari.py e scenarios/confronto.py (F08)", "scenarios/firenze_novoli/confronto.json e scn_fi_*.json", "scenarios/REPORT-F08.md",
     ["src_rt_uv_firenze_novoli", "src_fi_dsm2023", "src_fi_alberi", "src_osm_firenze", "src_fi_aree_pedonali"]),
    ("rifugi", "Rifugi climatici e percorsi verso i rifugi",
     "Quota di civici entro 5, 10 e 15 minuti a piedi dal rifugio climatico più vicino; per ogni rifugio, i civici per cui è il più vicino. Cinque percorsi campione (RC1-RC5) da fermate, scuola, Polo e un civico verso un rifugio, con lunghezza, attraversamenti e, se calcolata, l'ombra.",
     "I 7 rifugi del Comune (biblioteche e aree fresche) entro 700 m dal riquadro; ingresso = civico del Comune all'indirizzo dichiarato dalla fonte, non verificato; orari ignoti. Stessa rete e stesso motore dell'accessibilità, 1,2 m/s; RC3, RC4 e RC5 vanno al rifugio più vicino per rete. Stato dei percorsi: da verificare sul posto.",
     "analysis/accessibilita.py (F06), network/percorsi_firenze.py (F04), shadow/ombre.py (F07)", "analysis/firenze_novoli/riepilogo.json (chiave rifugi), accessibilita_rifugi.geojson e network/firenze_novoli/percorsi_campione.json", "analysis/REPORT-F2-RIFUGI.md",
     ["src_fi_rifugi_aree", "src_fi_rifugi_biblioteche", "src_fi_civici", "src_osm_firenze"]),
    ("costo", "Costo del filare S1",
     "Metri quadri di suolo che passano dal sole all'ombra per mille euro di fornitura e piantagione dei 7 alberi del filare S1.",
     "Ombra guadagnata con lo stesso motore degli scenari (15 luglio, 12:30-13:30, con vegetazione LiDAR); costo dal Prezzario dei Lavori della Regione Toscana 2026 (CC BY 4.0): platano orientale 18/20, la specie da ombra più piantata dal Comune vicino al tratto (D36), più la piantagione in sede stradale. Ombra di alberi adulti contro il prezzo di alberi da vivaio; scavo, pavimentazione, sottoservizi, manutenzione e IVA esclusi. Pensiline senza prezzo.",
     "scenarios/costo_filare.py", "scenarios/firenze_novoli/costo_filare.json e costo_voci.json", "docs/REPORT-AGENTE-F3.md",
     ["src_fi_alberi", "src_osm_firenze", "src_fi_aree_pedonali"]),
    ("edifici", "Edifici e alberi",
     "Volumi degli edifici con altezza, alberi con altezza e chioma, nella scena e come ostacoli per l'ombra.",
     "Impronte delle unità volumetriche 2011; altezza dal LiDAR 2023 (superficie meno terreno) dentro l'impronta; edifici nuovi solo da OSM. Alberi del censimento comunale con altezza e chioma dal LiDAR dove ci sono celle sufficienti, altrimenti stimate per classe.",
     "geometry/build_firenze.py (F05)", "geometry/firenze_novoli/report_firenze_novoli.json", "geometry/REPORT-F05.md",
     ["src_rt_uv_firenze_novoli", "src_fi_dsm2023", "src_fi_dtm2023", "src_fi_alberi", "src_osm_firenze"]),
    ("temperature", "Temperatura delle superfici",
     "Temperatura dei tetti, delle strade e del verde nelle giornate estive serene, per data, e differenze fra giornate.",
     "Banda termica Landsat 8 e 9 (Collection 2, livello 2) convertita in gradi; tenute le date con almeno l'80% di celle valide sul riquadro.",
     "pipeline/norm_firenze.py e scene/firenze_novoli/build.py (F09)", "assets/temperature.json.gz", "scene/firenze_novoli/ADR-F09.md",
     ["src_fi_landsat_st", "src_sir_termo_firenze"]),
    ("aria", "Qualità dell'aria",
     "Medie annue e superamenti dei limiti di legge per stazione ARPAT, con la distanza dal riquadro.",
     "Dati orari validati del 2025, contati per stazione; nessuna interpolazione fra stazioni.",
     "pipeline/norm_firenze.py e scene/firenze_novoli/build.py (F09)", "assets/aria.json.gz", "scene/firenze_novoli/ADR-F09.md",
     ["src_arpat_aria"]),
]

NON_SAPPIAMO = [
    "Nessun numero è validato sul posto: ingressi, linea effettiva del marciapiede e ombra osservata sono da verificare.",
    "L'ombra è misurata sull'asse della rete pedonale, non sulla linea dove si cammina; il lato del marciapiede non è noto.",
    "La rete pedonale viene solo da OpenStreetMap: larghezze, pendenze e stato dei marciapiedi sono ignoti dove non dichiarati.",
    "I civici sono punti d'indirizzo, non persone: una quota di civici non è una quota di abitanti.",
    "Gli ingressi del Polo sono un civico del Comune per edificio dell'Ateneo: il civico non è per forza la porta.",
    "La vegetazione LiDAR è trattata come un prisma opaco pieno: è un limite superiore dell'ombra.",
    "Le altezze sono del LiDAR 2023 su impronte del 2011; portici e volumi sospesi sono ignoti e trattati come pieni.",
    "Il datum verticale delle quote LiDAR non è confermato.",
    "La fermata San Donato - Università sta circa 100 m fuori dal riquadro: in scena c'è il terreno, non gli edifici attorno.",
    "La fattibilità degli interventi degli scenari non è valutata. Il solo costo calcolato è quello d'impianto del filare S1, dal prezzario regionale: non c'è un prezzo pubblico con licenza di riuso per le pensiline.",
    "Ingressi, orari e cancelli dei rifugi climatici non sono verificati; il Parco delle Cascine non entra nei calcoli perché i suoi ingressi non sono fra i civici.",
    "Non c'è un calcolo della temperatura percepita, del rischio da calore per le persone o delle isole di calore dell'aria.",
]


def link_fonte(sid):
    t = next((f["titolo"] for f in IDX["fonti"] if f["id"] == sid), None) or json.loads((ROOT / "pipeline/sources" / f"{sid}.json").read_text())["title"]
    return f'<a href="#{sid}">{e(t)}</a>'


def inline(s):
    """Markdown in linea delle schede: codice, link [testo](file.md) verso le ancore, URL nudi."""
    s = e(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((src_[a-z0-9_]+)\.md\)", r'<a href="#\2">\1</a>', s)
    return re.sub(r"(?<![\"=])(https?://[^\s<|)]+[^\s<|).,;])", r'<a href="\1" rel="noopener">\1</a>', s)


def md_html(md, livello=3):
    """Le schede usano solo titoli, elenchi, tabelle e paragrafi: basta un convertitore minimo."""
    out, lista, tab = [], False, []
    def chiudi():
        nonlocal lista, tab
        if lista: out.append("</ul>"); lista = False
        if tab:
            righe = [r for r in tab if not re.fullmatch(r"\|[-|]+\|", r)]
            celle = [[c.strip() for c in r.strip("|").split("|")] for r in righe]
            out.append('<div class="tab"><table><thead><tr>' + "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in celle[0]) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in celle[1:]) + "</tbody></table></div>")
            tab = []
    for r in md.splitlines():
        if r.startswith("|"): tab.append(r); continue
        if tab: chiudi()
        if r.startswith("# "): continue   # il titolo della scheda è nel summary
        if r.startswith("## "): chiudi(); out.append(f"<h{livello + 1} class=\"sk\">{inline(r[3:])}</h{livello + 1}>"); continue
        if r.startswith("- "):
            if not lista: out.append("<ul>"); lista = True
            out.append(f"<li>{inline(r[2:])}</li>"); continue
        chiudi()
        if r.strip(): out.append(f"<p>{inline(r)}</p>")
    chiudi()
    return "\n".join(out)


def pagina():
    file = schede.genera()
    righe = []
    for k, tit, cosa, come, motore, risultato, report, fonti in CALCOLI:
        righe.append(f"<tr id=\"{k}\"><th scope=\"row\">{e(tit)}</th><td>{e(cosa)}</td><td>{e(come)}</td><td><code>{e(motore)}</code><br><small>Risultato: <code>{e(risultato)}</code>. Report: <code>{e(report)}</code></small></td>"
                     f"<td>{', '.join(link_fonte(s) for s in fonti)}</td></tr>")
    livelli = []
    for k, L in IDX["livelli"].items():
        fonti = ", ".join(link_fonte(s) for s in L["fonti"]) or "nessuna fonte diretta: interventi ipotetici del progetto"
        livelli.append(f"<li><strong>{e(L['etichetta'])}</strong>: {fonti}</li>")
    sch = []
    for sid in schede.fonti():
        t = file[f"{sid}.md"]; titolo = t.splitlines()[0][2:]
        sch.append(f'<details id="{sid}"><summary><span>{e(titolo)}</span> <code>{sid}</code></summary>\n{md_html(t, 2)}\n</details>')
    b = IDX["baseline"] if isinstance(IDX.get("baseline"), str) else (IDX.get("baseline") or {}).get("baseline_id", schede.BASELINE["baseline_id"])
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>Metodo del gemello di Firenze Novoli</title>
<meta name="description" content="Da dove viene ogni numero della scena di Firenze Novoli, cosa calcola ogni livello, cosa non sappiamo e le schede delle fonti.">
<style>
:root{{color-scheme:light;--bg:#eef2f5;--pannello:#ffffff;--testo:#1b2430;--tenue:#4a5563;--bordo:#c4ccd6;--acc:#0b5cad;--focus:#c2410c}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--testo);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
a{{color:var(--acc)}}
:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
.salta{{position:absolute;left:-9999px}}.salta:focus{{left:12px;top:12px;background:#fff;padding:8px 12px;border-radius:8px;z-index:2}}
header,main,footer{{max-width:1040px;margin:0 auto;padding:0 16px}}
header{{padding-top:24px}}
.eyebrow{{font-size:11px;letter-spacing:.14em;font-weight:700;color:var(--tenue);margin:0}}
h1{{font-size:28px;margin:4px 0 8px}}
h2{{font-size:20px;margin:36px 0 10px}}
h3{{font-size:16px;margin:18px 0 6px}}
h3.sk{{font-size:14px;margin:14px 0 4px;color:var(--tenue);text-transform:uppercase;letter-spacing:.08em}}
.box{{background:var(--pannello);border:1px solid var(--bordo);border-radius:10px;padding:14px 18px}}
nav ul{{margin:8px 0 0;padding-left:20px}}
.tab{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:14px;background:var(--pannello)}}
th,td{{border:1px solid var(--bordo);padding:8px 10px;text-align:left;vertical-align:top}}
thead th{{background:#e4eaf0}}
tbody th{{font-weight:600}}
.calcoli td:nth-child(4){{min-width:200px}}
.calcoli code{{word-break:normal;overflow-wrap:anywhere}}
small,.tenue{{color:var(--tenue)}}
code{{font-size:.88em;background:#e7ecf1;padding:1px 4px;border-radius:4px;word-break:break-word}}
details{{background:var(--pannello);border:1px solid var(--bordo);border-radius:10px;margin:8px 0;padding:0 16px}}
details summary{{cursor:pointer;padding:12px 0;font-weight:600;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}}
details summary code{{font-weight:400}}
details[open]{{padding-bottom:12px}}
li{{margin-bottom:4px}}
.torna{{display:inline-block;margin:16px 0 0;font-weight:600}}
footer{{padding:32px 16px 40px;color:var(--tenue);font-size:14px}}
@media (max-width:700px){{h1{{font-size:23px}}table{{font-size:13px}}}}
</style>
</head>
<body>
<a class="salta" href="#contenuto">Vai al contenuto</a>
<header>
<p class="eyebrow">GEMELLO DIGITALE · OPEN DATA</p>
<h1>Metodo: da dove viene ogni numero</h1>
<p>Firenze Novoli - Firenze Nova, riquadro di 2 km². Tutti i numeri della scena vengono da open data con licenza di riuso e da motori di calcolo deterministici: stessa richiesta, stessi dati, stesso risultato. Baseline dei calcoli: <code>{e(b)}</code>.</p>
<a class="torna" href="index.html">← Torna alla scena</a>
</header>
<main id="contenuto">
<nav class="box" aria-label="In questa pagina"><strong>In questa pagina</strong><ul>
<li><a href="#calcoli">Cosa calcola ogni livello di analisi</a></li>
<li><a href="#livelli">Fonti di ogni livello della scena</a></li>
<li><a href="#non-sappiamo">Cosa non sappiamo</a></li>
<li><a href="#limiti-scena">Limiti della rappresentazione</a></li>
<li><a href="#schede">Schede delle fonti</a></li>
<li><a href="#verificare">Come verificare un numero</a></li>
</ul></nav>

<h2 id="calcoli">Cosa calcola ogni livello di analisi</h2>
<p>I livelli della scheda Analisi e degli Interventi mostrano risultati prodotti fuori dalla scena, da motori di calcolo versionati nel repository. La scena non ricalcola nulla.</p>
<div class="tab"><table class="calcoli">
<caption class="salta">Livelli di analisi: cosa calcolano, come, con quale motore e da quali fonti</caption>
<thead><tr><th scope="col">Livello</th><th scope="col">Cosa calcola</th><th scope="col">Come</th><th scope="col">Motore e risultato</th><th scope="col">Fonti</th></tr></thead>
<tbody>
{chr(10).join(righe)}
</tbody></table></div>
<p>Il sole e le ombre che si vedono muovendo l'ora nella scheda Sole sono del motore grafico: servono a leggere la scena, non sono un calcolo. I numeri dell'ombra sono solo quelli del livello Ombra sui percorsi.</p>

<h2 id="livelli">Fonti di ogni livello della scena</h2>
<ul>
{chr(10).join(livelli)}
</ul>

<h2 id="non-sappiamo">Cosa non sappiamo</h2>
<ul>
{chr(10).join(f"<li>{e(x)}</li>" for x in NON_SAPPIAMO)}
</ul>

<h2 id="limiti-scena">Limiti della rappresentazione</h2>
<ul>
{chr(10).join(f"<li>{e(x)}</li>" for x in IDX["limiti"])}
</ul>

<h2 id="schede">Schede delle fonti</h2>
<p>Una scheda per fonte: editore, licenza e uso consentito, data del dato, scarichi, campi usati, controlli e limiti. La data del dato è quella dichiarata dalla fonte; la data della scheda del catalogo non è mai la data del dato. Le stesse schede sono leggibili dagli assistenti tramite il servizio di interrogazione del progetto.</p>
{chr(10).join(sch)}

<h2 id="verificare">Come verificare un numero</h2>
<ul>
<li>Ogni risultato di calcolo ha un identificativo di job: lo stesso input dà sempre lo stesso identificativo e gli stessi numeri.</li>
<li>Il manifest del job elenca i dati usati (snapshot con impronta sha256 e licenza), i parametri, le metriche e i limiti.</li>
<li>I report di ogni motore riportano i numeri del calcolo e i test che li ricontrollano; i numeri dei report si cambiano solo rieseguendo il calcolo.</li>
</ul>
<a class="torna" href="index.html">← Torna alla scena</a>
</main>
<footer>Pagina generata da <code>scene/firenze_novoli/metodo.py</code> con le schede di <code>service/schede.py</code>. Nessun numero è validato sul posto.</footer>
</body>
</html>
"""


if __name__ == "__main__":
    (QUI / "metodo.html").write_text(pagina())
    print("scritto", (QUI / "metodo.html").relative_to(ROOT))
