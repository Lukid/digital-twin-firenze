"""LiDAR 2017 (1 m, tessere numerate 800x1000 in UTM32 ETRS89): legge l'intestazione di ogni tessera nello zip remoto, scarica solo quelle che toccano FA o FB."""
import os, sys, struct, zlib, re, json, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE, bbox_m
from zipremoto import apri, leggi
RAW=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../data/raw/fi_audit_20261001/lidar")
SRC={"dtm2017":"https://datigis.comune.fi.it/grid/MDT_LIDAR_2017_ASCII.zip","dsm2017":"https://datigis.comune.fi.it/grid/MDS_LIDAR_2017_ASCII.zip"}
def head(z,i):
    f=z.fp; f.seek(i.header_offset); h=f.read(30); nl,el=struct.unpack("<HH",h[26:30]); f.seek(i.header_offset+30+nl+el); raw=f.read(min(i.compress_size,1500))
    t=(raw if i.compress_type==0 else zlib.decompressobj(-15).decompress(raw)).decode()
    g=lambda k: float(re.search(k+r"\s+(-?[\d,\.]+)",t,re.I)[1].replace(",","."))
    return g("ncols"),g("nrows"),g("xllcorner"),g("yllcorner"),g("cellsize")
bb=[bbox_m(b) for b in ZONE.values()]; log={}
for k,u in SRC.items():
    z=apri(u); os.makedirs(f"{RAW}/{k}",exist_ok=True); n=0
    for i in z.infolist():
        if not i.filename.lower().endswith(".asc"): continue
        nc,nr,x,y,c=head(z,i); x1,y1=x+nc*c,y+nr*c
        if any(x<b[2] and x1>b[0] and y<b[3] and y1>b[1] for b in bb):
            p=f"{RAW}/{k}/{os.path.basename(i.filename)}"
            if not os.path.exists(p): open(p,"wb").write(leggi(z,i))
            log[f"{k}/{os.path.basename(i.filename)}"]=dict(sha256=hashlib.sha256(open(p,"rb").read()).hexdigest(),ncols=nc,nrows=nr,x=x,y=y,cell=c); n+=1
    print(k,n,"tessere scaricate")
json.dump(log,open(f"{RAW}/sha256_2017.json","w"),indent=1)
