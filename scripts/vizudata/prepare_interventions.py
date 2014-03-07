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
    sys.stderr.write('Error: could not find procedure data in directory %s' % sourcedir)
    exit(1)

def init_section(dic, key, inter):
    if inter[key] not in dic:
        dic[inter[key]] = {
            'source': inter['source'],
            'link': inter.get('url_nosdeputes', inter.get('url_nossenateurs')),
           # 'chambre': 'Assemblée nationale' if 'url_nosdeputes' in inter else 'Sénat',
           # 'date': inter['date'],
           # 'moment': inter['heure'],
            'total_intervs': 0,
            'total_mots': 0,
            'groupes': {},
            'orateurs': {}
        }

def add_intervs(dic, key, inter):
    if key not in dic:
        dic[key] = {
            'nom': key,
           # 'groupe': inter['intervenant_groupe'],
            'fonction': inter['intervenant_fonction'],
            'nb_intervs': 0,
            'nb_mots': 0
        }
    dic[key]['nb_intervs'] += 1
    dic[key]['nb_mots'] += int(inter['nbmots'])

steps = {}
for step in procedure['steps']:
    if not ('has_interventions' in step and step['has_interventions']):
        continue
    intervs = []
    for interv_file in step['intervention_files']:
        try:
            with open(os.path.join(sourcedir, 'procedure', step['intervention_directory'], "%s.json" % interv_file)) as interv_file:
                intervs += json.load(interv_file)['seance']
        except:
            sys.stderr.write('Error: intervention file %s listed in procedure.json missing from dir %s of %s' % (interv_file, step['intervention_directory'], sourcedir))
            exit(1)

    # By default divide in subsections, or by seance if no subsection
    sections = {}
    seances = {}
    for i in intervs:
        i['intervention']['intervenant_fonction'] = i['intervention'].get('intervenant_fonction', '') or ''
        init_section(seances, 'seance_titre', i['intervention'])
        init_section(sections, 'soussection', i['intervention'])
    sectype = 'soussection'
    if len(sections) < 2:
        sectype = 'seance_titre'
        sections = seances

    for inter in intervs:
        i = inter['intervention']
        if not i['intervenant_nom']:
            continue
        sections[i[sectype]]['total_intervs'] += 1
        sections[i[sectype]]['total_mots'] += int(i['nbmots'])

        # Consider as separate groups cases such as: personnalités, présidents and rapporteurs
        gpe = u"présidence" if i['intervenant_fonction'] in [u"président", u"présidente"] else i['intervenant_fonction'] if not i['intervenant_slug'] or i['intervenant_fonction'].startswith('rapporte') else i['intervenant_groupe']
        add_intervs(sections[i[sectype]]['groupes'], gpe, i)

        # Consider as two separate speakers a same perso with two different fonctions
        orateur = i['intervenant_nom']
        if i['intervenant_fonction']:
            orateur += ", %s" % i['intervenant_fonction']
        add_intervs(sections[i[sectype]]['orateurs'], orateur, i)
    steps[step['directory']] = sections

print json.dumps(steps, ensure_ascii=False).encode('utf8')
