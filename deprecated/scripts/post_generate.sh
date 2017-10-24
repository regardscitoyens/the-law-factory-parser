#!/bin/bash

datadir=$1

cd $datadir
zip -qr procedure.zip procedure/ 

NOMLONG=$(head -n 1 "procedure/procedure.csv" | cut -d ';' -f 2)
IDLOI=$(head -n 1 "procedure/procedure.csv" | cut -d ';' -f 5)
LELA=$(head -n 1 "procedure/procedure.csv" | awk -F ';' '{if ($5 ~ /ppl/) print "la" ; else print "le";}')
DEDU=$(head -n 1 "procedure/procedure.csv" | awk -F ';' '{if ($5 ~ /ppl/) print "de la" ; else print "du";}')

echo "<h1>Les données $DEDU "$NOMLONG"</h1>" > HEADER.html
echo '<p>Les données mises à disposition dans ces répertoires sont celles utilisées par <a href="http://lafabriquedelaloi.fr/">La Fabrique de la Loi</a> pour visualiser '$LELA' <a href="http://lafabriquedelaloi.fr/lois.html?loi='$IDLOI'">'$NOMLONG'</a>.</p>' >> HEADER.html
echo '<p>Elles ont été constituées par <a href="http://regardscitoyens.org">Regards Citoyens</a> à partir de <a href="http://nosdeputes.Fr/">NosDéputés.fr</a>, <a href="http://NosSénateurs.fr">NosSénateurs.fr<a/> et les sites du <a href="http://senat.fr/">Sénat</a> et de l'"'"'<a href="http://assemblee-nationale.fr">Assemblée nationale</a>. Elles sont réutilisables librement en <img src="http://www.nosdeputes.fr/images/opendata.png" alt="Open Data"/> sous la licence <a href="http://opendatacommons.org/licenses/odbl/">ODBL</a>.</p>' >> HEADER.html
echo '<p>Le répertoire <a href="procedure/"><img src="http://www.lafabriquedelaloi.fr/icons/folder.gif"/>&nbsp;procedure/</a> contient les données brutes aux formats CSV, JSON, XML sur les textes, les interventions et les amendements à chaque étape de la procédure. Le répertoire <a href="viz/"><img src="http://www.lafabriquedelaloi.fr/icons/folder.gif"/>&nbsp;viz/</a> contient les fichiers utilisés par l'"'"'application.</p>' >> HEADER.html
