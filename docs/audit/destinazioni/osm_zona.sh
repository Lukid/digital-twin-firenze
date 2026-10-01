#!/bin/bash
# uso: osm_zona.sh Z1 lat lon raggio endpoint outfile
Z=$1; LA=$2; LO=$3; R=$4; EP=$5; OUT=$6
cat > ${TMPDIR:-/tmp}/osm_$Z.ql <<Q
[out:json][timeout:60];
(
nwr["amenity"~"^(school|university|college|kindergarten)\$"](around:$R,$LA,$LO);
nwr["building"~"^(school|university|college|kindergarten)\$"](around:$R,$LA,$LO);
node["entrance"](around:$R,$LA,$LO);
node["barrier"~"^(gate|entrance)\$"](around:$R,$LA,$LO);
nwr["public_transport"~"^(platform|stop_position)\$"](around:$R,$LA,$LO);
nwr["highway"="bus_stop"](around:$R,$LA,$LO);
);
out center bb tags;
Q
curl -sS -m 90 -A "digital-twin-pisa-audit/0.1 (ai@netseven.it)" --data-urlencode "data@${TMPDIR:-/tmp}/osm_$Z.ql" "$EP" -o "$OUT" -w "$Z $EP %{http_code} %{size_download}\n"
