#!/bin/bash

datadir=$(pwd)/data/pjl14-psi
source /usr/local/bin/virtualenvwrapper.sh
workon lawfactory

echo "updating OpenData Amdmts..."
cd data/pjl14-psi/procedure/02_1èrelecture_assemblee_hemicycle
for f in json csv xml; do
  curl -sL http://nosdeputes.fr/14/amendements/3090/$f?$(date +%s) |
   perl ../../../../scripts/collectdata/sort_amendements.pl ../../.tmp/json/articles_antelaststep.json $f > amendements/amendements.$f
done 

echo "rebuild viz data..."
cd ../../../../scripts
cd collectdata/
perl reorder_interventions_and_correct_procedure.pl "$datadir/procedure" &&
 python procedure2json.py "$datadir/procedure/procedure.csv" > "$datadir/procedure/procedure.json"
cd ..
bash generate_vizudata.sh $datadir &&
 bash post_generate.sh $datadir

echo "uploading..."
cd ..
scp -r data/pjl14-psi/ ../the-law-factory-parser/data/ > /dev/null

echo "done."
