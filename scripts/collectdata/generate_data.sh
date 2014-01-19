#!/bin/bash

if ! test "$1"; then 
	echo "USAGE: $0 DOSSIER_DESC.CSV [DATADIR]"
	printf "\t DOSSIER_DESC.CSV: CSV décrivant un ou plusieurs dossiers parlementaires générés via parse_dosser.pl (de NosSénateurs)\n"
	printf "\t DATADIR: répertoire où vont être mises les données (par defaut data/)"
fi
data=$(if test "$2" ; then echo $2 ; else echo "data" ; fi)

function escapeit { perl -e 'use URI::Escape; print uri_escape shift();print"\n"' $1 ; }
#function download { curl -s $1 }
function download { cache=$cachedir"/"$(escapeit $1) ; if ! test -e $cache ; then curl -s $1 > $cache ; fi ; cat $cache ; } ; mkdir -p $data"/../.cache/web" ; cachedir=$data"/../.cache/web"

oldchambre=""
cat $1 | while read line ; do 
  #Variables
  dossier=$(echo $line | awk -F ';' '{print $1"_"$2"_"$3}' | sed 's/-\([0-9]*\)-/\1/')
  etape=$(echo $line | sed 's/ //g' | awk -F ';' '{print $4"_"$6"_"$7"_"$8}')
  projectdir=$data"/"$dossier"/"$etape
  order=$(echo $line | awk -F ';' '{print $4}')
  url=$(echo $line | awk -F ';' '{print $9}')
  escape=$(escapeit $url)
  chambre=$(echo $line | awk -F ';' '{print $7}')
  
  mkdir -p "$data/$dossier"
  if test "$dossier" = "$olddossier"; then
      echo $line >>  "$data/$dossier/procedure.csv"
  else
      echo $line >  "$data/$dossier/procedure.csv"
  fi
  python procedure2json.py "$data/$dossier/procedure.csv" > "$data/$dossier/procedure.json"
  olddossier=$dossier
  if echo $line | grep ';EXTRA;' > /dev/null ; then
	continue;
  fi
 
  mkdir -p $data/html $data/json
  #Text export
  download $url | sed 's/iso-?8859-?1/UTF-8/i' > $data/html/$escape;
  if file -i $data/html/$escape | grep -i iso > /dev/null; then recode ISO88591..UTF8 $data/html/$escape; fi
  python parse_texte.py $data/html/$escape $order > $data/json/$escape
  python json2arbo.py $data/json/$escape "$projectdir/texte"
  
  if test "$amdidtext" && test "$oldchambre" = "$chambre" && test "$olddossier" = "$dossier"; then
    urlchambre="http://www.nosdeputes.fr/14"
    if test "$chambre" = "senat"; then
    	urlchambre="http://www.nossenateurs.fr"
    fi

    #Amendements export
    mkdir -p "$data/$projectdir/amendements"
    cd "$data/$projectdir/amendements"
    download "$urlchambre/amendements/$amdidtext/csv" > amendements.csv
    if grep [a-z] amendements.csv > /dev/null; then 
    	download "$urlchambre/amendements/$amdidtext/json" > amendements.json
    	download "$urlchambre/amendements/$amdidtext/xml" > amendements.xml
    	cd - > /dev/null
    else
    	rm amendements.csv
    	cd - > /dev/null
    	rmdir $data/$projectdir/amendements
    fi

    #Interventions export
    inter_dir="$data/$projectdir/interventions"
    is_commission=''
    if echo $etape | grep commission > /dev/null; then
      is_commission='?commission=1'
    fi
    dossier_instit=$(echo $line | awk -F ';' '{print $2}')
    if test "$chambre" = "senat"; then
	dossier_instit=$(echo $line | awk -F ';' '{print $3}')
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
  amdidtext=$(echo $line | awk -F ';' '{print $10}')
  oldchambre=$chambre
  olddossier=$dossier
  echo "INFO: data exported in $data/$projectdir"
done 
