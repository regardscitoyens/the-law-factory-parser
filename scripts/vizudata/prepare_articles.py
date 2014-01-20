#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, csv, os, sys
from difflib import ndiff, SequenceMatcher
try:
    import json
except:
    import simplejson as json

sourcedir = sys.argv[1]
if not sourcedir:
    sys.stderr.write('Error could not find directory at %s' % sourcedir)
    exit(1)

def getParentFolder(root, f):
    abs = os.path.abspath(os.path.join(root, f))
    return os.path.basename(os.path.abspath(os.path.join(abs, os.pardir)))

def unifyStatus(status):
    return {
    "none" : "none",
    "conforme" : "none",
    "conformes" : "none",
    "non modifié" : "none",
    "nouveau" : "new",
    "supprimé" : "sup",
    "supprimés" : "sup",
    "suppression maintenue" : "sup",
    "suppression conforme" : "sup",
    "supprimé par la commission mixte paritaire" : "sup"
    }[status.strip()]

def create_step(step_id, article):
    s = {}
    s['id_step'] = step_id
    if article.get('statut'):
        s['status'] = unifyStatus(article['statut'].encode('utf8'))
    else:
        s['status'] = 'none'
    s['text'] = []
    for key in sorted(article['alineas'].keys()):
        if article['alineas'][key] != '':
            s['text'].append(article['alineas'][key])
    s['order'] = article['order']
    return s

with open(os.path.join(sourcedir, 'procedure.json'), "r") as properties:
    properties = json.load(properties)
title = properties.get("long_title", "Missing title").replace(properties.get("short_title", "").lower(), properties.get("short_title", ""))
title = title[0].upper() + title[1:]
out = {'law_title': title, 'articles': {}, 'short_title': properties.get("short_title", "")}

step_id = ''
old_step_id = ''
steps = properties['steps']
for step in steps:
    if not 'resulting_text_directory' in step:
        sys.stderr.write("WARNING no directory found for step %s\n" % step['stage'])
        continue
    try:
        path = os.path.join(sourcedir, step['resulting_text_directory'])
        if step_id:
            old_step_id = step_id
        step_id = '_'.join([step['stage'], step['institution'], step['step']]).strip()

        for root, dirs, files in os.walk(path):
            articleFiles = [os.path.abspath(os.path.join(root,f)) for f in files if re.search(r'^A.*', getParentFolder(root, f)) and re.search(r'^.*?json', f)]
            if len(articleFiles) > 0:
                for articleFile in articleFiles:
                    with open(articleFile,"r") as article:
                         article = json.load(article)

                    id = str(article['titre']).replace(' ', '_')
                    if out['articles'].get(id):
                        s = create_step(step_id, article)
                        txt = " ".join(s['text'])
                        oldtext = None
                        for st in out['articles'][id]['steps']:
                            if st['id_step'] == old_step_id:
                                oldtext = st['text']
                                break
                        if not oldtext:
                            s['status'] = 'new'
                            s['diff'] = 'add'
                            s['n_diff'] = 1
                        elif s['status'] == "sup":
                            s['diff'] = 'rem'
                            s['n_diff'] = 0
                        else:
                            oldtxt = " ".join(oldtext)
                            s['status'] = 'none'
                            if txt == oldtxt:
                                s['diff'] = 'none'
                                s['n_diff'] = 0
                            else:
                                compare = list(ndiff(s['text'], oldtext))
                                mods = {'+': 0, '-': 0}
                                for line in compare:
                                    mod = line.encode("utf8")[0]
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
                                a = SequenceMatcher(None, oldtxt, txt).ratio()
                                b = SequenceMatcher(None, txt, oldtxt).ratio()
                                s['n_diff'] = 1 - (a + b)/2
                    else:
                        out['articles'][id] = {}
                        out['articles'][id]['id'] = id
                        out['articles'][id]['titre'] = article['titre']
                        if article.get('section'):
                            out['articles'][id]['section'] = article['section']
                        else:
                            out['articles'][id]['section'] = 'none'
                        out['articles'][id]['steps'] = []
                        s = create_step(step_id, article)
                        s['n_diff'] = 1
                        s['diff'] = 'add'
                        s['status'] = 'new'
                        txt = " ".join(s['text'])
                    if s['status'] == 'sup':
                        s['length'] = 50
                        s['n_diff'] = 0
                    else:
                        s['length'] = len(txt)
                    out['articles'][id]['steps'].append(s)

    except Exception as e:
        sys.stderr.write("ERROR parsing step %s:\n%s: %s\n" % (step, type(e), e))
        exit(1)
print json.dumps(out, ensure_ascii=False).encode('utf8')
