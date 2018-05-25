#!/usr/bin/python

# Add links in texte

import os, sys, re
import urllib.parse
import metslesliens
try:
    from .common import open_json, print_json
except:
    from common import open_json, print_json

def process(dos):
    for step_i, step in enumerate(dos['steps']):
        articles = step.get('articles_completed', step.get('articles'))
        if not articles:
            continue

        for data in articles:
            if data["type"] == "article":
                data['liens'] = []
                for i in range(len(data["alineas"])):
                    text = data["alineas"]["%03d" % (i+1)]
                    for candidat in metslesliens.donnelescandidats(text, 'structuré'):
                        if 'texte' in candidat and not 'relatif' in candidat['texte']:
                            link = text[candidat['index'][0]:candidat['index'][1]]
                            if not re.search( r'(même|présent|précédent) ', link ):
                                data['liens'].append(link)
                            """
                            data['liens'].append({
                                'url': 'https://duckduckgo.com/?q=!ducky+' + urllib.parse.quote_plus(link),
                                'texte': link,
                                'alinea': i,
                                # 'index': candidat['index'],
                            })
                            """
    return dos


if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1])))
