"""Funzioni comuni di T03: percorsi, AOI, download con retry, snapshot (ok/failed)."""
import datetime as dt, hashlib, json, os, pathlib, time
import requests
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, NORM = ROOT / "data/raw", ROOT / "data/norm"
SNAP, SRCDIR = ROOT / "pipeline/snapshots", ROOT / "pipeline/sources"
DAY = os.environ.get("DT_DAY") or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
BUFFER_M = 500
UA = {"User-Agent": "digital-twin-pisa-T03/0.1 (prototipo; lettura pubblica)"}
OP = "EPSG:7791"

# --- AOI: Z2 (ZONE.json) + buffer 500 m, in EPSG:7791 (E,N) e in lon/lat (S,W,N,E) per i servizi
_to_en = Transformer.from_crs(6706, 7791, always_xy=True)   # lon/lat trattati come RDN2008 geografico (ADR-T02 p.4)
_to_ll = Transformer.from_crs(7791, 6706, always_xy=True)
def _bounds(pts): xs, ys = zip(*pts); return min(xs), min(ys), max(xs), max(ys)
def aoi():
    s, w, n, e = json.load(open(ROOT / "docs/audit/ZONE.json"))["zone"]["Z2"]["bbox"]
    z2 = _bounds([_to_en.transform(x, y) for x in (w, e) for y in (s, n)])
    b = (z2[0] - BUFFER_M, z2[1] - BUFFER_M, z2[2] + BUFFER_M, z2[3] + BUFFER_M)
    ll = _bounds([_to_ll.transform(x, y) for x in (b[0], b[2]) for y in (b[1], b[3])])
    return {"aoi_id": "aoi_z2", "buffer_m": BUFFER_M, "z2_ll_SWNE": [s, w, n, e],
            "z2_en": [round(v, 2) for v in z2], "buf_en": [round(v, 2) for v in b],
            "buf_ll_SWNE": [ll[1], ll[0], ll[3], ll[2]]}
AOI = aoi()
def to_en(lon, lat): return _to_en.transform(lon, lat)

def sha256(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(chunk): h.update(b)
    return h.hexdigest()

def now(): return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def rawdir(slug): d = RAW / slug / DAY; d.mkdir(parents=True, exist_ok=True); return d

def get(url, tries=4, params=None, check=None, timeout=180):
    """GET con retry. 'check(resp)' alza ValueError se la risposta e' un errore con HTTP 200."""
    err = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            if check: check(r)
            return r
        except Exception as ex:
            err = ex; time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")

def download(url, dest, tries=4):
    """File grande: stream su .part con ripresa (Range). Salta se il file c'e' gia' ed e' completo."""
    dest = pathlib.Path(dest)
    head = requests.head(url, headers=UA, allow_redirects=True, timeout=60)
    size = int(head.headers.get("Content-Length", 0))
    if dest.exists() and (not size or dest.stat().st_size == size): return dest
    part = dest.with_suffix(dest.suffix + ".part")
    err = None
    for i in range(tries):
        try:
            have = part.stat().st_size if part.exists() else 0
            h = dict(UA, **({"Range": f"bytes={have}-"} if have else {}))
            with requests.get(url, headers=h, stream=True, timeout=120) as r:
                if r.status_code == 416: have = size
                else:
                    r.raise_for_status()
                    if r.status_code == 200: have = 0
                    with open(part, "ab" if have else "wb") as f:
                        for c in r.iter_content(1 << 20): f.write(c)
            if size and part.stat().st_size != size: raise IOError(f"troncato {part.stat().st_size}/{size}")
            part.rename(dest); return dest
        except Exception as ex:
            err = ex; time.sleep(5 * (i + 1))
    raise RuntimeError(f"{url}: {err}")

def files_sha(files, d):
    """Snapshot multi-file: elenco 'sha256  nome' salvato in files.sha256; lo sha256 dello snapshot e' quello dell'elenco."""
    lines = [f"{sha256(f)}  {pathlib.Path(f).name}" for f in sorted(files)]
    p = pathlib.Path(d) / "files.sha256"; p.write_text("\n".join(lines) + "\n")
    return p, sum(pathlib.Path(f).stat().st_size for f in files)

def _snaps(source_id):
    out = []
    for p in sorted(SNAP.glob("snp_*.json")):
        s = json.load(open(p))
        if s["source_id"] == source_id: out.append(s)
    return out

def record(source_id, slug, fn):
    """Esegue fn() -> dict con url, file (lista) o un solo file, media_type, content_period, license_state, ...
    Se fn fallisce: snapshot 'failed' con previous_snapshot_id = ultimo valido (che resta intatto)."""
    SNAP.mkdir(parents=True, exist_ok=True)
    sid = f"snp_{slug}_{DAY}"
    ok_prev = [s for s in _snaps(source_id) if s["status"] == "ok" and s["snapshot_id"] != sid]
    try:
        r = fn()
        files = r.pop("files")
        d = rawdir(slug)
        multi = r.pop("multi", False)
        if len(files) == 1 and not multi:
            f = files[0]; sh, by = sha256(f), pathlib.Path(f).stat().st_size
            lp = str(pathlib.Path(f).relative_to(ROOT))
        else:
            p, by = files_sha(files, d); sh = sha256(p); lp = str(d.relative_to(ROOT)) + "/"
        snap = {"snapshot_id": sid, "source_id": source_id, "retrieved_at": r.pop("retrieved_at", None) or dt.datetime.fromtimestamp(max(pathlib.Path(f).stat().st_mtime for f in files), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bytes": by, "sha256": sh, "local_path": lp, "status": "ok", "stored": False, **r}
    except Exception as ex:
        if (SNAP / f"{sid}.json").exists() and json.load(open(SNAP / f"{sid}.json"))["status"] == "ok":
            sid = f"snp_{slug}_{DAY}_01"
        snap = {"snapshot_id": sid, "source_id": source_id, "retrieved_at": now(), "url": (__import__("re").search(r"https?://[^\s:]+(?::[0-9]+)?[^\s]*?(?=: |$)", str(ex)) or [None])[0] or "https://non.disponibile.invalid/",
                "status": "failed", "error": str(ex)[:500]}
        if ok_prev: snap["previous_snapshot_id"] = ok_prev[-1]["snapshot_id"]
        else:   # schema: failed richiede previous_snapshot_id; senza uno snapshot valido precedente il fallimento va solo nel registro
            fl = SNAP / "_fallimenti_senza_precedente.json"
            cur = json.load(open(fl)) if fl.exists() else []
            cur.append(snap); json.dump(cur, open(fl, "w"), indent=1, ensure_ascii=False)
            print(f"FALLITO {source_id}: {ex}"); return snap
    json.dump(snap, open(SNAP / f"{snap['snapshot_id']}.json", "w"), indent=1, ensure_ascii=False)
    print(snap["status"].upper(), snap["snapshot_id"], snap.get("bytes", ""), snap.get("error", ""))
    return snap
