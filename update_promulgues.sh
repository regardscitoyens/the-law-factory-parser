#!/bin/bash


trap ctrl_c INT
function ctrl_c() {
    exit 1;
}

cd $(dirname $0)
source ~/.bash_profile
pyenv activate lafabrique

DATADIR=data

echo "Parsing new promulgated texts..."
senapy-cli doslegs_urls --min-year=$((`date +%Y`)) | tlfp-parse-many $DATADIR --only-promulgated --quiet

echo
echo "Parsing texts in discussion..."
TMPDIR=$(mktemp -d)
anpy-cli doslegs_urls --in-discussion --senate-urls > $TMPDIR/urls_AN
senapy-cli doslegs_urls --in-discussion > $TMPDIR/urls_SENATE
sort -u $TMPDIR/* | tlfp-parse-many $DATADIR --quiet
rm -rf $TMPDIR

echo
python tlfp/generate_dossiers_csv.py $DATADIR
python tlfp/tools/assemble_procedures.py $DATADIR > /dev/null

echo
echo "Make metrics.csv..."
python tools/make_metrics_csv.py $DATADIR --quiet

python tlfp/tools/steps_as_dot.py $DATADIR | dot -Tsvg > $DATADIR/steps.svg
python tlfp/tools/steps_as_dot.py $DATADIR | dot -Tpng > $DATADIR/steps.png
python tlfp/tools/steps_as_dot.py $DATADIR 1 | dot -Tsvg > $DATADIR/steps-detailed.svg
python tlfp/tools/steps_as_dot.py $DATADIR 1 | dot -Tpng > $DATADIR/steps-detailed.png

