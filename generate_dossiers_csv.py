import json, glob, os, sys, csv

API_DIRECTORY = sys.argv[1]

dossiers = [json.load(open(dos)) for dos \
                in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json'))]
dossiers = [dos for dos in dossiers if dos.get('end_jo')]


csvfile = csv.writer(open(os.path.join(API_DIRECTORY, 'dossiers_promulgues.csv'), 'w'), delimiter=';')
csvfile.writerow(('id;Titre;Type de dossier;Date initiale;URL du dossier;État du dossier;Décision du CC;' \
    + 'Date de la décision;Date de promulgation;Numéro de la loi;Thèmes;total_amendements;total_mots;short_title').split(';'))

i = 0
for dos in dossiers:
    id = dos.get('senat_id', dos.get('assemblee_id'))

    if not dos.get('beginning'):
        print('INVALID BEGGINING DATE:', id)
        continue

    csvfile.writerow([
        id, # id
        dos.get('long_title'), # Titre
        # TODO: detect propo/pjl in AN doslegs
        'projet de loi' if 'pjl' in dos.get('senat_id', '') else 'proposition de loi', # Type de dossier
        dos.get('beginning'), # Date initiale
        dos.get('url_dossier_senat', dos.get('url_dossier_assemblee')), # URL du dossier
        'promulgué', # État du dossier
        '', # Décision du CC
        '', # Date de la décision
        dos.get('end_jo'), # Date de promulgation
        1234, # Numéro de la loi
        ','.join(dos.get('themes', [])), # Thèmes
        51, # total_amendements
        43, # total_mots
        dos.get('short_title') # short_title
        ])

    i += 1
print(i, 'doslegs')
