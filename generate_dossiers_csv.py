"""
Usage: python generate_dossiers_csv.py <api_directory>

Output in <api_directory>:
- dossiers_promulgues.csv with all the doslegs ready
- home.json for the homepage informations
"""
import glob, os, sys, csv, re

from tools.common import upper_first, open_json, print_json

API_DIRECTORY = sys.argv[1]

re_dos_ok = re.compile(r"%s/[^.]+/" % API_DIRECTORY.strip('/'))
dossiers = [(open_json(path), path) for path \
                in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json')) if re_dos_ok.search(path)]
dossiers = [(dos, path) for dos, path in dossiers if dos.get('end')]


csvfile = csv.writer(open(os.path.join(API_DIRECTORY, 'dossiers_promulgues.csv'), 'w'), delimiter=';')
csvfile.writerow(('id;Titre;Type de dossier;Date initiale;URL du dossier;État du dossier;Décision du CC;' \
    + 'Date de la décision;Date de promulgation;Numéro de la loi;Thèmes;total_amendements;total_mots;short_title;loi_dite').split(';'))

home_json_data = []

total_doslegs = 0
for dos, path in dossiers:
    id = dos.get('senat_id', dos.get('assemblee_id'))

    if not dos.get('beginning'):
        print('INVALID BEGGINING DATE:', id)
        continue

    total_mots = 0
    try:
        intervs = open_json(path.replace('procedure.json', 'interventions.json'))
        total_mots = sum([
            sum(i['total_mots'] for i in step['divisions'].values())
                for step in intervs.values()
        ])
    except FileNotFoundError:
        pass

    total_amendements = sum([step.get('nb_amendements', 0) for step in dos['steps']])

    decision_cc = None
    decision_cc_date = None
    for step in dos['steps']:
        if step.get('stage') == 'constitutionnalité':
            decision_cc = step.get('decision')
            decision_cc_date = step.get('date')
            break

    csvfile.writerow([
        id, # id
        dos.get('long_title'), # Titre
        # TODO: detect propo/pjl in AN doslegs
        'projet de loi' if 'pjl' in dos.get('senat_id', '') else 'proposition de loi', # Type de dossier
        dos.get('beginning'), # Date initiale
        dos.get('url_dossier_senat', dos.get('url_dossier_assemblee')), # URL du dossier
        'promulgué', # État du dossier
        decision_cc, # Décision du CC
        decision_cc_date, # Date de la décision
        dos.get('end'), # Date de promulgation
        dos.get('law_name'), # Numéro de la loi
        ','.join(dos.get('themes', [])), # Thèmes
        total_amendements, # total_amendements
        total_mots, # total_mots
        dos.get('short_title'), # short_title
        dos.get('loi_dite') # Nom commun de la loi
    ])

    if total_amendements == 0:
        status = 'Aucun amendement'
    elif total_amendements == 1:
        status = 'Un amendement'
    else:
        status = '%d amendements' % total_amendements

    """
    last_intervention = [
        step['intervention_files'][-1] for step in dos['steps'] \
            if step.get('has_interventions')
    ]
    if last_intervention:
        last_intervention = last_intervention[-1]
    else:
        last_intervention = None
    """

    title = dos.get('short_title')
    if dos.get('loi_dite'):
        title = "%s (%s)" % (upper_first(dos.get('loi_dite')), title)
    if total_amendements:
        home_json_data.append({
            'total_amendements': total_amendements,
            'end': dos['end'],
            'status': status,
            'loi': id,
            'titre': title
        })

    total_doslegs += 1

print(total_doslegs, 'doslegs in csv')


home_json_final = {
    "total": total_doslegs,
    "maximum": len([path for path in glob.glob(os.path.join(API_DIRECTORY, '*/parsing.log')) if re_dos_ok.search(path)]) + len(glob.glob(os.path.join(API_DIRECTORY, 'logs/*')))
}
home_json_data.sort(key=lambda x: -x['total_amendements'])
home_json_final["focus"] = {
    "titre": "Les textes les plus amendés",
    "lien": "Explorer les textes les plus amendés",
    "url": "lois.html?action=quanti",
    "textes": home_json_data[:6],
}
home_json_data.sort(key=lambda x: x['end'])
home_json_final["recent"] = {
    "titre": "Les derniers textes promulgués",
    "lien": "Explorer les textes récents",
    "url": "lois.html",
    "textes": list(reversed(home_json_data[-6:])),
}
print_json(home_json_final, os.path.join(API_DIRECTORY, 'home.json'))
print('home.json OK')
