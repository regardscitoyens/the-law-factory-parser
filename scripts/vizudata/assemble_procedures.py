#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from common import *
from aggregates_data import DossierWalker,CountAmendementComputation

sourcedir = os.path.join(sys.argv[1], 'data')
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
total = len(dossiers)

# Compute dates and length
maxdays = 0
mindate = "9999"
maxdate = ""
for d in dossiers:
    d0 = format_date(d["Date initiale"])
    d1 = format_date(d["Date de promulgation"])
    days =  (datize(d1) - datize(d0)).days + 1
    maxdays = max(maxdays, (datize(d1) - datize(d0)).days + 1)
    mindate = min(mindate, d0)
    maxdate = max(maxdate, d1)

dossiers.sort(key=lambda k: format_date(k['Date de promulgation']), reverse=True)

namefile = lambda npage: "dossiers_%s_%s.json" % (pagesize*npage, min(total, pagesize*(npage+1))-1)
def save_json_page(tosave, done):
    npage = (done - 1) / pagesize
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
for d in dossiers:

    computation = CountAmendementComputation()
    myWalker = DossierWalker(d["id"],computation)
    myWalker.walk()

    proc = open_json(os.path.join(sourcedir, d['id'], 'viz'), 'procedure.json')
    proc["id"] = d["id"]
    proc["beginning"] = format_date(d["Date initiale"])
    proc["end"] = format_date(d["Date de promulgation"])
    proc["total_days"] = (datize(proc["end"]) - datize(proc["beginning"])).days + 1
    proc["procedure"] = proc["type"]
    proc["type"] = d["Type de dossier"]
    proc["themes"] = [a.strip().lower() for a in d[u"Thèmes"].split(',')]
    proc["total_amendements"] = int(d["total_amendements"])
    proc["total_amendements_adoptes"] = computation.countAmdtAdoptes
    proc["total_mots"] = int(d["total_mots"])

# TODO:
# - take dates + décision CC from csv
# - take état du dossier from csv when more than promulgués (and handle better end date then)
# - take "numéro de la loi" from csv ? link to legifrance ? or just TA?
# - add more metrics (whole size diff, number echecs, diff total_articles, number amdmts adoptés majo/oppo, ...)

    tosave.append(proc)
    done += 1
    if done % pagesize == 0:
        save_json_page(tosave, done)
        tosave = []

if tosave:
    save_json_page(tosave, done)

