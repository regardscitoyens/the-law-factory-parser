#!/bin/bash

URLID=$1
if ! test "$URLID"; then 
        echo "USAGE: $0 SENAT_URL"
        printf "\t SENAT_URL: senat.fr url describing the legislative process for the bill\n"
	exit 1;
fi

if ! echo $URLID | grep '^http://www.senat.fr/dossier-legislatif/\S\+.html' > /dev/null ; then
  if echo $URLID | grep '^p[pj][rl][0-9][0-9]-[0-9]\+' > /dev/null ; then
    URLID="http://www.senat.fr/dossier-legislatif/$URLID.html"
  else
	echo "$URLID is not a senat.fr url describing the legislative process of the bill";
	exit 2;
  fi
fi

datadir=$(pwd)/data/$(echo $URLID | sed 's/.*dossier-legislatif.//' | sed 's/.html$//');

mkdir -p $datadir

cd scripts

bash generate_collectdata.sh $URLID $datadir && bash generate_vizudata.sh $datadir && cd $datadir &&  zip -qr procedure.zip procedure/ && cd - 
exit $?
