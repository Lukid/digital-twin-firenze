#!/bin/bash
# scarica OSM per le quattro zone, con ritentativi (Overpass risponde spesso 504)
cd "$(dirname "$0")/campioni"
python3 - <<'PY' > "${TMPDIR:-/tmp}/zone_args.txt"
import json
z=json.load(open('../zone.json'))
for k in ['Z1','Z2','Z3','Z4']: print(k,z[k]['lat'],z[k]['lon'],z[k]['raggio_m']+250)
PY
while read k la lo r; do
  for i in 1 2 3 4; do
    ../osm_zona.sh $k $la $lo $r https://overpass-api.de/api/interpreter osm_$k.tmp
    python3 -c "import json;json.load(open('osm_$k.tmp'))" 2>/dev/null && { mv osm_$k.tmp osm_$k.json; break; }
    sleep 20
  done
  sleep 3
done < "${TMPDIR:-/tmp}/zone_args.txt"
rm -f osm_*.tmp
