#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
try:
    import json
except:
    import simplejson as json

def print_json(dico):
    print json.dumps(dico, ensure_ascii=False).encode('utf8')

upper_first = lambda t: t[0].upper() + t[1:]

def identify_room(data, datatype):
    typeparl = "depute" if 'url_nosdeputes' in data[0][datatype] else "senateur"
    legis = data[0][datatype]['url_nos%ss' % typeparl]
    legis = legis[7:legis.find('.')]
    urlapi = "%s.nos%ss" % (legis, typeparl)
    return typeparl, urlapi.lower()

def personalize_link(link, obj, urlapi):
    slug = obj.get('intervenant_slug', obj.get('slug', ''))
    if not slug and 'amendement' in obj:
        slug = obj['amendement']['id']
    typeparl = "senateur" if urlapi.endswith("senateurs") else "depute"
    if slug:
        return link.replace("##URLAPI##", urlapi).replace("##TYPE##", typeparl).replace("##SLUG##", slug)
    return ""

parl_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/##SLUG##", obj, urlapi)
photo_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/##TYPE##/photo/##SLUG##", obj, urlapi)
groupe_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/groupe/##SLUG##", obj, urlapi)
amdapi_link = lambda obj, urlapi: personalize_link("http://##URLAPI##.fr/api/document/Amendement/##SLUG##/json", obj, urlapi)

class Context(object):

    def __init__(self, sysargs):
        self.DEBUG = (len(sysargs) > 2)
        self.sourcedir = sysargs[1] if (len(sysargs) > 1) else ""
        if not self.sourcedir:
            sys.stderr.write('ERROR: no input directory given\n')
            exit(1)
        self.allgroupes = {}
        self.get_groupes()

    def get_procedure(self):
        try:
            with open(os.path.join(self.sourcedir, 'procedure', 'procedure.json'), "r") as procedure:
                return json.load(procedure)
        except:
            sys.stderr.write('ERROR: could not find procedure data in directory %s\n' % self.sourcedir)
            exit(1)

    def get_groupes(self):
        for f in os.listdir(os.path.join(self.sourcedir, '..')):
            if f.endswith('-groupes.json'):
                url = f.replace('-groupes.json', '').lower()
                try:
                    with open(os.path.join(self.sourcedir, '..', f), "r") as gpes:
                        self.allgroupes[url] = {}
                        for gpe in json.load(gpes)['organismes']:
                            self.allgroupes[url][gpe["organisme"]["acronyme"].upper()] = {
                                "nom": gpe["organisme"]['nom'],
                                "color": "rgb(%s)" % gpe["organisme"]['couleur']}
                except:
                    sys.stderr.write('WARNING: could not read groupes file %s in data\n' % f)

    def add_groupe(self, groupes, gpe, urlapi):
        gpid = gpe.lower()
        if gpe.upper() in self.allgroupes[urlapi]:
            gpid = gpe.upper()
        if gpid not in groupes:
            groupes[gpid] = {'nom': upper_first(gpe),
                             'color': '#888888',
                             'link': ''}
            if gpid in self.allgroupes[urlapi]:
                groupes[gpid]['nom'] = self.allgroupes[urlapi][gpid]['nom']
                groupes[gpid]['color'] = self.allgroupes[urlapi][gpid]['color']
                groupes[gpid]['link'] = groupe_link({'slug': gpid}, urlapi)
        return gpid

