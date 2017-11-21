import os, glob, sys

print('coming soon...')
sys.exit(1)

for file in glob.glob(sys.argv[1]):
    dos = json.load(open(file))

    procedure = dos # TODO: add 'order'

    dos = json2arbo.process(dos) # dos with texte.json

    articles_etapes = prepare_articles.process(dos)

    # TODO: dump articles_etapes.json, procedure.json and steps directories