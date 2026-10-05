#!/bin/bash
# Overpass sul riquadro "contesto" (S,W,N,E da ../RIQUADRO.json) + Careggi. Dati grandi in data/raw/fi_audit_20261001/.
cd "$(dirname "$0")"; R=../../../data/raw/fi_audit_20261001; mkdir -p $R campioni
B=$(python3 -c "import json;print(','.join(map(str,json.load(open('../RIQUADRO.json'))['contesto']['bbox'])))")
cat > $R/osm_fi.ql <<Q
[out:json][timeout:90];
(
nwr["amenity"~"^(school|university|college|kindergarten)\$"]($B);
nwr["building"~"^(school|university|college|kindergarten)\$"]($B);
node["entrance"]($B);
nwr["public_transport"~"^(platform|stop_position)\$"]($B);
nwr["highway"="bus_stop"]($B);
nwr["railway"="tram_stop"]($B);
);
out geom tags;
Q
cat > $R/osm_careggi.ql <<Q
[out:json][timeout:90];
(nwr["amenity"="hospital"](43.77,11.20,43.82,11.28););
out geom tags;
Q
for n in fi careggi; do
 for i in 1 2 3 4 5; do
  curl -sS -m 120 -A "digital-twin-pisa-audit/0.1 (ai@netseven.it)" --data-urlencode "data@$R/osm_$n.ql" https://overpass-api.de/api/interpreter -o $R/osm_$n.tmp
  python3 -c "import json;json.load(open('$R/osm_$n.tmp'))" 2>/dev/null && { mv $R/osm_$n.tmp $R/osm_$n.json; break; }; sleep 20
 done; sleep 3
done
ls -la $R/osm_*.json
