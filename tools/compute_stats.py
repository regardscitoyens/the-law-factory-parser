import os, sys, glob
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import strip_text, compute_similarity_by_articles, open_json, print_json, \
    clean_text_for_diff, datize


def articles_modified(path, dos):
    etapes = open_json(os.path.join(path, 'viz/articles_etapes.json'))
    modified = 0
    first_step, _ = find_first_and_last_steps(dos)
    first_step_directory = dos['steps'][first_step]['directory']
    for art in etapes["articles"].values():
        first_step_found = False
        for step in art["steps"]:
            if step['directory'] == first_step_directory:
                first_step_found = True
                continue
            if first_step_found and step['n_diff'] != 0:
                modified += 1
                break
    return modified


def find_amendements(path):
    amdts = []
    for amdts_file in glob.glob(os.path.join(path, '**/amendements_*'), recursive=True):
        amendements = open_json(amdts_file)
        for subject in amendements.get('sujets', {}).values():
            for amdt in subject.get('amendements', []):
                amdts.append(amdt)
    return amdts


def find_interventions(path):
    intervs = []
    for seance_file in glob.glob(os.path.join(path, '**/interventions/*.json'), recursive=True):
        intervs += open_json(seance_file)["seance"]
    return intervs


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


def find_first_and_last_steps(dos):
    first_found = False
    for i, s in enumerate(dos['steps']):
        if s['debats_order'] is None or s.get('echec'):
            continue
        if s.get('step') != "depot":
            first_found = True
            last = i
        if not first_found and s.get('step') == "depot":
            first = i
    return first, last


def find_first_and_last_texts(dos):
    first, last = find_first_and_last_steps(dos)

    first_text = read_text(dos['steps'][first])
    first_arts = read_articles(dos['steps'][first])
    last_text = read_text(dos['steps'][last])
    last_arts = read_articles(dos['steps'][last])

    return first_text, first_arts, last_text, last_arts


def process(output_dir, dos):
    stats = {}

    intervs = open_json(os.path.join(output_dir, 'viz/interventions.json'))
    stats['total_mots'] = sum([ # TOOODO [0] +
        sum(i['total_mots'] for i in step['divisions'].values())
            for step in intervs.values()
    ])

    amendements = find_amendements(output_dir)
    stats['total_amendements'] = len(amendements)
    stats["total_amendements_adoptes"] = len([amdt for amdt in amendements if amdt["sort"] == "adopté"])
    stats["total_amendements_parlementaire"] = len([amdt for amdt in amendements if amdt["groupe"] != "Gouvernement"])
    stats["total_amendements_parlementaire_adoptes"] = len([amdt for amdt in amendements if amdt["sort"] == "adopté" and amdt["groupe"] != "Gouvernement"])
    stats["total_amendements_gouvernement"] = len([amdt for amdt in amendements if amdt["groupe"] == "Gouvernement"])
    stats["total_amendements_gouvernement_adoptes"] = len([amdt for amdt in amendements if amdt["sort"] == "adopté" and amdt["groupe"] == "Gouvernement"])

    stats["total_intervenants"] = len({interv["intervention"]["intervenant_slug"] for interv in find_interventions(output_dir)}) # TOOODO typpooo

    stats["echecs_procedure"] = len([step for step in dos['steps'] if step.get("echec")]) # TOOODO typpoooo

    last_date = [step.get('date') for step in dos['steps'] if step.get('date')][-1]
    stats["total_days"] = (datize(dos.get("end") or last_date) - datize(dos["beginning"])).days + 1

    if 'end' in dos:
        first_text, first_arts, last_text, last_arts = find_first_and_last_texts(dos)

        stats["total_articles"] = max(len(first_arts), len(last_arts))
        stats["total_articles_modified"] = articles_modified(output_dir, dos)
        stats["ratio_article_modif"] = stats["total_articles_modified"] / stats["total_articles"] if stats["total_articles"] != 0 else 0

        stats["ratio_texte_modif"] = 1 - compute_similarity_by_articles(first_arts, last_arts)
        stats["input_text_length"] = len("\n".join(first_text))
        stats["output_text_length"] = len("\n".join(last_text))

    return stats


if __name__ == '__main__':
    print_json(process(sys.argv[1], open_json(sys.argv[2])))
