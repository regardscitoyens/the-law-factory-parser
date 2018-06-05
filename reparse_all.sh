#!/bin/bash

TODAY=$(date +%Y%m%d)
DATADIR=data.$TODAY
mkdir -p $DATADIR

senapy-cli doslegs_urls | python tlfp/parse_many.py $DATADIR --only-promulgated

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

echo PARSED: $(ls $DATADIR/p*/viz/procedure.json | wc -l) "/ "$(ls data/p*/viz/procedure.json | wc -l)
echo ERROR: $(ls $DATADIR/logs/ | wc -l) "/ "$(ls data/logs/ | wc -l)
echo
tail -n 1 $DATADIR/logs/* | grep -v '^==>' | grep . | uniq --count | sort -rn
echo
echo "REGRESSIONS:"
ls $DATADIR/logs/ | while read id; do
  ls data/$id > /dev/null 2>&1 && echo "  <-  $id"
done
echo
echo "NEWLY HANDLED:"
ls $DATADIR/ | grep '^p' | grep -v '_tmp' | while read id; do
  ls data/logs/$id > /dev/null 2>&1 && echo "  ->  $id"
done
echo
echo "Deploy built data with:"
echo "mv data data.$TODAY.old && mv $DATADIR data"
