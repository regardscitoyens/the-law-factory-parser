#!/bin/bash

trap ctrl_c INT
function ctrl_c() {
    exit 1;
}

if [ -z "$1" ]; then
  TODAY=$(date +%Y%m%d)
  DATADIR=data.$TODAY
else
  DATADIR=$1
fi

senapy-cli doslegs_urls | tlfp-parse-many $DATADIR --only-promulgated

echo
echo "Handle non promulgated texts already parsed in data:"
ls data/ | grep '^p' | grep -v '_tmp' | while read id; do
  ls $DATADIR/$id > /dev/null 2>&1          ||
    ls $DATADIR/logs/$id > /dev/null 2>&1   ||
    tlfp-parse $id $DATADIR
done
echo

python tlfp/generate_dossiers_csv.py $DATADIR

python tlfp/tools/assemble_procedures.py $DATADIR

python tlfp/tools/make_metrics_csv.py $DATADIR

python tlfp/tools/steps_as_dot.py $DATADIR | dot -Tsvg > $DATADIR/steps.svg
python tlfp/tools/steps_as_dot.py $DATADIR | dot -Tpng > $DATADIR/steps.png
python tlfp/tools/steps_as_dot.py $DATADIR 1 | dot -Tsvg > $DATADIR/steps-detailed.svg
python tlfp/tools/steps_as_dot.py $DATADIR 1 | dot -Tpng > $DATADIR/steps-detailed.png

for f in .htaccess HEADER.html; do
  cp data/$f $DATADIR/$f
done

echo "Everything finished, data processed in $DATADIR"
echo "A few stats:"
echo

./stats.sh $DATADIR

echo
echo "Deploy built data with:"
echo "mv data data.$TODAY.old && mv $DATADIR data"

