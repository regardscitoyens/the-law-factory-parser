# Download all the ANPY dosleg in the json at
# data.assemblee-nationale.fr/travaux-parlementaires/dossiers-legislatifs
# usage: python download_from_json.py dosleg.json

import requests, json, sys, slugify, os

from anpy.dossier import Dossier, InvalidResponseException
from anpy.utils import json_dumps

DATA = json.load(open(sys.argv[1]))

for dossier in DATA['export']['dossiersLegislatifs']['dossier']:
    url = 'http://www.assemblee-nationale.fr/{}/dossiers/{}.asp'.format(
        dossier['dossierParlementaire']['legislature'], dossier['dossierParlementaire']['titreDossier']['titreChemin'])
    
    filepath = sys.argv[2] + slugify.slugify(url)
    filepath = filepath.replace('http-www-assemblee-nationale-fr-', '')
    print('downloading', url)
    if os.path.exists(filepath):
        continue
    resp = requests.get(url)
    if resp.status_code < 300:
        if "vous prie d'accepter toutes ses excuses pour le" in resp.text:
            print('ERROR IN RESP', resp.status_code)
        else:
            open(filepath, 'w').write(resp.text + '\n\n<!-- URL=%s -->' % url)
    else:
        print('INVALID RESPONSE:', resp.status_code)