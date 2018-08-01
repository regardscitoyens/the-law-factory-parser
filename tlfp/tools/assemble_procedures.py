#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys

from tlfp.tools.common import format_date, datize, print_json, open_json, open_csv

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

dossiers = open_csv(sourcedir, 'dossiers.csv')
total = len(dossiers)


def last_known_activity(d):
    # TODO: use last step date
    return d["Date de promulgation"] or d["Date initiale"]


dossiers.sort(key=lambda k: format_date(last_known_activity(k)), reverse=True)

namefile = lambda npage: "dossiers_%s.json" % npage
def save_json_page(tosave, done):
    npage = (done - 1) // pagesize
    data = {"total": total,
            "count": len(tosave),
            "page": npage,
            "next_page": None,
            "dossiers": tosave}
    if done < total:
        data["next_page"] = namefile(npage+1)
    print('[assemble_procedure] >', namefile(npage))
    print_json(data, os.path.join(sourcedir, namefile(npage)))

done = 0
tosave = []

for d in dossiers:
    proc = open_json(os.path.join(sourcedir, d['id'], 'viz'), 'procedure.json')
    proc["id"] = d["id"]

    for f in ["table_concordance", "objet_du_texte"]:
        if f in proc:
            proc.pop(f)

    tosave.append(proc)
    done += 1
    if done % pagesize == 0:
        save_json_page(tosave, done)
        tosave = []

if tosave:
    save_json_page(tosave, done)
