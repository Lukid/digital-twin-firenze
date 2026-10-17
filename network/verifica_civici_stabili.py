#!/usr/bin/env python3
"""Controllo D30: i civici citati da percorsi campione e destinazioni si ritrovano per CODICECIVI in un'altra copia dei civici (sola lettura).
Uso: pipeline/.venv/bin/python network/verifica_civici_stabili.py data.worker-2026-10-17/norm/firenze_novoli/fi_civici.gpkg
Confronta con data/norm/firenze_novoli/fi_civici.gpkg: CODICECIVI unico in tutte e due, stesso punto e stesso indirizzo per ogni civico citato."""
import json, pathlib, sys
import geopandas as gpd

ROOT = pathlib.Path(__file__).resolve().parents[1]; RES = ROOT / "network/firenze_novoli"
a = gpd.read_file(ROOT / "data/norm/firenze_novoli/fi_civici.gpkg"); b = gpd.read_file(sys.argv[1])
for g in (a, b): assert g.CODICECIVI.notna().all() and g.CODICECIVI.is_unique, "CODICECIVI non unico"
A, B = a.set_index("CODICECIVI"), b.set_index("CODICECIVI")
citati = {r["id"]: r["civico"] for r in json.load(open(RES / "percorsi_campione.json")) if "civico" in r}
citati |= {e["entrance_id"]: a.set_index("id").loc[e["civico_id"], "CODICECIVI"] for d in json.load(open(RES / "destinazioni.json"))["destinazioni"] for e in d["ingressi"] if "civico_id" in e}
for k, cod in citati.items():
    x, y = A.loc[cod], B.loc[cod]
    assert x.geometry.distance(y.geometry) < 0.01 and (x.STRADA, x.NUMEROCIVI) == (y.STRADA, y.NUMEROCIVI), (k, cod)
    print(f"  ok {k}: {cod} {x.STRADA.strip()} {x.NUMEROCIVI.strip()} (id {x.id} -> {y.id})")
print(f"OK: {len(a)} e {len(b)} civici, CODICECIVI unico; {len(citati)} civici citati ritrovati nello stesso punto")
