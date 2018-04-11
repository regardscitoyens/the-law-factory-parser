#!/bin/bash

TODAY=$(date +%Y%m%d)
DATADIR=data.$TODAY
mkdir -p $DATADIR

senapy-cli doslegs_urls | python parse_many.py $DATADIR

python generate_dossiers_csv.py $DATADIR

python tools/assemble_procedures.py $DATADIR

python tools/make_metrics_csv.py $DATADIR

python tools/steps_as_dot.py $DATADIR | dot -Tsvg > $DATADIR/steps.svg
python tools/steps_as_dot.py $DATADIR | dot -Tpng > $DATADIR/steps.png
python tools/steps_as_dot.py $DATADIR 1 | dot -Tsvg > $DATADIR/steps-detailed.svg
python tools/steps_as_dot.py $DATADIR 1 | dot -Tpng > $DATADIR/steps-detailed.png

for f in .htaccess HEADER.html; do
  cp {data,$DATADIR}/$f
done

mv data data.$TODAY.old
mv $DATADIR data
