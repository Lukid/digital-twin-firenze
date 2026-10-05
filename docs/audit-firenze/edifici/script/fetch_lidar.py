"""Scarica da zip remoti (Range) solo le tessere ASCII che coprono FA e FB: DTM e DSM 2023. Salva in data/raw/fi_audit_20261001/lidar/."""
import os, sys, hashlib, json
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE, tiles
from zipremoto import apri, leggi
RAW=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../data/raw/fi_audit_20261001/lidar")
SRC={"dtm2023":"https://datigis.comune.fi.it/grid/MDT_LIDAR_2023_ASCII.zip","dsm2023":"https://datigis.comune.fi.it/grid/MDS_LIDAR_2023_ASCII.zip"}
need=sorted({t for b in ZONE.values() for t in tiles(b)})
log={}
for k,u in SRC.items():
    os.makedirs(f"{RAW}/{k}",exist_ok=True); z=apri(u); names={i.filename:i for i in z.infolist()}
    for t in need:
        if t not in names: print(k,t,"NON PRESENTE nello zip"); log[f"{k}/{t}"]=None; continue
        p=f"{RAW}/{k}/{t}"
        if not os.path.exists(p) or os.path.getsize(p)==0: open(p,"wb").write(leggi(z,names[t]))
        log[f"{k}/{t}"]=hashlib.sha256(open(p,"rb").read()).hexdigest()
    print(k,"ok",len(need),"tessere richieste")
json.dump(log,open(f"{RAW}/sha256.json","w"),indent=1)
