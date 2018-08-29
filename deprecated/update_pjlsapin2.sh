#!/bin/bash

PARSER=/home/njoyard/the-law-factory-parser
LOI=pjl15-transparence_lutte_corruption_economie

LOCK=/tmp/njoyard-update-$LOI

[ -f $LOCK ] && exit
touch $LOCK

datadir=$PARSER/data/$LOI

cd $PARSER/scripts/collectdata

echo "1. generate_data"
bash generate_data.sh $datadir/.tmp/dossier.csv $datadir 1
echo "2. reorder_interventions"
perl reorder_interventions_and_correct_procedure.pl "$datadir/procedure"
echo "3. procedure2json"
python procedure2json.py "$datadir/procedure/procedure.csv" > "$datadir/procedure/procedure.json"

cd $PARSER/scripts
echo "4. generate_vizudata"
bash generate_vizudata.sh $datadir

rm $LOCK

