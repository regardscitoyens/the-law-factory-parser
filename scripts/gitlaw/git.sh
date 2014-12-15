#!/bin/bash

MYDIR=$(echo $0 | sed 's|[^/]*$||')"./"

if ! test -e $MYDIR"config.inc"; then
echo "ERROR "$MYDIR"config.inc missing";
exit 1;
fi
. $MYDIR"config.inc"

BILL=$1
mkdir $BILL
cd $BILL
git init

wget -q "http://www.lafabriquedelaloi.fr/api/"$BILL"/procedure.zip"
unzip -q procedure.zip
rm procedure.zip
mv procedure .procedure
GITLAB_GROUP=$($GITLAB group list | grep -B 1 parlement | head -n 1 | sed 's/.* //')

find . -name 'A*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/A|/Article_|')'"' ; done |sh
find . -name 'SS*' -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/SS|/SousSection_|')'"' ; done |sh
find . -name 'S*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/S|/Section_|')'"' ; done |sh
find . -name 'C*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/C|/Chapitre_|')'"' ; done |sh
find . -name 'T*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/T|/Titre_|')'"' ; done |sh
find . -name 'L*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/L|/Livre_|')'"' ; done |sh
find . -name 'V*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/V|/Volume_|')'"' ; done |sh

echo $GITLAB project create $(head -n 1 .procedure/procedure.csv  | awk -F ';' '{print " --description=\""$2"\" --name="$6}') --namespace-id=$GITLAB_GROUP --public=true | sh
sleep 2
touch /tmp/ChangeLog
cat .procedure/procedure.csv | while read line; do
  MSG=$(echo $line | awk -F ';' '{if ($8 == 1) print "Dépot du texte"; if ($8 != 1 && $11 != "depot" && $7 != "XX") print "Travaux en "$11", "$9;}'); 
  AUTEUR=$(echo $line | awk -F ';' '{if ($8 == 1 && $6 ~ /pjl/) print "gouv"; else print $10;}');
  ID=$(echo $line | awk -F ';' '{print $7}')
  DATE=$(echo $line | awk -F ';' '{print $14}')
  HDATE=$(date --date="$DATE" -R);

  echo ".procedure/"$ID"*/texte";
  if test -e .procedure/$ID*/texte ; then 
    rm -rf *
    cp -r .procedure/$ID*/texte texte
    echo $line | awk -F ';' '{print $2}' > texte/titre.txt

    find texte -name *json -exec rm '{}' ';'
    find texte -name '*alineas' | sed 's/\(.*\)/mv "\1" "\1"/' | sed 's|[^/]*$|article.txt"|' | sh
    find texte -name 'article.txt' | while read dir; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/article||')'"'; done | sh
    find texte -name '*titre' | sed 's/\(.*\)/mv "\1" "\1"/' | sed 's|[^/]*$|titre.txt"|' | sh
    find texte -size 0 -exec rm '{}' ';'

    if test "$AUTEUR" = "assemblee"; then
	export GIT_AUTHOR_NAME="Assemblée nationale"
        export GIT_AUTHOR_EMAIL="contact@assemblee-nationale.fr"
	GITUSER="assemblee"
    else if test "$AUTEUR" = "senat"; then
	export GIT_AUTHOR_NAME="Sénat"
        export GIT_AUTHOR_EMAIL="contact@senat.fr"
	GITUSER="senat"
    else if test "$AUTEUR" = "CMP"; then
	export GIT_AUTHOR_NAME="Commission mixte paritaire"
        export GIT_AUTHOR_EMAIL="contact@parlement.fr"
	GITUSER="cmp"
    else if test "$AUTEUR" = "gouv"; then
	export GIT_AUTHOR_NAME="gouvernement"
        export GIT_AUTHOR_EMAIL="contact@pm.gouv.fr"
	GITUSER="gouv"
    else
	echo "ERROR: Wrong autheur '$AUTEUR'"
    fi; fi; fi; fi;

    echo "* $DATE - $GIT_AUTHOR_NAME" > /tmp/modif.txt
    echo "  $MSG" >> /tmp/modif.txt
    echo >> /tmp/modif.txt

    cat /tmp/modif.txt /tmp/ChangeLog > texte/ChangeLog
    cp texte/ChangeLog /tmp/

    export GIT_COMMITER_NAME="$GIT_AUTHOR_NAME"
    git config --local user.name "$GIT_AUTHOR_NAME"
    export GIT_COMMITER_EMAIL="$GIT_AUTHOR_EMAIL"
    git config --local user.email "$GIT_AUTHOR_EMAIL"

    mv texte/* .
    rmdir texte

    find * -type f -exec git add '{}' ';'
    git status | grep supp | sed 's/.*: */git rm "/' | sed 's/$/"/' | sh

    git commit -m "$MSG" --date "$HDATE";
    git remote remove origin 
    git remote add origin "http://"$GITUSER":"$GITPASSWD"@git.lafabriquedelaloi.fr/parlement/"$BILL".git"
    git push -u origin master
  fi
done

cd -
