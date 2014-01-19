#!/bin/bash

url=$1
datadir=$2

cd collectdata

perl parse_dossier.pl $url > $datadir/dossier.csv

bash generate_data.sh $datadir/dossier.csv $datadir
