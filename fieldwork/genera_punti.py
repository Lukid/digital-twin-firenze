#!/usr/bin/env python3
"""Genera fieldwork/punti.json e punti.geojson dai report T04/T05/T06/T09.
Selezione e assegnazione uso (verifica/correzione) deterministiche: stesso input, stesso output.
Serve pipeline/.venv (geopandas, networkx) e data/norm/network (non versionata).
Uso: pipeline/.venv/bin/python fieldwork/genera_punti.py"""
import json, hashlib, sys, collections
from pathlib import Path
import geopandas as gpd, networkx as nx
import shapely.ops
from shapely.geometry import shape, Point, MultiPoint
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "fieldwork"
sys.path.insert(0, str(ROOT / "network"))
from rete_lib import carica, OUT  # noqa: E402

TO_M = Transformer.from_crs(4326, 7791, always_xy=True)
TO_LL = Transformer.from_crs(7791, 4326, always_xy=True)
def m(g): return shapely.ops.transform(lambda x, y, z=None: TO_M.transform(x, y), g)
def ll(g): return shapely.ops.transform(lambda x, y, z=None: TO_LL.transform(x, y), g)
def ll_xy(x, y): return [round(v, 6) for v in TO_LL.transform(x, y)]
def J(p): return json.load(open(ROOT / p))
def h01(s): return int(hashlib.sha256(s.encode()).hexdigest(), 16)

# ---------- dati ----------
perc = J("network/percorsi_campione.geojson")["features"]
PERC = {}
for f in perc:
    if "origine" in f["properties"]: PERC[f["properties"]["id"]] = f
R01 = m(shape(PERC["R01"]["geometry"]))
dest = {d["destination_id"]: d for d in J("network/destinazioni.json")["destinazioni"]}
batt = dest["dst_school_piee82101p"]
stops = {d["stop_code"]: d for d in dest.values() if d["categoria"] == "stop"}
B = gpd.read_file(ROOT / "geometry/edifici_z2.geojson").set_crs(4326).to_crs(7791)
A = gpd.read_file(ROOT / "geometry/alberi_z2.geojson").set_crs(4326).to_crs(7791)
Bi, Ai = B.set_index("id"), A.set_index("id")
sop = J("geometry/sopralluogo_z2.json")["oggetti"]
G, D = carica()
EA = gpd.read_file(ROOT / "data/norm/network/rete_z2.gpkg", layer="archi", engine="pyogrio").set_index("edge_id")
EN = gpd.read_file(ROOT / "data/norm/network/rete_z2.gpkg", layer="nodi", engine="pyogrio").set_index("node_id")
riep = J("analysis/out/riepilogo.json")["destinazioni"]

punti = []
def add(**k):
    k.setdefault("misure", []); k.setdefault("uso", "correzione"); k.setdefault("min", 5)
    k["esito"] = None; k["note_esito"] = None
    punti.append(k); return k
def mis(g, **k): d = {"grandezza": g, "valore_misurato": None}; d.update(k); return d
def pt_ll(g): return [round(g.x, 6), round(g.y, 6)]
def cat(g): return {"posizione": "posizione_oggetto"}.get(g, g)

# ---------- ingressi Battisti ----------
ents = {e["entrance_id"]: e for e in batt["ingressi"]}
main = ents[batt["ingresso_predefinito"]]
add(id="ING-01", gruppo="ingresso", tipo="ingresso_scuola", prio=1, nome="Ingresso principale probabile della Battisti (OSM entrance=main)", id_modello=main["entrance_id"],
    xy=main["xy"], motivo="Ingresso reale della scuola non noto: l'ingresso main OSM non ha civico; da cui dipendono tutti i risultati A (network/REPORT.md 'Da verificare', analysis/REPORT.md punto 1: è la scelta che sposta di più i risultati).",
    cosa="Quale ingresso è in uso (alunni, pubblico, personale), orari di apertura, tipo di cancello, civico esposto, posizione GPS sulla soglia.",
    come="Osservare dalla via pubblica a orario di lezione (senza foto di bambini). Foto di porta, cancello e civico. Posizione smartphone 30 s. Non entrare. Chiedere in portineria solo se già aperto al pubblico.",
    min=15, uso="correzione",
    misure=[mis("ingresso_in_uso", valore_modello="si"), mis("accesso_ingresso", valore_modello="aperto_a_orari"), mis("posizione_oggetto", valore_modello=0.0, unita="m")])
for i, (eid, e) in enumerate([(k, v) for k, v in sorted(ents.items(), key=lambda kv: kv[1]["dist_perimetro_m"]) if k != main["entrance_id"]], 2):
    t = e["tags"]
    add(id=f"ING-{i:02d}", gruppo="ingresso", tipo="ingresso_contiguo", prio=2 if "Corridoni" in t.get("addr:street", "") else 3,
        nome=f"Ingresso OSM {t.get('addr:street','')} {t.get('addr:housenumber','')} ({e['classe']})", id_modello=eid, xy=e["xy"],
        motivo="Ingresso OSM entro 25 m dal perimetro, classificato edificio contiguo solo dalla geometria; di altri edifici (network/REPORT.md). Serve a escludere che sia l'accesso della scuola e come limite superiore della sensibilità (analysis/REPORT.md).",
        cosa="Appartiene alla scuola o a un altro edificio? Civico esposto, porta aperta al pubblico.",
        come="Osservare dalla via, foto del civico. Posizione smartphone sulla soglia.", min=3, uso="correzione",
        misure=[mis("ingresso_in_uso", valore_modello="no"), mis("posizione_oggetto", valore_modello=0.0, unita="m")])

# ---------- via Poerio e cancelli privati ----------
o = gpd.read_file(ROOT / "data/norm/network/origini_snap.gpkg", layer="origini", engine="pyogrio").set_index("id")
p35 = MultiPoint([o.loc["adr_sit_11884"].geometry, o.loc["adr_sit_11917"].geometry]).centroid
add(id="POE-01", gruppo="accesso", tipo="strada_private", prio=1, nome="Via Poerio civici 3 e 5 (accesso privato?)", id_modello="adr_sit_11884+adr_sit_11917+edg_osm_326768263_*",
    xy=[p35.x, p35.y], motivo="V01: collegata al resto solo da 3 archi access=private; 21 civici forbidden in T06 (network/REPORT.md, analysis/REPORT.md punto 5). Se la strada è pubblica il percorso V01 e i 21 civici cambiano stato.",
    cosa="Strada privata, pubblica o con limitazioni? Cartelli, sbarre, targhe, citofoni, cancelli (aperti o chiusi). Da dove si entra.",
    come="Dalla via pubblica, foto dei cartelli e del cancello. Non entrare in area privata.", min=8, uso="correzione",
    misure=[mis("accesso_strada", valore_modello="privata"), mis("accesso_negato", valore_modello="negato")])
NB = gpd.read_file(ROOT / "data/norm/network/rete_z2.gpkg", layer="nodi_bloccati", engine="pyogrio").set_index("node_id")
gp = MultiPoint([NB.loc[n].geometry for n in ("nod_osm_3617796598", "nod_osm_3617796616", "nod_osm_3617796622")]).centroid
add(id="POE-02", gruppo="accesso", tipo="cancelli_privati", prio=3, nome="Tre cancelli access=private che bloccano la rete (nodi 3617796598, 3617796616, 3617796622)", id_modello="nod_osm_3617796598|nod_osm_3617796616|nod_osm_3617796622",
    xy=[gp.x, gp.y], motivo="Tre cancelli access=private bloccano la rete: nodi bloccanti (network/REPORT.md). NON sono quelli del caso V01 (via Poerio 3): V01 è bloccato da 3 archi access=private (edg_osm_326768263_*, coperti da POE-01), mentre questi 3 nodi sono circa 1,3 km a ovest della scuola e 700 m a ovest di Pellico, fuori dal giro principale: solo se si passa di là. Verificare che esistano e siano chiusi o vietati.",
    cosa="Per ciascuno dei tre cancelli: esiste? Aperto, chiuso, con cartello? Annotare quanti ne trovi.",
    come="Osservare dalla via pubblica, foto. Non entrare.", min=5, uso="correzione",
    misure=[mis("cancello_passabile", valore_modello="chiuso")])

# ---------- scala 38 gradini ----------
sc = EA.loc[["edg_osm_22717629_11480720548_11480720545", "edg_osm_22717629_1914050891_11480720548"]]
scp = sc.geometry.union_all().centroid
n_scala = int(gpd.read_file(ROOT / "data/norm/analysis/battisti/job_4d23232eb780b0c1_archi_usati.geojson").set_index("edge_id").loc["edg_osm_22717629_11480720548_11480720545", "n_origini"])
add(id="SCA-01", gruppo="scala", tipo="scala", prio=1, nome="Scala da 38 gradini sul percorso verso l'ingresso Battisti", id_modello="edg_osm_22717629_11480720548_11480720545+edg_osm_22717629_1914050891_11480720548",
    xy=[scp.x, scp.y], motivo=f"Usata da {n_scala} origini su 2.224 verso Battisti (archi usati T06, profilo base); il profilo ridotta la evita e allunga di 45 m (analysis/REPORT.md punti 2). Step_count 38 è un tag OSM non verificato.",
    cosa="Numero di gradini, corrimano, larghezza, rampa o alternativa senza gradini, cancello o barriera, stato (agibile o chiusa).",
    come="Contare salendo e scendendo; larghezza con rotella; foto dall'alto e dal basso.", min=8, uso="correzione",
    misure=[mis("scala_gradini", valore_modello=38, unita="gradini"), mis("cancello_passabile", valore_modello="passabile"), mis("posizione_oggetto", valore_modello=0.0, unita="m")])

# ---------- cancelli piu usati: stessi calcoli di T06 (profilo base, ingresso predefinito Battisti) ----------
sys.path.insert(0, str(ROOT / "analysis"))
import accessibilita as T06  # noqa: E402
cnt, orig_bar, _ris = collections.Counter(), 0, T06._riassunto
def _cattura(H, nodi, archi):
    r = _ris(H, nodi, archi); bn = [n for n in nodi if H.nodes[n].get("barriera")]
    if bn: cnt.update(bn)
    return r
T06._riassunto = _cattura
res06 = T06.compute_walk_access("dst_school_piee82101p")  # senza out_dir: nessun file scritto
T06._riassunto = _ris
n06 = res06["aggregati"]["origini_con_barriera"]
assert n06 == 596, n06  # coincide con analysis/REPORT.md
for i, (n, c) in enumerate(cnt.most_common(5), 1):
    g = EN.loc[n].geometry
    add(id=f"CAN-{i:02d}", gruppo="cancello", tipo="barriera_" + str(EN.loc[n].barriera), prio=1 if i <= 3 else 2, nome=f"Barriera {EN.loc[n].barriera} (nodo {n.split('_')[-1]})", id_modello=n, xy=[g.x, g.y],
        motivo=f"Barriera passabile solo per ipotesi: sul percorso di {c} delle {n06} origini con barriera verso Battisti (ricalcolo con il codice T06, profilo base: stesso totale di analysis/REPORT.md). 182 cancelli senza tag access sono passabili per ipotesi (network/REPORT.md, analysis/REPORT.md punto 2).",
        cosa="Tipo, larghezza libera, passabile a piedi (sempre, a orari, mai), aggirabile, orari esposti.",
        come="Osservare, larghezza con rotella o laser, foto. Non entrare in aree private.", min=4, uso="verifica" if i % 2 == 0 else "correzione",
        misure=[mis("cancello_passabile", valore_modello="passabile"), mis("posizione_oggetto", valore_modello=0.0, unita="m")])

# ---------- marciapiede ignoto: tratti più usati ----------
bad = {"edg_osm_1077907317_5264115226_9882762242", "edg_osm_152406786_1375182219_9882762242", "edg_osm_123258977_1375182228_1375182219", "edg_osm_1163413735_1375182231_1375182228"}  # coperti da FER-01 e ROT-01
cand = {}
for dname, r in riep.items():
    for a in r["archi_ignoti_piu_usati"][:12]:
        if a["edge_id"] in bad or a["edge_id"] not in EA.index: continue
        cand[a["edge_id"]] = max(cand.get(a["edge_id"], 0), a["n_origini"])
Gc = nx.Graph()
for e in cand: Gc.add_edge(EA.loc[e].nod_da, EA.loc[e].nod_a, e=e)
groups = []
for comp in nx.connected_components(Gc):
    es = [d["e"] for _, _, d in Gc.subgraph(comp).edges(data=True)]
    groups.append(es)
groups = sorted(groups, key=lambda es: -max(cand[e] for e in es))[:9]
for i, es in enumerate(groups, 1):
    g = shapely.ops.unary_union([EA.loc[e].geometry for e in es]); c = g.interpolate(0.5, normalized=True)
    nomi = list(dict.fromkeys(EA.loc[e]["name"] for e in es if isinstance(EA.loc[e]["name"], str)))
    nome = " e ".join(nomi) if nomi else "tratto senza nome"
    n_or = max(cand[e] for e in es); L = round(sum(EA.loc[e].length_m for e in es))
    add(id=f"MAR-{i:02d}", gruppo="marciapiede", tipo="marciapiede_ignoto", prio=1 if i <= 5 else 2, nome=f"{nome}: tratto di {L} m a marciapiede ignoto", id_modello="+".join(es), xy=[c.x, c.y], min=5,
        motivo=f"Tratto a marciapiede ignoto fra i più usati: fino a {n_or} origini (analysis/REPORT.md 'Tratti più usati a marciapiede ignoto'). Il lato del marciapiede cambia fino a 20 punti la frazione d'ombra (shadow/REPORT.md).",
        cosa="C'è marciapiede? Su quale lato (sinistro o destro andando verso la scuola o verso il centro del tratto)? Larghezza minima, ostacoli, percorribile in sicurezza.",
        come="Percorrere il tratto; larghezza minima con rotella o laser; foto del tratto nei due sensi, senza persone riconoscibili.",
        uso="verifica" if h01(f"MAR{i}") % 2 else "correzione",
        misure=[mis("marciapiede_stato", valore_modello="ignoto"), mis("marciapiede_lato", valore_modello="ignoto"), mis("percorribile", valore_modello="si")])

# ---------- fermate, rotatoria ----------
def stop_pt(code, i, prio, nome_extra, motivo, uso="correzione"):
    e = stops[code]["ingressi"][0]
    add(id=f"FER-{i:02d}", gruppo="fermata", tipo="fermata_bus", prio=prio, nome=f"Fermata {stops[code]['nome']} ({code}) {nome_extra}".strip(), id_modello=f"{stops[code]['destination_id']}|{e['entrance_id']}",
        xy=e["xy"], motivo=motivo, min=8, uso=uso,
        cosa="Posizione reale di palo e pensilina, lato della strada rispetto alla piattaforma OSM, marciapiede e attraversamento per raggiungerla.",
        come="Posizione smartphone al palo (30 s), bussola per il lato, foto del palo e della pensilina.",
        misure=[mis("posizione_fermata", valore_modello=0.0, unita="m"), mis("lato_fermata_ok", valore_modello="si"), mis("marciapiede_stato", valore_modello="ignoto")])
stop_pt("PI4390", 1, 1, "(Pellico, origine del percorso R01)", "Lato della fermata Pellico: piattaforma OSM a 4,1 m dal punto GTFS ma lato non verificato; il tratto di 5,8 m su via Pellico è usato da 1.335 origini (network/REPORT.md, analysis/REPORT.md punto 4).")
stop_pt("PI0001", 2, 2, "(origine di R08)", "Origine del percorso campione R08; piattaforma OSM a 3,9 m dal punto GTFS (network/REPORT.md).", uso="verifica")
stop_pt("PI0003", 3, 3, "(stazione)", "Fermata di stazione: pensiline e accesso (geometry/REPORT.md 'quota d'imposta delle pensiline').", uso="verifica")
stop_pt("PI4074", 4, 3, "(Corridoni 1, origine di R03)", "Fermata più vicina alla scuola, origine di R03 (network/REPORT.md).", uso="verifica")
e_rot = EA.loc["edg_osm_1163413735_1375182231_1375182228"].geometry.centroid
add(id="ROT-01", gruppo="fermata", tipo="rotatoria", prio=1, nome="Rotatoria dell'Ordine del Santo Sepolcro presso via Pellico", id_modello="edg_osm_1163413735_1375182231_1375182228+edg_osm_123258977_1375182228_1375182219+edg_osm_152406786_1375182219_9882762242",
    xy=[e_rot.x, e_rot.y], min=8, uso="correzione",
    motivo="Rotatoria e via Pellico a marciapiede ignoto, usate da circa 1.230 origini verso Pellico e dal percorso R01 (analysis/REPORT.md punto 4, network/REPORT.md).",
    cosa="Come si percorre a piedi la rotatoria: marciapiede, attraversamenti sui rami, isole, lato dove si cammina verso via Battisti.",
    come="Percorrerla a piedi, contare gli attraversamenti, foto dei rami, lato del marciapiede a ogni ramo.",
    misure=[mis("marciapiede_stato", valore_modello="ignoto"), mis("marciapiede_lato", valore_modello="ignoto"), mis("attraversamento_presente", valore_modello="si_strisce"), mis("percorribile", valore_modello="si")])

# ---------- alberi e edifici ----------
def chain(g): return R01.project(g.centroid)
def dR(g): return R01.distance(g)
sel = {o["oggetto"]: o for o in sop if o["tipo"] == "albero"}
trees = []
for tid, so in sel.items():
    r = Ai.loc[tid]; trees.append((chain(r.geometry), tid, r, so))
trees.sort(key=lambda t: t[0])
near = [t for t in trees if dR(t[2].geometry) <= 30]
completa = set()
# 16 alberi completi fra i vicini a R01, scelti a passo regolare sul percorso
step = max(1, len(near) // 16)
for i, t in enumerate(near):
    if len(completa) < 16 and i % step == 0 and t[3]["fonti"] == "osm": completa.add(t[1])
strata = collections.defaultdict(list)
for k, (ch, tid, r, so) in enumerate(trees, 1):
    liv = "completa" if tid in completa else "rapida"
    prio = 1 if tid in completa else (2 if dR(r.geometry) <= 30 else 3)
    strata[(liv, prio)].append(tid)
uso_alb = {}
for key, ids in strata.items():
    for j, tid in enumerate(sorted(ids, key=lambda s: h01(s))): uso_alb[tid] = "verifica" if j % 2 == 0 else "correzione"
for k, (ch, tid, r, so) in enumerate(trees, 1):
    liv = "completa" if tid in completa else "rapida"
    prio = 1 if tid in completa else (2 if dR(r.geometry) <= 30 else 3)
    fonti = r.fonti
    ms = [mis("esiste_oggetto", valore_modello="si"), mis("posizione_oggetto", valore_modello=0.0, unita="m"), mis("specie", valore_modello="ignoto")]
    if liv == "completa" or "dbt" in fonti:
        ms += [mis("altezza_albero", valore_modello=r.h, vmin=r.h_min, vmax=r.h_max, unita="m"),
               mis("chioma_diametro", valore_modello=r.chioma_d, vmin=r.chioma_d_min, vmax=r.chioma_d_max, unita="m"),
               mis("altezza_imposta", valore_modello=r.imposta, vmin=r.imposta_min, vmax=r.imposta_max, unita="m")]
    add(id=f"A{k:02d}", gruppo="albero", tipo="albero", prio=prio if "dbt" not in fonti else 2, nome=f"Albero {tid} (fonte {fonti}, a {dR(r.geometry):.0f} m da R01)", id_modello=tid, xy=[r.geometry.x, r.geometry.y],
        motivo=("Albero solo OSM: posizione, specie, altezza e chioma non verificati (geometry/REPORT.md, sopralluogo_z2.json priorità 1; tutte le chiome sono stimate). " if fonti == "osm" else "Albero presente nel 2010 (DBT10K), da confermare (sopralluogo_z2.json priorità 2). ")
               + (f"Livello {liv}: " + ("altezza, chioma e imposta da misurare." if liv == "completa" else "solo esistenza, posizione e specie.")),
        cosa="Esiste? Posizione al tronco; specie; trasparenza stagionale" + ("; altezza totale, diametro chioma (due assi), altezza d'imposta." if len(ms) > 3 else "."),
        come="Posizione smartphone al tronco" + (", laser e clinometro da due stazioni, rotella per la chioma." if len(ms) > 3 else "."), min=4 if len(ms) > 3 else 1.5,
        uso=uso_alb[tid], misure=ms, d_r01_m=round(dR(r.geometry), 1), ch_r01_m=round(ch))

# edifici: lista del report T05 più quelli entro 15 m da R01 con h>=9, non già in lista
bsel = {o["oggetto"]: o for o in sop if o["tipo"] != "albero"}
extra = [i for i, r in Bi.iterrows() if i not in bsel and dR(r.geometry) <= 15 and r.h >= 9]
ordine = sorted(list(bsel) + extra, key=lambda i: chain(Bi.loc[i].geometry))
def prio_b(i):
    if i in extra: return 2
    p = bsel[i]["prio"]
    if p == 1: return 1
    return 3 if (p == 3 or dR(Bi.loc[i].geometry) > 25) else 2
st = collections.defaultdict(list)
for i in ordine: st[prio_b(i)].append(i)
uso_b = {}
for p, ids in st.items():
    for j, i in enumerate(sorted(ids, key=lambda s: h01(s))): uso_b[i] = "verifica" if j % 2 == 0 else "correzione"
nb = 0
for i in ordine:
    r = Bi.loc[i]; nb += 1; p = prio_b(i)
    so = bsel.get(i, {})
    solo_portico = (so.get("prio") == 3) or (so and p == 3 and so["cosa"].startswith("portico"))
    solo_portico = bool(so) and so.get("prio") == 3
    ms = [mis("esiste_oggetto", valore_modello="si"), mis("portico", valore_modello="ignoto")]
    if not solo_portico:
        ms.insert(1, mis("altezza_edificio", valore_modello=r.h, vmin=r.h_min, vmax=r.h_max, classe=r.classe_h, unita="m"))
    motivo = so.get("perche") or f"Edificio entro 15 m da R01 con altezza {r.h:.1f} m (>= 9 m), non nella lista T05: ombra su R01."
    add(id=f"E{nb:02d}", gruppo="edificio", tipo=r.tipo, prio=p, nome=f"Edificio {i}", id_modello=i, xy=[r.geometry.centroid.x, r.geometry.centroid.y],
        motivo=f"{motivo}. Fonte: geometry/REPORT.md (sopralluogo_z2.json) " + ("priorità " + str(so["prio"]) if so else "e distanza da R01") + "; portici ignoti ovunque (T09 li tratta come pieni, limite superiore).",
        cosa=("Portico sì o no sul fronte strada." if solo_portico else "Altezza dalla strada (gronda e colmo se a falde), portico sì o no sul fronte strada, esistenza (demolito o sopraelevato?)."),
        come=("Osservazione dalla strada, foto del fronte." if solo_portico else "Laser per la distanza e clinometro da due stazioni; foto del fronte."), min=1.5 if solo_portico else 4,
        uso=uso_b[i], misure=ms, d_r01_m=round(dR(r.geometry), 1), ch_r01_m=round(chain(r.geometry)), classe_h=r.classe_h)

# riferimenti altezza assoluta: 4 edifici NON in lista, measured, area >= 200 m2, entro 60 m da R01, spaziati lungo il percorso
c_ref = Bi[(~Bi.index.isin(ordine)) & (Bi.classe_h == "measured") & (Bi.area_m2 >= 200) & (Bi.flag == "") & (Bi.h >= 6)].copy()
c_ref["d"] = [dR(g) for g in c_ref.geometry]; c_ref = c_ref[c_ref.d <= 60]; c_ref["ch"] = [chain(g) for g in c_ref.geometry]
for k, target in enumerate((120, 300, 480, 660), 1):
    r = c_ref.iloc[(c_ref.ch - target).abs().argsort()[:1]].iloc[0]; i = r.name; c_ref = c_ref.drop(i)
    add(id=f"REF-{k:02d}", gruppo="riferimento_altezza", tipo="edificio_riferimento", prio=2, nome=f"Edificio di riferimento {i}", id_modello=i, xy=[r.geometry.centroid.x, r.geometry.centroid.y],
        motivo="Altezza assoluta indipendente: unità volumetriche e DSM non sono fonti indipendenti, nessun riferimento esterno finora (geometry/REPORT.md 'Riserve'; sopralluogo_z2.json 'altezza assoluta di 3-5 edifici').",
        cosa="Altezza assoluta con due metodi indipendenti (laser e clinometro da due stazioni; numero piani per altezza piano), da concordare entro 0,7 m.",
        come="Scegliere un punto di vista con base e gronda visibili, due distanze, annotare altezza dell'occhio. Foto.", min=12, uso="verifica",
        misure=[mis("altezza_assoluta_riferimento", valore_modello=r.h, vmin=r.h_min, vmax=r.h_max, classe=r.classe_h, unita="m")], d_r01_m=round(r.d, 1), ch_r01_m=round(r.ch))

# ---------- pensiline ----------
pen = B[(B.tipo == "copertura_osm") & (B.area_m2 >= 1900)].copy(); pen["x"] = pen.geometry.centroid.x
pen = pen.sort_values("x")
for k, (i, r) in enumerate(pen.iterrows(), 1):
    full = k in (1, 4, 7)
    add(id=f"PEN-{k:02d}", gruppo="pensilina", tipo="copertura_osm", prio=1 if full else 3, nome=f"Pensilina stazione {i} ({r.area_m2:.0f} m2)", id_modello=i, xy=[r.geometry.centroid.x, r.geometry.centroid.y],
        motivo="Pensilina OSM della stazione: solo la quota del tetto è nota; base sospesa = tetto meno 0,4 m è una stima (shadow/REPORT.md 'Limiti', geometry/REPORT.md). Conta per ricevitori di tipo superficie.",
        cosa=("Altezza libera dal piano di calpestio all'intradosso, spessore soletta, tipo di copertura (piena, grigliata, vetrata), esistenza." if full else "Esistenza e tipo di copertura (foto); altezza libera se facile."),
        come="Laser verticale dal piano di calpestio; foto dal basso e di profilo. Sostare solo sul marciapiede di banchina consentito, mai oltre la linea gialla.", min=6 if full else 3, uso="verifica" if k in (4, 7) else "correzione",
        misure=[mis("esiste_oggetto", valore_modello="si")] + ([mis("quota_imposta_pensilina", valore_modello=round(r.h - 0.4, 2), unita="m", nota="modello: tetto meno 0,4 m, stima")] if full else []))

# ---------- osservazioni d'ombra su R01 ----------
SITI = (70, 200, 330, 460, 590, 700)
V_SITI = {1, 3, 4, 6}  # siti di verifica (12 osservazioni); 2 e 5 calibrazione (6 osservazioni)
WIN = {"A": ("mattina", 9 * 60 + 30, +1), "B": ("mezzogiorno", 12 * 60 + 30, -1), "C": ("pomeriggio", 15 * 60 + 30, +1)}
def hm(t): return f"{int(t)//60:02d}:{int(t)%60:02d}"
for s, ch in enumerate(SITI, 1):
    g = R01.interpolate(ch); slots = []
    for w, (nome, t0, dirn) in WIN.items():
        pos = ch if dirn > 0 else R01.length - ch
        t = t0 + pos / 1.2 / 60 + 3 * (s if dirn > 0 else (len(SITI) - s))
        slots.append(mis("ombra_osservata", slot=w, finestra=nome, ora_target=hm(t), ora_reale=None, valore_modello=None, bordo=None, cielo=None, foto=None))
    add(id=f"OMB-S{s}", gruppo="ombra", tipo="osservazione_ombra", prio=1 if s in V_SITI else 2, nome=f"Sito d'ombra {s} su R01 (a {ch} m dalla fermata Pellico)", id_modello=f"R01@{ch}m", xy=[g.x, g.y], min=9,
        motivo="Almeno 12 osservazioni d'ombra distribuite fra siti e orari (docs/SPEC_ANALISI.md sezione 6, docs/PIANO.md sezione 9). Siti a passo regolare sul percorso, scelti senza guardare i risultati d'ombra. Il lato del marciapiede è l'incertezza dominante (shadow/REPORT.md).",
        cosa="Ombra, sole o parziale al suolo nel punto, ora reale, bordo entro 1 m, cielo, lato e distanza dall'asse, oggetto che fa ombra. Tre finestre: mattina, mezzogiorno, pomeriggio.",
        come="Fermarsi sul marciapiede nel punto, entro 5 minuti dall'ora prevista. Foto del suolo con ombra e dell'orizzonte verso il sole, senza persone. Con cielo coperto ripetere.",
        uso="verifica" if s in V_SITI else "correzione", misure=slots + [mis("offset_laterale", valore_modello=0.0, unita="m")], ch_r01_m=ch, d_r01_m=0.0)

# ---------- percorsi campione ----------
DEF = {"R01": (1, "correzione"), "R03": (1, "verifica"), "R05": (1, "verifica"), "R08": (1, "verifica"), "R09": (1, "verifica"), "V01": (1, "correzione"),
       "R04": (2, "correzione"), "R06": (3, "verifica"), "R07": (3, "correzione"), "R02": (3, "correzione")}
for rid in ("R01", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "V01", "R02"):
    p = PERC.get(rid) or next(f for f in perc if f["properties"]["id"] == rid)
    pr = p["properties"]; g = shape(p["geometry"]); x0 = g.coords[0]; x1 = g.coords[-1]
    L = pr.get("lunghezza_totale_m"); ms = []
    if rid == "V01":
        ms = [mis("accesso_negato", valore_modello="negato")]
    else:
        ms = [mis("lunghezza_percorso", valore_modello=L, unita="m"), mis("tempo_percorso", valore_modello=round(L / 1.2, 0), unita="s"), mis("n_attraversamenti", valore_modello=pr["attraversamenti"], unita="n")]
    add(id=f"PER-{rid}", gruppo="percorso", tipo="percorso_campione", prio=DEF[rid][0], nome=f"{rid}: {pr['descrizione']}", id_modello=rid, xy=None, lon_lat=[round(x0[0], 6), round(x0[1], 6)], fine_lon_lat=[round(x1[0], 6), round(x1[1], 6)],
        motivo="5-10 percorsi campione da controllare a piedi con tempo (docs/SPEC_ANALISI.md sezione 6; network/REPORT.md 'Percorsi campione')." + (" Caso di accesso negato richiesto dalla SPEC." if rid == "V01" else ""),
        cosa=("Verificare che l'accesso sia negato dalla via pubblica; non percorrere." if rid == "V01" else "Percorrere l'itinerario stampato: tempo netto, lunghezza, numero di attraversamenti, deviazioni, barriere, marciapiede."),
        come=("Cartelli e cancelli dalla via pubblica, foto." if rid == "V01" else "Cronometro con parziali per le soste, rotella a ruota o traccia; annotare ogni deviazione."), min=3 if rid == "V01" else round(L / 1.2 / 60 + 3, 1), uso=DEF[rid][1], misure=ms, percorso_geom=p["geometry"]["coordinates"])

# ---------- finalizza ----------
poe = next(p for p in punti if p["id"] == "POE-01")
CENTRI = {"STAZ": Point(*TO_M.transform(10.3993, 43.7085)), "PELL": Point(*TO_M.transform(10.39756, 43.710459)),
          "BATT": Point(*TO_M.transform(10.404438, 43.707121)), "POE": Point(*poe["xy"])}
for p in punti:
    if p.get("xy"): p["lon_lat"] = ll_xy(*p["xy"])
    pg = Point(*TO_M.transform(*p["lon_lat"]))
    p["xy_m"] = [round(pg.x, 1), round(pg.y, 1)]
    p["d_r01_m"] = round(R01.distance(pg), 1); p["ch_r01_m"] = round(R01.project(pg))
    if p["id"] == "PER-V01": p["tappa"] = "POE"
    elif p["gruppo"] == "percorso": p["tappa"] = "PCS"
    elif p["gruppo"] == "ombra": p["tappa"] = "R01"
    elif p["gruppo"] in ("albero", "edificio", "riferimento_altezza") and p["d_r01_m"] <= 60: p["tappa"] = "R01"
    elif p["gruppo"] == "pensilina": p["tappa"] = "STAZ"
    elif p["id"] == "POE-02": p["tappa"] = "EXTRA"
    else: p["tappa"] = min(CENTRI, key=lambda c: CENTRI[c].distance(pg))
    p.pop("xy", None)
# ordine dentro la tappa: lungo R01 per chainage, altrove vicino-più-vicino dal punto di ingresso
ENTRY = {"STAZ": "FER-03", "PELL": "FER-01", "BATT": "ING-01", "POE": "POE-01", "EXTRA": "POE-02"}
for t in ("STAZ", "PELL", "BATT", "POE", "EXTRA", "R01", "PCS"):
    L_ = [p for p in punti if p["tappa"] == t]
    if t == "R01": L_.sort(key=lambda p: (p["ch_r01_m"], p["id"]))
    elif t == "PCS": L_.sort(key=lambda p: ("R08 R03 R04 R05 R09 R06 R07 R02 R01".split().index(p["id"][4:])))
    else:
        cur = next(p for p in L_ if p["id"] == ENTRY[t]); rest = [p for p in L_ if p is not cur]; L_ = [cur]
        while rest:
            nx_ = min(rest, key=lambda q: (q["xy_m"][0] - cur["xy_m"][0]) ** 2 + (q["xy_m"][1] - cur["xy_m"][1]) ** 2); rest.remove(nx_); L_.append(nx_); cur = nx_
    for i, p in enumerate(L_, 1): p["ordine"] = i
ORD = {"ingresso": 0, "fermata": 1, "pensilina": 2, "accesso": 3, "scala": 4, "cancello": 5, "marciapiede": 6, "albero": 7, "edificio": 8, "riferimento_altezza": 9, "ombra": 10, "percorso": 11}
n = collections.Counter(p["prio"] for p in punti)
tot = {k: round(sum(p["min"] for p in punti if p["prio"] <= k)) for k in (1, 2, 3)}
meta = {"protocollo": "T11-Z2-v1", "generato_da": "fieldwork/genera_punti.py", "crs": "EPSG:4326", "n_punti": len(punti), "per_priorita": {str(k): n[k] for k in sorted(n)},
        "per_gruppo": dict(collections.Counter(p["gruppo"] for p in punti)), "per_uso": dict(collections.Counter(p["uso"] for p in punti)),
        "minuti_sul_punto_cumulati_per_priorita": {str(k): v for k, v in tot.items()},
        "nota": "I valori valore_modello sono nel file per l'importatore e NON vanno stampati o mostrati a chi rileva (misura alla cieca). Il campo uso è fissato prima del rilievo. Il valore del modello per le osservazioni d'ombra si calcola dopo, all'ora reale.",
        "priorita": {"1": "indispensabile: decide la validità dei risultati", "2": "utile: se c'è tempo", "3": "facoltativo: solo se resta tempo o se il punto è sulla strada"}}
punti.sort(key=lambda p: (p["prio"], ORD[p["gruppo"]], p["id"]))
json.dump({"meta": meta, "punti": punti}, open(FW / "punti.json", "w"), ensure_ascii=False, indent=1)
feats = []
for p in punti:
    pr = {k: v for k, v in p.items() if k not in ("lon_lat", "percorso_geom", "fine_lon_lat", "misure")}
    pr["grandezze"] = [m_["grandezza"] for m_ in p["misure"]]
    feats.append({"type": "Feature", "properties": pr, "geometry": {"type": "Point", "coordinates": p["lon_lat"]}})
    if p["gruppo"] == "percorso" and p["id_modello"] != "V01":
        feats.append({"type": "Feature", "properties": {"id": p["id"] + "-linea", "gruppo": "percorso_linea", "prio": p["prio"], "nome": p["nome"]}, "geometry": {"type": "LineString", "coordinates": p["percorso_geom"]}})
json.dump({"type": "FeatureCollection", "name": "punti_rilievo_t11", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}, "features": feats}, open(FW / "punti.geojson", "w"), ensure_ascii=False)
import csv
COLS = ["id_punto", "grandezza", "slot", "valore_misurato", "valore_modello", "unita", "lon_misurato", "lat_misurato", "accuratezza_gps_m", "ora_locale", "bordo", "cielo", "foto", "rilevatore", "strumento", "note", "correzione_azione", "correzione_valore", "correzione_motivo"]
with open(FW / "esiti_modello.csv", "w", newline="", encoding="utf-8") as f:  # scheletro: una riga per misura, valori vuoti, nessun valore del modello
    w = csv.writer(f); w.writerow(COLS)
    for p in sorted(punti, key=lambda q: (q["tappa"], q["ordine"])):
        for m_ in p["misure"]:
            w.writerow([p["id"], m_["grandezza"], m_.get("slot", ""), "", "", m_.get("unita", "")] + [""] * (len(COLS) - 6))
print(json.dumps(meta, ensure_ascii=False, indent=1))
