#!/usr/bin/env python3
"""Compone inventario.json e inventario-tabella.txt dai dump CKAN e dalla verifica URL. Segnala i conflitti di licenza (scheda vs risorsa)."""
import json, os, re
from layers import LAYERS
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "..", "..", "research")
L = lambda n: json.load(open(os.path.join(R, "ckan-toscana-fi-" + n + ".json")))
pk = L("pacchetti")["packages"]; url = {r["url"]: r for r in L("url")["risultati"]}; cont = L("contenuto")["geojson"]
PK = {"cc-by-4.0": "CC BY 4.0", "cc-by": "CC BY (versione non indicata)", "cc-by-nc-4.0": "CC BY-NC 4.0", "cc-by-sa": "CC BY-SA (versione non indicata)",
      "iodl2": "IODL 2.0", "other-nc": "altra, non commerciale"}
def res_lic(u):
    if not u: return "non indicata"
    for k, v in (("licenses/by-nc/4.0", "CC BY-NC 4.0"), ("licenses/by/4.0", "CC BY 4.0"), ("A21_CCBY40", "CC BY 4.0"), ("A31_CCBYSA40", "CC BY-SA 4.0"),
                 ("C1_Unknown", "sconosciuta (C1_Unknown)"), ("italian-open-data-license-v20", "IODL 2.0")):
        if k in u: return v
    return u
fam = lambda s: "NC" if "NC" in s or "non comm" in s else "SA" if "SA" in s else "BY" if "BY" in s else "IODL" if "IODL" in s else s
def mb(n): return "n.d." if n is None else (f"{n/1e6:.1f} MB" if n >= 1e5 else f"{n/1e3:.0f} kB")
rows, conflitti = [], []
for lay, ids in LAYERS.items():
    ds = []
    for i in ids:
        p = pk[i]; rl = sorted({res_lic(r.get("license_type")) for r in p["resources"]}); pl = PK.get(p["license_id"], p["license_id"])
        flags = []
        if {fam(x) for x in rl if x != "non indicata"} - {fam(pl)}: flags.append("scheda e risorse in conflitto")
        if "non indicata" in rl: flags.append("licenza assente su alcune risorse")
        if "sconosciuta (C1_Unknown)" in rl: flags.append("risorsa con licenza sconosciuta")
        if "versione non indicata" in pl: flags.append("versione CC non indicata")
        us = []
        for r in p["resources"]:
            u = url.get(r["url"]); f = r.get("format") or "?"
            if not u or r["url"] is None: continue
            us.append({"formato": f, "nome": r.get("name"), "codice": u["code"], "contenuto": u.get("primo_byte") or u.get("primi_byte"),
                       "byte": u.get("dimensione_byte"), "url_finale": u.get("final_url"), "url": r["url"]})
        d = {"layer": lay, "id": i, "titolo": p["title"], "org": (p.get("organization") or {}).get("name"), "formati": sorted({u["formato"] for u in us}),
             "licenza_scheda": f'{p["license_id"]} ({p.get("license_title")})', "licenza_risorse": rl, "flags": flags, "dato_modified": p.get("modified"),
             "emesso": p.get("issued"), "scheda_aggiornata": p["metadata_modified"][:10], "frequenza": p.get("frequency"),
             "srs_scheda": next((e["value"] for e in p["extras"] if e["key"] == "spatial-reference-system"), None),
             "url": us, "contenuto_json": cont.get(i)}
        if flags: conflitti.append({"id": i, "titolo": p["title"], "flags": flags, "scheda": d["licenza_scheda"], "risorse": rl})
        ds.append(d)
    rows.append({"layer": lay, "dataset": ds})
json.dump({"layers": rows, "conflitti": conflitti}, open(os.path.join(H, "inventario.json"), "w"), ensure_ascii=False, indent=1)
# tabella: una riga per layer
def cell(lay, ds):
    d0 = ds[0]
    ids = "; ".join(d["id"] for d in ds) if len(ds) <= 4 else f'{len(ds)} dataset (id in inventario.json)'
    lic = sorted({d["licenza_scheda"].split(" (")[0] for d in ds}); lr = sorted({x for d in ds for x in d["licenza_risorse"]})
    fl = sorted({f for d in ds for f in d["flags"]})
    dm = sorted({d["dato_modified"] or "n.d." for d in ds}); sc = sorted({d["scheda_aggiornata"] for d in ds}); fr = sorted({(d["frequenza"] or "n.d.") for d in ds})
    fm = sorted({f for d in ds for f in d["formati"]})
    cods = sorted({u["codice"] for d in ds for u in d["url"]}, key=str); sz = [u["byte"] for d in ds for u in d["url"] if u["formato"] not in ("WMS", "TXT") and u["byte"]]
    html = sum(1 for d in ds for u in d["url"] if u["contenuto"] == "html")
    return f'| {lay} | {ids} | {d0["org"]} | {", ".join(fm)} | scheda {", ".join(lic)}; risorse {", ".join(lr)}{" **" + "; ".join(fl) + "**" if fl else ""} | dato {", ".join(dm)}; scheda {", ".join(sc)} | {", ".join(fr)} | HTTP {", ".join(map(str, cods))}; {mb(min(sz)) if sz else "n.d."}-{mb(max(sz)) if sz else "n.d."}{"; " + str(html) + " pagine HTML al posto del file" if html else ""} |'
t = ["| Layer | Dataset (id) | Organizzazione | Formati | Licenza | Aggiornamento | Frequenza | Download |", "|---|---|---|---|---|---|---|---|"]
t += [cell(r["layer"], r["dataset"]) for r in rows]
open(os.path.join(H, "inventario-tabella.txt"), "w").write("\n".join(t) + "\n")
print(len(rows), "layer;", len(conflitti), "dataset con segnalazioni di licenza")
