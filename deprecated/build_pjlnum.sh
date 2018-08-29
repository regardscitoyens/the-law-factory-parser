#!/bin/bash

datadir=/home/roux/the-law-factory-parser.rens/data/pjl15-republique_numerique
echo "Working from $datadir/.tmp/dossier.csv"
cat $datadir/.tmp/dossier.csv
cd scripts                                                                                                                                                                                                                                
bash generate_collectdata.sh "" $datadir && bash generate_vizudata.sh $datadir && bash post_generate.sh $datadir


#DEBATS COMM
#commission-des-lois-constitutionnelles-de-la-legislation-et-de-l-administration-generale-de-la-republique
#    spliitable https://www.nosdeputes.fr/14/seance/6016 fin
#    splittable https://www.nosdeputes.fr/14/seance/6055 début
#    https://www.nosdeputes.fr/14/seance/6056
#    https://www.nosdeputes.fr/14/seance/6066
#    https://www.nosdeputes.fr/14/seance/6067
#    https://www.nosdeputes.fr/14/seance/6068
#    https://www.nosdeputes.fr/14/seance/6072
#commission-des-affaires-culturelles-et-de-l-education
#    https://www.nosdeputes.fr/14/seance/6045
#commission-des-affaires-sociales
#    https://www.nosdeputes.fr/14/seance/6038
#commission-des-affaires-economiques
#    splittable https://www.nosdeputes.fr/14/seance/6047 début
#    https://www.nosdeputes.fr/14/seance/6073
#commission des affaires européennes
#    splitter https://www.nosdeputes.fr/14/seance/6010 fin/debut
#délégation de l'Assemblée nationale aux droits des femmes et à l'égalité des chances entre les hommes et les femmes
#    https://www.nosdeputes.fr/14/seance/5277
#    https://www.nosdeputes.fr/14/seance/5395
#    https://www.nosdeputes.fr/14/seance/5491
#    https://www.nosdeputes.fr/14/seance/5559
#    https://www.nosdeputes.fr/14/seance/5639
#    https://www.nosdeputes.fr/14/seance/5774
#    https://www.nosdeputes.fr/14/seance/5830
#    https://www.nosdeputes.fr/14/seance/5927
#    https://www.nosdeputes.fr/14/seance/6029
#


