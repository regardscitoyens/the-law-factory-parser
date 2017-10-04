# Download the doslegs from the assemblee-nationale.fr directly
# usage: python download_from_AN.py output_dir

import requests, json, sys, slugify, os, bs4

from anpy.dossier import Dossier, InvalidResponseException
from anpy.utils import json_dumps

URLS = [
    'http://www.assemblee-nationale.fr/15/documents/index-dossier.asp',
    'http://www.assemblee-nationale.fr/14/documents/index-dossier.asp',
    'http://www.assemblee-nationale.fr/13/documents/index-dossier.asp',
]

OUTPUT_DIR = sys.argv[1]

for index_url in URLS:
    for link in bs4.BeautifulSoup(requests.get(index_url).text, 'lxml').select('p > a'):
        url = 'http://www.assemblee-nationale.fr' + link.attrs.get('href', '')
        if '/dossiers/' in url:
            filepath = OUTPUT_DIR + '/' + slugify.slugify(url) + '.json'
            print(url)
            if os.path.exists(filepath):
                continue
            try:
                result = Dossier.download_and_build(url)
            except InvalidResponseException as e:
                print(e)
                print()
                continue
            except Exception as e:
                print(e)
                print()
                continue
            result = result.to_dict()
            open(filepath, 'w').write(json_dumps(result, indent=4, sort_keys=True, ensure_ascii=False))
