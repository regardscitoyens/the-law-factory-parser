import json, sys, re
from pprint import pprint as pp
from urllib.parse import urljoin, parse_qs, urlparse, urlunparse

import requests
# import dateparser
from bs4 import BeautifulSoup, Comment


def _log_error(error):
    print('## ERROR ###', error, file=sys.stderr)


def format_date(date):
    parsed = dateparser.parse(date, languages=['fr'])
    return parsed.strftime("%Y-%m-%d")


def clean_url(url):
    if 'legifrance.gouv.fr' in url:
        scheme, netloc, path, params, query, fragment = urlparse(url)
        url_jo_params = parse_qs(query)
        if 'cidTexte' in url_jo_params:
            query = 'cidTexte=' + url_jo_params['cidTexte'][0]
        return urlunparse((scheme, netloc, path, '', query, fragment))
    # url like 'pjl09-518.htmlhttp://www.assemblee-nationale.fr/13/ta/ta0518.asp'
    if url.find('http://') > 0:
        url = 'http://' + url.split('http://')[1]
    return url


def parse(html, url_an=None, verbose=True):
    data = {
        'url_dossier_assemblee': url_an,
    }

    log_error = _log_error
    if not verbose:
        log_error = lambda x: None

    soup = BeautifulSoup(html, 'lxml')

    meta = {}
    for meta in soup.select('meta'):
        if 'name' in meta.attrs:
            meta[meta.attrs['name']] = meta.attrs['content']

    data['steps'] = []
    last_parsed = None
    curr_institution = 'assemblee'
    curr_stage = None
    last_section = None # Travaux des commissions/Discussion en séance publique
    travaux_prep_already = False
    promulgation_step = None
    another_dosleg_inside = None

    url_jo = meta.get('LIEN_LOI_PROMULGUEE')
    if url_jo:
        data['url_jo'] = clean_url(url_jo)
        promulgation_step = {
            'institution': 'gouvernement',
            'stage': 'promulgation',
            'source_url': data['url_jo'],
        }

    for i, line in enumerate(html.split('\n')):

        def parsed():
            nonlocal last_parsed
            last_parsed = BeautifulSoup(line, 'lxml')
            return last_parsed.text.strip()

        if '<font face="ARIAL" size="3" color="#000080">' in line:
            data['long_title'] = parsed()
        if '<br><b><font color="#000099">Travaux des commissions</font></b><br>' in line:
            last_section = parsed()
        if '<p align="center"><b><font color="#000080">Travaux préparatoires</font></b><br>' in line:
            if travaux_prep_already:
                log_error('FOUND ANOTHER DOSLEG INSIDE THE DOSLEG')
                another_dosleg_inside = '\n'.join(html.split('\n')[i:])
                break
            travaux_prep_already = True


        # Senat 1ère lecture, CMP, ...
        if '<font color="#000099" size="2" face="Arial">' in line:
            text = parsed()
            last_section = None
            if 'Dossier en ligne sur le site du Sénat' in text:
                data['url_dossier_senat'] = last_parsed.select('a')[-1].attrs['href']
                text = text.replace('(Dossier en ligne sur le site du Sénat)', '')
            if 'Sénat' in text:
                curr_institution = 'senat'
            elif 'Assemblée nationale' in text:
                curr_institution = 'assemblee'
            elif 'Commission Mixte Paritaire' in text or 'Lecture texte CMP' in text:
                curr_institution = 'CMP'
                curr_stage = 'CMP'
            elif 'Conseil Constitutionnel' in text:
                curr_institution = 'conseil constitutionnel'
                curr_stage = 'constitutionnalité'
                curr_step = None
            elif 'Congrès du Parlement' in text:
                curr_institution = 'congrès'
                curr_stage = 'congrès'
            
            if '1ère lecture' in text:
                curr_stage = '1ère lecture'
            elif '2e lecture' in text:
                curr_stage = '2ème lecture'
            elif 'Nouvelle lecture' in text:
                curr_stage = 'nouv. lect.'
            elif 'Lecture définitive' in text:
                curr_stage = 'l. définitive'
            if not curr_stage:
                curr_stage = text.split('-')[-1].strip().lower()

            if curr_stage == "création de la commission d'enquête":
                log_error('COMMISSION D\'ENQUETE')
                return None

        if '>Proposition de résolution européenne<' in line:
            log_error('PROPOSITION DE RESOLUTION EUROPEENE')
            return None

        curr_step = None
        if 'Rapport portant également sur les propositions' in line:
            continue
        elif '>Projet de loi' in line or '>Proposition de loi' in line or '>Proposition de résolution' in line:
            curr_step = 'depot'

            if curr_stage == 'CMP':
                continue
        elif ">Texte de la commission" in line or '/ta-commission/' in line:
            if len(data['steps']) > 0 and data['steps'][-1]['step'] == 'commission':
                log_error('DOUBLE COMMISSION LINE: %s' % line)
                continue
            curr_step = 'commission'
        elif '/ta/' in line or '/tas' in line:
            curr_step = 'hemicycle'
        elif '/rapports/' in line and last_section and 'commissions' in last_section:
            if len(data['steps']) > 0 and data['steps'][-1]['step'] == 'commission':
                log_error('DOUBLE COMMISSION LINE: %s' % line)
                continue
            curr_step = 'commission'

        if curr_step:
            text = parsed()
            links = [a.attrs.get('href') for a in last_parsed.select('a')]
            links = [href for href in links if href and 'fiches_id' not in href and '/senateur/' not in href]
            if not links:
                log_error('NO LINK IN LINE: %s' % (line,))
                continue
            urls_raps = []
            urls_others = []
            for href in links:
                if '/rap/' in href or '/rapports/' in href:
                    urls_raps.append(href)
                else:
                    urls_others.append(href)

            if len(urls_others) > 0:
                url = urls_others[0]
            else:
                url = urls_raps[0]

            if 'fiches_id' in url:
                import pudb;pu.db

            url = clean_url(urljoin(url_an, url))
            data['steps'].append({
                'institution': curr_institution,
                'stage': curr_stage,
                'step': curr_step,
                'source_url': url,
                # '<text>': text,
            })


        if 'publiée au Journal Officiel' in line:
            text = parsed()
            links = [a.attrs['href'] for a in last_parsed.select('a') if 'legifrance' in a.attrs.get('href', '')]
            if not links:
                log_error('NO GOOD LINK IN LINE: %s' % (line,))
                continue
            promulgation_step = {
                'institution': 'gouvernement',
                'stage': 'promulgation',
                'source_url': clean_url(links[-1]),
            }

        if 'Le Gouvernement a engagé la procédure accélérée' in line:
            data['urgence'] = True

    if promulgation_step:
        data['steps'].append(promulgation_step)

    if another_dosleg_inside:
        others = parse(another_dosleg_inside, url_an)
        if others:
            return [data] + others
    return [data]


if __name__ == '__main__':
    url = sys.argv[1]
    if url.startswith('http'):
        html = requests.get(url).text
        data = parse(html, url)
    else:
        html = open(url).read()
        url = html.split('-- URL=')[-1].split('-->')[0].strip()
        data = parse(html, url)
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))