#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Create a json from from a procedure csv one"""

import sys, os, re
import simplejson as json
import csv

csvpath = sys.argv[1]
projectdir = csvpath.replace('/procedure.csv', '')

def row2dir(row):
    return row[6]+'_'+row[8].replace(' ', '')+'_'+row[9]+'_'+row[10]

re_clean_texte = re.compile(r'(\s\+|de la sécurité sociale de financement |rectificative de finances |règlement portant |\.$)', re.I)
re_shorten_title = re.compile(r"^pro(jet|position) de (loi|résolution)[\s:]*( (constitutionnelle|organique))* (sur |(port|ratifi|proroge|modifi|institu|habilit|interdis|tend|approuv|autoris|r[eé](lati[vfe]|tablissa|nforç))[ant,àux ]*)*(l(a ratific|'approb)ation d(e( l(a|')|s)? ?|u |'une? ))*(l['ea]s?\s*)?", re.I)

upper_first = lambda t: t[0].upper() + t[1:]
url_jo = ""

procedure = {'type': 'Normale'}
steps = []
with open(csvpath, 'rb') as csvfile:
    csvproc = csv.reader(csvfile, delimiter=';')
    for row in csvproc:
        if len(row) < 15:
            row.append("")
        step = {'date': row[13], 'enddate': row[14], 'stage': row[8], 'institution': row[9], 'source_url': row[11], 'echec': row[15] or None}
        if row[7] != 'EXTRA':
            step['directory'] = row2dir(row)
            try:
                amdfile = os.path.join(projectdir, step['directory'], 'amendements', 'amendements.csv')
                if os.stat(amdfile):
                    try:
                        with open(amdfile, 'r') as amdf:
                            step['nb_amendements'] = len(list(csv.DictReader(amdf, delimiter=";")))
                    except:
                        sys.stderr.write('ERROR: Could not read file %s' % amdfile)
                        exit(1)
                    step['amendement_directory'] = os.path.join(step['directory'], 'amendements')
            except:
                step['nb_amendements'] = 0
            try:
                interv_dir = os.path.join(step['directory'], 'interventions')
                intervention_dir = os.path.join(projectdir, interv_dir)
                if (os.stat(intervention_dir)):
                    step['has_interventions'] = True
            except:
                step['has_interventions'] = False
            if step['has_interventions']:
                files = [f.replace('.json', '') for f in os.listdir(intervention_dir) if f.endswith('.json')]
                step['intervention_files'] = files
                step['intervention_directory'] = interv_dir
            step['step'] = row[10]
            step['resulting_text_directory'] =  os.path.join(row2dir(row), 'texte')
            if row[6] != 'XX' and int(row[6]) > 0:
                step['working_text_directory'] = os.path.join(row2dir(prevrow), 'texte')
            steps.append(step)
        else:
            if (row[8] == 'URGENCE'):
                procedure['type'] = 'urgence'
            else:
                if (row[8] == "constitutionnalité"):
                    step['decision'] = row[10]
                elif (row[8] == "promulgation"):
                    url_jo = row[11]
                steps.append(step)
        prevrow = row
    procedure['steps'] = steps
    procedure['beginning'] = steps[0]['date']
    procedure['end'] = row[14]
    procedure['long_title'] = re_clean_texte.sub('', row[1]).replace('règlement de règlement', 'règlement')
    if row[2]:
        procedure['short_title'] = row[2]
        if " de loi organique" in procedure['long_title']:
            procedure['short_title'] += " (texte organique)"
    else:
        procedure['short_title'] = upper_first(re_shorten_title.sub('', procedure['long_title']))
    procedure['url_dossier_senat'] = "http://www.senat.fr/dossier-legislatif/%s.html" % row[5]
    procedure['url_dossier_assemblee'] = "http://www.assemblee-nationale.fr/%s/dossiers/%s.asp" % (row[3], row[4])
    procedure['url_jo'] = url_jo

    print json.dumps(procedure, sort_keys=True, ensure_ascii=False).encode("utf-8")

