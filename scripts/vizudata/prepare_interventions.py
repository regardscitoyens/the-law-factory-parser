#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
from common import *

context = Context(sys.argv)
procedure = context.get_procedure()
allgroupes = context.get_groupes()

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

re_gouv = re.compile(r'(ministre|garde.*sceaux|secr[ée]taire.*[eé]tat|haut-commissaire)', re.I|re.U)
re_parl = re.compile(r'(d[eé]put[eé]|s[eé]nateur|membre du parlement|parlementaire)', re.I|re.U)

steps = {}
for step in procedure['steps']:
    if not ('has_interventions' in step and step['has_interventions']):
        continue
    intervs = []
    step['intervention_files'].sort()
    warndone = []
    for interv_file in step['intervention_files']:
        try:
            with open(os.path.join(context.sourcedir, 'procedure', step['intervention_directory'], "%s.json" % interv_file)) as interv_file:
                intervs += json.load(interv_file)['seance']
        except:
            sys.stderr.write('ERROR: intervention file %s listed in procedure.json missing from dir %s of %s' % (interv_file, step['intervention_directory'], context.sourcedir))
            exit(1)

    typeparl = "depute" if 'url_nosdeputes' in intervs[0]['intervention'] else "senateur"
    legis = intervs[0]['intervention']['url_nos%ss' % typeparl]
    legis = legis[7:legis.find('.')]
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
            gpe = u"Présidence"
        elif i['intervenant_fonction'].startswith('rapporte'):
            gpe = "Rapporteurs"
        elif re_gouv.search(i['intervenant_fonction']):
            gpe = "Gouvernement"
        elif re_parl.match(i['intervenant_fonction']):
            gpe = "Autres parlementaires"
        elif not i['intervenant_slug']:
            gpe = i['intervenant_fonction']
        if not gpe:
            if context.DEBUG and i['intervenant_nom'] not in warndone:
                warndone.append(i['intervenant_nom'])
                sys.stderr.write('WARNING: neither groupe nor function found for %s at %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl]))
            gpe = "Auditionnés"
        gpid = gpe.lower()
        if gpid not in groupes:
            groupes[gpid] = {'id': gpid,
                             'nom': gpe[0].upper() + gpe[1:],
                             'color': '#888888',
                             'link': ''}
            if gpid in allgroupes[urlapi]:
                groupes[gpid]['nom'] = allgroupes[urlapi][gpid]['nom']
                groupes[gpid]['color'] = allgroupes[urlapi][gpid]['color']
                groupes[gpid]['link'] = groupe_link({'slug': gpe}, urlapi)
        add_intervs(sections[i[sectype]]['groupes'], gpid, i)

        # Consider as two separate speakers a same perso with two different fonctions
        orateur = i['intervenant_nom']
        if orateur not in orateurs:
            orateurs[orateur] = {'nom': i['intervenant_nom'],
                                 'fonction': i['intervenant_fonction'],
                                 'groupe': i['intervenant_groupe'],
                                 'color': '#888888',
                                 'link': parl_link(i, urlapi),
                                 'photo': photo_link(i, urlapi)}
            if i['intervenant_groupe'] and i['intervenant_groupe'] in allgroupes[urlapi]:
                orateurs[orateur]['color'] = allgroupes[urlapi][i['intervenant_groupe']]['color']
        else:
            if len(i['intervenant_fonction']) > len(orateurs[orateur]['fonction']):
                if context.DEBUG and ((orateurs[orateur]['fonction'] and not i['intervenant_fonction'].startswith(orateurs[orateur]['fonction'])) or
                  (not orateurs[orateur]['fonction'] and not (i['intervenant_fonction'].startswith('rapporte') or i['intervenant_fonction'].startswith(u'président')))):
                    sys.stderr.write('WARNING: found different functions for %s at %s : %s / %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl], orateurs[orateur]['fonction'], i['intervenant_fonction']))
                orateurs[orateur]['fonction'] = i['intervenant_fonction']

        if not "orateurs" in sections[i[sectype]]['groupes'][gpid]:
            sections[i[sectype]]['groupes'][gpid]['orateurs'] = {}
        add_intervs(sections[i[sectype]]['groupes'][gpid]['orateurs'], orateur, i)

    # Remove sections with less than 3 interventions
    for s in dict(sections):
        if sections[s]['total_intervs'] < 3:
            del(sections[s])

    steps[step['directory']] = {'groupes': groupes, 'orateurs': orateurs, 'divisions': sections}

print_json(steps)
