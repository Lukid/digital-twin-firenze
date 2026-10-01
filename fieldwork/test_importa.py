#!/usr/bin/env python3
"""TEST CON DATI FITTIZI. Nessuno di questi esiti proviene da un sopralluogo reale: valori inventati
per provare l'importatore. Non usare mai fieldwork/out generato da questo test come risultato di verifica.
Esegui: python3 fieldwork/test_importa.py"""
import csv, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importa_esiti as I

FW = Path(__file__).resolve().parent
prot = json.load(open(FW / "protocollo.json")); punti = json.load(open(FW / "punti.json"))["punti"]
P = {p["id"]: p for p in punti}
def prima(**k): return next(p for p in punti if all(p[a] == b for a, b in k.items()))
ver_alb = prima(gruppo="albero", prio=1, uso="verifica"); cor_alb = prima(gruppo="albero", prio=1, uso="correzione")
ver_edi = prima(gruppo="edificio", prio=1, uso="verifica") if any(p["gruppo"] == "edificio" and p["prio"] == 1 and p["uso"] == "verifica" for p in punti) else prima(gruppo="edificio", uso="verifica")
mis = lambda p, g: next(m for m in p["misure"] if m["grandezza"] == g)
H = ver_edi["misure"][1] if ver_edi["misure"][1]["grandezza"] == "altezza_edificio" else mis(ver_edi, "altezza_edificio")
site = next(p for p in punti if p["id"] == "OMB-S1")

def riga(**k):
    r = {c: "" for c in I.COLONNE}; r.update(k); return r
righe = [
    # FITTIZIO: altezza edificio dentro tolleranza
    riga(id_punto=ver_edi["id"], grandezza="altezza_edificio", valore_misurato=str(H["valore_modello"] + 0.8).replace(".", ","), unita="m"),
    # FITTIZIO: altezza albero fuori intervallo -> non ok
    riga(id_punto=ver_alb["id"], grandezza="altezza_albero", valore_misurato=str(mis(ver_alb, "altezza_albero")["vmax"] + 5), unita="m"),
    # FITTIZIO: posizione albero da lon e lat a circa 2 m
    riga(id_punto=ver_alb["id"], grandezza="posizione_oggetto", lon_misurato=str(ver_alb["lon_lat"][0] + 0.00002), lat_misurato=str(ver_alb["lon_lat"][1]), accuratezza_gps_m="4"),
    # FITTIZIO: scartata per GPS impreciso
    riga(id_punto=cor_alb["id"], grandezza="posizione_oggetto", lon_misurato=str(cor_alb["lon_lat"][0]), lat_misurato=str(cor_alb["lon_lat"][1]), accuratezza_gps_m="25"),
    # FITTIZIO: correzione ammessa su oggetto uso=correzione
    riga(id_punto="ING-01", grandezza="ingresso_in_uso", valore_misurato="no", correzione_azione="correggi_posizione", correzione_valore="altro ingresso", correzione_motivo="fittizio", rilevatore="TEST", foto="f1.jpg"),
    # FITTIZIO: correzione NON ammessa su oggetto di verifica -> errore, nessuna correzione emessa
    riga(id_punto=ver_alb["id"], grandezza="esiste_oggetto", valore_misurato="si", correzione_azione="cambia_attributo", correzione_valore="x", correzione_motivo="fittizio"),
    # FITTIZIO: ombra senza fuso orario -> errore
    riga(id_punto=site["id"], grandezza="ombra_osservata", slot="A", valore_misurato="ombra", valore_modello="ombra", ora_locale="2026-10-14T09:40:00", bordo="no", cielo="sereno", foto="o1.jpg"),
    # FITTIZIO: ombra valida, modello concorde
    riga(id_punto=site["id"], grandezza="ombra_osservata", slot="B", valore_misurato="sole", valore_modello="sole", ora_locale="2026-10-14T12:40:00+02:00", bordo="no", cielo="sereno", foto="o2.jpg"),
    # FITTIZIO: id sconosciuto -> errore
    riga(id_punto="XXX-99", grandezza="altezza_edificio", valore_misurato="10"),
    # FITTIZIO: riga non compilata dello scheletro -> ignorata
    riga(id_punto="SCA-01", grandezza="scala_gradini"),
]
with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "esiti_FITTIZI.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=I.COLONNE); w.writeheader(); w.writerows(righe)
    r = I.importa(f, prot, punti, Path(d) / "out")
    e = " | ".join(r["errori"])
    assert r["righe_non_compilate"] == 1, r["righe_non_compilate"]
    assert len(r["errori"]) == 3, r["errori"]
    assert "id_punto sconosciuto" in e and "uso=verifica" in e and "fuso" in e, e
    assert len(r["correzioni"]) == 1 and r["correzioni"][0]["properties"]["target"] == P["ING-01"]["id_modello"]
    assert len(r["scartate"]) == 1 and cor_alb["id"] in r["scartate"][0]
    ok = {(x["id_punto"], x["grandezza"], x["slot"]): x["ok"] for x in r["righe"]}
    assert ok[(ver_edi["id"], "altezza_edificio", "")] is True
    assert ok[(ver_alb["id"], "altezza_albero", "")] is False
    assert ok[(ver_alb["id"], "posizione_oggetto", "")] is True
    assert ok[(site["id"], "ombra_osservata", "B")] is True
    # separazione: i file di uscita esistono e le correzioni non contengono oggetti di verifica
    cg = json.load(open(Path(d) / "out" / "correzioni_proposte.geojson"))
    assert all(P[ft["properties"]["osservazione_id"].split(":")[0]]["uso"] == "correzione" for ft in cg["features"])
    # pochi dati: nessuna classe si dichiara validata
    assert all(b["verifica"]["esito"] != "validato" for b in r["riepilogo"].values() if "verifica" in b)
    # il congelamento rileva modifiche alle tolleranze
    h = I.sha_grandezze(prot); prot2 = json.loads(json.dumps(prot)); prot2["grandezze"]["posizione_oggetto"]["tol_m"] = 50
    assert I.sha_grandezze(prot2) != h
print("OK test_importa (dati fittizi)")
