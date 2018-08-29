#!/bin/bash

cd /home/roux/the-law-factory-parser

# njoyard: variables deplacees avant la verif mutex (sinon $loi == '')
datadir=/home/roux/the-law-factory-parser/data/pjl15-republique_numerique
step="05_1èrelecture_senat_hemicycle"
loi="20152016-535"
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

nocache=$(date +%Y%m%d%H%M%S)

cd scripts/collectdata/
download "http://www.nossenateurs.fr/amendements/$loi/csv?$nocache" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.senat.fr%2Fleg%2Fpjl15-535.html csv > "$datadir/procedure/$step/amendements/amendements.csv"
if grep [a-z] "$datadir/procedure/$step/amendements/amendements.csv" > /dev/null; then
  download "http://www.nossenateurs.fr/amendements/$loi/json?$nocache" | perl sort_amendements.pl $datadir/.tmp/json/http%3A%2F%2Fwww.senat.fr%2Fleg%2Fpjl15-535.html json > /tmp/amendements.json
  if grep [a-z] /tmp/amendements.json > /dev/null && diff /tmp/amendements.json "$datadir/procedure/$step/amendements/amendements.json" | grep [a-z] > /dev/null ; then
    mv -f /tmp/amendements.json "$datadir/procedure/$step/amendements/amendements.json"
    cd /home/roux/the-law-factory-parser.rens/scripts/vizudata
    python /home/roux/the-law-factory-parser/scripts/collectdata/procedure2json.py "$datadir/procedure/procedure.csv" > "$datadir/procedure/procedure.json"
    python prepare_amendements.py $datadir
    python update_procedure.py $datadir > $datadir/viz/procedure.json 2> /dev/null
  fi
else
  rm "$datadir/procedure/$step/amendements/amendements.csv"
fi

rm -f "$lockfile"
