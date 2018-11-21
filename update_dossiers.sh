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
head -n 2 data/logs-encours/* | grep '^http' > $TMPDIR/urls_ERRORS
sort -u $TMPDIR/* | tlfp-parse-many $DATADIR --quiet
rm -rf $TMPDIR

echo
python tlfp/generate_dossiers_csv.py $DATADIR
python tlfp/tools/assemble_procedures.py $DATADIR > /dev/null

echo
echo "Make metrics.csv..."
python tlfp/tools/make_metrics_csv.py $DATADIR --quiet

python tlfp/tools/steps_as_dot.py $DATADIR | dot -Tsvg > $DATADIR/stats/steps.svg
python tlfp/tools/steps_as_dot.py $DATADIR | dot -Tpng > $DATADIR/stats/steps.png
python tlfp/tools/steps_as_dot.py $DATADIR 1 | dot -Tsvg > $DATADIR/stats/steps-detailed.svg
python tlfp/tools/steps_as_dot.py $DATADIR 1 | dot -Tpng > $DATADIR/stats/steps-detailed.png

