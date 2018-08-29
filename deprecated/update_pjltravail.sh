#!/bin/bash

PARSER=/home/njoyard/the-law-factory-parser
LOI=pjl15-nouvelles_libertes_entreprises_actifs

LOCK=/tmp/njoyard-update-$LOI

[ -f $LOCK ] && exit
touch $LOCK

datadir=$PARSER/data/$LOI

cd $PARSER/scripts/collectdata

bash generate_data.sh $datadir/.tmp/dossier.csv $datadir 1
perl reorder_interventions_and_correct_procedure.pl "$datadir/procedure"
python procedure2json.py "$datadir/procedure/procedure.csv" > "$datadir/procedure/procedure.json"

cd $PARSER/scripts

bash generate_vizudata.sh $datadir

rm $LOCK

