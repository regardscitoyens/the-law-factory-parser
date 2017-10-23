# Download all the ANPY dosleg in the json at
# data.assemblee-nationale.fr/travaux-parlementaires/dossiers-legislatifs
# usage: python download_from_json.py downloads/an_json/

import requests, json, sys, slugify, os, zipfile
from io import BytesIO
from anpy.dossier import Dossier, InvalidResponseException
from anpy.utils import json_dumps

print('downloading Dossiers_Legislatifs_XIV.json...')
doslegs_resp = requests.get('http://data.assemblee-nationale.fr/static/openData/repository/LOI/dossiers_legislatifs/Dossiers_Legislatifs_XIV.json.zip')
doslegs_zip = zipfile.ZipFile(BytesIO(doslegs_resp.content))
DATA = json.loads(doslegs_zip.open('Dossiers_Legislatifs_XIV.json').read().decode('utf-8'))

OUTPUT_DIR = sys.argv[1]
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for dossier in DATA['export']['dossiersLegislatifs']['dossier']:
    url = 'http://www.assemblee-nationale.fr/{}/dossiers/{}.asp'.format(
        dossier['dossierParlementaire']['legislature'], dossier['dossierParlementaire']['titreDossier']['titreChemin'])
    
    filepath = OUTPUT_DIR + slugify.slugify(url)
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