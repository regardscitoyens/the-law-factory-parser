import os, sys, random
from functools import cmp_to_key

from lawfactory_utils.urls import download

try:
    from .common import *
    from .sort_articles import compare_articles
except SystemError:
    from common import *
    from sort_articles import compare_articles

def process(OUTPUT_DIR, procedure):
    context = Context([0, OUTPUT_DIR], load_parls=True)

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

    def sort_amendements(texte, amendements):
        articles = {}
        for article in texte:
            if article['type'] == 'article':
                titre = article.get('titre')
                if titre:
                    articles[titre.lower()] = article.get('order') * 10

        def clean_subject(subj):
            subj = subj.lower().strip()
            for regex, replacement in [
                    (r' (prem)?ier', '1er'),
                    (r'unique', '1er'),
                    (r'\s*\(((avant|apr).*)\)', r'\1'),
                    (r'\s*\(.*$', ''),
                    (r'^(\d)', r'article \1'),
                    (r'^(\d)', r'article \1'),
                    (r'articles', 'article'),
                    (r'art(\.|icle|\s)*(\d+)', r'article \2'),
                    (r'^(apr\S+s|avant)\s*', r'article additionnel \1 '),
                    (r'^(apr\S+s|avant)\s+article', r"\1 l'article"),
                    (r'^(\d+e?r? )([a-z]{1,2})$', lambda x: x.group(1) + x.group(2).upper()),
                    (r'^(\d+e?r? \S+ )([a-z]+)$', lambda x: x.group(1) + x.group(2).upper()),
                    (r'^ annexe.*', ''),
                    (r'^ rapport.*', ''),
                    (r'article 1$', 'article 1er'),
                ]:
                subj = re.sub(regex, replacement, subj)
                subj = subj.strip()
            return subj

        def solveorder(art):
            nonlocal articles
            art = art.lower()
            order = 10000;
            if art == 'titre' or art.startswith('intitul'):
                return 0
            elif art.startswith('motion'):
                return 1
            elif art.startswith('projet') \
                or art.startswith('proposition') \
                or art.startswith('texte'):
                return 5
            else:
                m = re.search(r'article (1er.*|(\d+).*)$', art, re.I)
                if m:
                    for match in m.group(1), m.group(2):
                        matched_order = articles.get(match)
                        if matched_order:
                            order = matched_order
                    if 'avant' in art:
                        order -= 1
                    elif re.match(r'apr\S+s', art, re.I):
                        order += 1
            return order


        for amendement in amendements:
            amdt = amendement['amendement']
            amdt['sujet'] = clean_subject(amdt['sujet'])
            amdt['ordre_article'] = solveorder(amdt['sujet'])

        return amendements


    CACHE_BUSTING = 'cache=%d' % random.randint(0, 10000)
    steps = {}
    last_text_id = None
    for i, step in enumerate(procedure['steps']):
        print('     * amendement step -', step.get('source_url'))
        if step.get('step') not in ('commission', 'hemicycle') or step.get('echec'):
            continue

        if i == 0:
            continue

        texte_url = None
        # for a CMP hemicycle we have to get the right text inside the CMP commission
        if step.get('stage') == 'CMP' and step.get('step') == 'hemicycle':
            last_step = [step for step in procedure['steps'] if step.get('stage') == 'CMP' and step.get('step') == 'commission'][0]
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
            # TODO: review this to get the real text the amendements are done on
            last_step = procedure['steps'][i-1]
            texte_url = last_step.get('source_url')

        if texte_url is None:
            print('ERROR - no texte url', step.get('source_url'), file=sys.stderr)

        texte = open_json(os.path.join(context.sourcedir, 'procedure', last_step['directory']), 'texte/texte.json')

        amdt_url = None
        if "nationale.fr" in texte_url:
            amdt_url = 'https://nosdeputes.fr/%s/amendements/%s/json?%s' % (procedure['assemblee_legislature'], get_text_id(texte_url), CACHE_BUSTING)
        elif "senat.fr" in texte_url:
            amdt_url = 'https://nossenateurs.fr/amendements/%s/json?%s' % (get_text_id(texte_url), CACHE_BUSTING)

        if amdt_url is None:
            continue

        print('     * downloading amendments:', amdt_url, 'for', texte_url)

        amendements_src = download(amdt_url).json().get('amendements', [])

        # TA texts can be zero-paded or not (TA0XXX or TAXXX), we try both
        if 'amendements/TA' in amdt_url:
            textid = get_text_id(texte_url)
            if 'TA0' in textid:
                alternative_url = amdt_url.replace(textid, 'TA' + textid.replace('TA', '').lstrip('0'))
            else:
                alternative_url = amdt_url.replace(textid, 'TA' + textid.replace('TA', '').zfill(4))
            print(' WARNING: TA - trying alternative url too', alternative_url)
            amendements_src += download(alternative_url).json().get('amendements', [])

        print('  parsing amendments:', len(amendements_src))

        step['nb_amendements'] = len(amendements_src)

        if len(amendements_src) == 0:
            continue

        amendements_src = sort_amendements(texte['articles'], amendements_src)

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

        print('    * downloading interventions')
        inter_dir = os.path.join(context.sourcedir, 'procedure', step['directory'], 'interventions')
        if not os.path.exists(inter_dir):
            os.makedirs(inter_dir)
        commission_or_hemicycle = '?commission=1' if step.get('step') == 'commission' else '?hemicycle=1'
        # TODO: TA texts can be zero-paded or not (TA0XXX or TAXXX), we should try both
        # TODO: last_text_id check same stage same institution
        seance_name = None
        intervention_files = []
        for loiid in get_text_id(texte_url), last_text_id:
            url_seances = 'https://{}.fr/seances/{}/json{}'.format(urlapi, loiid, commission_or_hemicycle)
            print('         * downloading seances - ', url_seances)
            for id_seance_obj in download(url_seances).json().get('seances', []):
                url_seance = 'https://{}.fr/seance/{}/{}/json'.format(urlapi, id_seance_obj['seance'], loiid)
                print('             * downloading seance - ', url_seance)
                resp = download(url_seance).json()
                if resp.get('seance'):
                    inter = resp.get('seance')[0]['intervention']
                    seance_name = inter['date'] + 'T' + inter['heure'] + '_' + inter['seance_id']
                    print('                 * dumping seance -', seance_name)
                    intervention_files.append(seance_name)
                    print_json(resp, os.path.join(inter_dir, seance_name + '.json'))
            if seance_name:
                step['has_interventions'] = True
                step['intervention_files'] = intervention_files
                break

        last_text_id = get_text_id(texte_url)

    return procedure

if __name__ == '__main__':
    process(sys.argv[1], json.load(open(os.path.join(sys.argv[1], 'viz/procedure.json'))))
