import os, glob, sys, json, csv, random, shutil

from tools import json2arbo, prepare_articles, update_procedure, prepare_amendements

def process(dos, OUTPUT_DIR, skip_already_done=False):
    dos_id = dos.get('senat_id', dos.get('assemblee_id'))
    
    output_dir = os.path.join(OUTPUT_DIR, dos_id)
    print('     writing to:', output_dir)

    if skip_already_done and os.path.exists(output_dir):
        print(' - already done')
        return

    shutil.rmtree(output_dir, ignore_errors=True)

    # add texte.json and write all the text files tree
    dos = json2arbo.process(dos, output_dir + '/procedure')

    json2arbo.mkdirs(output_dir + '/viz')
    articles_etapes = prepare_articles.process(dos)
    open(output_dir + '/viz/articles_etapes.json', 'w').write(json.dumps(articles_etapes, indent=2, sort_keys=True, ensure_ascii=True))

    procedure = update_procedure.process(dos, articles_etapes)

    print(' - process amendements')
    prepare_amendements.process(output_dir, procedure)

    # remove intermediate data
    for step in procedure['steps']:
        for key in 'articles_completed', 'articles', 'texte.json':
            try:
                step.pop(key)
            except KeyError:
                pass

    open(output_dir + '/viz/procedure.json', 'w').write(
        json.dumps(procedure, indent=2, sort_keys=True, ensure_ascii=False))

