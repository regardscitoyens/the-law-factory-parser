#!/bin/bash

MYDIR=$(echo $0 | sed 's|[^/]*$||')"./"
. $MYDIR"config.inc"

EXTRA=cat
if test "$1"; then
EXTRA="grep $1 ";
fi

ls -d data/*/ | sed 's/data.//' | sed 's|/||' | grep ^p | $EXTRA |
  while read dossier ; do
    file="data/"$dossier"/procedure/procedure.csv";
    if test -e $file ; then
         head -n 1 $file | iconv -f UTF8 -t ISO88591 | sed 's/"//g' | awk -F ';' '{print "UPDATE projects SET created_at = \""$15" 00:00:00\",  name = \"'$dossier'\" WHERE path = \""$6"\";"}'; 
         echo "SELECT e.id FROM events e, projects p WHERE p.path = '$dossier' and p.id = e.project_id ORDER BY e.id" | mysql -u $MYSQL_USER -p$MYSQL_PASS gitlab | grep '[0-9]' | perl -e 'open(FILE, "'$file'"); @procedure = <FILE>; $i = -1; while (<STDIN>) {chomp ; $i++ ; $i++ if ($i != 0 && $procedure[$i] =~ /;depot;/); $procedure[$i] =~ /;([^;]*);[^;]*$/; print "UPDATE events SET created_at = \"$1\" WHERE id = $_;\n";}'
    fi ;
done  | mysql -u $MYSQL_USER -p$MYSQL_PASS gitlab
