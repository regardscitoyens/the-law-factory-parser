import json, glob, os, sys, csv, random, traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lawfactory_utils.urls import enable_requests_cache
from senapy.dosleg import opendata

from tools.process_conscons import get_decision_length
from tools.process_jo import count_signataires, get_texte_length
from tools import parse_texte
from parse_one import *


def annee(date):
    return int(date.split('/')[-1])


def parse_senat_open_data():
    senat_csv = opendata.fetch_csv()
    # filter non-promulgués
    senat_csv = [dos for dos in senat_csv if dos['Date de promulgation']]
    # filter after 1998
    senat_csv = [dos for dos in senat_csv if annee(dos['Date initiale']) >= 2008]
    return senat_csv


def find_parsed_doslegs(api_directory):
    dossiers_json = {}
    for path in glob.glob(os.path.join(api_directory, 'dossiers_*.json')):
        for dos in json.load(open(path))['dossiers']:
            if dos.get('senat_id'):
                dossiers_json[dos['senat_id']] = dos
    print(len(dossiers_json), 'parsed found')
    return dossiers_json


def custom_number_of_steps(steps):
    # count the number of coulumns minus CMP hemicycle
    c = 0
    for step in steps:
        if step['stage'] == 'CMP':
            if step['step'] == 'commission':
                c += 1
        elif step.get('step') == 'hemicycle':
            c += 2
    return c


def read_text(articles):
    texte = []
    for art in articles:
        if 'alineas' in art:
            for key in sorted(art['alineas'].keys()):
                if art['alineas'][key] != '':
                    texte.append(art['alineas'][key])
    return len("\n".join(texte))


def add_metrics(dos, parsed_dos):
    parsed_dos = dossiers_json[senat_id]
    dos['Taille initiale'] = parsed_dos['input_text_length2']
    dos['Taille finale'] = parsed_dos['output_text_length2']
    dos['Étapes de la procédure'] = custom_number_of_steps(parsed_dos['steps'])
    cc_step = [step['source_url'] for step in parsed_dos['steps'] if step.get('stage') == 'constitutionnalité']
    dos['Taille de la décision du CC'] = get_decision_length(cc_step[0]) if cc_step else ''
    dos['Signataires au JO'] = count_signataires(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''


def add_metrics_via_adhoc_parsing(dos):
    senat_dos = download_senat(dos['URL du dossier'])
    if not senat_dos:
        print('  /!\ INVALID SENAT DOS')

    # Add AN version if there's one
    if 'url_dossier_assemblee' in senat_dos:
        an_dos = download_an(senat_dos['url_dossier_assemblee'], senat_dos['url_dossier_senat'])
        if 'url_dossier_senat' in an_dos:
            assert an_dos['url_dossier_senat'] == senat_dos['url_dossier_senat']
        parsed_dos = merge_senat_with_an(senat_dos, an_dos)
    else:
        parsed_dos = senat_dos
    dos['Étapes de la procédure'] = custom_number_of_steps(parsed_dos['steps'])
    cc_step = [step['source_url'] for step in parsed_dos['steps'] if step.get('stage') == 'constitutionnalité']
    dos['Taille de la décision du CC'] = get_decision_length(cc_step[0]) if cc_step else ''
    dos['Signataires au JO'] = count_signataires(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''

    last_depot = None
    for step in parsed_dos['steps']:
        if not step.get('step') == 'depot':
            break
        last_depot = step
    last_text = None
    for step in reversed(parsed_dos['steps']):
        last_text = step
        if step.get('step') == 'hemicycle':
            break
        if step.get('step') == 'commission':
            raise Exception('commission as last step')
    dos['Taille initiale'] = read_text(parse_texte.parse(last_depot['source_url']))
    articles = parse_texte.parse(last_text['source_url'])
    if articles[0].get('definitif'):
        dos['Taille finale'] = read_text(parse_texte.parse(last_text['source_url']))
    else:
        dos['Taille finale'] = get_texte_length(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''

def clean_type_dossier(dos):
    # TODO
    # existing values:
#    594 projet de loi
#      2 projet de loi  constitutionnelle
#     11 projet de loi de financement de la sécurité sociale
#      1 projet de loi de financement rectificative de la sécurité soc
#     10 projet de loi de finances
#     23 projet de loi de finances rectificative
#      1 projet de loi de programmation
#      7 projet de loi de règlement
#     32 projet de loi organique
#    171 proposition de loi
#     15 proposition de loi organique
    # desired values:
#    1 = ordinaire
#    2 = ordinaire, accord international
#    3 = organique
#    4 = constitutionnelle
#    5 = ratification d&#39;ordonnances
#    6 = textes budgétaires (projet de loi de finances, projets de la loi de financement de la sécurité sociale et les textes rectificatifs)
    return dos

HEADERS = [
    "Numéro de la loi",
    "Titre",
    "Année initiale",
    "Date initiale",
    "Date de promulgation",
    "Taille initiale",
    "Taille finale",
    "Initiative du texte",
    "Type de texte",
    "Étapes de la procédure",
    "CMP",
    "Décision du CC",
    "Date de la décision du CC",
    "Taille de la décision du CC",
    "Signataires au JO",
    "Thèmes",
    "URL du dossier",
    "Source données"
]

# TODO:
# - clean types de dossier
# - fill CMP field
# - check accords internationaux : taille should include annexes and finale == initiale

if __name__ == '__main__':
    enable_requests_cache()
    senat_csv = parse_senat_open_data()
    dossiers_json = find_parsed_doslegs(sys.argv[1])

    random.shuffle(senat_csv)

    c = 0
    fixed = 0
    for dos in senat_csv:
        print()
        print(dos['URL du dossier'])

        dos['Année initiale'] = annee(dos['Date initiale'])

        dos['Initiative du texte'] = upper_first(dos['Type de dossier'].split(' de loi ')[0]) + ' de loi'
        dos['Type de texte'] = clean_type_dossier(dos['Type de dossier'])
        dos['CMP'] = "TODO"

        if not dos["Décision du CC"]:
            dos["Décision du CC"] = "pas de saisine"
        dos["Date de la décision du CC"] = dos["Date de la décision"]

        senat_id = dos['URL du dossier'].split('/')[-1].replace('.html', '')
        if senat_id in dossiers_json:
            print(' - matched')
            c += 1
            parsed_dos = dossiers_json[senat_id]
            try:
                add_metrics(dos, parsed_dos)
                dos['Source données'] = 'LaFabrique'
            except KeyboardInterrupt:
                break
        else:
            # do a custom parsing when the parsed dos is missing
            try:
                dos['Source données'] = 'parsing ad-hoc'
                add_metrics_via_adhoc_parsing(dos)
                fixed += 1
            except KeyboardInterrupt:
                break
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print('- adhoc parsing failed', e)
                pass

        if dos.get('Taille de la décision du CC') == -1:
            dos['Taille de la décision du CC'] = ''
        if dos.get('Signataires au JO') == -1:
            dos['Signataires au JO'] = ''

    print(len(senat_csv), 'dos')
    print(c, 'matched')
    print(fixed, 'fixed')
    senat_csv.sort(key=lambda x: ''.join(reversed(x['Date de promulgation'].split('/'))))

    # output the metrics CSV
    out = os.path.join(sys.argv[1], 'metrics.csv')
    print('output:', out)
    writer = csv.DictWriter(open(out, 'w'), fieldnames=HEADERS)
    writer.writeheader()
    for dos in senat_csv:
        writer.writerow(dos)

