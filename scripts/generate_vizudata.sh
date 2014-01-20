#!/bin/bash

datadir=$1
mkdir -p $datadir/viz

cd vizudata
python prepare_articles.py $datadir/procedure > $datadir/viz/articles_etapes.json

