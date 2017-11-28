import os, glob, sys, json, csv, random

from tools import json2arbo, prepare_articles, update_procedure


INPUT_GLOB = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

csvfile = csv.writer(open(OUTPUT_DIR + '/dossiers_promulgues.csv', 'w'), delimiter=';')

csvfile.writerow('id;Titre;Type de dossier;Date initiale;URL du dossier;État du dossier;Décision du CC;Date de la décision;Date de promulgation;Numéro de la loi;Thèmes;total_amendements;total_mots;short_title'.split(';'))

all_files = list(glob.glob(INPUT_GLOB))

for i, file in enumerate(all_files):
    print()
    try:
        dos = json.load(open(file))
    except json.decoder.JSONDecodeError:
        print('invalid JSON', file)
        continue
    print(file, ' - ', i, '/', len(all_files))

    if not (dos.get('url_jo') and len(dos['steps']) > 8):
        print('     - passed')
        continue

    dos_id = file.split('/')[-1]

    output_dir = OUTPUT_DIR + file.split('/')[-1]
    print('     out:', output_dir)

    if os.path.exists(output_dir):
        print('alread_done')
        continue
    else:
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

    csvfile.writerow([
        dos_id, # id
        dos.get('long_title'), # Titre
        'projet de loi', # Type de dossier
        dos.get('beginning'), # Date initiale
        dos.get('url_dossier_senat'), # URL du dossier
        'promulgué', # État du dossier
        '', # Décision du CC
        '', # Date de la décision
        dos.get('end_jo'), # Date de promulgation
        1234, # Numéro de la loi
        '', # Thèmes
        42, # total_amendements
        43, # total_mots
        dos.get('short_title') # short_title
        ])
