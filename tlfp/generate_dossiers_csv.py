"""
Usage: python generate_dossiers_csv.py <api_directory>

Output in <api_directory>:
- dossiers_promulgues.csv with all the doslegs ready
- home.json for the homepage informations
"""
import glob, os, sys, csv, re

from tlfp.tools.common import upper_first, open_json, print_json

API_DIRECTORY = sys.argv[1]

re_dos_ok = re.compile(r"%s/[^.]+/" % API_DIRECTORY.strip('/'))
dossiers = [(open_json(path), path) for path \
                in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json')) if re_dos_ok.search(path)]
dossiers = [(dos, path) for dos, path in dossiers if "_tmp" not in path]


csvfile = csv.writer(open(os.path.join(API_DIRECTORY, 'dossiers.csv'), 'w'), delimiter=';')
csvfile.writerow(('id;Titre;Type de dossier;Date initiale;URL du dossier;État du dossier;Décision du CC;'
    'Date de la décision;Date de promulgation;Numéro de la loi;Thèmes;total_amendements;total_mots;'
    'short_title;loi_dite;assemblee_id').split(';'))

home_json_data = []

total_doslegs = total_promulgues = 0
for dos, path in dossiers:
    if not dos.get('beginning'):
        print('INVALID BEGGINING DATE:', dos['id'])
        continue

    decision_cc = None
    decision_cc_date = None
    for step in dos['steps']:
        if step.get('stage') == 'constitutionnalité':
            decision_cc = step.get('decision')
            decision_cc_date = step.get('date')
            break

    csvfile.writerow([
        dos['id'], # id
        dos.get('long_title'), # Titre
        # TODO: detect propo/pjl in AN doslegs
        'proposition de loi' if dos.get('proposal_type') == 'PPL' else 'projet de loi', # Type de dossier
        dos.get('beginning'), # Date initiale
        dos.get('url_dossier_senat', dos.get('url_dossier_assemblee')), # URL du dossier
        'promulgué' if dos.get('end') else '', # État du dossier
        decision_cc, # Décision du CC
        decision_cc_date, # Date de la décision
        dos.get('end'), # Date de promulgation
        dos.get('law_name'), # Numéro de la loi
        ','.join(dos.get('themes', [])), # Thèmes
        dos['stats']['total_amendements'], # total_amendements
        dos['stats']['total_mots'], # total_mots
        dos.get('short_title'), # short_title
        dos.get('loi_dite'), # Nom commun de la loi
        dos.get('assemblee_id'), # ex: 14-peche_et_chasse
    ])

    if dos['stats']['total_amendements'] == 0:
        status = 'Aucun amendement'
    elif dos['stats']['total_amendements'] == 1:
        status = 'Un amendement'
    else:
        status = '%d amendements' % dos['stats']['total_amendements']

    title = dos.get('short_title')
    if dos.get('loi_dite'):
        title = "%s (%s)" % (upper_first(dos.get('loi_dite')), title)

    maxdate = dos.get('end')
    if not maxdate:
        for step in dos['steps']:
            if step.get('date'):
                maxdate = step.get('enddate') or step.get('date')

    home_json_data.append({
        'total_amendements': dos['stats']['total_amendements'],
        'end': dos.get('end'),
        'maxdate': maxdate,
        'status': status,
        'loi': dos['id'],
        'titre': title
    })

    total_doslegs += 1
    if dos.get('url_jo'):
        total_promulgues += 1

total_encours = total_doslegs - total_promulgues

erreurs = len(glob.glob(os.path.join(API_DIRECTORY, 'logs/*')))
erreurs_encours = len(glob.glob(os.path.join(API_DIRECTORY, 'logs-encours/*')))

max_promulgues = total_promulgues + erreurs
max_encours = total_encours + erreurs_encours
maximum = max_promulgues + max_encours

print(total_doslegs, 'doslegs in csv')
print('%.1f%s (%d/%d)' % (100*total_promulgues/max_promulgues, '%', total_promulgues, max_promulgues), 'de promulgués qui passent')
print('%.1f%s (%d/%d)' % (100*total_encours/max_encours, '%', total_encours, max_encours), 'de textes en cours qui passent')


#### Make home.json

home_json_final = {
    "total": total_promulgues,
    "encours": total_encours,
    "maximum": max_promulgues,
}

TEXTS_PER_COLUMN = 6

most_amended = [dos for dos in sorted(home_json_data, key=lambda x: -x['total_amendements']) if dos['end']]
home_json_final["focus"] = {
    "titre": "Les textes les plus amendés",
    "lien": "Explorer les textes les plus amendés",
    "url": "lois.html?action=quanti",
    "textes": most_amended[:TEXTS_PER_COLUMN],
}

recent = sorted(home_json_data, key=lambda x: x['end'] or "0")
recent = [dos for dos in reversed(recent) if dos['end'] and dos['total_amendements']]
recent = list(recent)
home_json_final["recent"] = {
    "titre": "Les derniers textes promulgués",
    "lien": "Explorer les textes récents",
    "url": "lois.html",
    "textes": recent[:TEXTS_PER_COLUMN],
}

live = sorted(home_json_data, key=lambda x: x['maxdate'])
live = [dos for dos in reversed(live) if not dos['end']]
live = list(live)
home_json_final["live"] = {
    "titre": "Les textes en cours",
    "lien": "Explorer les textes en cours",
    "url": "lois.html?encours",
    "textes": live[:TEXTS_PER_COLUMN],
}

print_json(home_json_final, os.path.join(API_DIRECTORY, 'home.json'))
print('home.json OK')
