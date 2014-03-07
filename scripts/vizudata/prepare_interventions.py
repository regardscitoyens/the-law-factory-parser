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

def init_section(dic, key, inter, order):
    if inter[key] not in dic:
        dic[inter[key]] = {
            'source': inter['source'],
            'link': inter.get('url_nosdeputes', inter.get('url_nossenateurs')),
           # 'date': inter['date'],
           # 'moment': inter['heure'],
            'total_intervs': 0,
            'total_mots': 0,
            'groupes': {},
            'orateurs': {},
            'order': order
        }
        order += 1
    return order

def add_intervs(dic, key, inter):
    if key not in dic:
        dic[key] = {
            'nb_intervs': 0,
            'nb_mots': 0
        }
    dic[key]['nb_intervs'] += 1
    dic[key]['nb_mots'] += int(inter['nbmots'])

def personalize_link(link, inter, chambre):
    if inter['intervenant_slug']:
        return link.replace("##TYPE##", "senateur" if chambre == "Sénat" else "depute").replace("##SLUG##", inter['intervenant_slug'])
    return ""

photos_root_url = "http://www.nos##TYPE##s.fr/##TYPE##/photo/##SLUG##"
mps_root_url = "http://www.nos##TYPE##s.fr/##SLUG##"
steps = {}
for step in procedure['steps']:
    if not ('has_interventions' in step and step['has_interventions']):
        continue
    intervs = []
    step['intervention_files'].sort()
    for interv_file in step['intervention_files']:
        try:
            with open(os.path.join(sourcedir, 'procedure', step['intervention_directory'], "%s.json" % interv_file)) as interv_file:
                intervs += json.load(interv_file)['seance']
        except:
            sys.stderr.write('Error: intervention file %s listed in procedure.json missing from dir %s of %s' % (interv_file, step['intervention_directory'], sourcedir))
            exit(1)

    chambre = 'Assemblée nationale' if 'url_nosdeputes' in intervs[0]['intervention'] else 'Sénat'

    # By default divide in subsections, or by seance if no subsection
    sections = {}
    seances = {}
    sec_order = se_order = 1
    for i in intervs:
        i['intervention']['intervenant_fonction'] = i['intervention'].get('intervenant_fonction', '') or ''
        se_order = init_section(seances, 'seance_titre', i['intervention'], se_order)
        sec_order = init_section(sections, 'soussection', i['intervention'], sec_order)
    sectype = 'soussection'
    if len(sections) < 2:
        sectype = 'seance_titre'
        sections = seances

    groupes = []
    orateurs = []
    for inter in intervs:
        i = inter['intervention']
        if not i['intervenant_nom']:
            continue
        sections[i[sectype]]['total_intervs'] += 1
        sections[i[sectype]]['total_mots'] += int(i['nbmots'])

        # Consider as separate groups cases such as: personnalités, présidents and rapporteurs
        gpe = u"présidence" if i['intervenant_fonction'] in [u"président", u"présidente"] else i['intervenant_fonction'] if not i['intervenant_slug'] or i['intervenant_fonction'].startswith('rapporte') else i['intervenant_groupe']
        if gpe not in groupes:
            groupes.append(gpe)
        add_intervs(sections[i[sectype]]['groupes'], gpe, i)

        # Consider as two separate speakers a same perso with two different fonctions
        orateur = i['intervenant_nom']
        if i['intervenant_fonction']:
            orateur += ", %s" % i['intervenant_fonction']
        if orateur not in orateurs:
            orateurs.append(orateur)
        add_intervs(sections[i[sectype]]['orateurs'], orateur, i)
        sections[i[sectype]]['orateurs'][orateur]['groupe'] = i['intervenant_groupe']
        sections[i[sectype]]['orateurs'][orateur]['fonction'] = i['intervenant_fonction']
        sections[i[sectype]]['orateurs'][orateur]['link'] = personalize_link(mps_root_url, i, chambre)
        sections[i[sectype]]['orateurs'][orateur]['photo'] = personalize_link(photos_root_url, i, chambre)
    steps[step['directory']] = {'groupes': groupes, 'orateurs': orateurs, 'divisions': sections}

print json.dumps(steps, ensure_ascii=False).encode('utf8')
