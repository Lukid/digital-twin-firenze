"""Legge lo zip remoto con richieste Range (niente download completo): elenco, estrazione di singoli file."""
import io, urllib.request, zipfile
class HttpFile(io.RawIOBase):
    def __init__(s,url): s.url=url; s.pos=0; s.size=int(urllib.request.urlopen(urllib.request.Request(url,method="HEAD"),timeout=60).headers["Content-Length"]); s.n=0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s,o,w=0): s.pos={0:o,1:s.pos+o,2:s.size+o}[w]; return s.pos
    def readinto(s,b):
        n=min(len(b),s.size-s.pos)
        if n<=0: return 0
        r=urllib.request.Request(s.url,headers={"Range":f"bytes={s.pos}-{s.pos+n-1}"}); d=urllib.request.urlopen(r,timeout=120).read(); s.n+=1
        b[:len(d)]=d; s.pos+=len(d); return len(d)
def apri(url): return zipfile.ZipFile(io.BufferedReader(HttpFile(url),buffer_size=1<<20))

def leggi(z,info):
    """Estrae un file; supporta anche Deflate64 (metodo 9) tramite inflate64 (installato con py7zr)."""
    if info.compress_type!=9: return z.read(info)
    import struct, inflate64
    f=z.fp; f.seek(info.header_offset); h=f.read(30); nl,el=struct.unpack("<HH",h[26:30]); f.seek(info.header_offset+30+nl+el)
    raw=f.read(info.compress_size); out=inflate64.Inflater().inflate(raw)
    assert len(out)==info.file_size,(len(out),info.file_size); return out
