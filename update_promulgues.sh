#!/bin/bash

cd $(dirname $0)
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
workon lawfactory

DATADIR=data

senapy-cli doslegs_urls --min-year=$((`date +%Y`)) | python parse_many.py $DATADIR --only-promulgated --quiet

# Update RGPD
python parse_one.py pjl17-296

echo
python generate_dossiers_csv.py $DATADIR
python tools/assemble_procedures.py $DATADIR

echo
#python tools/make_metrics_csv.py $DATADIR --quiet

python tools/steps_as_dot.py $DATADIR | dot -Tsvg > $DATADIR/steps.svg
python tools/steps_as_dot.py $DATADIR | dot -Tpng > $DATADIR/steps.png
python tools/steps_as_dot.py $DATADIR 1 | dot -Tsvg > $DATADIR/steps-detailed.svg
python tools/steps_as_dot.py $DATADIR 1 | dot -Tpng > $DATADIR/steps-detailed.png

