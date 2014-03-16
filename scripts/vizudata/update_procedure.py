#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, csv, os, sys
try:
    import json
except:
    import simplejson as json

sourcedir = sys.argv[1]
if not sourcedir:
    sys.stderr.write('Error, no input directory given')
    exit(1)

try:
    with open(os.path.join(sourcedir, 'procedure', 'procedure.json'), "r") as procedure:
        procedure = json.load(procedure)
except:
    sys.stderr.write('Error: could not find procedure.json in directory %s/procedure' % sourcedir)
    exit(1)

try:
    with open(os.path.join(sourcedir, 'viz', 'articles_etapes.json'), "r") as articles:
        articles = json.load(articles)['articles']
except:
    sys.stderr.write('Error: could not find articles_etapes.json in directory %s/viz' % sourcedir)
    exit(1)

good_steps = {}
for _, a in articles.iteritems():
    for s in a['steps']:
        stepid = s['directory']
        if stepid not in good_steps:
             good_steps[stepid] = int(s['id_step'][:2])

for s in procedure['steps']:
    s['debats_order'] = None
    if 'directory' in s:
        s['debats_order'] = good_steps.get(s['directory'], None)
    for field in s:
        if field.endswith('_directory') or field.endswith('_files'):
            del(s[field])

print json.dumps(procedure, ensure_ascii=False).encode('utf8')

