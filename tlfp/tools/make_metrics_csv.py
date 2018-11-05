import glob, os, sys, csv, random, traceback

from lawfactory_utils.urls import enable_requests_cache
from senapy.dosleg import opendata

from tlfp.parse_one import *
from tlfp.tools import parse_texte
from tlfp.tools.common import upper_first, format_date, datize, strip_text, open_json
from tlfp.tools.process_conscons import get_decision_length
from tlfp.tools.process_jo import count_signataires, get_texte_length


def annee(date):
    return int(date.split('/')[-1])


def find_last_depot(steps):
    last_depot = None
    for step in steps:
        if not step.get('step') == 'depot':
            break
        last_depot = step
    return last_depot


def parse_senat_open_data(run_old=False):
    senat_csv = opendata.fetch_csv()
    # filter non-promulgués
    senat_csv = [dos for dos in senat_csv if dos['Date de promulgation']]
    # filter before 2008
    if run_old:
        senat_csv = [dos for dos in senat_csv if annee(dos['Date initiale']) < 2008]
    else:
        senat_csv = [dos for dos in senat_csv if annee(dos['Date initiale']) >= 2008]
    senat_csv.sort(key=lambda dos: annee(dos['Date initiale']))
    return senat_csv


def find_parsed_doslegs(api_directory):
    dossiers_json = {}
    for path in glob.glob(os.path.join(api_directory, '**/procedure.json'), recursive=True):
        dos = open_json(path)
        if dos.get('senat_id'):
            dossiers_json[dos['senat_id']] = dos
    print(len(dossiers_json), 'parsed found')
    return dossiers_json


def custom_number_of_steps(steps):
    # count the number of columns minus CMP hemicycle
    c = 0
    for step in steps:
        if step.get('stage') == 'CMP':
            if step['step'] == 'commission':
                c += 1
        elif step.get('step') == 'hemicycle':
            c += 2
    return c


def count_echecs(steps):
    return len([s for s in steps if s.get('echec')])


def get_CMP_type(steps):
    steps = [s for s in steps if s.get('stage') == 'CMP']
    if not steps:
        return 'pas de CMP'
    if len(steps) == 3 and not any([s.get('echec') for s in steps]):
        return 'succès'
    return 'échec'


def read_text(articles):
    texte = []
    for art in articles:
        if 'alineas' in art:
            for key in sorted(art['alineas'].keys()):
                if art['alineas'][key] != '':
                    texte.append(strip_text(art['alineas'][key]))
    return len("\n".join(texte))


def add_metrics(dos, parsed_dos, fast=False):
    parsed_dos = dossiers_json[senat_id]
    dos['Titre court'] = parsed_dos['short_title']
    dos['Type de procédure'] = "accélérée" if parsed_dos['urgence'] else "normale"
    dos['Étapes de la procédure'] = custom_number_of_steps(parsed_dos['steps'])
    dos['Étapes échouées'] = count_echecs(parsed_dos['steps'])
    dos['CMP'] = get_CMP_type(parsed_dos['steps'])
    cc_step = [step['source_url'] for step in parsed_dos['steps'] if step.get('stage') == 'constitutionnalité']
    dos['URL CC'] = cc_step[0] if cc_step else ''
    if not fast:
        dos['Taille de la décision du CC'] = get_decision_length(cc_step[0]) if cc_step else ''
        dos['Signataires au JO'] = count_signataires(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''
    dos['URL JO'] = parsed_dos['url_jo'] if 'url_jo' in parsed_dos else ''

    dos['Taille finale'] = parsed_dos['stats']['output_text_length']
    dos['Taille initiale'] = parsed_dos['stats']['input_text_length']
    dos['Proportion de texte modifié'] = parsed_dos['stats']['ratio_texte_modif']
    dos["Nombre initial d'articles"] = parsed_dos['stats']['total_input_articles']
    dos["Nombre final d'articles"] = parsed_dos['stats']['total_output_articles']
    dos["Croissance du nombre d'articles"] = parsed_dos['stats']['ratio_articles_growth']
    dos["Nombre de mots prononcés"] = parsed_dos['stats']['total_mots']
    dos["Nombre d'intervenants"] = parsed_dos['stats']['total_intervenants']
    dos["Nombre d'interventions"] = parsed_dos['stats']['total_interventions']
    dos["Nombre de séances"] = parsed_dos['stats']['total_seances']
    dos["Nombre de séances à l'Assemblée"] = parsed_dos['stats']['total_seances_assemblee']
    dos["Nombre de séances au Sénat"] = parsed_dos['stats']['total_seances_senat']
    dos["Dernière lecture"] = parsed_dos['stats']['last_stage']

    dos['Textes cités'] = ';'.join(parsed_dos['textes_cites'])
    dos['Nombre de textes cités'] = len(parsed_dos['textes_cites'])

    dos['URL OpenData La Fabrique'] = 'https://www.lafabriquedelaloi.fr/api/%s/' % parsed_dos['id']


def add_metrics_via_adhoc_parsing(dos, log=sys.stderr):
    senat_dos = download_senat(dos['URL du dossier'], log=log)
    if not senat_dos:
        print('  /!\ INVALID SENAT DOS')
        return

    # Add AN version if there's one
    parsed_dos = senat_dos
    if 'url_dossier_assemblee' in senat_dos:
        an_dos = download_an(senat_dos['url_dossier_assemblee'], senat_dos['url_dossier_senat'], log=log)
        if 'url_dossier_senat' in an_dos and are_same_doslegs(senat_dos, an_dos):
            parsed_dos = merge_senat_with_an(senat_dos, an_dos)
    dos['Titre court'] = parsed_dos['short_title']
    dos['Type de procédure'] = "accélérée" if parsed_dos['urgence'] else "normale"
    dos['Étapes de la procédure'] = custom_number_of_steps(parsed_dos['steps'])
    dos['Étapes échouées'] = count_echecs(parsed_dos['steps'])
    dos['CMP'] = get_CMP_type(parsed_dos['steps'])
    cc_step = [step['source_url'] for step in parsed_dos['steps'] if step.get('stage') == 'constitutionnalité']
    dos['Taille de la décision du CC'] = get_decision_length(cc_step[0]) if cc_step else ''
    dos['URL CC'] = cc_step[0] if cc_step else ''
    dos['Signataires au JO'] = count_signataires(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''
    dos['URL JO'] = parsed_dos['url_jo'] if 'url_jo' in parsed_dos else ''

    last_depot = find_last_depot(parsed_dos['steps'])
    last_text = None
    for step in reversed(parsed_dos['steps']):
        last_text = step
        if step.get('step') == 'hemicycle':
            break
        if step.get('step') == 'commission':
            raise Exception('commission as last step')

    if 'source_url' in last_text:
        try:
            articles = parse_texte.parse(last_text['source_url'])
            if articles and articles[0].get('definitif'):
                dos['Taille finale'] = read_text(parse_texte.parse(last_text['source_url']))
            else:
                dos['Taille finale'] = get_texte_length(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''
        except:
            print("WARNING: Taille finale impossible to evaluate")

    try:
        input_text_length = read_text(parse_texte.parse(last_depot['source_url']))
        if input_text_length > 0:
            dos['Taille initiale'] = input_text_length
    except:
        print("WARNING: Taille initiale impossible to evaluate")

    # TODO
    # dos['Proportion de texte modifié'] = ...
    # dos["Nombre initial d'articles"] = ...
    # dos["Nombre final d'articles"] = ...
    # dos["Croissance du nombre d'articles"] = ...


def clean_type_dossier(dos):
#   TODO ?  propositions de résolution ? (attention : statut = adopté pas promulgué)
    typ = dos['Type de dossier'].lower()
    for t in ['constitutionnel', 'organique']:
        if t in typ:
            return t
    for t in ['finance', 'règlement']:
        if t in typ:
            return 'budgétaire'
    tit = dos['Titre'].lower()
    # lois de programmation budgétaire seem to follow regular procédures, so set as programmation rather than budgétaire
    for t in ['programmation', 'loi de programme']:
        if t in tit:
            return 'programmation'
    for t in ['financement de la sécurité', 'règlement des comptes']:
        if t in tit:
            return 'budgétaire'
    if 'accord international' not in tit:
        if (' ratifi' in tit and 'ordonnance' in tit.split(' ratifi')[1]):
            return "ratification d'ordonnances"
        for t in [
            "autorisant le Gouvernement",
            "habilitant le gouvernement",
            "habilitation du Gouvernement",
            "habilitation à prendre par ordonnance",
            "loi d'habilitation",
            "transposition par ordonnances"
        ]:
            if t in tit:
                return "habilitation d'ordonnances"
    if typ.startswith('projet'):
        for t in ['autorisa', 'approba', 'ratifi', ' accord ', 'amendement', 'convention']:
            if t in tit:
                tit2 = " ".join(tit.split(t)[1:])
                for d in ['accord', 'avenant', 'adhésion', 'traité', 'france',
                  'gouvernement français', 'gouvernement d', 'coopération',
                  'protocole', 'arrangement', 'approbation de la décision',
                  'convention', 'ratification de la décision', 'principauté',
                  'international']:
                    if d in tit2:
                        return 'accord international'
    #for t in ["dispositions d'adaptation", 'transposition de la directive', 'portant adaptation']:
    #    if t in tit:
    #        return 'transposition EU'
    return 'ordinaire'


HEADERS = [
    "Numéro de la loi",
#   "IDs internes/institutions"
    "Titre",
    "Titre court",
    "Année initiale",
    "Date initiale",
    "Date de promulgation",
    "Durée d'adoption",
    "Initiative du texte",
    "Taille initiale",
    "Taille finale",
#   "Proportion de texte allongé"
    "Proportion de texte modifié",
    "Nombre initial d'articles",
    "Nombre final d'articles",
    "Croissance du nombre d'articles",
#   "Nombre d'articles inchangés",
#   "Proportion d'articles inchangés",
#   "Nombre initial d'alinéas",
#   "Nombre final d'alinéas",
#   "Nombre d'amendements déposés (+ ventilation Gouv/AN/Sénat)",
#   "Nombre d'amendements adoptés (+ ventilation Gouv/AN/Sénat)",
    "Nombre de mots prononcés", # (+ ventilation Gouv/AN/Sénat)
    "Nombre d'interventions",
    "Nombre d'intervenants",
    "Nombre de séances",
    "Nombre de séances à l'Assemblée",
    "Nombre de séances au Sénat",
    "Dernière lecture", # exemple d'application: si lecture déf., alors il y a beaucoup de chance que le Sénat se soit fait écrasé/bypassé
    "Type de texte",
    "Type de procédure",
    "Étapes de la procédure",
    "Étapes échouées",
    "CMP",
    "Décision du CC",
    "Date de la décision du CC",
    "Taille de la décision du CC",
    "Textes cités",
    "Nombre de textes cités",
    "Signataires au JO",
    "Thèmes",
    "URL du dossier",
    "URL JO",
    "URL CC",
    "URL OpenData La Fabrique",
    "Source données",
]


# TODO:
# - check accords internationaux : taille should include annexes and finale == initiale

if __name__ == '__main__':
    verbose = "--quiet" not in sys.argv
    fast_mode = "--fast" in sys.argv # no network requests
    if not verbose:
        sys.argv.remove("--quiet")
    args = [arg for arg in sys.argv[1:] if '--' not in arg]
    run_old = len(args) > 1
    enable_requests_cache()
    senat_csv = parse_senat_open_data(run_old=run_old)
    dossiers_json = find_parsed_doslegs(args[0])

    # random.shuffle(senat_csv)

    # silence the output if we use the --quiet flag
    with log_print(only_log=not verbose) as log:
        c = 0
        fixed = 0
        for dos in senat_csv:
            if verbose:
                print()
                print(dos['URL du dossier'])

            dos['Année initiale'] = annee(dos['Date initiale'])
            dos['Date initiale'] = format_date(dos['Date initiale'])
            dos['Date de promulgation'] = format_date(dos['Date de promulgation'])
            dos["Durée d'adoption"] = (datize(dos["Date de promulgation"]) - datize(dos["Date initiale"])).days + 1

            dos['Initiative du texte'] = upper_first(dos['Type de dossier'].split(' de loi')[0]) + ' de loi'
            dos['Type de texte'] = clean_type_dossier(dos)

            senat_id = dos['URL du dossier'].split('/')[-1].replace('.html', '')
            if senat_id in dossiers_json:
                if verbose:
                    print(' - matched')
                c += 1
                parsed_dos = dossiers_json[senat_id]
                try:
                    add_metrics(dos, parsed_dos, fast=fast_mode)
                    dos['Source données'] = 'LaFabrique'
                except KeyboardInterrupt:
                    break
            elif not fast_mode:
                # do a custom parsing when the parsed dos is missing
                try:
                    dos['Source données'] = 'parsing ad-hoc'
                    add_metrics_via_adhoc_parsing(dos, log=log)
                    fixed += 1
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    traceback.print_tb(e.__traceback__)
                    print('- adhoc parsing failed for', dos['URL du dossier'], e)
                    continue

            if not dos["Décision du CC"]:
                if dos.get("URL CC"):
                    dos["Décision du CC"] = "conforme"
                else:
                    dos["Décision du CC"] = "pas de saisine"
            elif not dos.get("URL CC"):
                dos["Décision du CC"] = "pas de saisine"
            dos["Date de la décision du CC"] = format_date(dos["Date de la décision"])
            if dos.get('Taille de la décision du CC') == -1:
                dos['Taille de la décision du CC'] = ''
            if dos.get('Signataires au JO') == -1:
                dos['Signataires au JO'] = ''

    print(len(senat_csv), 'dos')
    print(c, 'matched')
    print(fixed, 'fixed')
    senat_csv.sort(key=lambda x: x['Date de promulgation'])

    # output the metrics CSV
    out = os.path.join(sys.argv[1], 'metrics%s.csv' % ('-old' if run_old else ''))
    print('output:', out)
    writer = csv.DictWriter(open(out, 'w'), fieldnames=HEADERS, extrasaction='ignore')
    writer.writeheader()
    for dos in senat_csv:
        writer.writerow(dos)
