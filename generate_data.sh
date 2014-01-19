#!/bin/bash

if ! test "$1"; then 
        echo "USAGE: $0 SENAT_URL"
        printf "\t SENAT_URL: senat.fr url describing the legislative process for the bill\n"
	exit 1;
fi

if ! echo $1 | grep '^http://www.senat.fr/dossier-legislatif/p[plfj]*[0-9\-]*.html' > /dev/null ; then
	echo "$1 is not a senat.fr url describing the legislative process of the bill";
	exit 2;
fi

cd scripts

datadir=$(echo $1 | sed 's/.*dossier-legislatif.//' | sed 's/.html$//');

mkdir data/$datadir

bash generate_collectdata.sh $1 $datadir
bash generate_vizudata.sh $datadir
