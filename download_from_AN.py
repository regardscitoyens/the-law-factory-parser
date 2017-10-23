# Download the doslegs from the assemblee-nationale.fr directly
# usage: python download_from_AN.py output_dir

import requests, json, sys, slugify, os, bs4

from anpy.dossier import Dossier, InvalidResponseException
from anpy.utils import json_dumps

URLS = [
    'http://www.assemblee-nationale.fr/15/documents/index-dossier.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-dossier.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-dossier.asp',

    'http://www.assemblee-nationale.fr/15/documents/index-conventions.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-conventions.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-conventions.asp',
]

OUTPUT_DIR = sys.argv[1]
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


for index_url in URLS:
    print('finding links in', index_url)
    for link in bs4.BeautifulSoup(requests.get(index_url).text, 'lxml').select('a'):
        url = 'http://www.assemblee-nationale.fr' + link.attrs.get('href', '')
        if '/dossiers/' in url:
            url = url.split('#')[0]
            filepath = OUTPUT_DIR + '/' + slugify.slugify(url)
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