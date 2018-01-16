import os, sys
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

    steps = {}
    for i, step in enumerate(procedure['steps']):
        if step.get('step') not in ('commission', 'hemicycle') or step.get('echec'):
            continue

        if i == 0:
            continue

        # TODO: CMP get hemicycle text and the good one
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
        print_json(data, linksfile)

if __name__ == '__main__':
    process(sys.argv[1], json.load(open(os.path.join(sys.argv[1], 'viz/procedure.json'))))
