#!/bin/bash
# OSM per i riquadri canonici di ../ZONE.json (S,W,N,E), con ritentativi
cd "$(dirname "$0")/campioni"
python3 -c "
import json
for k,v in json.load(open('../../ZONE.json'))['zone'].items(): print(k,*v['bbox'])" > "${TMPDIR:-/tmp}/zc.txt"
while read k s w n e; do
 B="$s,$w,$n,$e"
 cat > "${TMPDIR:-/tmp}/c_$k.ql" <<Q
[out:json][timeout:60];
(
nwr["amenity"~"^(school|university|college|kindergarten)\$"]($B);
nwr["building"~"^(school|university|college|kindergarten)\$"]($B);
node["entrance"]($B);
);
out center bb tags;
Q
 for i in 1 2 3 4 5; do
  curl -sS -m 90 -A "digital-twin-pisa-audit/0.1" --data-urlencode "data@${TMPDIR:-/tmp}/c_$k.ql" https://overpass-api.de/api/interpreter -o osmc_$k.tmp
  python3 -c "import json;json.load(open('osmc_$k.tmp'))" 2>/dev/null && { mv osmc_$k.tmp osmc_$k.json; break; }; sleep 20
 done; sleep 3
done < "${TMPDIR:-/tmp}/zc.txt"
rm -f osmc_*.tmp
