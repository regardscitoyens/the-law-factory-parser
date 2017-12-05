#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, csv, os, sys, json
from .common import open_json, print_json


def process(procedure, articles, intervs={}):
    articles = articles['articles']

    good_steps = {}
    for _, a in articles.items():
        for s in a['steps']:
            stepid = s['directory']
            if stepid not in good_steps:
                good_steps[stepid] = int(s['directory'].split('_')[0])

    for i, s in enumerate(procedure['steps']):

        # hacks
        s['enddate'] = s.get('date')
        
        s['debats_order'] = None
        if 'has_interventions' in s and s['has_interventions'] and s['directory'] not in intervs:
            print("WARNING: removing nearly empty interventions steps for %s" % s['directory'].encode('utf-8'), file=sys.stderr)
            s['has_interventions'] = False
        if 'directory' in s:
            if i == len(procedure['steps'])-1 and not s['enddate']:
                s['debats_order'] = max(good_steps.values()) + 1
            else:
                s['debats_order'] = good_steps.get(s['directory'], None)
        if s.get('step', '') == 'depot' and s['debats_order'] != None:
            if '/propositions/' in s.get('source_url', ''):
                s['auteur_depot'] = "Députés"
            elif '/leg/ppl' in s.get('source_url',''):
                s['auteur_depot'] = "Sénateurs"
            else:
                s['auteur_depot'] = "Gouvernement"
        for field in dict(s):
            if field.endswith('_directory') or field.endswith('_files'):
                del(s[field])

    return procedure
