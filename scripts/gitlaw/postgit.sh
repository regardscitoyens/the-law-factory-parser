#!/bin/bash

MYDIR=$(echo $0 | sed 's|[^/]*$||')"./"

ls -d data/*/ | sed 's/data.//' | sed 's|/||' | grep ^p | while read dossier ; do 
file="data/"$dossier"/procedure/procedure.csv";  
if test -e $file ; then 
    head -n 1 $file | iconv -f UTF8 -t ISO88591 | sed 's/"//g' | awk -F ';' '{print "UPDATE projects SET created_at = \""$15" 00:00:00\",  name = \""$3"\" WHERE path = \""$6"\";"}'; 
    echo "SELECT e.id FROM events e, projects p WHERE p.path = '$dossier' and p.id = e.project_id ORDER BY e.id" | mysql -u gitlab -pGitLAB gitlab | grep '[0-9]' | perl -e 'open(FILE, "'$file'"); @procedure = <FILE>; $i = 0; while (<STDIN>) {chomp ; $i++ if ($i && $procedure[$i] =~ /;depot;/); $procedure[$i] =~ /;([^;]*);$/; print "UPDATE events SET created_at = \"$1\" WHERE id = $_;\n";$i++;}'
fi ; 
done  | mysql -u $MYSQL_USER -p$MYSQL_PASS gitlab
