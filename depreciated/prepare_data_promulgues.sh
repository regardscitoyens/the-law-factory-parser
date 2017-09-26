#!/bin/bash

if [ -z "$1" ]; then
  rm -rf data/.cache
  mkdir -p data/.cache
  curl -sL http://data.senat.fr/data/dosleg/dossiers-legislatifs.csv |
   iconv -f "iso-8859-15" -t "utf-8" > data/.cache/list_dossiers_senat.csv
  head -n 1 data/.cache/list_dossiers_senat.csv |
   sed 's/^/id;/' | sed 's/$/;total_amendements;total_mots;short_title/' > data/dossiers_promulgues.csv
fi

cat data/.cache/list_dossiers_senat.csv      |
#grep ';"promulgu.*20\(0[8-9]\|1[0-9]\)";'    |
 grep ';"promulgu.*20\(1[4-9]\)";'  | grep -vi "loi de finance" |
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
    nb_mots=$(cat data/$id/viz/interventions.json | sed 's/"total_mots"/\n"total_mots"/g' | grep '"total_mots"' | sed 's/"total_mots": //' | sed 's/, "total.*$//' | paste -s -d+ | bc)
    if [ -z "$nb_mots" ]; then
      nb_mots=0
    fi
    short_title=$(cat data/$id/viz/procedure.json | sed 's/^.*"short_title": "//' | sed 's/"[,}\s].*$//')
    echo "$id;$line;$nb_amdts;$nb_mots;$short_title" >> data/dossiers_promulgues.csv
  else
    rm -rf "data/$id"
  fi
  echo
 done

python scripts/vizudata/assemble_procedures.py $(pwd) 50

rm data/dossiers/*
for file in $(ls data/dossiers_*); do
  outfile=$(echo $file | sed 's#dossiers#dossiers/lafabriquedelaloi.fr-dossiers#')
  ln -s "$(pwd)/$file" "$(pwd)/$outfile"
done

