#!/bin/bash

if ! test "$1"; then 
	echo "USAGE: $0 DOSSIER_DESC.CSV [DATADIR]"
	printf "\t DOSSIER_DESC.CSV: CSV décrivant un ou plusieurs dossiers parlementaires générés via parse_dosser.pl (de NosSénateurs)\n"
	printf "\t DATADIR: répertoire où vont être mises les données (par defaut data/)"
fi
data=$(if test "$2" ; then echo $2 ; else echo "data" ; fi)

function escapeit { perl -e 'use URI::Escape; print uri_escape shift();print"\n"' $1 | sed 's/\s/_/g'; }
#function download { curl -s $1 }
function download { cache=$cachedir"/"$(escapeit $1) ; if ! test -e $cache ; then curl -s $1 > $cache.tmp ; mv $cache.tmp $cache ; fi ; cat $cache ; } ; mkdir -p $data"/../.cache/web" ; cachedir=$data"/../.cache/web"

mkdir -p $data/.tmp/html $data/.tmp/json
rm -f $data/.tmp/json/articles_laststep.json
oldchambre=""
cat $1 | while read line ; do 
  #Variables
#  dossier=$(echo $line | awk -F ';' '{print $1"_"$5"_"$6}' | sed 's/-\([0-9]*\)-/\1/')
  dossier="procedure"
  etape=$(echo $line | sed 's/ //g' | awk -F ';' '{print $7"_"$9"_"$10"_"$11}')
  etapid=$(echo $etape | sed 's/^\([0-9]\+\)_.*$/\1/')
  projectdir=$data"/"$dossier"/"$etape
  norder=$(echo $line | awk -F ';' '{print $8}')
  order=$(echo $line | awk -F ';' '{print $7}')
  url=$(echo $line | awk -F ';' '{print $12}')
  escape=$(escapeit $url)
  chambre=$(echo $line | awk -F ';' '{print $10}')
  stage=$(echo $line | awk -F ';' '{print $11}')
  
  mkdir -p "$data/$dossier"
  rm -rf "$projectdir"
  if test "$dossier" = "$olddossier"; then
      if [ "$norder" == "1" ] || echo $line | grep -v ';depot;' > /dev/null ; then 
	  echo $line >>  "$data/$dossier/procedure.csv"
      fi
  else
      echo $line >  "$data/$dossier/procedure.csv"
  fi
  python procedure2json.py "$data/$dossier/procedure.csv" > "$data/$dossier/procedure.json"
  olddossier=$dossier
  if echo $line | grep ';\(EXTRA\|texte retire\);' > /dev/null ; then
	continue;
  fi
 if echo $line | grep ';renvoi en commission;' > /dev/null ; then
  if ! test -s $data/.tmp/json/articles_antelaststep.json; then
    echo "ERROR retrieving texte renvoyé en commission $data/.tmp/json/articles_antelaststep.json empty"
    exit 1
  fi
  head -n 1 $data/.tmp/json/articles_antelaststep.json | sed 's/^{\("expose": "\).*"\(, "id": "\)\([0-9]\+\)\(_[^"]*", \)/{"echec": true, \1Le texte est renvoyé en commission."\2'"$etapid"'\4/' > $data/.tmp/json/$escape
  tail -n $(($(cat $data/.tmp/json/articles_antelaststep.json | wc -l) - 1)) $data/.tmp/json/articles_antelaststep.json >> $data/.tmp/json/$escape
 else 
  #Text export
  download $url | sed 's/iso-?8859-?1/UTF-8/i' > $data/.tmp/html/$escape;
  #if file -i $data/.tmp/html/$escape | grep -i iso > /dev/null; then recode ISO885915..UTF8 $data/.tmp/html/$escape; fi
  if ! python parse_texte.py $data/.tmp/html/$escape $order > $data/.tmp/json/$escape; then
    echo "ERROR parsing $data/.tmp/html/$escape"
    exit 1
  fi
 fi
  # Complete articles with missing "conforme" or "non-modifié" text
  if [ "$norder" != "1" ] && test -s $data/.tmp/json/articles_laststep.json; then
    previous="$data/.tmp/json/articles_laststep.json"
    if echo "$etape" | grep "_nouv.lect._senat_hemicycle" > /dev/null && grep '"type": "echec"' "$data/.tmp/json/$escape" > /dev/null; then
      previous="$data/.tmp/json/articles_nouvlect.json"
    fi
    if ! python complete_articles.py $data/.tmp/json/$escape "$previous" > $data/.tmp/json/$escape.tmp; then
      echo "ERROR completing $data/.tmp/html/$escape"
      exit 1
    fi
    mv $data/.tmp/json/$escape{.tmp,}
  fi
  if ! test -s $data/.tmp/json/$escape && [ "$stage" = "depot" ] && [ "$order" != "00" ]; then
    echo "WARNING: creating depot step $projectdir from last step since no data found"
    head -n 1 $data/.tmp/json/articles_laststep.json | sed 's/\("echec": true, \)\?\("expose": "\)[^"]*\(", "id": "\)\([0-9]\+\)\(_[^"]*", \)/\2\3'"$etapid"'\5/' > $data/.tmp/json/$escape
    tail -n $(($(cat $data/.tmp/json/articles_laststep.json | wc -l) - 1)) $data/.tmp/json/articles_laststep.json >> $data/.tmp/json/$escape
  fi
  if ! python json2arbo.py $data/.tmp/json/$escape "$projectdir/texte"; then
    rm -rf "$projectdir"
    echo "ERROR creating arbo from $data/.tmp/json/$escape"
    exit 1
  fi
  if test -s $data/.tmp/json/articles_laststep.json; then
    cp -f $data/.tmp/json/articles_laststep.json $data/.tmp/json/articles_antelaststep.json
  fi
  if [ "$norder" != "1"  ] || [ "$order" = "00" ]; then
    cp -f $data/.tmp/json/$escape $data/.tmp/json/articles_laststep.json
  fi
  if echo "$etape" | grep "_nouv.lect._assemblee_hemicycle" > /dev/null; then
   cp -f $data/.tmp/json/$escape $data/.tmp/json/articles_nouvlect.json
  fi
  if test "$amdidtext" && test "$oldchambre" = "$chambre" && test "$olddossier" = "$dossier"; then
    if test "$chambre" = "senat"; then
	  dossier_instit=$(echo $line | awk -F ';' '{print $6}')
      urlchambre="http://www.nossenateurs.fr"
    else
      dossier_instit=$(echo $line | awk -F ';' '{print $5}')
      legislature=$(echo $line | awk -F ';' '{print $4}')
      urlchambre="http://www.nosdeputes.fr/$legislature"
    fi

    #Amendements export
    mkdir -p "$projectdir/amendements"
    download "$urlchambre/amendements/$amdidtext/csv" | perl sort_amendements.pl $data/.tmp/json/$escape csv >  "$projectdir/amendements/amendements.csv"
    if grep [a-z] "$projectdir/amendements/amendements.csv" > /dev/null; then
    	download "$urlchambre/amendements/$amdidtext/json" | perl sort_amendements.pl $data/.tmp/json/$escape json > "$projectdir/amendements/amendements.json"
    	download "$urlchambre/amendements/$amdidtext/xml"  | perl sort_amendements.pl $data/.tmp/json/$escape xml > "$projectdir/amendements/amendements.xml"
    else
    	rm "$projectdir/amendements/amendements.csv"
    	rmdir $projectdir/amendements
    fi

    #Interventions export
    inter_dir="$projectdir/interventions"
    is_commission=''
    if echo $etape | grep commission > /dev/null; then
      is_commission='?commission=1'
    fi
    download "$urlchambre/seances/$amdidtext/csv$is_commission" | grep "[0-9]" | sed 's/;//g' | while read id_seance; do
      tmpseancecsv="."$id_seance".csv"
      download "$urlchambre/seance/$id_seance/$dossier_instit/csv" > $tmpseancecsv
      if head -n 1 $tmpseancecsv  | grep -v '404' | grep '[a-z]' > /dev/null; then
	seance_name=$(head -n 2 $tmpseancecsv | tail -n 1 | awk -F ';' '{print $4 "T" $5 "_" $1}' | sed 's/ //g')
        mkdir -p $inter_dir
        cat $tmpseancecsv > $inter_dir/$seance_name.csv
        download "$urlchambre/seance/$id_seance/$dossier_instit/json" > $inter_dir/$seance_name.json
        download "$urlchambre/seance/$id_seance/$dossier_instit/xml" > $inter_dir/$seance_name.xml
      fi
      rm $tmpseancecsv
    done

  fi

  #End
  amdidtext=$(echo $line | awk -F ';' '{print $13}')
  oldchambre=$chambre
  olddossier=$dossier
  echo "INFO: data exported in $projectdir"
done

