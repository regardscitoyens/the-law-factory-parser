#!/bin/bash

TMPDIR=/tmp/lafabrique_blame

mkdir -p $TMPDIR

cd $TMPDIR

curl -q http://www.lafabriquedelaloi.fr/api/  | sed 's/.*\/">//' | sed 's/.<.*//' | grep ^p | sed 's|^|git clone http://git.lafabriquedelaloi.fr/parlement/|' | sed 's/$/.git/' | sh

ls -d */ | while read dir ; do 
	cd $dir ; 
	find * -type f | grep 'txt$' | sed 's/^/git blame "/' | sed 's/$/"/' | sh | sed 's/^[^(]*(//' | awk '{print $1}' ; 
	cd - ; 
done | grep -v $TMPDIR > blame.txt

sort blame.txt | uniq -c | sed 's/Commission/CMP/'
