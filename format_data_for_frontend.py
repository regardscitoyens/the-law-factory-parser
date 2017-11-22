import os, glob, sys, json

sys.path.append('deprecated/scripts/collectdata')
import json2arbo

print('coming soon...')

for file in glob.glob(sys.argv[1]):
    print()
    try:
        dos = json.load(open(file))
    except json.decoder.JSONDecodeError:
        print('invalid JSON', file)
        continue
    print(file)

    dos = json2arbo.process(dos)
    articles_etapes = prepare_articles.process(dos)
    procedure = update_procedure.process(dos)