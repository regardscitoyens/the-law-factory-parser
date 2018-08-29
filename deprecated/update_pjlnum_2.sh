#!/bin/bash

cd /home/roux/the-law-factory-parser

# njoyard: variables deplacees avant la verif mutex (sinon $loi == '')
datadir=/home/roux/the-law-factory-parser/data/pjl15-republique_numerique
step="04_1èrelecture_senat_commission/"
loi="20152016-325"
lockfile="/tmp/currently_loading_amendments_$loi"

if test -e "$lockfile"; then
  exit
fi
touch "$lockfile"

mkdir -p "$datadir/procedure/$step/amendements"

function download {
  if ! curl -sLI $1 | grep " 404" > /dev/null; then
    curl -sL $1
  fi
  echo
}

cd scripts/collectdata/
download "http://www.nossenateurs.fr/amendements/$loi/csv?$$" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.senat.fr%2Fleg%2Fpjl15-325.html csv > "$datadir/procedure/$step/amendements/amendements.csv"
if grep [a-z] "$datadir/procedure/$step/amendements/amendements.csv" > /dev/null; then
  download "http://www.nossenateurs.fr/amendements/$loi/json?$$" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.senat.fr%2Fleg%2Fpjl15-325.html json > /tmp/amendements.json
  if grep [a-z] /tmp/amendements.json > /dev/null && diff /tmp/amendements.json "$datadir/procedure/$step/amendements/amendements.json" | grep [a-z] > /dev/null ; then
    mv -f /tmp/amendements.json "$datadir/procedure/$step/amendements/amendements.json"
    cd /home/roux/the-law-factory-parser.rens/scripts/vizudata
    python prepare_amendements.py $datadir
  fi
else
  rm "$datadir/procedure/$step/amendements/amendements.csv"
fi

rm -f "$lockfile"
