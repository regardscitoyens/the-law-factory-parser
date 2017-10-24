#!/bin/bash

if ! test "$1"; then
	echo "USAGE: $0 DOSSIER_DESC.CSV [DATADIR] [WITHOUTCACHE]"
	printf "\t DOSSIER_DESC.CSV: CSV décrivant un ou plusieurs dossiers parlementaires générés via parse_dosser.pl (de NosSénateurs)\n"
	printf "\t DATADIR: répertoire où vont être mises les données (par defaut data/)"
fi
data=$(if test "$2" ; then echo $2 ; else echo "data" ; fi)

function escapeit { perl -e 'use URI::Escape; print uri_escape shift();print"\n"' "$1" | sed 's/\s/_/g'; }
function download {
  cache=$cachedir"/"$(escapeit $1)
  if ! test -e $cache ; then
    if curl -sLI $1 | grep " 404" > /dev/null; then
      echo > $cache.tmp
    else
      curl -sL $1 > $cache.tmp
      if echo $1 | grep "petite-loi-ameli" > /dev/null; then
        iconv $cache.tmp -f "windows-1252" -t "utf-8" > $cache.enc
        mv $cache.{enc,tmp}
      fi
    fi
    mv $cache.tmp $cache
  fi
  cat $cache
}

if test "$3"; then
	CACHEVAL=$(date | md5sum | sed 's/ .*//')
fi

mkdir -p $data"/../.cache/web" ; cachedir=$data"/../.cache/web"
mkdir -p $data/.tmp/html $data/.tmp/json
rm -f $data/.tmp/json/articles_laststep.json

for url in "2007-2012.nosdeputes" "www.nosdeputes" "www.nossenateurs"; do
  download "http://$url.fr/organismes/groupe/json" > "$data/../$url-groupes.json"
  typeparl=$(echo $url | sed 's/^.*nos//')
  download "http://$url.fr/$typeparl/json?"$CACHEVAL > "$data/../$url.parlementaires.json"
done

# Fix occasional wrong order of votes post CMP
if grep ";CMP;assemblee;hemicycle;" $1 > /dev/null && grep ";CMP;senat;hemicycle;" $1 > /dev/null; then
  reorder=false
  line_a=$(grep ";CMP;assemblee;hemicycle;" $1)
  line_s=$(grep ";CMP;senat;hemicycle;" $1)
  num_a=$(echo $line_a | awk -F ';' '{print $7}' | sed 's/^0//')
  num_s=$(echo $line_s | awk -F ';' '{print $7}' | sed 's/^0//')
  min_num=$(($num_a<$num_s?$num_a:$num_s))
  url=$(echo $line_a | awk -F ';' '{print $12}')
  if [ ! -z "$url" ]; then
    escape=$(escapeit "$url")
    download $url | sed 's/iso-?8859-?1/UTF-8/i' > $data/.tmp/html/$escape
    if grep -i 'Texte d\(&eacute;\|.\)finitif' $data/.tmp/html/$escape > /dev/null && [ $min_num -ne $num_s ]; then
      reorder=true
    else
      url=$(echo $line_s | awk -F ';' '{print $12}')
      escape=$(escapeit "$url")
      download $url | sed 's/iso-?8859-?1/UTF-8/i' > $data/.tmp/html/$escape
      if grep -i "Texte d\(&eacute;\|.\)finitif" $data/.tmp/html/$escape > /dev/null && [ $min_num -ne $num_a ]; then
        reorder=true
      fi
    fi
    if $reorder; then
      echo "INFO: Reordering CMP hemicycle steps to handle renumbered texte définitif last"
      grep -v ";CMP;[a-z]*;hemicycle;" $1 > $1.tmp
      echo "$line_a" | sed "s/\(;0*\)$num_a\(;[0-9]\+;CMP\)/\1$num_s\2/" >> $1.tmp
      echo "$line_s" | sed "s/\(;0*\)$num_s\(;[0-9]\+;CMP\)/\1$num_a\2/" >> $1.tmp
      sort $1.tmp > $1
    fi
  fi
fi

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
  escape=$(escapeit "$url")
  chambre=$(echo $line | awk -F ';' '{print $10}')
  stage=$(echo $line | awk -F ';' '{print $11}')

  mkdir -p "$data/$dossier"
  rm -rf "$projectdir"
  if echo $line | grep ';\(EXTRA\|texte retire\);' > /dev/null ; then
	echo "$line;" >>  "$data/$dossier/procedure.csv"
    python procedure2json.py "$data/$dossier/procedure.csv" > "$data/$dossier/procedure.json"
    olddossier=$dossier
	continue
  fi
  if echo $line | grep ';renvoi en commission;' > /dev/null ; then
    if ! test -s $data/.tmp/json/articles_antelaststep.json; then
      echo "ERROR retrieving texte renvoyé en commission $data/.tmp/json/articles_antelaststep.json empty"
      exit 1
    fi
    head -n 1 $data/.tmp/json/articles_antelaststep.json | sed 's/^{\("expose": "\).*"\(, "id": "\)\([0-9]\+\)\(_[^"]*", \)/{"echec": true, \1Le texte est renvoyé en commission."\2'"$etapid"'\4/' > $data/.tmp/json/$escape
    tail -n $(($(cat $data/.tmp/json/articles_antelaststep.json | wc -l) - 1)) $data/.tmp/json/articles_antelaststep.json >> $data/.tmp/json/$escape
  elif test -z "$url"; then
    echo "MISSING URL $line"
  else
    depot="false"
    if [ "$stage" = "depot" ]; then
      depot="true"
    fi
    #Text export
    download $url | sed 's/iso-?8859-?1/UTF-8/i' > $data/.tmp/html/$escape;
    if ! python parse_texte.py $data/.tmp/html/$escape $order | sed 's/\("type": "texte"\)}$/\1, "depot": '"$depot"'}/' > $data/.tmp/json/$escape; then
      echo "ERROR parsing $data/.tmp/html/$escape"
      exit 1
    fi
  fi

 if ! test -z "$url"; then # START AVOIDED PART WHEN MISSING TEXT

  # Complete missing intermediate depots from last step
  if [ $(cat $data/.tmp/json/$escape  | wc -l) -lt 2 ] && [ "$stage" = "depot" ] && [ "$order" != "00" ]; then
    echo "WARNING: creating depot step $projectdir from last step since no data found"
    head -n 1 $data/.tmp/json/articles_laststep.json | sed 's/\("echec": true, \)\?\("expose": "\)[^"]*\(", "id": "\)\([1-9]\+\)\(_[^"]*", \)/\2\3'"$etapid"'\5/' > $data/.tmp/json/$escape
    tail -n $(($(cat $data/.tmp/json/articles_laststep.json | wc -l) - 1)) $data/.tmp/json/articles_laststep.json >> $data/.tmp/json/$escape
  fi
  # Complete articles with missing "conforme" or "non-modifié" text for all steps except depots 1ère lecture
  if [ "$norder" != "1" ] && [ "$norder" != 4 ] && test -s $data/.tmp/json/articles_laststep.json; then
    anteprevious=""
    if echo "$etape" | grep hemicycle > /dev/null && test -s "$data/.tmp/json/articles_antelaststep.json"; then
      anteprevious="$data/.tmp/json/articles_antelaststep.json"
    fi
    previous="$data/.tmp/json/articles_laststep.json"
    if echo "$etape" | grep "_nouv.lect._senat_hemicycle" > /dev/null && grep '"echec"[:,}]' "$data/.tmp/json/$escape" > /dev/null; then
      previous="$data/.tmp/json/articles_nouvlect.json"
    elif echo "$etape" | grep "l.définitive" > /dev/null; then
      previous="$data/.tmp/json/articles_nouvlect.json"
      anteprevious="$previous"
    elif grep '"echec"[:,}]' "$data/.tmp/json/articles_laststep.json" > /dev/null; then
      previous="$data/.tmp/json/articles_antelaststep.json"
    fi
    if ! python complete_articles.py $data/.tmp/json/$escape "$previous" "$anteprevious" > $data/.tmp/json/$escape.tmp; then
      echo "ERROR completing $data/.tmp/html/$escape"
      exit 1
    fi
    mv $data/.tmp/json/$escape{.tmp,}
  fi

  echec=""
  if grep '"echec"[:,}]' "$data/.tmp/json/$escape" > /dev/null; then
    echec="rejet"
    if echo $line | grep ';renvoi en commission;' > /dev/null; then
      echec="renvoi en commission"
    elif echo $line | grep ';CMP;CMP;commission;' > /dev/null; then
      echec="échec"
    fi
  fi
  if ! python json2arbo.py $data/.tmp/json/$escape "$projectdir/texte"; then
    rm -rf "$projectdir"
    echo "$line;$echec"
    echo "ERROR creating arbo from $data/.tmp/json/$escape"
    exit 1
  fi
 else
  rm -f $data/.tmp/json/articles_laststep.json
 fi # END AVOIDED PART WHEN MISSING TEXT

  if test -s $data/.tmp/json/articles_laststep.json; then
    cp -f $data/.tmp/json/articles_laststep.json $data/.tmp/json/articles_antelaststep.json
  fi
  if test -f $data/.tmp/json/$escape; then
    if [ "$norder" != "1" ] || [ "$order" = "00" ]; then
      cp -f $data/.tmp/json/$escape $data/.tmp/json/articles_laststep.json
    fi
    if echo "$etape" | grep "_nouv.lect._assemblee_hemicycle" > /dev/null; then
     cp -f $data/.tmp/json/$escape $data/.tmp/json/articles_nouvlect.json
    fi
  fi


  if test "$dossier" = "$olddossier"; then
	echo "$line;$echec" >>  "$data/$dossier/procedure.csv"
  else
    echo "$line;$echec" >  "$data/$dossier/procedure.csv"
  fi
  python procedure2json.py "$data/$dossier/procedure.csv" > "$data/$dossier/procedure.json"

  if echo $line | grep ';CMP;assemblee;' > /dev/null; then
    amdidtext=$amdidtextcmpa
  elif echo $line | grep ';CMP;senat;' > /dev/null; then
    amdidtext=$amdidtextcmps
  fi
  if test "$amdidtext" && (test "$stage" = "commission" || test "$stage" = "hemicycle") && test "$olddossier" = "$dossier"; then
    if test "$chambre" = "senat"; then
	  dossier_instit=$(echo $line | awk -F ';' '{print $6}')
      urlchambre="http://www.nossenateurs.fr"
    else
      dossier_instit=$(echo $line | awk -F ';' '{print $5}')
      legislature=$(echo $line | awk -F ';' '{print $4}')
      urlchambre="http://www.nosdeputes.fr/$legislature"
    fi

    #Amendements export
    if [ -z "$echec" ]; then
      mkdir -p "$projectdir/amendements"
      download "$urlchambre/amendements/$amdidtext/csv?"$CACHEVAL | perl sort_amendements.pl $data/.tmp/json/articles_antelaststep.json csv > "$projectdir/amendements/amendements.csv"
      if grep [a-z] "$projectdir/amendements/amendements.csv" > /dev/null; then
    	download "$urlchambre/amendements/$amdidtext/json?"$CACHEVAL | perl sort_amendements.pl $data/.tmp/json/articles_antelaststep.json json > "$projectdir/amendements/amendements.json"
    	download "$urlchambre/amendements/$amdidtext/xml?"$CACHEVAL | perl sort_amendements.pl $data/.tmp/json/articles_antelaststep.json xml > "$projectdir/amendements/amendements.xml"
      else
    	rm "$projectdir/amendements/amendements.csv"
    	rmdir $projectdir/amendements
      fi
    fi

    #Interventions export
    inter_dir="$projectdir/interventions"
    commission_or_hemicycle=''
    if echo $etape | grep commission > /dev/null; then
      commission_or_hemicycle='?commission=1'
    else
      commission_or_hemicycle='?hemicycle=1'
    fi
    if ! test "$oldamdidtext" ; then oldamdidtext=$amdidtext; fi
    for (( i = 1 ; i < 3 ; i++ )) do
      if test $i = 1 ; then
        loiid=$amdidtext
      else
        loiid=$oldamdidtext
      fi
      id_seance=""
      download "$urlchambre/seances/$loiid/csv$commission_or_hemicycle&"$CACHEVAL | grep "[0-9]" | sed 's/;//g' | while read id_seance; do
        tmpseancecsv="."$id_seance".csv"
        download "$urlchambre/seance/$id_seance/$loiid/csv?"$CACHEVAL > $tmpseancecsv
        if head -n 1 $tmpseancecsv | grep '[a-z]' > /dev/null; then
          seance_name=$(head -n 2 $tmpseancecsv | tail -n 1 | awk -F ';' '{print $4 "T" $5 "_" $1}' | sed 's/ //g')
          mkdir -p $inter_dir
          cat $tmpseancecsv > $inter_dir/$seance_name.csv
          download "$urlchambre/seance/$id_seance/$loiid/json?"$CACHEVAL > $inter_dir/$seance_name.json
          download "$urlchambre/seance/$id_seance/$loiid/xml?"$CACHEVAL > $inter_dir/$seance_name.xml
        fi
        rm $tmpseancecsv
      done
      if test "$id_seance" ; then break; fi
    done
    oldamdidtext=$amdidtext
  fi

  #End
  if [ -z "$echec" ]; then
    amdidtext=$(echo $line | awk -F ';' '{print $13}')
    if echo $line | grep ';CMP;CMP;commission;' > /dev/null; then
      if echo $line | grep 'senat.fr' > /dev/null; then
        amdidtextcmpa=
        amdidtextcmps=$amdidtext
      elif echo $line | grep 'nationale.fr' > /dev/null; then
        amdidtextcmpa=$amdidtext
        amdidtextcmps=
      fi
    fi
  fi
  
  olddossier=$dossier
  echo "INFO: data exported in $projectdir"
done
