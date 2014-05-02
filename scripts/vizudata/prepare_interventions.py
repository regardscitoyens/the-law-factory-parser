#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
from common import *

context = Context(sys.argv)
procedure = context.get_procedure()

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

gouv_members = {}
re_hash_gm = re.compile(r'\W+')
hash_gm = lambda x: re_hash_gm.sub('', x).lower()
def save_gm(i):
    hgm = hash_gm(i['intervenant_nom'])
    if hgm not in gouv_members or len(gouv_members[hgm]) < len(i['intervenant_fonction']):
        gouv_members[hgm] = i['intervenant_fonction']
def get_gm(i):
    hgm = hash_gm(i['intervenant_nom'])
    return gouv_members[hgm] if hgm in gouv_members else ""

re_gouv = re.compile(u'(ministre|garde.*sceaux|secr[eéÉ]taire.*[eéÉ]tat|haut-commissaire)', re.I)
re_parl = re.compile(u'(d[eéÉ]put[eéÉ]|s[eéÉ]nateur|membre du parlement|parlementaire)', re.I)
re_rapporteur = re.compile(ur'((vice|co|pr[eéÉ]sidente?)[,\-\s]*)?rapporte', re.I)
steps = {}
for step in procedure['steps']:
    if not ('has_interventions' in step and step['has_interventions']):
        continue
    intervs = []
    step['intervention_files'].sort()
    warndone = []
    for interv_file in step['intervention_files']:
        for i in open_json(os.path.join(context.sourcedir, 'procedure', step['intervention_directory']), "%s.json" % interv_file)['seance']:
            del(i['intervention']['contenu'])
            intervs.append(i)

    typeparl, urlapi = identify_room(intervs, 'intervention')

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
        i['intervenant_fonction'] = decode_html(i['intervenant_fonction'])
        if i['intervenant_fonction'].lower() in [u"président", u"présidente"]:
            gpe = u"Présidence"
        elif re_rapporteur.match(i['intervenant_fonction']):
            gpe = "Rapporteurs"
        elif re_gouv.search(i['intervenant_fonction']):
            gpe = "Gouvernement"
            save_gm(i)
        elif re_parl.match(i['intervenant_fonction']):
            gpe = "Autres parlementaires"
        # Consider auditionnés individually ?
#        elif not i['intervenant_slug']:
#            gpe = i['intervenant_fonction']
        # or not:
        if not gpe:
            if context.DEBUG and i['intervenant_nom'] not in warndone:
                warndone.append(i['intervenant_nom'])
                sys.stderr.write('WARNING: neither groupe nor function found for %s at %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl]))
            gm = get_gm(i)
            if gm:
                gpe = "Gouvernement"
                i['intervenant_fonction'] = gm
            else:
                gpe = u"Auditionnés"
        gpid = context.add_groupe(groupes, gpe, urlapi)
        add_intervs(sections[i[sectype]]['groupes'], gpid, i)

        # Consider as two separate speakers a same perso with two different fonctions
        orateur = i['intervenant_nom'].lower()
        if orateur not in orateurs:
            orateurs[orateur] = {'nom': i['intervenant_nom'],
                                 'fonction': i['intervenant_fonction'],
                                 'groupe': i['intervenant_groupe'],
                                 'color': '#888888',
                                 'link': parl_link(i, urlapi),
                                 'photo': photo_link(i, urlapi)}
            if i['intervenant_groupe'] and i['intervenant_groupe'].upper() in context.allgroupes[urlapi]:
                orateurs[orateur]['color'] = context.allgroupes[urlapi][i['intervenant_groupe'].upper()]['color']
        else:
            if len(i['intervenant_fonction']) > len(orateurs[orateur]['fonction']):
                if context.DEBUG and ((orateurs[orateur]['fonction'] and not i['intervenant_fonction'].startswith(orateurs[orateur]['fonction'])) or
                  (not orateurs[orateur]['fonction'] and not (i['intervenant_fonction'].startswith('rapporte') or i['intervenant_fonction'].startswith(u'président')))):
                    sys.stderr.write('WARNING: found different functions for %s at %s : %s / %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl], orateurs[orateur]['fonction'], i['intervenant_fonction']))
                orateurs[orateur]['fonction'] = i['intervenant_fonction']

        if not "orateurs" in sections[i[sectype]]['groupes'][gpid]:
            sections[i[sectype]]['groupes'][gpid]['orateurs'] = {}
        add_intervs(sections[i[sectype]]['groupes'][gpid]['orateurs'], orateur, i)
        if sections[i[sectype]]['groupes'][gpid]['orateurs'][orateur]['nb_intervs'] == 1:
            sections[i[sectype]]['groupes'][gpid]['orateurs'][orateur]['link'] = i['url_nos%ss' % typeparl]

    # Remove sections with less than 3 interventions
    for s in dict(sections):
        if sections[s]['total_intervs'] < 3:
            del(sections[s])

    steps[step['directory']] = {'groupes': groupes, 'orateurs': orateurs, 'divisions': sections}

print_json(steps)
