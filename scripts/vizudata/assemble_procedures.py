#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, csv
from datetime import date
try:
    import json
except:
    import simplejson as json
from common import print_json


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

try:
    with open(os.path.join(sourcedir, 'dossiers_promulgues.csv'), "r") as dossiers_file:
        dossiers = list(csv.DictReader(dossiers_file, delimiter=";"))
except:
    sys.stderr.write('ERROR: could not read dossiers_promulgues.csv in directory %s\n' % sourcedir)
    exit(1)

total = len(dossiers)
dossiers = sorted(dossiers, key=lambda k: k['Date de promulgation'])

namefile = lambda npage: "dossiers_%s_%s.json" % (pagesize*npage, min(total, pagesize*(npage+1))-1)
def save_json_page(tosave, done):
    npage = done / pagesize
    data = {"total": total,
            "page": npage,
            "next_page": None,
            "dossiers": tosave}
    if done < total:
        data["next_page"] = namefile(npage+1)
    print_json(data, os.path.join(sourcedir, namefile(npage)))

def format_date(d):
    da = d.split('/')
    da.reverse()
    return "-".join(da)
datize = lambda d: date(*tuple([int(a) for a in d.split('-')]))

delay_stats = 30
bin_stat = lambda x: "<%s" % (delay_stats * (x / delay_stats + 1))
stats = {}
done = 0
tosave = []
for d in dossiers:
    try:
        with open(os.path.join(sourcedir, d['id'], 'viz', 'procedure.json'), 'r') as proc_file:
            proc = json.loads(proc_file.read())
    except:
        sys.stderr.write('ERROR: could not read procedure.json in %s/%s/viz\n' % (sourcedir, d['id']))
        continue #exit(1)
    proc["id"] = d["id"]
    proc["beginning"] = format_date(d["Date initiale"])
    proc["end"] = format_date(d["Date de promulgation"])
    proc["total_days"] = (datize(proc["end"]) - datize(proc["beginning"])).days + 1
    proc["procedure"] = proc["type"]
    proc["type"] = d["Type de dossier"]
    proc["themes"] = [a.strip().lower() for a in d["Thèmes"].split(',')]
    proc["total_amendements"] = int(d["total_amendements"])
    proc["total_mots"] = int(d["total_mots"])

# TODO:
# - Add metric on all steps
# - take dates + décision CC from csv
# - take état du dossier from csv when more than promulgués (and handle better end date then)
# - take "numéro de la loi" from csv ? link to legifrance ? or just TA?

    statbin = bin_stat(proc["total_days"])
    if statbin not in stats:
        stats[statbin] = 0
    stats[statbin] += 1

    tosave.append(proc)
    done += 1
    if not done % pagesize:
        save_json_page(tosave, done)
        tosave = []

if tosave:
    save_json_page(tosave, done)

print_json(stats, os.path.join(sourcedir, 'stats_dossiers.json'))

