import os, sys, glob

from tlfp.tools.common import strip_text, compute_similarity_by_articles, open_json, print_json, \
    clean_text_for_diff, datize


def find_amendements(path):
    for amdts_file in glob.glob(os.path.join(path, '**/amendements_*'), recursive=True):
        institution = None
        if 'senat' in amdts_file:
            institution = 'senat'
        if 'assemblee' in amdts_file:
            institution = 'assemblee'

        amendements = open_json(amdts_file)
        for subject in amendements.get('sujets', {}).values():
            for amdt in subject.get('amendements', []):
                yield amdt, institution


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
    first, last = None, None
    first_found = False
    for i, s in enumerate(dos['steps']):
        if s['debats_order'] is None or s.get('echec') or s.get('in_discussion'):
            continue
        if s.get('step') != "depot":
            first_found = True
            last = i
        if not first_found and s.get('step') == "depot":
            first = last = i
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
    stats['total_mots'] = sum([
        sum(i['total_mots'] for i in step['divisions'].values())
            for step in intervs.values()
    ])

    stats["total_intervenants"] = len({orat for step in intervs.values() for orat in step['orateurs'].keys()})
    stats["total_interventions"] = sum({division['total_intervs'] for step in intervs.values() for division in step['divisions'].values()})

    stats["total_seances"] = sum([step['total_seances'] for step in intervs.values()])
    stats["total_seances_assemblee"] = sum([step['total_seances'] for dir, step in intervs.items() if '_assemblee' in dir])
    stats["total_seances_senat"] = sum([step['total_seances'] for dir, step in intervs.items() if '_senat' in dir])

    stats['total_amendements'] \
        = stats["total_amendements_adoptes"] \
        = stats["total_amendements_senateurs"] \
        = stats["total_amendements_senateurs_adoptes"] \
        = stats["total_amendements_gouvernement"] \
        = stats["total_amendements_gouvernement_adoptes"] \
        = stats["total_amendements_gouvernement_senat"] \
        = stats["total_amendements_gouvernement_senat_adoptes"] \
        = stats["total_amendements_deputes"] \
        = stats["total_amendements_deputes_adoptes"] \
        = stats["total_amendements_gouvernement_assemblee"] \
        = stats["total_amendements_gouvernement_assemblee_adoptes"] \
        = 0

    for amdt, institution in find_amendements(output_dir):
        stats['total_amendements'] += 1

        from_gouv = amdt["groupe"] == "Gouvernement"

        if amdt["sort"] == "adopté":
            stats["total_amendements_adoptes"] += 1
            if from_gouv:
                stats["total_amendements_gouvernement_adoptes"] += 1
            if institution == 'senat':
                stats["total_amendements_senateurs_adoptes"] += 1
                if from_gouv:
                    stats["total_amendements_gouvernement_senat_adoptes"] += 1
            if institution == 'assemblee':
                stats["total_amendements_deputes_adoptes"] += 1
                if from_gouv:
                    stats["total_amendements_gouvernement_assemblee_adoptes"] += 1
        if from_gouv:
            stats["total_amendements_gouvernement"] += 1
        if institution == 'senat':
            stats["total_amendements_senateurs"] += 1
            if from_gouv:
                stats["total_amendements_gouvernement_senat"] += 1
        if institution == 'assemblee':
            stats["total_amendements_deputes"] += 1
            if from_gouv:
                stats["total_amendements_gouvernement_assemblee"] += 1

    stats["echecs_procedure"] = len([step for step in dos['steps'] if step.get("echec")])

    first_text, first_arts, last_text, last_arts = find_first_and_last_texts(dos)

    stats["total_input_articles"] = len(first_arts)
    stats["total_output_articles"] = len(last_arts)
    stats["ratio_articles_growth"] = len(last_arts) / len(first_arts)

    stats["ratio_texte_modif"] = 1 - compute_similarity_by_articles(first_arts, last_arts)
    stats["input_text_length"] = len("\n".join(first_text))
    stats["output_text_length"] = len("\n".join(last_text))

    last_step_in_parliament = [step for step in dos['steps'] if step.get('stage') not in ('constitutionnalité', 'promulgation')][-1]
    stats['last_stage'] = last_step_in_parliament.get('stage')

    maxdate = dos.get('end')
    if not maxdate:
        for step in dos['steps']:
            if step.get('date'):
                maxdate = step.get('enddate') or step.get('date')
    stats["total_days"] = (datize(maxdate) - datize(dos['beginning'])).days + 1

    return stats


if __name__ == '__main__':
    print_json(process(sys.argv[1], open_json(sys.argv[2])))
