#!/bin/bash

url=$1
datadir=$2

cd collectdata

mkdir -p "$datadir/.tmp"

perl parse_dossier.pl $url | perl correct_from_dossieran.pl > $datadir/.tmp/dossier.csv

if ! cat  $datadir/.tmp/dossier.csv | perl check_dossier.pl "$url($datadir/.tmp/dossier.csv)" ; then
    echo "ERR: Errors in dossier.csv :(";
    rm $datadir/.tmp/dossier.csv
    exit 1;
fi

bash generate_data.sh $datadir/.tmp/dossier.csv $datadir || exit 1

perl reorder_interventions_and_correct_procedure.pl "$datadir/procedure"
python procedure2json.py "$datadir/procedure/procedure.csv" > "$datadir/procedure/procedure.json"
