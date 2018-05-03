import os, sys, glob, traceback

import parse_one

from tools.common import open_json


API_DIRECTORY = sys.argv[1]

already_done = {}
for jsondos in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json')):
    dos = open_json(jsondos)
    if dos.get('url_jo'):
        already_done[dos.get('url_dossier_senat')] = True

for url in sys.stdin:
    print()
    print('======')
    url = url.strip()
    if url in already_done:
        print('  + passed, already done:', url)
        continue
    try:
        parse_one.process(API_DIRECTORY, url)
    except KeyboardInterrupt:
        break
    except Exception as e:
        traceback.print_exc()
