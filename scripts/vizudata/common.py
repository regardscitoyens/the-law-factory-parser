#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
try:
    import json
except:
    import simplejson as json

def print_json(dico):
    print json.dumps(dico, ensure_ascii=False).encode('utf8')

def personalize_link(link, obj, urlapi):
    slug = obj.get('intervenant_slug', obj.get('slug', ''))
    typeparl = "senateur" if urlapi.endswith("senateurs") else "depute"
    if slug:
        return link.replace("##URLAPI##", urlapi).replace("##TYPE##", typeparl).replace("##SLUG##", slug)
    return ""

parl_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/##SLUG##", obj, urlapi)
photo_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/##TYPE##/photo/##SLUG##", obj, urlapi)
groupe_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/groupe/##SLUG##", obj, urlapi)

class Context(object):

    def __init__(self, sysargs):
        self.DEBUG = (len(sysargs) > 2)
        self.sourcedir = sysargs[1] if (len(sysargs) > 1) else ""
        if not self.sourcedir:
            sys.stderr.write('ERROR: no input directory given\n')
            exit(1)

    def get_procedure(self):
        try:
            with open(os.path.join(self.sourcedir, 'procedure', 'procedure.json'), "r") as procedure:
                return json.load(procedure)
        except:
            sys.stderr.write('ERROR: could not find procedure data in directory %s\n' % self.sourcedir)
            exit(1)

    def get_groupes(self):
        allgroupes = {}
        for f in os.listdir(os.path.join(self.sourcedir, '..')):
            if f.endswith('-groupes.json'):
                url = f.replace('-groupes.json', '')
                try:
                    with open(os.path.join(self.sourcedir, '..', f), "r") as gpes:
                        allgroupes[url] = {}
                        for gpe in json.load(gpes)['organismes']:
                            allgroupes[url][gpe["organisme"]["acronyme"]] = {
                                "nom": gpe["organisme"]['nom'],
                                "color": "rgb(%s)" % gpe["organisme"]['couleur']}
                except:
                    sys.stderr.write('WARNING: could not read groupes file %s in data\n' % f)
        return allgroupes

