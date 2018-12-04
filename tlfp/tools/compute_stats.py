import os, sys, glob, re

from tlfp.tools.common import strip_text, compute_similarity_by_articles, open_json, print_json, \
    clean_text_for_diff, datize, clean_statuses


def count_words(content):
    """
    Counts the number of words in the specified string.
    Based on the regexes / logic from Countable.js:
    https://github.com/RadLikeWhoa/Countable

    Taken from: https://github.com/Jaza/word-count/blob/master/word_count.py
    With fix from https://github.com/Jaza/word-count/issues/1
    And updated regex from: https://github.com/RadLikeWhoa/Countable/blob/4d2812d7b53736d2bca4268b783997545d261c43/Countable.js#L149

    Divergences with others applications:
        ╔════════════════════════╦═══════════════════════════════════════════════════════════════════════════╗
        ║                        ║                               Number of words                             ║
        ║ Input                  ╠═════════════╦══════════════╦═════════════╦════════════════╦═══════╦═══════╣
        ║                        ║ This script ║ Libre Office ║ Google Docs ║ Microsoft Word ║ Gedit ║ wc -w ║
        ╠════════════════════════╬═════════════╬══════════════╬═════════════╬════════════════╬═══════╬═══════╣
        ║ "L'article"            ║ 2           ║ 1            ║ 1           ║ 1              ║ 2     ║ 1     ║
        ╠════════════════════════╬═════════════╬══════════════╬═════════════╬════════════════╬═══════╬═══════╣
        ║ "Ceci :"               ║ 1           ║ 2            ║ 1           ║ 2              ║ 1     ║ 2     ║
        ╠════════════════════════╬═════════════╬══════════════╬═════════════╬════════════════╬═══════╬═══════╣
        ║ "321-32"               ║ 1           ║ 2            ║ 1           ║ 1              ║ 2     ║ 1     ║
        ╠════════════════════════╬═════════════╬══════════════╬═════════════╬════════════════╬═══════╬═══════╣
        ║ "L'article L.O. 321-3" ║ 4           ║ 3            ║ 4           ║ 3              ║ 6     ║ 3     ║
        ╚════════════════════════╩═════════════╩══════════════╩═════════════╩════════════════╩═══════╩═══════╝

    NOTE: "wc -w" only count spaces-separated words

    >>> count_words("L'article L.O. 321-3")
    4
    >>> count_words("<td>Exécution 2017</td><td>Prévision d'exécution 2018</td>")
    6
    """

    striptags_re = re.compile(r'<\/?[a-z][^>]*>', re.IGNORECASE)
    stripsymbols_re = re.compile(r'[";:,.?¿\-!¡/]+')
    splitsymbols_re = re.compile(r"'")
    words_re = re.compile(r'\S+')

    c = content.strip()
    c = striptags_re.sub(' ', c)
    c = stripsymbols_re.sub('', c)
    c = splitsymbols_re.sub(' ', c)

    match = words_re.findall(c)

    return len(match) if match else 0


def has_been_censored(dos):
    cc_step = [step for step in dos['steps'] if step.get('stage') == 'constitutionnalité']
    if cc_step:
        return cc_step[0].get('decision') == 'partiellement conforme'


def find_amendements(path):
    for amdts_file in glob.glob(os.path.join(path, '**/amendements_*'), recursive=True):
        amendements = open_json(amdts_file)
        for subject in amendements.get('sujets', {}).values():
            for amdt in subject.get('amendements', []):
                yield amdt, amdts_file


def read_alineas(art):
    return [art['alineas'][al] for al in sorted(art['alineas'].keys())]


def read_text(step):
    articles = step['texte.json']['articles']
    for art in articles:
        # yield art['titre']
        for al in read_alineas(art):
            yield al


def step_word_count(step):
    return count_words('\n'.join(clean_statuses(al) for al in read_text(step)))


def step_text_length(step):
    return len(''.join(strip_text(al) for al in read_text(step)))


def count_initial_depots(steps):
    count = 0
    for step in steps:
        if step.get('step') == 'depot':
            count += 1
        else:
            break
    return count


def count_navettes(steps):
    count = 0
    last_step = None
    for step in steps:
        if step.get('step') == 'depot':
            if not last_step or last_step.get('step') != 'depot':
                count += 1
        elif step.get('stage') == 'CMP' and step.get('step') == 'commission':
            count += 1
        elif step.get('stage') in ('congrès', 'constitutionnalité'):
            count += 1
        last_step = step
    return count


def count_texts(steps):
    return len([step for step in steps if step.get('debats_order') is not None])


def read_articles(step):
    articles = step['texte.json']['articles']
    arts = {art['titre']: clean_text_for_diff(read_alineas(art)) for art in articles}
    return {titre: txt for titre, txt in arts.items() if txt}


def count_censored_articles(step):
    articles = step['texte.json']['articles']
    censored_articles = 0
    fully_censored_articles = 0
    for art in articles:
        txt = ''.join(read_alineas(art))
        if '(Censuré)' in txt:
            censored_articles += 1
        if txt == '(Censuré)':
            fully_censored_articles += 1
    return censored_articles, fully_censored_articles


def find_first_and_last_steps(dos, include_CC=True):
    first, last = None, None
    first_found = False
    for i, s in enumerate(dos['steps']):
        if s['debats_order'] is None or s.get('echec') or s.get('in_discussion'):
            continue
        if s.get('stage') == 'constitutionnalité' and not include_CC:
            break
        if s.get('step') != "depot":
            first_found = True
            last = i
        if not first_found and s.get('step') == "depot":
            first = last = i
    return dos['steps'][first], dos['steps'][last]


def add_amendments_stats(stats, amendements):
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
        = stats['total_amendements_hemicycle'] \
        = stats["total_amendements_hemicycle_adoptes"] \
        = stats["total_amendements_hemicycle_senateurs"] \
        = stats["total_amendements_hemicycle_senateurs_adoptes"] \
        = stats["total_amendements_hemicycle_gouvernement"] \
        = stats["total_amendements_hemicycle_gouvernement_adoptes"] \
        = stats["total_amendements_hemicycle_gouvernement_senat"] \
        = stats["total_amendements_hemicycle_gouvernement_senat_adoptes"] \
        = stats["total_amendements_hemicycle_deputes"] \
        = stats["total_amendements_hemicycle_deputes_adoptes"] \
        = stats["total_amendements_hemicycle_gouvernement_assemblee"] \
        = stats["total_amendements_hemicycle_gouvernement_assemblee_adoptes"] \
        = 0

    for amdt, amdts_file in amendements:
        senat = '_senat' in amdts_file
        assemblee = '_assemblee' in amdts_file
        hemicycle = '_hemicycle' in amdts_file
        from_gouv = amdt["groupe"] == "Gouvernement"

        stats['total_amendements'] += 1
        if hemicycle:
            stats['total_amendements_hemicycle'] += 1

        if amdt["sort"] == "adopté":
            stats["total_amendements_adoptes"] += 1
            if hemicycle:
                stats["total_amendements_hemicycle_adoptes"] += 1

            if from_gouv:
                stats["total_amendements_gouvernement_adoptes"] += 1
                if hemicycle:
                    stats["total_amendements_hemicycle_gouvernement_adoptes"] += 1

            if senat:
                stats["total_amendements_senateurs_adoptes"] += 1
                if hemicycle:
                    stats["total_amendements_hemicycle_senateurs_adoptes"] += 1

                if from_gouv:
                    stats["total_amendements_gouvernement_senat_adoptes"] += 1
                    if hemicycle:
                        stats["total_amendements_hemicycle_gouvernement_senat_adoptes"] += 1

            if assemblee:
                stats["total_amendements_deputes_adoptes"] += 1
                if hemicycle:
                    stats["total_amendements_hemicycle_deputes_adoptes"] += 1

                if from_gouv:
                    stats["total_amendements_gouvernement_assemblee_adoptes"] += 1
                    if hemicycle:
                        stats["total_amendements_hemicycle_gouvernement_assemblee_adoptes"] += 1

        if from_gouv:
            stats["total_amendements_gouvernement"] += 1
            if hemicycle:
                stats["total_amendements_hemicycle_gouvernement"] += 1

        if senat:
            stats["total_amendements_senateurs"] += 1
            if hemicycle:
                stats["total_amendements_hemicycle_senateurs"] += 1

            if from_gouv:
                stats["total_amendements_gouvernement_senat"] += 1
                if hemicycle:
                    stats["total_amendements_hemicycle_gouvernement_senat"] += 1

        if assemblee:
            stats["total_amendements_deputes"] += 1
            if hemicycle:
                stats["total_amendements_hemicycle_deputes"] += 1

            if from_gouv:
                stats["total_amendements_gouvernement_assemblee"] += 1
                if hemicycle:
                    stats["total_amendements_hemicycle_gouvernement_assemblee"] += 1


def process(output_dir, dos):
    stats = {}

    # # # INTERVENTIONS # # #

    intervs = open_json(os.path.join(output_dir, 'viz/interventions.json'))
    # only keep seances in hemicycle
    intervs = {step_name: step for step_name, step in intervs.items() if '_hemicycle' in step_name}

    stats['total_mots'] = sum([
        sum(i['total_mots'] for i in step['divisions'].values())
            for step in intervs.values()
    ])

    stats["total_intervenants"] = len({orat for step in intervs.values() for orat in step['orateurs'].keys()})
    stats["total_interventions"] = sum({division['total_intervs'] for step in intervs.values() for division in step['divisions'].values()})

    stats["total_seances"] = sum([step['total_seances'] for step in intervs.values()])
    stats["total_seances_assemblee"] = sum([step['total_seances'] for dir, step in intervs.items() if '_assemblee' in dir])
    stats["total_seances_senat"] = sum([step['total_seances'] for dir, step in intervs.items() if '_senat' in dir])

    # # # AMENDMENTS # # #

    add_amendments_stats(stats, find_amendements(output_dir))

    # # # TEXTS # # #

    first_step, last_step = find_first_and_last_steps(dos)
    first_arts = read_articles(first_step)
    last_arts = read_articles(last_step)

    stats["total_input_articles"] = len(first_arts)
    stats["total_output_articles"] = len(last_arts)
    stats["ratio_articles_growth"] = (stats["total_output_articles"] - stats["total_input_articles"]) / stats["total_input_articles"]

    stats["input_text_length"] = step_text_length(first_step)
    stats["output_text_length"] = step_text_length(last_step)
    stats["ratio_text_length_growth"] = (stats["output_text_length"] - stats["input_text_length"]) / stats["input_text_length"]

    stats["input_text_word_count"] = step_word_count(first_step)
    stats["output_text_word_count"] = step_word_count(last_step)
    stats["ratio_word_count_growth"] = (stats["output_text_word_count"] - stats["input_text_word_count"]) / stats["input_text_word_count"]

    adopted_step = find_first_and_last_steps(dos, include_CC=False)[1]
    if has_been_censored(dos):
        stats["censored_articles"], stats["fully_censored_articles"] = count_censored_articles(last_step)
        stats["output_text_before_CC_length"] = step_text_length(adopted_step)
        stats["output_text_before_CC_word_count"] = step_word_count(adopted_step)

    stats["ratio_texte_modif"] = 1 - compute_similarity_by_articles(first_arts, last_arts)

    # # # PROCEDURE # # #

    stats["echecs_procedure"] = len([step for step in dos['steps'] if step.get("echec")])

    # TODO: first institution
    stats['last_stage'] = adopted_step.get('stage')
    if stats['last_stage'] == 'CMP':
        stats['last_institution'] = 'CMP'
    else:
        stats['last_institution'] = adopted_step.get('institution')

    maxdate = dos.get('end')
    if not maxdate:
        for step in dos['steps']:
            if step.get('date'):
                maxdate = step.get('enddate') or step.get('date')
    stats["total_days"] = (datize(maxdate) - datize(dos['beginning'])).days + 1

    stats["attached_law_proposals"] = count_initial_depots(dos['steps']) - 1
    stats["depots_in_institutions"] = count_navettes(dos['steps'])
    stats["texts_produced"] = count_texts(dos['steps'])

    return stats


if __name__ == '__main__':
    print_json(process(sys.argv[1], open_json(sys.argv[2])))
