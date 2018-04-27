#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Create file arborescence corresponding to a law json output from parse_texte.py

Run with python json2arbo.py JSON_FILE PROJECT
where LAW_FILE results from perl download_loi.pl URL > LAW_FILE
Outputs results to stdout"""

import os, sys, re
try:
    from .common import print_json
except:
    from common import print_json

def mkdirs(d):
    if not os.path.exists(d):
        os.makedirs(d)

re_sec_path = re.compile(r"(\de?r?)([TCVLS])")
def sec_path(s):
    return re_sec_path.sub(r"\1/\2", s)

def orderabledir(titre):
    extrazero = ''
    try:
        titre2num = int(re.compile(r"\D.*$").sub('', titre))
        if (titre2num < 10):
            extrazero = '00'
        elif (titre2num < 100):
            extrazero = '0'
    except:
        pass
    return extrazero+re_cl_ids.sub('_', titre)

re_cl_ids = re.compile(r"\s+")

replace_str = [
#  (re.compile(r'"'), ""),
#  (re.compile(r"^[IVXLCDM]+[\.\s-]+"), ""),
#  (re.compile(r"^([0-9]+|[a-z])[°)\s]+"), ""),
    (re.compile(r"\s+"), " ")
]
def clean_text(t):
    for regex, repl in replace_str:
        t = regex.sub(repl, t.strip())
#  return t
    return t.strip()


def get_step_id(nstep, step):
    clean = lambda x: x.replace(' ', '').replace('è','e').lower() if x else ''
    return '%s_%s_%s_%s' % (
        str(nstep).zfill(2),
        clean(step.get('stage')),
        clean(step.get('institution')),
        clean(step.get('step')),
    )


def process(dos, OUTPUT_DIR):
    def log_err(txt, arg=None):
        raise Exception()

    for step_i, step in enumerate(dos['steps']):

        step['directory'] = get_step_id(step_i, step)
        step_dir = os.path.join(OUTPUT_DIR, os.path.join(step['directory'], 'texte'))

        articles = step.get('articles_completed', step.get('articles'))
        if not articles:
            # print('no articles for step')
            continue

        mkdirs(step_dir)
        for data in articles:
            if not data or not "type" in data:
                log_err("JSON badly formatted, missing field type: %s" % data)
                sys.exit(1)
            if data["type"] == "texte":
                textid = data["id"]
                alldata = dict(data)
                alldata['sections'] = []
                alldata['articles'] = []
            elif textid == "":
                log_err("JSON missing first line with text infos")
                sys.exit(1)
            elif data["type"] == "section":
                path = step_dir + '/' + sec_path(data["id"])
                alldata['sections'].append(data)
            elif data["type"] == "article":
                path = step_dir + '/'
                if "section" in data:
                    path += sec_path(data["section"])+"/"
                path += "A"+orderabledir(data["titre"])+"/"
                alldata['articles'].append(data)
                text = ""
                for i in range(len(data["alineas"])):
                    if text != "":
                        text += "\n"
                    text += clean_text(data["alineas"]["%03d" % (i+1)])
            elif data["type"] == "echec":
                alldata['expose'] = data['texte']

        print_json(alldata, os.path.join(step_dir, 'texte.json'))

        step['texte.json'] = alldata

    return dos
