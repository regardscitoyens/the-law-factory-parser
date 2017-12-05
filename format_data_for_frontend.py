import os, glob, sys, json, csv, random

from tools import json2arbo, prepare_articles, update_procedure

def process(dos, OUTPUT_DIR, skip_already_done=False):
    dos_id = dos.get('senat_id', dos.get('assemblee_id'))
    print('processing', dos_id)
    
    # TODO: rm -rf output dir
    output_dir = os.path.join(OUTPUT_DIR, dos_id)
    print('     writing to:', output_dir)

    if skip_already_done and os.path.exists(output_dir):
        print(' - already done')
        return

    # add texte.json and write all the text files tree
    dos = json2arbo.process(dos, output_dir + '/procedure')

    json2arbo.mkdirs(output_dir + '/viz')
    articles_etapes = prepare_articles.process(dos)
    open(output_dir + '/viz/articles_etapes.json', 'w').write(json.dumps(articles_etapes, indent=2, sort_keys=True, ensure_ascii=True))

    procedure = update_procedure.process(dos, articles_etapes)

    # remove intermediate data
    for step in procedure['steps']:
        for key in 'articles_completed', 'articles', 'texte.json':
            try:
                step.pop(key)
            except KeyError:
                pass

    open(output_dir + '/viz/procedure.json', 'w').write(
        json.dumps(procedure, indent=2, sort_keys=True, ensure_ascii=False))

    print(output_dir, 'done')


if __name__ == '__main__':
    INPUT_GLOB = sys.argv[1]
    OUTPUT_DIR = sys.argv[2]

    json2arbo.mkdirs(OUTPUT_DIR)

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

        if len(dos.get('steps', [])) < 2:
            print ('  -> pass single step dossier')
            continue

        process(dos, OUTPUT_DIR, skip_already_done=True)

        csvfile.writerow([
            file.split('/')[-1], # id
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
