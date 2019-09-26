#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, os, sys
from difflib import ndiff
from functools import cmp_to_key

from tlfp.tools import _step_logic
from tlfp.tools.common import open_json, print_json, clean_text_for_diff, compute_similarity, format_display_date
from tlfp.tools.sort_articles import compare_articles


def getParentFolder(root, f):
    abs = os.path.abspath(os.path.join(root, f))
    return os.path.basename(os.path.abspath(os.path.join(abs, os.pardir)))


def unifyStatus(status):
    status = status.lstrip().rstrip('s. ')
    if status.endswith('constitution') or status.startswith('sup'):
        return "sup"
    if status.startswith("nouveau"):
        return "new"
    return "none"


def create_step(step_id, article=None, echec_type=None):
    s = {}
    s['id_step'] = step_id
    s['directory'] = step_id
    s['text'] = []
    if article:
        if article.get('statut'):
            s['status'] = unifyStatus(article['statut'])
        else:
            s['status'] = 'none'
        for key in sorted(article['alineas'].keys()):
            if article['alineas'][key] != '':
                s['text'].append(article['alineas'][key])
    else:
        s['status'] = echec_type.upper()
        s['length'] = 0
        s['n_diff'] = 0
    return s


def mark_missing_articles_as_deleted(articles, old_step_id, step_id, last_match_with_previous_step, current_match):
    # we look for *non-deleted* articles in the previous step to mark them as deleted in this step
    # articles to recover = articles with index between last_match_with_previous_step and current_match
    for article_id, article in sorted(articles.items()):
        for step in article['steps']:
            if step['id_step'] == old_step_id \
                    and last_match_with_previous_step < step['_original_index'] < current_match \
                    and step['status'] != 'sup':
                print('Matched an article deleted in this step', article_id)
                def_s = dict(step)
                def_s['id_step'] = step_id
                def_s['directory'] = step_id
                def_s['status'] = 'sup'
                def_s['length'] = 0
                def_s['diff'] = 'rem'
                def_s['n_diff'] = 0
                articles[article_id]['steps'].append(def_s)


def check_text_match_dosleg(url, senat_id):
    # test if the text is the one 
    if url.endswith('/%s.html' % senat_id):
        return True


    # test the short version: pjl2014-211 -> pjl14-211
    if len(senat_id) > len('pjlYY-XXX') and senat_id.startswith('pjl20'): # TODO: update in one century :)
        senat_id = senat_id.replace('pjl20', 'pjl') 
        if url.endswith('/%s.html' % senat_id):
            return True

    return False


def reordered_steps(procedure):
    # Handle reorder of repeated depots (typically a few PPL from Senat similar to a PJL added to its dossier)
    senat_id = procedure.get('senat_id')
    first = None
    steps = []
    latersteps = []
    for i, step in enumerate(procedure['steps']):
        if step.get('step', '') == 'depot':
            if not first and (step.get('institution', '') == 'assemblee' or check_text_match_dosleg(step.get('source_url', ''), senat_id)):
                first = step
            elif first and step.get('institution', '') == 'assemblee' and check_text_match_dosleg(step.get('source_url', ''), senat_id):
                continue
            elif step.get('institution', '') == 'senat' and "/ppl" in step.get('source_url', '') and step.get('stage', '') == '1ère lecture':
                # check next step is a depot too
                if len(procedure['steps']) > i + 1 and procedure['steps'][i + 1].get('step') == 'depot':
                    steps.append(step)
            else:
                continue
        else:
            latersteps.append(step)
    steps.append(first)
    depots = len(steps)
    steps += latersteps
    return depots, steps


def process(procedure):
    title = procedure.get("long_title", "Missing title").replace(procedure.get("short_title", "").lower(), procedure.get("short_title", ""))
    title = title[0].upper() + title[1:]
    out = {'law_title': title, 'articles': {}, 'sections': {}, 'short_title': procedure.get("short_title", "")}
    if 'loi_dite' in procedure:
        out['loi_dite'] = procedure['loi_dite']

    depots, steps = reordered_steps(procedure)

    # TODO : check whether it should be reintegrated or not
    # skip step presently happening
    # if not steps[-1].get('enddate'):
    #   steps.pop(-1)

    re_upper_first = re.compile(r'^(.)(.*)$')
    step_id = ''
    old_step_index = None
    for nstep, step in enumerate(steps):
        data = step.get('texte.json')
        if step['stage'] == 'promulgation':
            continue
        if not data and not step.get('echec'):
            if not ((procedure.get('is_old_procedure') or _step_logic.use_old_procedure(step)) and step.get('step') == 'commission'):
                print('       WARNING: prepare_articles: no data for', step.get('stage'), step.get('step'), step.get('institution'), file=sys.stderr)
            continue

        step_id = step['directory']
        print('      * preparing articles for step', step_id)

        # hack
        step['echec'] = step.get('echec')

        if step['echec']:
            if 'echec' not in out['articles']:
                out['articles']['echec'] = {'id': 'echec', 'titre': step['echec'], 'section': 'echec', 'steps': []}
            next_step = create_step(step_id, echec_type=step['echec'])
            out['articles']['echec']['steps'].append(next_step)
            if 'echec' not in out['sections']:
                out['sections']['echec'] = {}
            if step['echec'] == 'renvoi en commission' and not data:
                data = {'expose': 'Siégeant en hémicycle le %s, les %s ont adopté une motion de renvoi du texte en commission.' % (format_display_date(step.get('enddate', step['date'])), "sénateurs" if step['institution'] == "senat" else "députés")}
            out['sections']['echec'][step_id] = {'title': data['expose'] if data else '', 'type': step['echec'].upper()}
            continue
        for section in data['sections']:
            if not section['id'] in out['sections']:
                out['sections'][section['id']] = {}
            out['sections'][section['id']][step_id] = {'title': section['titre'], 'type': re_upper_first.sub(lambda x: x.group(1).upper() + x.group(2), section['type_section'])}
            if 'newid' in section:
                out['sections'][section['id']][step_id]['newnum'] = section['newid']
        last_match_with_previous_step = -1
        for article_index, article in enumerate(data['articles']):
            id = article['titre'].replace(' ', '_')
            if out['articles'].get(id):
                s = create_step(step_id, article=article)
                if 'newtitre' in article:
                    s['newnum'] = article['newtitre']
                txt = clean_text_for_diff(s['text'])

                oldtext = []
                if old_step_index is not None:
                    old_step_id = steps[old_step_index]['directory']
                    for st in out['articles'][id]['steps']:
                        if st['id_step'] == old_step_id:
                            if st['_original_index'] != last_match_with_previous_step + 1:
                                mark_missing_articles_as_deleted(out['articles'], old_step_id, step_id, last_match_with_previous_step, st['_original_index'])
                            last_match_with_previous_step = st['_original_index']
                            if st['status'] != 'sup':
                                oldtext = st['text']
                            break

                if txt and (not oldtext or nstep < depots):
                    s['status'] = 'new' if nstep >= depots else 'none'
                    s['diff'] = 'add'
                    s['n_diff'] = 1
                elif s['status'] == "sup":
                    s['diff'] = 'rem'
                    s['n_diff'] = 0
                else:
                    oldtxt = clean_text_for_diff(oldtext)
                    s['status'] = 'none'
                    if txt == oldtxt:
                        s['diff'] = 'none'
                        s['n_diff'] = 0
                    else:
                        compare = list(ndiff(s['text'], oldtext))
                        mods = {'+': 0, '-': 0}
                        for line in compare:
                            mod = line[0]
                            if mod not in mods:
                                mods[mod] = 0
                            mods[mod] += 1
                        if mods['+'] > mods['-']:
                            s['diff'] = 'add'
                        elif mods['+'] < mods['-']:
                            s['diff'] = 'rem'
                        elif mods['+'] * mods['-']:
                            s['diff'] = 'both'
                        else:
                            s['diff'] = 'none'
                        s['n_diff'] = 1 - compute_similarity(oldtxt, txt)
            else:
                out['articles'][id] = {}
                out['articles'][id]['id'] = id
                out['articles'][id]['titre'] = article['titre']
                if article.get('section'):
                    out['articles'][id]['section'] = article['section']
                else:
                    out['articles'][id]['section'] = 'A%s' % article['titre']
                out['articles'][id]['steps'] = []
                s = create_step(step_id, article)
                s['n_diff'] = 1
                s['diff'] = 'add'
                if nstep >= depots:
                    s['status'] = 'new'
                else:
                    s['status'] = 'depot'
            if s['status'] == 'sup':
                s['length'] = 0
                s['n_diff'] = 0
            else:
                s['length'] = len("\n".join(s['text']))
            s['_original_index'] = article_index
            out['articles'][id]['steps'].append(s)
        old_step_index = nstep

        # except Error as e:
        #     sys.stderr.write("ERROR parsing step %s:\n%s: %s\n" % (str(step)[:50], type(e), e))
        #    exit(1)

    for a in sorted(out['articles']):
        new_steps = []
        for s in out['articles'][a]['steps']:
            del s['text']
            s.pop('_original_index', None)
            if len(new_steps) > 0 and new_steps[-1]['id_step'] == s['id_step']:
                print('same id_step', s['id_step'], file=sys.stderr)
                continue
            new_steps.append(s)
        out['articles'][a]['steps'] = new_steps

    # Set articles' order values after having reinserted missing ones
    orders = {k: n for n, k in enumerate(
        sorted(
            [a['titre'] for a in out['articles'].values() if a['id'] != 'echec'],
            key=cmp_to_key(compare_articles)
        ))
    }
    for a in out['articles'].values():
        if a['id'] == 'echec':
            a['order'] = -1
        else:
            a['order'] = orders[a['titre']]

    return out


if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1])))
