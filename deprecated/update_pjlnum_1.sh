#!/bin/bash

cd /home/roux/the-law-factory-parser

if test -e "/tmp/currently_loading_amendments"; then
  exit
fi
touch "/tmp/currently_loading_amendements_$loi"

datadir=/home/roux/the-law-factory-parser/data/pjl15-republique_numerique
step="02_1èrelecture_assemblee_hemicycle"
loi_id="3399"
mkdir -p "$datadir/procedure/$step/amendements"

function download {
  if ! curl -sLI $1 | grep " 404" > /dev/null; then
    curl -sL $1
  fi
  echo
}

cd scripts/collectdata/
download "http://www.nosdeputes.fr/14/amendements/$loi_id/csv?$$" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.assemblee-nationale.fr%2F14%2Fta-commission%2Fr3399-a0.asp csv > "$datadir/procedure/$step/amendements/amendements.csv"
if grep [a-z] "$datadir/procedure/$step/amendements/amendements.csv" > /dev/null; then
  download "http://www.nosdeputes.fr/14/amendements/$loi_id/json?$$" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.assemblee-nationale.fr%2F14%2Fta-commission%2Fr3399-a0.asp json > /tmp/amendements.json
  if grep [a-z] /tmp/amendements.json > /dev/null && diff /tmp/amendements.json "$datadir/procedure/$step/amendements/amendements.json" | grep [a-z] > /dev/null; then
    mv -f /tmp/amendements.json "$datadir/procedure/$step/amendements/amendements.json"
    cd /home/roux/the-law-factory-parser.rens/scripts/vizudata
    python prepare_amendements.py $datadir
  fi
else
  rm "$datadir/procedure/$step/amendements/amendements.csv"
fi

rm -f "/tmp/currently_loading_amendements_$loi"
