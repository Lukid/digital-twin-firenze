#!/usr/bin/env python3
"""Controllo dei contratti. Uso: contracts/.venv/bin/python contracts/validate.py
Valida examples/ (i *.valid* devono passare, gli *.invalid* devono fallire), il campione in sample/
e alcune regole che JSON Schema non esprime (hash del job_id, classe di ogni attributo)."""
import hashlib, json, pathlib, sys
try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError:
    sys.exit("jsonschema/referencing mancanti: creare il venv con 'python3 -m venv --system-site-packages contracts/.venv'")

R = pathlib.Path(__file__).resolve().parent
load = lambda p: json.loads(p.read_text())
schemas = {p.name.split(".")[0]: load(p) for p in sorted((R/"schemas").glob("*.schema.json"))}
reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas.values()])
for name, s in schemas.items(): Draft202012Validator.check_schema(s)

def validator(schema, defname=""):
    node = schemas[schema]
    if defname: node = {"$ref": f"{node['$id']}#/$defs/{defname}"}
    return Draft202012Validator(node, registry=reg)

errors, seen = [], {}     # seen[(schema, def)] = {"valid": n, "invalid": n}
canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def extra(schema, kind, doc, label):
    if kind != "valid": return
    if schema == "job":
        h = hashlib.sha256(canon({"tool": doc["tool"], "inputs": doc["inputs"], "params": doc["params"]}).encode()).hexdigest()[:16]
        if doc["job_id"] != "job_" + h: errors.append(f"{label}: job_id non coincide con l'hash dell'input (atteso job_{h})")
    if schema == "manifest" and doc["manifest_id"][4:] != doc["job_id"][4:]:
        errors.append(f"{label}: manifest_id e job_id hanno cifre diverse")
    if schema == "sample":
        for f in doc["features"]:
            p = f["properties"]; skip = {"id", "layer", "source_id", "cls", "orig_wgs84", "destination_id"}
            miss = [k for k in p if k not in skip and k not in p["cls"]]
            if miss: errors.append(f"{label}: {p['id']} attributi senza classe: {miss}")

def run(schema, defname, kind, doc, label):
    k = seen.setdefault((schema, defname), {"valid": 0, "invalid": 0}); k[kind] += 1
    errs = sorted(validator(schema, defname).iter_errors(doc), key=lambda e: list(e.path))
    if kind == "valid" and errs: errors.append(f"{label}: doveva passare: {errs[0].message[:150]} @ {list(errs[0].path)}")
    elif kind == "invalid" and not errs: errors.append(f"{label}: doveva fallire e invece passa")
    else: print(f"  ok {label}" + (f"  (rifiutato: {errs[0].message[:70]})" if kind == "invalid" else ""))
    extra(schema, kind, doc, label)

for p in sorted((R/"examples").glob("*.json")):
    t = p.stem.split("."); i = next(i for i, x in enumerate(t) if x in ("valid", "invalid"))
    run(t[0], ".".join(t[1:i]), t[i], load(p), p.name)
run("sample", "", "valid", load(R/"sample/z2_campione.geojson"), "sample/z2_campione.geojson")

for (schema, d), k in sorted(seen.items()):
    if not k["valid"]: errors.append(f"{schema} {d}: nessun esempio valido")
    if not k["invalid"] and not d: errors.append(f"{schema}: nessun esempio non valido")
for name in schemas:
    if name != "common" and not any(s == name for s, _ in seen): errors.append(f"{name}: nessun esempio")
for d in schemas["mcp"]["$defs"]:
    if ("mcp", d) not in seen: errors.append(f"mcp {d}: nessun esempio")
nmcp_inv = sum(k["invalid"] for (s, _), k in seen.items() if s == "mcp")
if not nmcp_inv: errors.append("mcp: nessun esempio non valido")
print(f"\n{sum(k['valid'] for k in seen.values())} validi passati, {sum(k['invalid'] for k in seen.values())} non validi respinti")
print("FALLITO" if errors else "TUTTO OK")
for e in errors: print(" -", e)
sys.exit(bool(errors))
