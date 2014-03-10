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

procedure = {'type': 'Normale'}
steps = []
with open(csvpath, 'rb') as csvfile:
    csvproc = csv.reader(csvfile, delimiter=';')
    for row in csvproc:
        if len(row) < 15:
            row.append("")
        step = {'date': row[13], 'enddate': row[14], 'stage': row[8], 'institution': row[9], 'source_url': row[11]}
        if (row[7] != 'EXTRA'):
            step['directory'] = row2dir(row)
            try:
                if (os.stat(projectdir+'/'+step['directory']+'/amendements/amendements.csv')):
                    step['has_amendements'] = True
                    step['amendement_directory'] = step['directory']+'/amendements'
            except:
                step['has_amendements'] = False
            try:
                intervention_dir = projectdir+'/'+step['directory']+'/interventions/'
                if (os.stat(intervention_dir)):
                    step['has_interventions'] = True
            except:
                step['has_interventions'] = False
            if (step['has_interventions']):
                files = []
                for f in os.listdir(intervention_dir):
                    if re.search('.json$', f):
                        files.append(f.replace('.json', ''))
                step['intervention_files'] = files
                step['intervention_directory'] = step['directory']+'/interventions'
            step['step'] = row[10]
            step['resulting_text_directory'] =  row2dir(row)+'/texte'
            if ((row[6] != 'XX') and (int(row[6]) > 0)):
                step['working_text_directory'] = row2dir(prevrow)+'/texte'
            steps.append(step)
        else:
            if (row[8] == 'URGENCE'):
                procedure['type'] = 'urgence'
            else:
                steps.append(step)
        prevrow = row
    procedure['steps'] = steps
    procedure['beginning'] = steps[0]['date']
    procedure['end'] = row[14]
    procedure['long_title'] = row[1]
    procedure['short_title'] = row[2]
    procedure['url_dossier_senat'] = "http://www.senat.fr/dossier-legislatif/%s.html" % row[5]
    procedure['url_dossier_assemblee'] = "http://www.assemblee-nationale.fr/%s/dossiers/%s.asp" % (row[3], row[4])

    print json.dumps(procedure, sort_keys=True, ensure_ascii=False).encode("utf-8")

