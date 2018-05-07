import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import strip_text, compute_similarity_by_articles, open_json, print_json


def read_text(step):
    articles = step['texte.json']['articles']
    texte = ''
    for art in articles:
        for key in sorted(art['alineas'].keys()):
            if art['alineas'][key] != '':
                texte += strip_text(art['alineas'][key])
    return texte


def find_first_and_last_texts(dos):
    first_found = False
    for s in dos['steps']:
        if s['debats_order'] == None or s.get('echec'):
            continue
        if s.get('step') != "depot":
            first_found = True
            last_text = read_text(s)
        if not first_found and s.get('step') == "depot":
            first_text = read_text(s)
    return first_text, last_text


def process(dos):
    stats = {}

    first_text, last_text = find_first_and_last_texts(dos)
    stats["ratio_texte_modif"] = 1 - compute_similarity_by_articles(first_text, last_text)
    stats["input_text_length2"] = len("\n".join(first_text))
    stats["output_text_length2"] = len("\n".join(last_text))

    return stats

if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1])))
