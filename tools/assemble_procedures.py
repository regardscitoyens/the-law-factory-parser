#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from common import *
from aggregates_data import DossierWalker,CountAmendementComputation

sourcedir = sys.argv[1]
if not sourcedir:
    sys.stderr.write('ERROR: no input directory given\n')
    exit(1)

pagesize = 50
if len(sys.argv) > 2:
    try:
        pagesize = int(sys.argv[2])
    except:
        sys.stderr.write('ERROR: pagesize given as input should be an integer: %s\n' % sys.argv[2])
        exit(1)

dossiers = open_csv(sourcedir, 'dossiers_promulgues.csv')
dossiers = [d for d in dossiers if d.get('Date de promulgation')]
total = len(dossiers)

# Compute dates and length
maxdays = 0
mindate = "9999"
maxdate = ""
for d in dossiers:
    d0 = format_date(d["Date initiale"])
    d1 = format_date(d["Date de promulgation"])
    days = (datize(d1) - datize(d0)).days + 1
    maxdays = max(maxdays, (datize(d1) - datize(d0)).days + 1)
    mindate = min(mindate, d0)
    maxdate = max(maxdate, d1)

dossiers.sort(key=lambda k: format_date(k['Date de promulgation']), reverse=True)

namefile = lambda npage: "dossiers_%s.json" % npage
def save_json_page(tosave, done):
    npage = (done - 1) // pagesize
    data = {"total": total,
            "min_date": mindate,
            "max_date": maxdate,
            "max_days": maxdays,
            "count": len(tosave),
            "page": npage,
            "next_page": None,
            "dossiers": tosave}
    if done < total:
        data["next_page"] = namefile(npage+1)
    print_json(data, os.path.join(sourcedir, namefile(npage)))

done = 0
tosave = []

def read_articles(text_id, step_id):
    articles = open_json(os.path.join(sourcedir, text_id, 'procedure', step_id, 'texte'), 'texte.json')['articles']
    return {art['titre']: clean_text_for_diff([art['alineas'][al] for al in sorted(art['alineas'].keys())]) for art in articles}

def read_text(text_id, step_id):
    articles = open_json(os.path.join(sourcedir, text_id, 'procedure', step_id, 'texte'), 'texte.json')['articles']
    texte = []
    for art in articles:
        for key in sorted(art['alineas'].keys()):
            if art['alineas'][key] != '':
                texte.append(strip_text(art['alineas'][key]))
    return texte

for d in dossiers:
    computation = CountAmendementComputation()
    myWalker = DossierWalker(d["id"], computation, sourcedir)
    myWalker.walk()

    proc = open_json(os.path.join(sourcedir, d['id'], 'viz'), 'procedure.json')
    proc["id"] = d["id"]
    proc["beginning"] = format_date(d["Date initiale"])
    proc["end"] = format_date(d["Date de promulgation"])
    proc["total_days"] = (datize(proc["end"]) - datize(proc["beginning"])).days + 1
    # proc["procedure"] = proc["type"]
    proc["type"] = d["Type de dossier"]
    proc["themes"] = [a.strip().lower() for a in d["Thèmes"].split(',')]
    proc["total_amendements"] = int(d["total_amendements"])
    proc["total_amendements_adoptes"] = computation.countAmdtAdoptes
    proc["total_amendements_parlementaire"] = computation.countAmdtParl
    proc["total_amendements_parlementaire_adoptes"] = computation.countAmdtParlAdoptes
    proc["total_mots"] = int(d["total_mots"])
    proc["total_mots2"] = computation.countNbMots
    proc["total_intervenant"] = len(computation.dicoIntervenants)
    proc["total_accident_procedure"] = computation.countAccidentProcedure
    proc["total_articles"] = computation.totalArticles
    proc["total_articles_modified"] = computation.totalArticlesModified
    proc["ratio_article_modif"] = computation.totalArticlesModified/computation.totalArticles if computation.totalArticles != 0 else 0
    proc["input_text_length"] = computation.firstStepTextLength
    proc["output_text_length"] = computation.lastStepTextLength
    first_found = False
    for s in proc['steps']:
        if s['debats_order'] == None or s.get('echec'):
            continue
        if s.get('step') != "depot":
            first_found = True
            lastText = read_text(d['id'], s['directory'])
            #lastArts = read_articles(d['id'], s['directory'])
        # TODO take real first depot in case of multiple depots
        if not first_found and s.get('step') == "depot":
            firstText = read_text(d['id'], s['directory'])
            #firstArts = read_articles(d['id'], s['directory'])
    proc["ratio_texte_modif"] = 1 - compute_approx_similarity(firstText, lastText)
    #proc["ratio_texte_modif"] = 1 - compute_similarity(firstArts, lastArts)
    #proc["ratio_texte_modif"] = 1 - compute_similarity_by_articles(firstArts, lastArts)
    proc["input_text_length2"] = len("\n".join(firstText))
    proc["output_text_length2"] = len("\n".join(lastText))


# TODO:
# - take dates + décision CC from csv
# - take état du dossier from csv when more than promulgués (and handle better end date then)

    for f in ["table_concordance", "objet_du_texte"]:
        if f in proc:
            proc.pop(f)

    tosave.append(proc)
    done += 1
    if done % pagesize == 0:
        print('dossiers.json dumping:', done, 'doslegs')
        save_json_page(tosave, done)
        tosave = []

if tosave:
    save_json_page(tosave, done)

