"""Valida pipeline/snapshots/*.json (snapshot.schema) e pipeline/sources/*.json (source.schema) con gli schemi in contracts/schemas."""
import json, pathlib, sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
R = pathlib.Path(__file__).resolve().parents[1]
sch = {p.name.split(".")[0]: json.load(open(p)) for p in (R / "contracts/schemas").glob("*.schema.json")}
reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in sch.values()])
bad = 0
for kind, folder in (("snapshot", "snapshots"), ("source", "sources")):
    v = Draft202012Validator(sch[kind], registry=reg)
    for p in sorted((R / "pipeline" / folder).glob("*.json")):
        if p.name.startswith("_"): continue
        errs = list(v.iter_errors(json.load(open(p))))
        print(("OK     " if not errs else "ERRORE ") + f"{kind:8} {p.name}" + (f"  {errs[0].message[:120]}" if errs else "")); bad += bool(errs)
print("FALLITO" if bad else "TUTTO OK"); sys.exit(bad)
