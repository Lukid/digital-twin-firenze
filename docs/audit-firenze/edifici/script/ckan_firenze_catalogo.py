"""Scarica titoli e descrizioni di tutti i dataset del Comune di Firenze su dati.toscana.it e cerca quelli su edifici, quote, verde."""
import json, urllib.request, urllib.parse, re, sys
out=[]; start=0
while True:
    u="https://dati.toscana.it/api/3/action/package_search?"+urllib.parse.urlencode({"fq":"organization:comune-di-firenze","rows":500,"start":start})
    r=json.load(urllib.request.urlopen(u,timeout=120))["result"]
    for p in r["results"]:
        out.append({"id":p["name"],"title":p["title"],"notes":(p.get("notes") or "")[:300],"license":p.get("license_id"),"modified":p.get("metadata_modified","")[:10],
                    "res":[(x.get("format"),x.get("url")) for x in p["resources"]]})
    start+=500
    if start>=r["count"]: break
json.dump(out,open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"../campioni/ckan_firenze_catalogo.json"),"w"),ensure_ascii=False)
print(len(out),"dataset")
pat=re.compile(sys.argv[1] if len(sys.argv)>1 else r"edific|volum|cassone|costruz|fabbric|portic|altezz|albero|alberi|vegetaz|chiom|lidar|dsm|dtm|mdt|mds|quot|escapos|tetto|copertur",re.I)
for d in out:
    if pat.search(d["title"]): print(d["id"][:38],"|",d["title"],"|",d["license"],"|",d["modified"])
