#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, csv, os, sys
from common import open_json, print_json

sourcedir = sys.argv[1]
if not sourcedir:
    sys.stderr.write('Error, no input directory given')
    exit(1)

procedure = open_json(os.path.join(sourcedir, 'procedure'), 'procedure.json')
articles = open_json(os.path.join(sourcedir, 'viz'), 'articles_etapes.json')['articles']
intervs = open_json(os.path.join(sourcedir, 'viz'), 'interventions.json')
good_steps = {}
for _, a in articles.iteritems():
    for s in a['steps']:
        stepid = s['directory']
        if stepid not in good_steps:
            good_steps[stepid] = int(s['id_step'][:2])

for s in procedure['steps']:
    s['debats_order'] = None
    if 'has_interventions' in s and s['has_interventions'] and s['directory'] not in intervs:
        print >> sys.stderr, u"WARNING: removing nearly empty interventions steps for %s" % s['directory']
        s['has_interventions'] = False
    if 'directory' in s:
        s['debats_order'] = good_steps.get(s['directory'], None)
    if s.get('step', '') == 'depot' and s['debats_order'] != None:
        if '/propositions/' in s.get('source_url', ''):
            s['auteur_depot'] = u"Députés"
        elif '/leg/ppl' in s.get('source_url',''):
            s['auteur_depot'] = u"Sénateurs"
        else:
            s['auteur_depot'] = u"Gouvernement"
    for field in dict(s):
        if field.endswith('_directory') or field.endswith('_files'):
            del(s[field])

print_json(procedure)

