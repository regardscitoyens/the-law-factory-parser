#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys

from lawfactory_utils.urls import download, enable_requests_cache, clean_url
enable_requests_cache()

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
    if sort in "adopté favorable":
        return "adopté"
    if sort in "rejeté ":
        return "rejeté"
    if sort in "indéfini":
        return "en attente"
    return "non-voté"

re_clean_first = re.compile(r'^(.*?)(,| et) .*$')
def first_author(signataires):
    if signataires is None or "gouvernement" in signataires.lower():
        return ""
    return re_clean_first.sub(r'\1, …', signataires)

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
for i, step in enumerate(procedure['steps']):
    if step.get('step') not in ('commission', 'hemicycle'):
        continue

    if i == 0:
        continue

    last_step = procedure['steps'][i-1]
    texte = open_json(os.path.join(context.sourcedir, 'procedure', last_step['directory']), 'texte/texte.json')

    amdt_url = None
    if 'nosdeputes_id' in texte:
        amdt_url = 'https://nosdeputes.fr/%s/amendements/%s/json' % (procedure['assemblee_legislature'], texte['nosdeputes_id'])
    elif 'nossenateurs_id' in texte:
        amdt_url = 'https://nossenateurs.fr/amendements/%s/json' % texte['nossenateurs_id']
    if amdt_url is None:
        continue

    amendements = download(amdt_url).json()
    amendements_src = amendements['amendements']

    print(amdt_url, len(amendements_src), texte['source'])

    if len(amendements_src) == 0:
        continue

    typeparl, urlapi = identify_room(amendements_src, 'amendement',
        legislature=step.get('assemblee_legislature', procedure.get('assemblee_legislature')))

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
            print(a, file=sys.stderr)
        if a["sort"] == "Rectifié":
            continue
        try:
            key = format_sujet(a['sujet'])
        except:
            sys.stderr.write('WARNING: amendment has no subject %s\n' % a['url_nos%ss' % typeparl])
            continue
        if key not in sujets:
            orders.append(key)
            sujets[key] = {
              'titre': key,
              'details': a['sujet'],
              # TODO: port sort_amendements.pl
              'order': a.get('ordre_article', 10),
              'amendements': []
            }
        if a.get('ordre_article', 10) > 9000:
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
          'id_api': a['id'],
          'aut': first_author(a['signataires'])
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
            'links': list(links.values()),
            'parlementaires': dict((p["i"], dict((k, p[k]) for k in "psang")) for p in list(parls.values()))}
    print_json(data, linksfile)


