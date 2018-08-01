#!/bin/bash

DATADIR=$1
if [ -z "$DATADIR"]; then
  DATADIR=data
fi


echo PARSED: $(ls $DATADIR/p*/viz/procedure.json | wc -l) "/ "$(ls data/p*/viz/procedure.json | wc -l)
echo ERROR: $(ls $DATADIR/logs/ | wc -l) "/ "$(ls data/logs/ | wc -l)
echo
tail -n 1 $DATADIR/logs/* | grep -v '^==>' | grep . | sort | uniq --count | sort -rn
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
