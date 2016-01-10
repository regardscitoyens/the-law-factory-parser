# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

import dateparser
import re
import urlparse

SENAT_URL = 'http://www.senat.fr'
DOSSIER_ID_RE = re.compile('dossier-legislatif/([^/]+)\.html$')
LEGISLATURE_RE = re.compile('(\d+)-\d+')
DATE_RE = re.compile('(?: le |\()(\d+\w*\s+\w+\s+\d{4})', re.UNICODE)


def parse_dossier_senat(url, html):
    soup = BeautifulSoup(html)

    dossier_id = DOSSIER_ID_RE.search(url).groups()[0]

    return {
        'url': url,
        'dossier_id': dossier_id,
        'legislature': LEGISLATURE_RE.search(dossier_id).groups()[0],
        'short_title': soup.find('title').text.split(' - ')[0],
        'title': soup.find('meta', attrs={'name': 'Description'})['content'],
        'steps': list(step_gen(soup))
    }


def step_gen(soup):
    current_stage = None

    for element in soup.find_all(id=re.compile('timeline-\d+')):
        stage, step = find_stage_and_step(element)

        if stage:
            current_stage = stage

        documents = list(parse_documents(element))

        if not documents:
            continue

        yield {
            'stage': current_stage,
            'step': step,
            'documents': list(parse_documents(element)),
            'place': find_place(documents) if current_stage != 'CMP' else 'CMP'
        }


def parse_documents(element):
    for li in element.find_all('li'):
        if li.find_all('ul'):
            continue

        for anchor in li.find_all('a'):
            if not anchor.has_attr('href') or 'senateur' in anchor['href']:
                continue

            document_type = ''

            if anchor.text.startswith('Texte'):
                document_type = 'texte'
            elif anchor.text.startswith('Rapport'):
                document_type = 'rapport'
            elif anchor.text.startswith('Avis'):
                document_type = 'avis'
            elif anchor.text.startswith('Amendements'):
                document_type = 'amendement'
            elif anchor.text.startswith('Compte'):
                document_type = 'compte-rendu'
            elif anchor.text.startswith(u'Résumé des débats'):
                document_type = 'debates-summary'
            elif anchor.text.startswith('scrutins'):
                document_type = 'scrutin'

            yield {
                'type': document_type,
                'url': urlparse.urljoin(SENAT_URL, anchor['href']),
                'date': parse_date(li.text)
            }


def find_place(documents):
    first_url = documents[0]['url']

    if 'assemblee-nationale.fr' in first_url:
        return 'assemblee'

    if 'senat.fr' in first_url:
        return 'senat'

    if 'conseil-constitutionnel.fr' in first_url:
        return 'conseil constitutionnel'

    if 'legifrance.gouv.fr' in first_url:
        return 'gouvernement'


def find_stage_and_step(element):
    picto = element.find(class_='picto')
    stage = picto.find('em').text if picto and picto.find('em') else ''
    src = element.find(attrs={'href': '#block-timeline'}).find('img')['src']

    if src.endswith('01_on.png'):
        return stage, 'depot'

    if src.endswith('02_on.png'):
        return stage, 'depot'

    if src.endswith('03_on.png'):
        return stage, 'commission'

    if src.endswith('04_on.png'):
        return stage, 'hemicycle'

    if src.endswith('05_on.png'):
        return 'CMP', 'CMP'

    if src.endswith('06_on.png'):
        return 'constitutionnalité', 'CC'

    if src.endswith('07_on.png'):
        return 'promulgation', 'JO'


def parse_date(text):
    match = DATE_RE.search(text)

    if not match:
        return ''

    date = dateparser.parse(match.groups()[0], languages=['fr'])

    return date.strftime('%Y-%m-%d') if date else ''


if __name__ == '__main__':
    import json
    import requests
    import sys

    dossier_url = sys.argv[1]
    print json.dumps(parse_dossier_senat(dossier_url, requests.get(dossier_url).content), indent=4)