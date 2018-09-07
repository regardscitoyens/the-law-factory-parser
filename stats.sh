#!/bin/bash

DATADIR=$1
if [ -z "$DATADIR" ]; then
  DATADIR=data
fi


echo PARSED: $(ls $DATADIR/p*/viz/procedure.json | wc -l) "/ "$(ls data/p*/viz/procedure.json | wc -l)
echo ERROR: $(ls $DATADIR/logs/ | wc -l) "/ "$(ls data/logs/ | wc -l)
echo
find $DATADIR/logs/ -type f | while read f; do
  tail -n 2 $f | head -1
done | sort | uniq -c | sort -rn 
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
