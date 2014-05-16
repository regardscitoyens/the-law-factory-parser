#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from common import *

context = Context(sys.argv)
procedure = context.get_procedure()

re_clean_add = re.compile(r'^.*additionnel[le\s]*', re.I)
format_sujet = lambda t: upper_first(re_clean_add.sub('', t))

#['Indéfini', 'Adopté', 'Irrecevable', 'Rejeté', 'Retiré', 'Tombe', 'Non soutenu', 'Retiré avant séance', 'Rectifié', 'Favorable' ,'Satisfait']
def simplify_sort(sort):
    sort = sort.lower()
    if sort in u"adopté favorable":
        return u"adopté"
    if sort in u"rejeté ":
        return u"rejeté"
    return u"non-voté"

def find_groupe(amd):
    if amd['signataires'] and "gouvernement" in amd['signataires'].lower():
        return "Gouvernement"
    ct = {}
    maxc = 0
    result = ""
    for gpe in amd['groupes_parlementaires']:
        g = gpe['groupe'].upper()
        if g not in ct:
            ct[g] = 0
        ct[g] += 1
        if ct[g] > maxc:
            maxc = ct[g]
            result = g
    return result

steps = {}
for step in procedure['steps']:
    if not 'nb_amendements' in step or not step['nb_amendements']:
        continue

    amendements_src = open_json(os.path.join(context.sourcedir, 'procedure', step['amendement_directory']), 'amendements.json')['amendements']

    typeparl, urlapi = identify_room(amendements_src, 'amendement')

    sujets = {}
    groupes = {}
    for amd in amendements_src:
        a = amd['amendement']
        if "sort" not in a:
            print >> sys.stderr, a
        if a["sort"] == u"Rectifié":
            continue
        key = format_sujet(a['sujet'])
        if key not in sujets:
            sujets[key] = {
              'titre': key,
              'details': a['sujet'],
              'order': a['ordre_article'],
              'amendements': []
            }

        gpe = find_groupe(a)
        if not gpe:
            sys.stderr.write('WARNING: no groupe found for %s\n' % a['url_nos%ss' % typeparl])
            gpe = "Inconnu"
        context.add_groupe(groupes, gpe, urlapi)

        sujets[key]['amendements'].append({
          'numero': a['numero'],
          'date': a['date'],
          'sort': simplify_sort(a['sort']),
          'groupe': gpe,
          'id_api': a['id']

        })


    amdtsfile = os.path.join(context.sourcedir, 'viz', 'amendements_%s.json' % step['directory'])
    data = {'id_step': step['directory'],
            'api_root_url': amdapi_link(urlapi),
            'groupes': groupes,
            'sujets': sujets}
    print_json(data, amdtsfile)

