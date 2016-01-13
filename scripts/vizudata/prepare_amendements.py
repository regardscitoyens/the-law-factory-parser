#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from common import *
sys.path.append(os.path.join("..", "collectdata"))
from sort_articles import compare_articles

context = Context(sys.argv, load_parls=True)
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
    if sort in u"indéfini":
        return u"en attente"
    return u"non-voté"

def find_groupe(amd):
    if amd['signataires'] and "gouvernement" in amd['signataires'].lower():
        return "Gouvernement"
    ct = {}
    maxc = 0
    result = ""
    for gpe in amd['groupes_parlementaires']:
        g = slug_groupe(gpe['groupe'])
        if g not in ct:
            ct[g] = 0
        ct[g] += 1
        if ct[g] > maxc:
            maxc = ct[g]
            result = g
    return result

def add_link(links, pA, pB, weight=1):
    p1 = min(pA, pB)
    p2 = max(pA, pB)
    linkid = "%s-%s" % (p1, p2)
    if linkid not in links:
        links[linkid] = {
          "1": p1,
          "2": p2,
          "w": 0
        }
    links[linkid]["w"] += weight


steps = {}
for step in procedure['steps']:
    if not 'nb_amendements' in step or not step['nb_amendements']:
        continue

    amendements_src = open_json(os.path.join(context.sourcedir, 'procedure', step['amendement_directory']), 'amendements.json')['amendements']

    typeparl, urlapi = identify_room(amendements_src, 'amendement')

    sujets = {}
    groupes = {}

    fix_order = False
    orders = []
    parls = {}
    links = {}
    idents = {}
    for amd in amendements_src:
        a = amd['amendement']
        if "sort" not in a:
            print >> sys.stderr, a
        if a["sort"] == u"Rectifié":
            continue
        key = format_sujet(a['sujet'])
        if key not in sujets:
            orders.append(key)
            sujets[key] = {
              'titre': key,
              'details': a['sujet'],
              'order': a['ordre_article'],
              'amendements': []
            }
        if a['ordre_article'] > 9000:
            fix_order = True

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

        cosign = []
        hmd5 = a["cle_unicite"]
        if hmd5 not in idents:
            idents[hmd5] = []
        for parll in a["parlementaires"]:
            parl = parll["parlementaire"]
            if parl not in parls:
                p = context.get_parlementaire(urlapi, parl)
                parls[parl] = {
                  "i": p["id"],
                  "s": parl,
                  "a": 0,
                  "n": p["nom"],
                  "g": p["groupe_sigle"],
                  "p": p["place_en_hemicycle"]
                }
            pid = parls[parl]["i"]
            parls[parl]["a"] += 1
            for cid in cosign:
                add_link(links, pid, cid)
                #add_link(links, pid, cid, 2)
            cosign.append(pid)
            for cid in idents[hmd5]:
                add_link(links, pid, cid)
            idents[hmd5].append(pid)

    if fix_order:
        orders.sort(compare_articles)
        for i, k in enumerate(orders):
            sujets[k]["order"] = i

    amdtsfile = os.path.join(context.sourcedir, 'viz', 'amendements_%s.json' % step['directory'])
    data = {'id_step': step['directory'],
            'api_root_url': amdapi_link(urlapi),
            'groupes': groupes,
            'sujets': sujets}
    print_json(data, amdtsfile)

    linksfile = os.path.join(context.sourcedir, 'viz', 'amendements_links_%s.json' % step['directory'])
    data = {'id_step': step['directory'],
            'links': links.values(),
            'parlementaires': dict((p["i"], dict((k, p[k]) for k in "psang")) for p in parls.values())}
    print_json(data, linksfile)


