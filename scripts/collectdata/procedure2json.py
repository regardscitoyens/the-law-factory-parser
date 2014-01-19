#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Create a json from from a procedure csv one"""

import sys, os, re
import simplejson as json
import csv

csvpath = sys.argv[1]
projectdir = csvpath.replace('/procedure.csv', '')

def row2dir(row):
    return row[5]+'_'+row[7].replace(' ', '')+'_'+row[8]+'_'+row[9]

procedure = {'type': 'Normale'}
steps = []
with open(csvpath, 'rb') as csvfile:
    csvproc = csv.reader(csvfile, delimiter=';')
    for row in csvproc:
        step = {'date': row[12], 'stage': row[7], 'institution': row[8], 'source_url': row[10]}
        if (row[6] != 'EXTRA'):
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
            step['step'] = row[9]
            step['resulting_text_directory'] =  row2dir(row)+'/texte'
            if ((row[5] != 'XX') and (int(row[5]) > 0)):
                step['working_text_directory'] = row2dir(prevrow)+'/texte'
            steps.append(step)
        else:
            if (row[7] == 'URGENCE'):
                procedure['type'] = 'urgence'
            else:
                steps.append(step)
        prevrow = row
    procedure['steps'] = steps
    procedure['beginning'] = steps[0]['date']
    procedure['long_title'] = row[1];
    procedure['short_title'] = row[2];

    print json.dumps(procedure, sort_keys=True, ensure_ascii=False).encode("utf-8")

