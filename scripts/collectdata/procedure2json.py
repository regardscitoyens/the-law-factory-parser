#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Create a json from from a procedure csv one"""

import sys, os, re
import simplejson as json
import csv

csvpath = sys.argv[1]
projectdir = csvpath.replace('/procedure.csv', '')

def row2dir(row):
    return row[3]+'_'+row[5].replace(' ', '')+'_'+row[6]+'_'+row[7]

procedure = {'type': 'Normale'}
steps = []
with open(csvpath, 'rb') as csvfile:
    csvproc = csv.reader(csvfile, delimiter=';')
    for row in csvproc:
        step = {'date': row[10], 'stage': row[5], 'institution': row[6], 'source_url': row[8]}
        if (row[4] != 'EXTRA'):
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
            step['step'] = row[7]
            step['resulting_text_directory'] =  row2dir(row)+'/texte'
            if ((row[3] != 'XX') and (int(row[3]) > 0)):
                step['working_text_directory'] = row2dir(prevrow)+'/texte'
            steps.append(step)
        else:
            if (row[5] == 'URGENCE'):
                procedure['type'] = 'urgence'
            else:
                steps.append(step)
        prevrow = row
    procedure['steps'] = steps
    procedure['beginning'] = steps[0]['date']
    print json.dumps(procedure, sort_keys=True, ensure_ascii=False).encode("utf-8")

