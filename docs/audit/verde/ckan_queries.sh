#!/bin/bash
# Query CKAN registrate con conteggio (anche zero). Output: campioni/ckan_<portale>_<n>.json e campioni/ckan_log.tsv
cd "$(dirname "$0")"; : > campioni/ckan_log.tsv
i=0
for P in "https://dati.toscana.it/api/3/action" "https://www.dati.gov.it/opendata/api/3/action"; do
 for Q in "alberi" "albero" "alberate" "alberature" "censimento arboreo" "patrimonio arboreo" "verde urbano" "verde pubblico" "chiome" "tree cover" "copertura arborea" "uso del suolo" "uso suolo" "LiDAR" "canopy" "Pisa alberi" "Pisa verde" "Pisa alberature" "comune di Pisa verde pubblico"; do
  i=$((i+1)); f=campioni/ckan_$i.json
  curl -s -m 60 -G "$P/package_search" --data-urlencode "q=$Q" --data-urlencode "rows=20" -o $f
  n=$(python3 -c "import json;d=json.load(open('$f'));print(d['result']['count'] if d.get('success') else 'ERR')" 2>/dev/null || echo ERR)
  printf "%s\t%s\t%s\t%s\n" "$i" "$P" "$Q" "$n" >> campioni/ckan_log.tsv
 done
done
cat campioni/ckan_log.tsv
