import os, glob, sys, json

sys.path.append('deprecated/scripts/collectdata')
import json2arbo

sys.path.append('deprecated/scripts/vizudata')
import prepare_articles
import update_procedure

INPUT_GLOB = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

for file in glob.glob(INPUT_GLOB):
    print()
    try:
        dos = json.load(open(file))
    except json.decoder.JSONDecodeError:
        print('invalid JSON', file)
        continue
    print(file)

    if not (dos.get('url_jo') and len(dos['steps']) > 8):
        print('     - passedp')
        continue

    output_dir = OUTPUT_DIR + file.split('/')[-1]
    print('     out:', output_dir)

    if os.path.exists(output_dir):
        print('alread_done')
        continue

    # add texte.json and write all the text files tree
    dos = json2arbo.process(dos, output_dir + '/procedure')

    json2arbo.mkdirs(output_dir + '/viz')

    articles_etapes = prepare_articles.process(dos)
    open(output_dir + '/viz/articles_etapes.json', 'w').write(json.dumps(articles_etapes, indent=2, sort_keys=True, ensure_ascii=True))

    procedure = update_procedure.process(dos, articles_etapes)

    for step in procedure['steps']:
        try:
            step.pop('articles_completed')
        except KeyError:
            pass

        try:
            step.pop('articles')
        except KeyError:
            pass

        try:
            step.pop('texte.json')
        except KeyError:
            pass

    open(output_dir + '/viz/procedure.json', 'w').write(json.dumps(procedure, indent=2, sort_keys=True, ensure_ascii=True))

    print(output_dir, 'done !! :)')