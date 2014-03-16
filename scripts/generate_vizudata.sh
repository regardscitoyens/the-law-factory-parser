#!/bin/bash

datadir=$1
mkdir -p $datadir/viz

cd vizudata
python prepare_articles.py $datadir/procedure > $datadir/viz/articles_etapes.json
python prepare_interventions.py $datadir > $datadir/viz/interventions.json
python prepare_amendements.py $datadir > $datadir/viz/amendements.json
python update_procedure.py $datadir > $datadir/viz/procedure.json


