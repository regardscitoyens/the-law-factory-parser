import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import strip_text, compute_similarity_by_articles, open_json, print_json, clean_text_for_diff


def read_text(step):
    articles = step['texte.json']['articles']
    texte = ''
    for art in articles:
        for key in sorted(art['alineas'].keys()):
            if art['alineas'][key] != '':
                texte += strip_text(art['alineas'][key])
    return texte


def read_articles(step):
    articles = step['texte.json']['articles']
    return {art['titre']: clean_text_for_diff([art['alineas'][al] for al in sorted(art['alineas'].keys())]) for art in articles}


def find_first_and_last_texts(dos):
    first_found = False
    for s in dos['steps']:
        if s['debats_order'] == None or s.get('echec'):
            continue
        if s.get('step') != "depot":
            first_found = True
            last_text = read_text(s)
            last_arts = read_articles(s)
        if not first_found and s.get('step') == "depot":
            first_text = read_text(s)
            first_arts = read_articles(s)
    return first_text, first_arts, last_text, last_arts


def process(dos):
    stats = {}

    first_text, first_arts, last_text, last_arts = find_first_and_last_texts(dos)
    stats["ratio_texte_modif"] = 1 - compute_similarity_by_articles(first_arts, last_arts)
    stats["input_text_length2"] = len("\n".join(first_text))
    stats["output_text_length2"] = len("\n".join(last_text))

    return stats

if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1])))
