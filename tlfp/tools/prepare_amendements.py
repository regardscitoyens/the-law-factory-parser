import os
import sys
import re
from time import time
from functools import cmp_to_key

from lawfactory_utils.urls import download

from .common import Context, open_json, get_text_id, \
    identify_room, print_json, amdapi_link, \
    national_assembly_text_legislature
from .sort_articles import compare_articles
from ._step_logic import get_previous_step


def process(OUTPUT_DIR, procedure):
    context = Context(OUTPUT_DIR, load_parls=True)

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

    def find_groupe(amd, typeparl, urlapi):
        if amd['signataires'] and "gouvernement" in amd['signataires'].lower():
            return "Gouvernement"

        # Fix groupes not historicized in NosSénateurs
        if typeparl == "senateur" and amd["parlementaires"]:
            return context.get_senateur_groupe(amd["parlementaires"][0]["parlementaire"], amd["date"], urlapi)

        return amd['auteur_groupe_acronyme']

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

    article_number_regexp = re.compile(r'article (1er.*|(\d+).*)$', re.I)
    def sort_amendements(texte, amendements):
        articles = {}
        for article in texte:
            if article['type'] == 'article':
                titre = article.get('titre')
                if titre:
                    articles[titre.lower()] = article.get('order') * 10

        def solveorder(art):
            nonlocal articles
            art = art.lower()
            order = 10000
            if art == 'titre' or art.startswith('intitul'):
                return 0
            elif art.startswith('motion'):
                return 1
            elif art.startswith('projet') \
                or art.startswith('proposition') \
                or art.startswith('texte'):
                return 5
            else:
                m = article_number_regexp.search(art)
                if m:
                    if articles.get(m.group(1)):
                        order = articles.get(m.group(1))
                    elif articles.get(m.group(2)):
                        order = articles.get(m.group(2))
                    if 'avant' in art:
                        order -= 1
                    elif 'après' in art or 'apres' in art:
                        order += 1
            return order


        for amendement in amendements:
            amdt = amendement['amendement']
            amdt['ordre_article'] = solveorder(amdt['sujet'])

        return amendements


    CACHE_BUSTING = 'cache=%d' % time()
    if 'url_jo' in procedure:
        CACHE_BUSTING = 'cache=lfdll-prod' # fixed cache busting for promulgated laws
    steps = {}
    last_text_id, last_text_typeparl = None, None
    steps = procedure['steps']
    for i, step in enumerate(steps):
        print('    * step -', step.get('stage'), step.get('step'), step.get('source_url'))
        if step.get('step') not in ('commission', 'hemicycle'):
            continue
        if step.get('step') == 'commission' and step.get('stage') == 'CMP':
            continue

        if i == 0:
            continue

        last_step_index = get_previous_step(steps, i, is_old_procedure=procedure.get('use_old_procedure'))
        last_step = steps[last_step_index]
        last_step_with_good_text_number = steps[get_previous_step(steps, i,
            is_old_procedure=procedure.get('use_old_procedure'), get_depot_step=True)
        ]
        texte_url = last_step_with_good_text_number.get('source_url')

        if last_step.get('in_discussion'):
            print('WARNING: ignoring future steps further than current discussion', file=sys.stderr)
            break

        if step.get('stage') != 'CMP' and last_step_with_good_text_number.get('institution') != step.get('institution'):
            print('ERROR - last step is from another institution', file=sys.stderr)
            continue

        # for a CMP hemicycle we have to get the right text inside the CMP commission
        if step.get('stage') == 'CMP' and step.get('step') == 'hemicycle':
            urls = [last_step.get('source_url')]
            if 'cmp_commission_other_url' in last_step:
                urls.append(last_step.get('cmp_commission_other_url'))
            an_url = [url for url in urls if 'nationale.fr' in url]
            senat_url = [url for url in urls if 'senat.fr' in url]
            if step.get('institution') == 'assemblee' and an_url:
                texte_url = an_url[0]
            elif step.get('institution') == 'senat' and senat_url:
                texte_url = senat_url[0]
            else:
                print('WARNING - missing the CMP commission text for', step.get('source_url'), file=sys.stderr)
                continue

        if texte_url is None:
            print('ERROR - no texte url', step.get('source_url'), file=sys.stderr)
            continue

        legislature = None
        if 'assemblee-nationale.fr' in texte_url:
            legislature = national_assembly_text_legislature(texte_url)

        texte = open_json(os.path.join(context.sourcedir, 'procedure', last_step['directory']), 'texte/texte.json')

        typeparl, urlapi = identify_room(texte_url, legislature)

        amdt_url = None
        if "nationale.fr" in texte_url:
            if 'assemblee_legislature' not in procedure:
                print('         + no AN legislature - pass text')
                continue
            amdt_url = 'https://%s.fr/%s/amendements/%s/json?%s' % (urlapi, legislature, get_text_id(texte_url), CACHE_BUSTING)
        elif "senat.fr" in texte_url:
            amdt_url = 'https://%s.fr/amendements/%s/json?%s' % (urlapi, get_text_id(texte_url), CACHE_BUSTING)

        if amdt_url is None:
            continue

        print('      * downloading amendments:', amdt_url, 'for', texte_url)

        try:
            amendements_src = download(amdt_url).json().get('amendements', [])
        except:
            raise Exception("ERROR: amendements JSON at %s is badly formatted, it should probably be hardcached on ND/NS" % amdt_url)

        # TA texts can be zero-paded or not (TA0XXX or TAXXX), we try both
        if 'amendements/TA' in amdt_url:
            textid = get_text_id(texte_url)
            if 'TA0' in textid:
                alternative_url = amdt_url.replace(textid, 'TA' + textid.replace('TA', '').lstrip('0'))
            else:
                alternative_url = amdt_url.replace(textid, 'TA' + textid.replace('TA', '').zfill(4))
            print(' WARNING: TA - trying alternative url too', alternative_url)
            try:
                amendements_src += download(alternative_url).json().get('amendements', [])
            except:
                raise Exception("ERROR: amendements JSON at %s is badly formatted, it should probably be hardcached on ND/NS" % alternative_url)

        print('        parsing amendments:', len(amendements_src))

        # ignore amendments if they are not for the correct step
        amendements_src_filtered = []
        for amd in amendements_src:
            a = amd['amendement']
            if step.get('institution') == 'assemblee':
                # commission amendments can have two forms
                #    - /amendements/LOI/NUM.asp (13th legislature)
                #    - /amendements/LOI/COMMISSION_NAME/NUM.asp (14+ legislature)
                # hemicycle amendments are:
                #    - /amendements/LOI/NUM.asp (13th legislature)
                #    - /amendements/LOI/AN/NUM.asp (14+ legislature)
                amdt_step = 'hemicycle'
                if '/cr-' in a['source']:
                    amdt_step = 'commission'
                else:
                    url_parts = a['source'].split('amendements/')[1].split('/')
                    if len(url_parts) == 3 and url_parts[1] != 'AN':
                        amdt_step = 'commission'
            elif step.get('institution') == 'senat':
                amdt_step = 'commission' if '/commissions/' in a['source'] else 'hemicycle'
            else:
                # CMP - there's not way for now to distinguish the step
                amdt_step = step['step']
            if step['step'] != amdt_step:
                continue
            amendements_src_filtered.append(amd)

        if len(amendements_src_filtered) != len(amendements_src):
            print('WARNING: amendments ignored (not the right step) %s' %
                    (len(amendements_src) - len(amendements_src_filtered)), file=sys.stderr)
        amendements_src = amendements_src_filtered

        step['nb_amendements'] = len(amendements_src)

        if len(amendements_src) > 0:
            amendements_src = sort_amendements(texte['articles'], amendements_src)

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
                    print('WARNING: amendment has no sort %s\n' % a['url_nos%ss' % typeparl], file=sys.stderr)
                    continue
                if a["sort"] == "Rectifié":
                    continue
                if "sujet" not in a or not a["sujet"]:
                    if a["sort"] not in ["Irrecevable", "Retiré avant séance"]:
                        print('WARNING: amendment has no subject %s\n' % a['url_nos%ss' % typeparl], file=sys.stderr)
                    continue
                key = a['sujet']
                if not key:
                    print('WARNING: amendment has no subject %s\n' % a['url_nos%ss' % typeparl], file=sys.stderr)
                    continue
                if key not in sujets:
                    orders.append(key)
                    sujets[key] = {
                      'titre': key,
                      'order': a['ordre_article'],
                      'amendements': []
                    }
                if a['ordre_article'] > 9000:
                    fix_order = True

                gpe = find_groupe(a, typeparl, urlapi)
                if not gpe:
                    if a["sort"] != "Irrecevable":
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
                orders.sort(key=cmp_to_key(compare_articles))
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
            # print_json(data, linksfile)

        ###########  INTERVENTIONS #############
        # TODO: move this to a dedicated file

        print('      * downloading interventions')
        typeparl, urlapi = identify_room(texte_url, legislature)
        inter_dir = os.path.join(context.sourcedir, 'procedure', step['directory'], 'interventions')
        commission_or_hemicycle = '?commission=1' if step.get('step') == 'commission' else '?hemicycle=1'
        # TODO: TA texts can be zero-paded or not (TA0XXX or TAXXX), we should try both
        seance_name = None
        intervention_files = []

        texts = (get_text_id(texte_url),)
        if last_text_typeparl == typeparl:
            texts = (get_text_id(texte_url), last_text_id)

        for loiid in texts:
            if typeparl == 'depute':
                url_seances = 'https://%s.fr/%s/seances/%s/json%s' % (urlapi, legislature, loiid, commission_or_hemicycle)
            else:
                url_seances = 'https://%s.fr/seances/%s/json%s' % (urlapi, loiid, commission_or_hemicycle)

            print('        * downloading seances - ', url_seances)
            for id_seance_obj in sorted(download(url_seances).json().get('seances', []), key=lambda x: x["seance"]):
                if typeparl == 'depute':
                    url_seance = 'https://%s.fr/%s/seance/%s/%s/json' % (urlapi, legislature, id_seance_obj['seance'], loiid)
                else:
                    url_seance = 'https://%s.fr/seance/%s/%s/json' % (urlapi, id_seance_obj['seance'], loiid)

                print('           downloading seance - ', url_seance)
                resp = download(url_seance).json()
                if resp.get('seance'):
                    inter = resp.get('seance')[0]['intervention']
                    seance_name = inter['date'] + 'T' + inter['heure'] + '_' + inter['seance_id']
                    print('            dumping seance -', seance_name)
                    intervention_files.append(seance_name)
                    if not os.path.exists(inter_dir):
                        os.makedirs(inter_dir)
                    print_json(resp, os.path.join(inter_dir, seance_name + '.json'))
            if seance_name:
                step['has_interventions'] = True
                step['intervention_files'] = intervention_files
                break

        last_text_id = get_text_id(texte_url)
        last_text_typeparl = typeparl

    return procedure


if __name__ == '__main__':
    process(sys.argv[1], open_json(os.path.join(sys.argv[1], 'viz/procedure.json')))
