#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Create file arborescence corresponding to a law json output from parse_texte.py

Run with python json2arbo.py JSON_FILE PROJECT
where LAW_FILE results from perl download_loi.pl URL > LAW_FILE
Outputs results to stdout"""

import os, sys, re
import urllib.parse

from .common import print_json, open_json


def mkdirs(d):
    if not os.path.exists(d):
        os.makedirs(d)


def get_step_id(nstep, step):
    clean = lambda x: x.replace(' ', '').replace('è','e').lower() if x else ''
    return '%s_%s_%s_%s' % (
        str(nstep).zfill(2),
        clean(step.get('stage')),
        clean(step.get('institution')),
        clean(step.get('step')),
    )


def process(dos, OUTPUT_DIR):
    def log_err(txt):
        raise Exception(txt)

    for step_i, step in enumerate(dos['steps']):

        step['directory'] = get_step_id(step_i, step)
        step_dir = os.path.join(OUTPUT_DIR, os.path.join(step['directory'], 'texte'))

        articles = step.get('articles_completed', step.get('articles'))
        if not articles:
            continue

        mkdirs(step_dir)
        textid = None
        for data in articles:
            if not data or not "type" in data:
                log_err("JSON badly formatted, missing field type: %s" % data)
            if data["type"] == "texte":
                textid = data["id"]
                alldata = dict(data)
                alldata['sections'] = []
                alldata['articles'] = []
            elif not textid:
                log_err("JSON missing first line with text infos for step %s" % step_dir)
            elif data["type"] == "section":
                alldata['sections'].append(data)
            elif data["type"] == "article":
                alldata['articles'].append(data)
            elif data["type"] == "echec":
                alldata['expose'] = data['texte']


        print_json(alldata, os.path.join(step_dir, 'texte.json'))

        step['texte.json'] = alldata

    return dos


if __name__ == '__main__':
    print_json(process(open_json(sys.argv[1]), 'test_out'))
