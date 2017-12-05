#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, csv, os, sys
from difflib import ndiff, SequenceMatcher
from .common import json, open_json, print_json
from ._step_logic import get_previous_step


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

def create_step(step_id, directory, article=None, echec_type=None):
    s = {}
    s['id_step'] = step_id
    s['directory'] = directory
    s['text'] = []
    if article:
        if article.get('statut'):
            s['status'] = unifyStatus(article['statut'])
        else:
            s['status'] = 'none'
        for key in sorted(article['alineas'].keys()):
            if article['alineas'][key] != '':
                s['text'].append(article['alineas'][key])
        s['order'] = article['order']
    else:
        s['status'] = echec_type.upper()
        s['length'] = 0
        s['n_diff'] = 0
        s['order'] = 1
    return s


def process(procedure):
    title = procedure.get("long_title", "Missing title").replace(procedure.get("short_title", "").lower(), procedure.get("short_title", ""))
    title = title[0].upper() + title[1:]
    out = {'law_title': title, 'articles': {}, 'sections': {}, 'short_title': procedure.get("short_title", "")}

    # Handle reorder of repeated depots (typically a few PPL from Senat similar to a PJL added to its dossier)
    dossier_id = procedure.get('senat_id')
    first = None
    steps = []
    latersteps = []
    for step in procedure['steps']:
        if step.get('step', '') == 'depot':
            if not first and (step.get('institution', '') == 'assemblee' or step.get('source_url', '').endswith("/%s.html" % dossier_id)):
                first = step
            elif first and first.get('institution', '') == 'assemblee' and step.get('source_url', '').endswith("/%s.html" % dossier_id):
                continue
            elif step.get('institution', '') == 'senat' and "/ppl" in step.get('source_url', '') and step.get('stage', '') == '1ère lecture':
                steps.append(step)
            else:
                continue
        else:
            latersteps.append(step)
    steps.append(first)
    depots = len(steps)
    steps += latersteps

    # skip step presently happening
    # if not steps[-1].get('enddate'):
    #   steps.pop(-1)

    bister = '(un|duo|tre|bis|qua|quin[tqu]*|sex|sept|octo?|novo?|non|dec|vic|ter|ies)+'
    re_alin_sup = re.compile(r'supprimés?\)$', re.I)
    re_clean_alin = re.compile(r'^"?([IVXCDLM]+|\d+|[a-z]|[°)\-\.\s]+)+\s*((%s|[A-Z]+)[°)\-\.\s]+)*' % bister)
    re_upper_first = re.compile(r'^(.)(.*)$')
    step_id = ''
    for nstep, step in enumerate(steps):
        data = step.get('texte.json')
        if step['stage'] in ["promulgation", "constitutionnalité"]:
            continue
        if not data:
            print('no data for', step.get('stage'), step.get('step'), step.get('institution'), file=sys.stderr)
            continue

        #step['directory'] = str(nstep)
        step_id = step['directory']
        # step_id = "%02d%s" % (nstep, step['directory'][2:])
        step['echec'] = step.get('echec')

        echec = (step['echec'] and step['echec'] != "renvoi en commission")
        if echec:
            if not 'echec' in out['articles']:
                out['articles']['echec'] = {'id': 'echec', 'titre': step['echec'], 'section': 'echec', 'steps': []}
            next_step = create_step(step_id, step['directory'], echec_type=step['echec'])
            out['articles']['echec']['steps'].append(next_step)
            if not 'echec' in out['sections']:
                out['sections']['echec'] = {}
            out['sections']['echec'][step_id] = {'title': data['expose'], 'type': step['echec'].upper()}
            continue
        for section in data['sections']:
            if not section['id'] in out['sections']:
                out['sections'][section['id']] = {}
            out['sections'][section['id']][step_id] = {'title': section['titre'], 'type': re_upper_first.sub(lambda x: x.group(1).upper() + x.group(2), section['type_section'])}
            if 'newid' in section:
                out['sections'][section['id']][step_id]['newnum'] = section['newid']
        for article in data['articles']:
            id = article['titre'].replace(' ', '_')
            if out['articles'].get(id):
                s = create_step(step_id, step['directory'], article=article)
                if 'newtitre' in article:
                    s['newnum'] = article['newtitre']
                txt = "\n".join([re_clean_alin.sub('', v) for v in s['text'] if not re_alin_sup.search(v)])
                
                old_step_index = get_previous_step(steps, nstep)
                oldtext = []
                if old_step_index:
                    old_step_id = steps[old_step_index]['directory']
                    for st in out['articles'][id]['steps']:
                        if st['id_step'] == old_step_id:
                            oldtext = [re_clean_alin.sub('', v) for v in st['text'] if not re_alin_sup.search(v)]
                            break

                if txt and (not oldtext or nstep < depots):
                    s['status'] = 'new' if nstep >= depots else 'none'
                    s['diff'] = 'add'
                    s['n_diff'] = 1
                elif s['status'] == "sup":
                    s['diff'] = 'rem'
                    s['n_diff'] = 0
                else:
                    oldtxt = "\n".join(oldtext)
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
                        a = SequenceMatcher(None, oldtxt, txt).get_matching_blocks()
                        s['n_diff'] = 1 - float(sum([m[2] for m in a])) / max(a[-1][0], a[-1][1])
            else:
                out['articles'][id] = {}
                out['articles'][id]['id'] = id
                out['articles'][id]['titre'] = article['titre']
                if article.get('section'):
                    out['articles'][id]['section'] = article['section']
                else:
                    out['articles'][id]['section'] = 'A%s' % article['titre']
                out['articles'][id]['steps'] = []
                s = create_step(step_id, step['directory'], article)
                s['n_diff'] = 1
                s['diff'] = 'add'
                if nstep >= depots:
                    s['status'] = 'new'
                else:
                    s['status'] = 'depot'
                txt = "\n".join(s['text'])
            if s['status'] == 'sup':
                s['length'] = 50
                s['n_diff'] = 0
            else:
                s['length'] = len(txt)
            out['articles'][id]['steps'].append(s)

        # except Error as e:
        #     sys.stderr.write("ERROR parsing step %s:\n%s: %s\n" % (str(step)[:50], type(e), e))
        #    exit(1)

    for a in out['articles']:
        new_steps = []
        for s in out['articles'][a]['steps']:
            del(s['text'])
            if len(new_steps) > 0 and new_steps[-1]['id_step'] == s['id_step']:
                print('same id_step', s['id_step'], file=sys.stderr)
                continue
            new_steps.append(s)
        out['articles'][a]['steps'] = new_steps

    return out


if __name__ == '__main__':
    print((
        json.dumps(
            process(json.load(open(sys.argv[1]))),
            indent=2, sort_keys=True, ensure_ascii=False
        )))
