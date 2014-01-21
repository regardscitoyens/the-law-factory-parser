#!/bin/bash

mkdir -p data/.cache

curl -sL http://data.senat.fr/data/dosleg/dossiers-legislatifs.csv |
 iconv -f "iso-8859-15" -t "utf-8" > data/.cache/list_dossiers_senat.csv

head -n 1 data/.cache/list_dossiers_senat.csv > data/dossiers_promulgues.csv
cat data/.cache/list_dossiers_senat.csv     |
#grep '/20\(0[8-9]\|1[0-9]\)";.*;"promulgu' |
 grep '/20\(50[8-9]\|1[3-9]\)";.*;"promulgu' |
 while read line; do
  url=$(echo $line | sed 's/^.*";"\(http[^"]\+\)";.*$/\1/')
  id=$(echo $url | sed 's/.*dossier-legislatif.//' | sed 's/.html$//');
  echo "TRYING $id on $url"
  bash generate_data_from_senat_url.sh "$url"
  if [ $? -eq 0 ]; then
    echo " -> GOOD, saving it"
    echo "$id;$line" >> data/dossiers_promulgues.csv
  fi
 done
