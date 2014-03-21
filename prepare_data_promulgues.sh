#!/bin/bash

if [ -z "$1" ]; then
  rm -rf data/.cache
  mkdir -p data/.cache
  curl -sL http://data.senat.fr/data/dosleg/dossiers-legislatifs.csv |
   iconv -f "iso-8859-15" -t "utf-8" > data/.cache/list_dossiers_senat.csv
  head -n 1 data/.cache/list_dossiers_senat.csv | sed 's/^/id;/' > data/dossiers_promulgues.csv
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
    echo "$id;$line" >> data/dossiers_promulgues.csv
  else
    rm -rf "data/$id"
  fi
  echo
 done
