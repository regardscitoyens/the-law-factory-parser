# Download the doslegs from the assemblee-nationale.fr directly
# usage: python download_from_AN.py output_dir

import requests, json, sys, slugify, os, bs4, glob

from anpy.dossier import DossierParser
from anpy.utils import json_dumps

INPUT_GLOB = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

files = glob.glob(INPUT_GLOB)
print(len(files), 'files to parse')
for file in files:
    html = open(file).read()
    url = html.split('URL=')[-1].split('-->')[0].strip()

    filepath = OUTPUT_DIR + '/' + slugify.slugify(url) + '.json'
    filepath = filepath.replace('http-www-assemblee-nationale-fr-', '')

    if os.path.exists(filepath):
        print(file, 'already parsed')
        continue

    print('parsing', file)

    result = DossierParser(url, html).parse()
    result = result.to_dict()
    open(filepath, 'w').write(json_dumps(result, indent=4, sort_keys=True, ensure_ascii=False))
