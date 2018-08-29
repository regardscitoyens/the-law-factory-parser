#!/bin/bash

cd /home/roux/the-law-factory-parser

datadir=/home/roux/the-law-factory-parser/data/pjl15-republique_numerique
step="01_1èrelecture_assemblee_commission"
loi_id="3318"

function download {
  if ! curl -sLI $1 | grep " 404" > /dev/null; then
    curl -sL $1
  fi
  echo
}

cd scripts/collectdata/
download "http://www.nosdeputes.fr/14/amendements/$loi_id/csv?$$" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.assemblee-nationale.fr%2F14%2Fprojets%2Fpl3318.asp csv > "$datadir/procedure/$step/amendements/amendements.csv"
if grep [a-z] "$datadir/procedure/$step/amendements/amendements.csv" > /dev/null; then
  download "http://www.nosdeputes.fr/14/amendements/$loi_id/json?$$" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.assemblee-nationale.fr%2F14%2Fprojets%2Fpl3318.asp json > "$datadir/procedure/$step/amendements/amendements.json"
  ./filter_com_lois.py "$datadir/procedure/$step/amendements/amendements.json"
else
  rm "$datadir/procedure/$step/amendements/amendements.csv"
  rmdir $datadir/procedure/$step/amendements
fi
cd - > /dev/null

cd scripts/vizudata
python prepare_amendements.py $datadir

