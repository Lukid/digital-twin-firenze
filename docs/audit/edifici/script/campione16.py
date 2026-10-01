"""16 edifici (4 per zona, seme fisso) con uv_av, altezza da DSM2021 (p90 - uv_qs) e piani/altezza OSM se abbinati."""
import csv, random
random.seed(7)
nd=list(csv.DictReader(open("campioni/ndsm_confronto.csv"))); os_={}
for r in csv.DictReader(open("campioni/osm_vs_uv.csv")): os_[r["uv_id"]]=r
out=[]
for z in ("Z1","Z2","Z3","Z4"):
    c=[r for r in nd if r["zona"]==z and float(r["area"])>=100]
    # preferisce edifici con OSM abbinato, poi completa a caso
    a=[r for r in c if r["uv_id"] in os_]; b=[r for r in c if r["uv_id"] not in os_]
    random.shuffle(a); random.shuffle(b); pick=(a[:2]+b)[:4] if len(a)>=2 else (a+b)[:4]
    for r in pick:
        o=os_.get(r["uv_id"],{})
        out.append(dict(zona=z,uv_id=r["uv_id"],area_m2=r["area"],uv_av_m=r["uv_av"],dsm_p90_meno_suolo_m=round(float(r["dsm_p90"])-float(r["uv_qs"]),2),
            osm_levels=o.get("osm_levels",""),osm_height=o.get("osm_height","")))
w=csv.DictWriter(open("campioni/campione_coerenza.csv","w",newline=""),out[0].keys()); w.writeheader(); w.writerows(out)
for r in out: print(*r.values(),sep="\t")
