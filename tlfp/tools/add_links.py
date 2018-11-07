#!/usr/bin/python

# Add links in texte

import sys, re
import metslesliens

from .common import open_json, print_json

STATS_BLACKLIST = [
    'loi',
    'ordonnance',
    'décret',
    'arrété',
    'circulaire',
    'directive',
    'règlement'
]


def get_code(candidat):
    code = candidat['texte']['nom'].lower()
    for prefix in STATS_BLACKLIST:
        if code.startswith(prefix):
            return None

    if 'numero' in candidat['texte']:
        code += ' ' + candidat['texte']['numero']
    elif 'date' in candidat['texte']:
        code += ' du ' + candidat['texte']['date']

    return code


def process(dos):
    for step_i, step in enumerate(dos['steps']):
        articles = step.get('articles_completed', step.get('articles'))
        if not articles:
            continue
        dos["textes_cites"] = [] # only keep the latest version
        for data in articles:
            if data["type"] == "article":
                data['liens'] = []
                for i in range(len(data["alineas"])):
                    text = data["alineas"]["%03d" % (i+1)]
                    for candidat in metslesliens.donnelescandidats(text, 'structuré'):
                        if 'texte' in candidat and 'relatif' not in candidat['texte']:
                            code = get_code(candidat)
                            if code and code not in dos["textes_cites"]:
                                dos["textes_cites"].append(code)

                            link_text = text[candidat['index'][0]:candidat['index'][1]]
                            link_text = re.sub(r'^(aux?|les?|la|du|des)(dite?s?)? ', '', link_text, 0, re.I)
                            link_text = re.sub(r"^l'", '', link_text, 0, re.I)
                            if not re.search(r'(même|présente?|précédente?) ', link_text ) and link_text not in data['liens']:
                                """
                                link = {
                                    'texte': link_text
                                }
                                if 'eli_alias' in candidat:
                                    link['url'] = "https://www.legifrance.gouv.fr/" + candidat['eli_alias']
                                """
                                data['liens'].append(link_text)
        dos["textes_cites"].sort()
    return dos


if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1])))
