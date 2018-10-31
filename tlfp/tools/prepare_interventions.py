#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re

from tlfp.tools.common import *

re_short_orga = re.compile(r'(,| et) (à |aux |d).*$')
def clean_orga(orga):
    orga = orga.replace(" de l'assemblée nationale", "")
    orga = orga.replace(" du sénat", "")
    orga = re_short_orga.sub('', orga)
    return orga

def init_section(dic, key, inter, order):
    if inter[key] and inter['seance_lieu'] != 'Hémicycle':
        inter[key] = clean_orga(inter['seance_lieu']) + " <br/> " + inter[key]
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

re_hash = re.compile(r'\W+')
hash_name = lambda x: re_hash.sub('', x).lower()
def save_hash(i, dico, val=None):
    if not val:
        val = i['intervenant_fonction']
    h = hash_name(i['intervenant_nom'])
    if h not in dico or len(dico[h]) < len(val):
        dico[h] = val
def get_hash(i, dico):
    h = hash_name(i['intervenant_nom'])
    return dico[h] if h in dico else ""

re_gouv = re.compile('(ministre|garde.*sceaux|secr[eéÉ]taire.*[eéÉ]tat|haut-commissaire)', re.I)
re_parl = re.compile('(d[eéÉ]put[eéÉ]|s[eéÉ]nateur|membre du parlement|parlementaire)', re.I)
re_rapporteur = re.compile(r'((vice|co|pr[eéÉ]sidente?)[,\-\s]*)?rapporte', re.I)

re_id_laststep = re.compile(r'/[^/\d]*(\d+)\D[^/]*$')

DEBUG = '--debug' in sys.argv

def process(OUTPUT_DIR, procedure):
    context = Context(OUTPUT_DIR, load_parls=True)

    gouv_members = {}
    rapporteurs = {}
    orat_gpes = {}
    def save_gm(i):
        save_hash(i, gouv_members)
    def get_gm(i):
        return get_hash(i, gouv_members)
    def save_rap(i):
        save_hash(i, rapporteurs)
    def get_rap(i):
        return get_hash(i, rapporteurs)
    def save_o_g(i, gpe):
        save_hash(i, orat_gpes, gpe)
    def get_o_g(i):
        return get_hash(i, orat_gpes)

    steps = {}
    id_step = None
    for step in procedure['steps']:
        legislature = step.get('assemblee_legislature', procedure.get('assemblee_legislature'))
        done_links = {}
        id_laststep = id_step
        try:
            id_step = re_id_laststep.search(step["source_url"]).group(1)
        except:
            id_step = None
        if not ('has_interventions' in step and step['has_interventions']):
            continue
        intervs = []
        step['intervention_files'].sort()
        warndone = []
        for seance_file in step['intervention_files']:
            interventions = open_json(os.path.join(context.sourcedir, 'procedure', step['directory'], 'interventions'), "%s.json" % seance_file)['seance']
            has_tag_loi = 0
            if id_laststep:
                for i in interventions:
                    if {"loi": id_laststep} in i['intervention']['lois']:
                        has_tag_loi += 1
            for i in interventions:
                del(i['intervention']['contenu'])
                if has_tag_loi > 2 and {"loi": id_laststep} not in i['intervention']['lois']:
                    if DEBUG:
                        print("SKIPPING interv " + i['intervention']['id'] + " with missing tag loi", file=sys.stderr)
                    continue
                intervs.append(i)

        if step.get('institution') == 'assemblee' and intervs:
            legislature = national_assembly_text_legislature(intervs[0]['intervention']['source'])
        typeparl, urlapi = identify_room(step.get('institution'), legislature)

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
        orat_gpes = {}
        for inter in intervs:
            i = inter['intervention']
            if not i['intervenant_nom']:
                continue
            sections[i[sectype]]['total_intervs'] += 1
            sections[i[sectype]]['total_mots'] += int(i['nbmots'])

            # Fix groupes not historicized in NosSénateurs
            if typeparl == "senateur" and i["intervenant_slug"]:
                i["intervenant_groupe"] = context.get_senateur_groupe(i["intervenant_slug"], i["date"], urlapi)

            # Consider as separate groups cases such as: personnalités, présidents and rapporteurs
            gpe = i['intervenant_groupe']
            i['intervenant_fonction'] = decode_html(i['intervenant_fonction'])
            if i['intervenant_fonction'].lower() in ["président", "présidente"]:
                gpe = "Présidence"
            elif re_rapporteur.match(i['intervenant_fonction']):
                gpe = "Rapporteurs"
                save_rap(i)
            elif re_gouv.search(i['intervenant_fonction']):
                gpe = "Gouvernement"
                save_gm(i)
            elif not gpe and re_parl.search(i['intervenant_fonction']+' '+i['intervenant_nom']):
                gpe = "Autres parlementaires"
                # unmeaningful information hard to rematch to the groups, usually invectives, skipping it
                if DEBUG and i['intervenant_nom'] not in warndone:
                    warndone.append(i['intervenant_nom'])
                    print('WARNING: skipping interventions from %s at %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl]), file=sys.stderr)
                continue
            if not gpe:
                if DEBUG and i['intervenant_nom'] not in warndone:
                    warndone.append(i['intervenant_nom'])
                    print('WARNING: neither groupe nor function found for %s at %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl]), file=sys.stderr)
                gm = get_gm(i)
                if gm:
                    gpe = "Gouvernement"
                    i['intervenant_fonction'] = gm
                else:
                    gpe = "Auditionnés"
            else:
                ra = get_rap(i)
                if ra:
                    gpe = "Rapporteurs"
                    i['intervenant_fonction'] = ra
            existing = get_o_g(i)
            if not (existing and gpe == "Présidence") and gpe != get_o_g(i):
                save_o_g(i, gpe)

        for inter in intervs:
            i = inter['intervention']
            gpe = get_o_g(i)
            if not gpe:
                continue
            gpid = context.add_groupe(groupes, get_o_g(i), urlapi)
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
                    if DEBUG and ((orateurs[orateur]['fonction'] and not i['intervenant_fonction'].startswith(orateurs[orateur]['fonction'])) or
                      (not orateurs[orateur]['fonction'] and not (i['intervenant_fonction'].startswith('rapporte') or i['intervenant_fonction'].startswith('président')))):
                        print('WARNING: found different functions for %s at %s : %s / %s\n' % (i['intervenant_nom'], i['url_nos%ss' % typeparl], orateurs[orateur]['fonction'], i['intervenant_fonction']), file=sys.stderr)
                    orateurs[orateur]['fonction'] = i['intervenant_fonction']

            if not "orateurs" in sections[i[sectype]]['groupes'][gpid]:
                sections[i[sectype]]['groupes'][gpid]['orateurs'] = {}
            add_intervs(sections[i[sectype]]['groupes'][gpid]['orateurs'], orateur, i)

            orat_sec = "%s-%s-%s" % (i[sectype],gpid,orateur)
            if orat_sec not in done_links:
                if not "link" in sections[i[sectype]]['groupes'][gpid]['orateurs'][orateur] or int(i['nbmots']) > 20:
                    sections[i[sectype]]['groupes'][gpid]['orateurs'][orateur]['link'] = i['url_nos%ss' % typeparl]
                    if int(i['nbmots']) > 20:
                        done_links[orat_sec] = True

        # Remove sections with less than 3 interventions or invalid section name
        for s in dict(sections):
            if not s or sections[s]['total_intervs'] < 3 or sections[s]['total_mots'] < 150 or list(sections[s]['groupes'].keys()) == ['Présidence']:
                del(sections[s])

        if sections:
            steps[step['directory']] = {
                'groupes': groupes,
                'orateurs': orateurs,
                'divisions': sections,
                'total_seances': len(seances),
            }

    print_json(steps, os.path.join(context.sourcedir, 'viz/interventions.json'))


if __name__ == '__main__':
    process(sys.argv[1], json.load(open(os.path.join(sys.argv[1], 'viz/procedure.json'))))
