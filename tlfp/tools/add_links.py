#!/usr/bin/python

# Add links in texte

import os, sys, re
import urllib.parse
import metslesliens

from .common import open_json, print_json


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
                        if 'texte' in candidat and 'relatif' not in candidat['texte']:
                            link_text = text[candidat['index'][0]:candidat['index'][1]]
                            link_text = re.sub(r'^(aux?|les?|la|du|des)(dite?s?)? ', '', link_text, 0, re.I)
                            link_text = re.sub(r"^l'", '', link_text, 0, re.I)
                            if not re.search(r'(même|présente?|précédente?) ', link_text ):
                                """
                                link = {
                                    'texte': link_text
                                }
                                if 'eli_alias' in candidat:
                                    link['url'] = "https://www.legifrance.gouv.fr/" + candidat['eli_alias']
                                """
                                data['liens'].append(link_text)
    return dos


if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1])))
