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
    
    filepath = 'an_dossiers/' + slugify.slugify(url) + '.json'
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
    result['extra_from_json'] = dossier
    open(filepath, 'w').write(json_dumps(result, indent=4, sort_keys=True, ensure_ascii=False))
