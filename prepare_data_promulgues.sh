#!/bin/bash

if [ -z "$1" ]; then
  rm -rf data/.cache
  mkdir -p data/.cache
  curl -sL http://data.senat.fr/data/dosleg/dossiers-legislatifs.csv |
   iconv -f "iso-8859-15" -t "utf-8" > data/.cache/list_dossiers_senat.csv
  head -n 1 data/.cache/list_dossiers_senat.csv |
   sed 's/^/id;/' | sed 's/$/;total_amendements;total_mots/' > data/dossiers_promulgues.csv
fi

cat data/.cache/list_dossiers_senat.csv     |
#grep '/20\(0[8-9]\|1[0-9]\)";.*;"promulgu' |
 grep '/20\(50[8-9]\|1[0-9]\)";.*;"promulgu' |
 while read line; do
  url=$(echo $line | sed 's/^.*";"\(http[^"]\+\)";.*$/\1/')
  id=$(echo $url | sed 's/.*dossier-legislatif.//' | sed 's/.html$//')
  if test -d "data/$id" && grep "^$id;" data/dossiers_promulgues.csv > /dev/null; then
    echo "## Already done $id"
    continue
  fi
  echo "## Working on $url"
  rm -rf "data/$id"
  bash generate_data_from_senat_url.sh "$url"
  if [ $? -eq 0 ]; then
    nb_amdts=$(cat data/$id/viz/amendements_*.json 2> /dev/null | sed 's/"id_api"/\n"id_api"/g' | grep '"id_api"' | wc -l)
    if [ -s data/$id/viz/interventions.json ]; then
      nb_mots=$(cat data/$id/viz/interventions.json | sed 's/"total_mots"/\n"total_mots"/g' | grep '"total_mots"' | sed 's/"total_mots": //' | sed 's/, "total.*$//' | paste -s -d+ | bc)
    else
      nb_mots=0
    fi
    echo "$id;$line;$nb_amdts;$nb_mots" >> data/dossiers_promulgues.csv
  else
    rm -rf "data/$id"
  fi
  echo
 done

python scripts/vizudata/assemble_procedures.py $(pwd) 50
