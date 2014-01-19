#!/bin/bash

url=$1
datadir=$2

cd collectdata

mkdir -p "$datadir/.tmp"

perl parse_dossier.pl $url > $datadir/.tmp/dossier.csv

bash generate_data.sh $datadir/.tmp/dossier.csv $datadir
