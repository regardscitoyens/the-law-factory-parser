#!/bin/bash

TODAY=$(date +%Y%m%d)
DATADIR=data.$TODAY
mkdir -p $DATADIR

senapy-cli doslegs_urls | python parse_many.py $DATADIR

python generate_dossiers_csv.py $DATADIR

python tools/assemble_procedures.py $DATADIR

python tools/make_metrics_csv.py $DATADIR

python tools/steps_as_dot.py $DATADIR | dot -Tsvg > $DATADIR/steps.svg

for f in .htaccess HEADER.html; do
  cp {data,$DATADIR}/$f
done

mv data data.$TODAY.old
mv $DATADIR data
