import os, sys, glob, traceback, json

import parse_one


API_DIRECTORY = sys.argv[1]

alread_done = {json.load(open(dos)).get('url_dossier_senat') for dos \
                in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json'))}

for url in sys.stdin:
    print()
    print('======')
    url = url.strip()
    if url in alread_done:
        print('  + passed, already done:', url)
        continue

    try:
        parse_one.process(API_DIRECTORY, url, disable_cache=True)
    except Exception as e:
        traceback.print_exc()
