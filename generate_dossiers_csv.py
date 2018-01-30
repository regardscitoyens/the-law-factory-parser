"""
Usage: python generate_dossiers_csv.py <api_directory>

Output in <api_directory>:
- dossiers_promulgues.csv with all the doslegs ready
- home.json for the homepage informations
"""
import json, glob, os, sys, csv

API_DIRECTORY = sys.argv[1]

dossiers = [(json.load(open(path)), path) for path \
                in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json'))]
dossiers = [(dos, path) for dos, path in dossiers if dos.get('end_jo')]


csvfile = csv.writer(open(os.path.join(API_DIRECTORY, 'dossiers_promulgues.csv'), 'w'), delimiter=';')
csvfile.writerow(('id;Titre;Type de dossier;Date initiale;URL du dossier;État du dossier;Décision du CC;' \
    + 'Date de la décision;Date de promulgation;Numéro de la loi;Thèmes;total_amendements;total_mots;short_title').split(';'))

home_json_data = []

total_doslegs = 0
for dos, path in dossiers:
    id = dos.get('senat_id', dos.get('assemblee_id'))

    if not dos.get('beginning'):
        print('INVALID BEGGINING DATE:', id)
        continue

    total_mots = 0
    try:
        intervs = json.load(open(path.replace('procedure.json', 'interventions.json')))
        total_mots = sum([
            sum(i['total_mots'] for i in step['divisions'].values())
                for step in intervs.values()
        ])
    except FileNotFoundError:
        pass

    total_amendements = sum([step.get('nb_amendements', 0) for step in dos['steps']])

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
        total_amendements, # total_amendements
        total_mots, # total_mots
        dos.get('short_title') # short_title
    ])

    if total_amendements == 0:
        status = 'Aucun amendement'
    elif total_amendements == 1:
        status = 'Un amendement'
    else:
        status = '%d amendements' % total_amendements

    last_intervention = [
        step['intervention_files'][-1] for step in dos['steps'] \
            if step.get('has_interventions')
    ]
    if last_intervention:
        last_intervention = last_intervention[-1]
    else:
        last_intervention = None

    home_json_data.append({
        'total_amendements': total_amendements,
        'last_intervention': last_intervention,
        'status': status,
        'loi': id,
        'titre': dos.get('short_title'),
    })

    total_doslegs += 1

print(total_doslegs, 'doslegs in csv')


home_json_final = {
    "total": total_doslegs,
    "maximum": 841, # TODO: how can I get it ?
}
home_json_data.sort(key=lambda x: -x['total_amendements'])
home_json_final["focus"] = {
    "titre": "Les textes les plus amendés",
    "lien": "Explorer les textes les plus amendés",
    "url": "lois.html",
    "textes": home_json_data[:4],
}
home_json_data.sort(key=lambda x: x['last_intervention'] if x['last_intervention'] else '0')
home_json_final["recent"] = {
    "titre": "Les derniers textes débattus",
    "lien": "Explorer les textes récents",
    "url": "lois.html?action=quanti",
    "textes": home_json_data[-4:],
}
open(os.path.join(API_DIRECTORY, 'home.json'), 'w').write(
    json.dumps(home_json_final, sort_keys=True, indent=2, ensure_ascii=False))
print('home.json OK')
