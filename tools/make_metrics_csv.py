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
    dos['Initial size of the law'] = parsed_dos['input_text_length2']
    dos['Final size of the law'] = parsed_dos['output_text_length2']
    dos['Steps in the legislative procedures'] = custom_number_of_steps(parsed_dos['steps'])
    cc_step = [step['source_url'] for step in parsed_dos['steps'] if step.get('stage') == 'constitutionnalité']
    dos['Size Decision CC'] = get_decision_length(cc_step[0]) if cc_step else ''
    dos['Signataires JO'] = count_signataires(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''


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
    dos['Steps in the legislative procedures'] = custom_number_of_steps(parsed_dos['steps'])
    cc_step = [step['source_url'] for step in parsed_dos['steps'] if step.get('stage') == 'constitutionnalité']
    dos['Size Decision CC'] = get_decision_length(cc_step[0]) if cc_step else ''
    dos['Signataires JO'] = count_signataires(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''

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
    dos['Initial size of the law'] = read_text(parse_texte.parse(last_depot['source_url']))
    articles = parse_texte.parse(last_text['source_url'])
    if articles[0].get('definitif'):
        dos['Final size of the law'] = read_text(parse_texte.parse(last_text['source_url']))
    else:
        dos['Final size of the law'] = get_texte_length(parsed_dos['url_jo']) if 'url_jo' in parsed_dos else ''


if __name__ == '__main__':
    enable_requests_cache()
    senat_csv = parse_senat_open_data()
    dossiers_json = find_parsed_doslegs(sys.argv[1])

    random.shuffle(senat_csv)

    sample_for_header = None
    c = 0
    fixed = 0
    for dos in senat_csv:
        print()
        print(dos['URL du dossier'])

        dos['Aneee initiale'] = annee(dos['Date initiale'])

        senat_id = dos['URL du dossier'].split('/')[-1].replace('.html', '')
        if senat_id in dossiers_json:
            print(' - matched')
            c += 1
            parsed_dos = dossiers_json[senat_id]
            try:
                add_metrics(dos, parsed_dos)
                dos['parse_source'] = 'parsed'
                sample_for_header = dos
            except KeyboardInterrupt:
                break
        else:
            # do a custom parsing when the parsed dos is missing
            try:
                dos['parse_source'] = 'adhoc'
                add_metrics_via_adhoc_parsing(dos)
                fixed += 1
            except KeyboardInterrupt:
                break
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print('- adhoc parsing failed', e)
                pass

        if dos.get('Size Decision CC') == -1:
            dos['Size Decision CC'] = ''
        if dos.get('Signataires JO') == -1:
            dos['Signataires JO'] = ''

    print(len(senat_csv), 'dos')
    print(c, 'matched')
    print(fixed, 'fixed')
    senat_csv.sort(key=lambda x: ''.join(reversed(x['Date de promulgation'].split('/'))))

    # output the metrics CSV
    out = os.path.join(sys.argv[1], 'metrics.csv')
    print('output:', out)
    writer = csv.DictWriter(open(out, 'w'), fieldnames=sorted(list(sample_for_header.keys())))
    writer.writeheader()
    for dos in senat_csv:
        writer.writerow(dos)

