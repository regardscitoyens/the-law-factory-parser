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
    for field in dict(s):
        if field.endswith('_directory') or field.endswith('_files'):
            del(s[field])

print_json(procedure)

