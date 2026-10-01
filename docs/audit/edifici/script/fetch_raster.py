"""Scarica tile DTM/DSM 1 m dal WMS Geoscopio (GetMap image/tiff) per un riquadro di test in ogni zona (centro zona, 500x500 m)."""
import sys, os, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from zone import ZONE
from pyproj import Transformer
M="https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia"
T=Transformer.from_crs(4326,32632,always_xy=True)
LAY={"dtm":"rt_morfologia.iddtm.1m.irs","dsm":"rt_morfologia.iddsm2021.1m.rt","dtm10":"rt_morfologia.iddtm.10m.rt"}
def get(layer,x0,y0,size,out,fmt="image/tiff"):
    p={"SERVICE":"WMS","VERSION":"1.3.0","REQUEST":"GetMap","LAYERS":LAY[layer],"STYLES":"","CRS":"EPSG:32632","BBOX":f"{x0},{y0},{x0+size},{y0+size}",
       "WIDTH":size,"HEIGHT":size,"FORMAT":fmt}
    d=urllib.request.urlopen(M+"&"+urllib.parse.urlencode(p),timeout=180).read()
    open(out,"wb").write(d); return len(d)
if __name__=="__main__":
    z=sys.argv[1]; size=int(sys.argv[2]) if len(sys.argv)>2 else 500
    s,w,n,e=ZONE[z]; x,y=T.transform((w+e)/2,(s+n)/2); x0=round(x-size/2); y0=round(y-size/2)
    for l in LAY: print(z,l,x0,y0,get(l,x0,y0,size,f"campioni/{l}_{z}_{x0}_{y0}_{size}.tif"))
