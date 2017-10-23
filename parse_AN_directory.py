# Download the doslegs from the assemblee-nationale.fr directly
# usage: python download_from_AN.py output_dir

import requests, json, sys, slugify, os, bs4, glob, tqdm

from anpy.dossier2 import parse

INPUT_GLOB = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

files = glob.glob(INPUT_GLOB)
print(len(files), 'files to parse')
for file in tqdm.tqdm(files):
    html = open(file).read()
    url = html.split('URL=')[-1].split('-->')[0].strip()

    filepath = OUTPUT_DIR + '/' + slugify.slugify(url)
    filepath = filepath.replace('http-www-assemblee-nationale-fr-', '')

    if os.path.exists(filepath):
        # print(file, 'already parsed')
        continue

    # print('parsing', file)

    result = parse(html, url, verbose=False)
    if result:
        for i, dos in enumerate(result):
            full_filepath = filepath
            if i != 0:
                full_filepath += '_%d' % i
            open(full_filepath, 'w').write(json.dumps(dos, indent=4, sort_keys=True, ensure_ascii=False))
    else:
        open(filepath, 'w').write(json.dumps(None, indent=4, sort_keys=True, ensure_ascii=False))