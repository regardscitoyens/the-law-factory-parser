#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, csv, os, sys
try:
    import json
except:
    import simplejson as json

DEBUG = (len(sys.argv) > 2)

sourcedir = sys.argv[1]
if not sourcedir:
    sys.stderr.write('ERROR: no input directory given\n')
    exit(1)
try:
    with open(os.path.join(sourcedir, 'procedure', 'procedure.json'), "r") as procedure:
        procedure = json.load(procedure)
except:
    sys.stderr.write('ERROR: could not find procedure data in directory %s\n' % sourcedir)
    exit(1)

allgroupes = {}
for f in os.listdir(os.path.join(sourcedir, '..')):
    if f.endswith('-groupes.json'):
        url = f.replace('-groupes.json', '')
        try:
            with open(os.path.join(sourcedir, '..', f), "r") as gpes:
                allgroupes[url] = {}
                for gpe in json.load(gpes)['organismes']:
                    allgroupes[url][gpe["organisme"]["acronyme"]] = {
                        "nom": gpe["organisme"]['nom'],
                        "color": "rgb(%s)" % gpe["organisme"]['couleur']}
        except:
            sys.stderr.write('WARNING: could not read groupes file %s in data\n' % f)

def init_section(dic, key, inter, order):
    if inter[key] not in dic:
        dic[inter[key]] = {
            'source': inter['source'],
            'link': inter.get('url_nosdeputes', inter.get('url_nossenateurs')),
            'first_date': inter['date'],
            'last_date': inter['date'],
            'total_intervs': 0,
            'total_mots': 0,
            'groupes': {},
            'orateurs': {},
            'order': order
        }
        order += 1
    dic[inter[key]]['last_date'] = inter['date']
    return order

def add_intervs(dic, key, inter):
    if key not in dic:
        dic[key] = {
            'nb_intervs': 0,
            'nb_mots': 0
        }
    dic[key]['nb_intervs'] += 1
    dic[key]['nb_mots'] += int(inter['nbmots'])

photos_root_url = "http://##URLAPI##.fr/##TYPE##/photo/##SLUG##"
mps_root_url = "http://##URLAPI##.fr/##SLUG##"
groupes_root_url = "http://##URLAPI##.fr/groupe/##SLUG##"
def personalize_link(link, obj, urlapi):
    slug = obj.get('intervenant_slug', obj.get('slug', ''))
    typeparl = "senateur" if urlapi.endswith("senateurs") else "depute"
    if slug:
        return link.replace("##URLAPI##", urlapi).replace("##TYPE##", typeparl).replace("##SLUG##", slug)
    return ""

findpos = lambda t, c: t.find(c) if c in t else 1000

steps = {}
for step in procedure['steps']:
    if not ('has_interventions' in step and step['has_interventions']):
        continue
    intervs = []
    step['intervention_files'].sort()
    warndone = []
    for interv_file in step['intervention_files']:
        try:
            with open(os.path.join(sourcedir, 'procedure', step['intervention_directory'], "%s.json" % interv_file)) as interv_file:
                intervs += json.load(interv_file)['seance']
        except:
            sys.stderr.write('ERROR: intervention file %s listed in procedure.json missing from dir %s of %s' % (interv_file, step['intervention_directory'], sourcedir))
            exit(1)

    typeparl = "depute" if 'url_nosdeputes' in intervs[0]['intervention'] else "senateur"
    legis = intervs[0]['intervention']['url_nos%ss' % typeparl]
    legis = legis[7:min(findpos(legis, '-'), findpos(legis, '.'))]
    urlapi = "%s.nos%ss" % (legis, typeparl)

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

    groupes = {}
    orateurs = {}
    for inter in intervs:
        i = inter['intervention']
        if not i['intervenant_nom']:
            continue
        sections[i[sectype]]['total_intervs'] += 1
        sections[i[sectype]]['total_mots'] += int(i['nbmots'])

        # Consider as separate groups cases such as: personnalités, présidents and rapporteurs
        gpe = i['intervenant_groupe']
        if i['intervenant_fonction'] in [u"président", u"présidente"]:
            gpe = u"présidence"
        elif i['intervenant_fonction'].startswith('rapporte'):
            gpe = "rapporteurs"
        elif not i['intervenant_slug']:
            gpe = i['intervenant_fonction']
        # TODO : group gouvernement, reste = auditionnés ?
        if not gpe:
            if DEBUG and i['intervenant_nom'] not in warndone:
                warndone.append(i['intervenant_nom'])
                sys.stderr.write('WARNING: neither groupe nor function found for %s at %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl]))
            gpe = "autre"
        if gpe not in groupes:
            groupes[gpe] = {'nom': allgroupes[urlapi][gpe]['nom'] if gpe in allgroupes[urlapi] else gpe[0].upper() + gpe[1:],
                            'color': '#888888',
                            'link': personalize_link(groupes_root_url, {'slug': gpe if gpe in allgroupes[urlapi] else ''}, urlapi)}
            if gpe in allgroupes[urlapi]:
                groupes[gpe]['color'] = allgroupes[urlapi][gpe]['color']
        add_intervs(sections[i[sectype]]['groupes'], gpe, i)

        # Consider as two separate speakers a same perso with two different fonctions
        orateur = i['intervenant_nom']
        if orateur not in orateurs:
            orateurs[orateur] = {'nom': i['intervenant_nom'],
                                 'fonction': i['intervenant_fonction'],
                                 'groupe': i['intervenant_groupe'],
                                 'color': '#888888',
                                 'link': personalize_link(mps_root_url, i, urlapi),
                                 'photo': personalize_link(photos_root_url, i, urlapi)}
            if i['intervenant_groupe'] and i['intervenant_groupe'] in allgroupes[urlapi]:
                orateurs[orateur]['color'] = allgroupes[urlapi][i['intervenant_groupe']]['color']
        else:
            if len(i['intervenant_fonction']) > len(orateurs[orateur]['fonction']):
                if DEBUG and ((orateurs[orateur]['fonction'] and not i['intervenant_fonction'].startswith(orateurs[orateur]['fonction'])) or
                  (not orateurs[orateur]['fonction'] and not (i['intervenant_fonction'].startswith('rapporte') or i['intervenant_fonction'].startswith(u'président')))):
                    sys.stderr.write('WARNING: found different functions for %s at %s : %s / %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl], orateurs[orateur]['fonction'], i['intervenant_fonction']))
                orateurs[orateur]['fonction'] = i['intervenant_fonction']
        add_intervs(sections[i[sectype]]['orateurs'], orateur, i)
    steps[step['directory']] = {'groupes': groupes, 'orateurs': orateurs, 'divisions': sections}

print json.dumps(steps, ensure_ascii=False).encode('utf8')
