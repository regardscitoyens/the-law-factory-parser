# Download the doslegs from the assemblee-nationale.fr directly
# usage: python download_from_AN.py output_dir

import requests, json, sys, slugify, os, bs4

from urllib.parse import urljoin, urlparse


URLS = [
    'http://www.assemblee-nationale.fr/15/documents/index-dossier.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-dossier.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-dossier.asp',

    'http://www.assemblee-nationale.fr/15/documents/index-conventions.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-conventions.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-conventions.asp',

    'http://www.assemblee-nationale.fr/15/documents/index-proposition.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-proposition.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-proposition.asp',

    'http://www.assemblee-nationale.fr/15/documents/index-projets.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-projets.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-projets.asp',

    'http://www.assemblee-nationale.fr/13/documents/index-depots.asp',

    # TODO: http://www2.assemblee-nationale.fr/documents/liste/%28type%29/propositions-loi
]


def normalized_filename(url):
    scheme, netloc, path, params, query, fragment = urlparse(url)
    return slugify.slugify(path.replace('dossiers/', '') \
        .replace('.asp', ''))


OUTPUT_DIR = sys.argv[1]
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


for index_url in URLS:
    print('finding links in', index_url)
    for link in bs4.BeautifulSoup(requests.get(index_url).text, 'lxml').select('a'):
        url = urljoin('http://www.assemblee-nationale.fr', link.attrs.get('href', ''))
        if '/dossiers/' in url:
            url = url.split('#')[0]
            filepath = OUTPUT_DIR + '/' + normalized_filename(url)
            filepath = filepath.replace('http-www-assemblee-nationale-fr-', '')
            if os.path.exists(filepath):
                continue
            print('downloading', url)
            resp = requests.get(url)
            if resp.status_code < 300:
                if "vous prie d'accepter toutes ses excuses pour le" in resp.text:
                    print('ERROR IN RESP', resp.status_code)
                else:
                    open(filepath, 'w').write(resp.text + '\n\n<!-- URL=%s -->' % url)
            else:
                print('INVALID RESPONSE:', resp.status_code)