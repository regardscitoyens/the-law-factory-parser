#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, time, re, requests, io
from datetime import date, datetime
from html.entities import name2codepoint
from csv import DictReader
from difflib import SequenceMatcher
import json
import locale
import contextlib

from diff_match_patch import diff_match_patch


locale.setlocale(locale.LC_TIME, 'fr_FR.utf-8')

from .sort_articles import bister

from lawfactory_utils.urls import download


@contextlib.contextmanager
def log_print(file=None, only_log=False):
    """capture all outputs to a log file while still printing it"""
    class Logger:
        def __init__(self, file):
            self.terminal = sys.stdout
            self.log = file
            self.only_log = only_log

        def write(self, message):
            if not self.only_log:
                self.terminal.write(message)
            self.log.write(message)

        def __getattr__(self, attr):
            return getattr(self.terminal, attr)

    if file is None:
        file = io.StringIO()

    logger = Logger(file)

    _stdout = sys.stdout
    _stderr = sys.stderr
    sys.stdout = logger
    sys.stderr = logger
    try:
        yield logger.log
    finally:
        sys.stdout = _stdout
        sys.stderr = _stderr


def open_csv(dirpath, filename, delimiter=";"):
    try:
        data = []
        with open(os.path.join(dirpath, filename), 'r') as f:
            for row in DictReader(f, delimiter=delimiter):
                data.append(dict([(k, v) for k, v in row.items()]))
            return data
    except Exception as e:
        print(type(e), e, file=sys.stderr)
        sys.stderr.write("ERROR: Could not open file %s in dir %s\n" % (filename, dirpath))
        raise e


def open_json(dirpath, filename=None):
    if filename:
        path = os.path.join(dirpath, filename)
    else:
        path = dirpath
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(type(e), e, file=sys.stderr)
        sys.stderr.write("ERROR: Could not open file %s" % (path,))
        raise e


def download_daily(url_or_collecter, filename, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    yesterday = time.time() - 86400
    destfile = os.path.join(output_directory, filename + ".json")
    if not os.path.exists(destfile) or os.path.getmtime(destfile) < yesterday:
        print('downloading', filename)
        if isinstance(url_or_collecter, str):
            jsondata = download(url_or_collecter).json()
        else:
            jsondata = url_or_collecter()
        print_json(jsondata, destfile)
    else:
        jsondata = open_json(destfile)
    return jsondata


def print_json(dico, filename=None):
    jdump = json.dumps(dico, ensure_ascii=False, sort_keys=True, indent=2)
    if filename:
        # create parent directories if necessary
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        try:
            with open("%s.tmp" % filename, 'w') as f:
                f.write(jdump)
            if os.path.exists(filename):
                os.remove(filename)
            os.rename("%s.tmp" % filename, filename)
        except Exception as e:
            print(type(e), e, file=sys.stderr)
            sys.stderr.write("ERROR: Could not write in file %s" % filename)
            raise e
    else:
        print(jdump)


def debug_file(data, filename):
    if '--debug' in sys.argv:
        path = os.path.join('debug', filename)
        print_json(data, path)
        print('   DEBUG - dumped', path)


datize = lambda d: date(*tuple([int(a) for a in d.split('-')]))
def format_date(d):
    da = d.split('/')
    da.reverse()
    return "-".join(da)

def format_display_date(d):
    return datetime.strftime(datize(d), '%A %d %B %Y').replace(' 0', ' ')

upper_first = lambda t: t[0].upper() + t[1:] if len(t) > 1 else t.upper()

re_entities = re.compile(r'&([^;]+)(;|$)')
decode_char = lambda x: chr(int(x.group(1)[1:]) if x.group(1).startswith('#') else name2codepoint[x.group(1)])
decode_html = lambda text: re_entities.sub(decode_char, text)

re_clean_spaces = re.compile(r"[\s\n]+")
clean_spaces = lambda x: re_clean_spaces.sub(" ", x)

re_clean_balises = re.compile(r"<\/?[!a-z][^>]*>", re.I)
clean_balises = lambda x: re_clean_balises.sub("", x)

clean_statuses = lambda x: re_alin_sup.sub("", x)

strip_text = lambda x: clean_spaces(clean_statuses(clean_balises(x))).strip()

re_non_alphanum = re.compile(r"[^a-z0-9]+")

upcase_accents = "ÇÀÂÄÉÈÊËÎÏÔÖÙÛÜ"
locase_accents = "çàâäéèêëîïôöùûü"
case_noaccents = "caaaeeeeiioouuu"

def real_lower(text):
    for a in upcase_accents:
        text = text.replace(a, locase_accents[upcase_accents.find(a)])
    return text.lower()

def clean_accents(text):
    text = real_lower(text)
    for a in locase_accents:
        text = text.replace(a, case_noaccents[locase_accents.find(a)])
    return text

re_clean_alin = re.compile(r'^"?(([IVXCDLM]+|\d+|[a-z])[°)\-\.\s]+)+\s*((%s|[A-Z%s]+)[°)\-\.\s]+)*' % (bister, upcase_accents))
re_alin_sup = re.compile(r'\s*\((censur|supprim)és?\)$', re.I)

def clean_text_for_diff(text):
    if type(text) == list:
        text = [clean_statuses(re_clean_alin.sub('', t)) for t in text]
        text = "\n".join([t for t in text if t])
    else:
        text = clean_statuses(re_clean_alin.sub('', text))
    text = clean_balises(text)
    text = clean_accents(text)
    text = re_non_alphanum.sub('', text)
    return text

def compute_approx_similarity(text1, text2):
    a = SequenceMatcher(None, text1, text2, autojunk=False)
    return 1 - a.real_quick_ratio()

def compute_similarity(text1, text2):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    diff = dmp.diff_main(text1, text2)

    # similarity
    common_text = sum([len(txt) for op, txt in diff if op == 0])
    text_length = max(len(text1), len(text2))
    sim = common_text / text_length
    return sim

def compute_similarity_by_articles(text1, text2):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    arts = set(text1.keys()) | set (text2.keys())
    common_text = 0
    text_length = 0
    for a in arts:
        if a in text1 and a in text2:
            diff = dmp.diff_main(text1[a], text2[a])
            common_text += sum([len(txt) for op, txt in diff if op == 0])
            text_length += max(len(text1[a]), len(text2[a]))
        elif a in text1:
            text_length += len(text1[a])
        else:
            text_length += len(text2[a])
    sim = common_text / text_length
    return sim


def identify_room(url_or_institution, legislature):
    typeparl = "depute" if 'nationale.fr' in url_or_institution \
        or url_or_institution == 'assemblee' else "senateur"
    if typeparl == 'depute':
        year = 1942 + 5*legislature
        legis = '%s-%s' % (year, year+5)
    else:
        legis = 'www'
    urlapi = "%s.nos%ss" % (legis, typeparl)
    return typeparl, urlapi


def national_assembly_text_legislature(url_text):
    return int(url_text.split('.fr/')[1].split('/')[0])


def personalize_link(link, obj, urlapi):
    if isinstance(obj, dict):
        slug = obj.get('intervenant_slug', obj.get('slug', ''))
    else: slug = obj
    typeparl = "senateur" if urlapi.endswith("senateurs") else "depute"
    if slug:
        return link.replace("##URLAPI##", urlapi).replace("##TYPE##", typeparl).replace("##SLUG##", slug)
    return ""

parl_link = lambda obj, urlapi: personalize_link("https://##URLAPI##.fr/##SLUG##", obj, urlapi)
photo_link = lambda obj, urlapi: personalize_link("https://##URLAPI##.fr/##TYPE##/photo/##SLUG##", obj, urlapi)
groupe_link = lambda obj, urlapi: personalize_link("https://##URLAPI##.fr/groupe/##SLUG##", obj, urlapi)
amdapi_link = lambda urlapi: personalize_link("https://##URLAPI##.fr/api/document/Amendement/", {'slug': 'na'}, urlapi)

def slug_groupe(g):
    # on the senat side, some senators have obsolete groups
    g = g.upper()
    g = g.replace("SOCV", "SOC")
    g = g.replace("CRC-SPG", "CRC")
    g = g.replace("ECOLO", "ECO")
    g = g.replace("ECO", "ECOLO")
    return g


class Context(object):

    def __init__(self, sourcedir, load_parls=False):
        self.sourcedir = sourcedir
        if not self.sourcedir:
            sys.stderr.write('ERROR: no input directory given\n')
            exit(1)
        self.allgroupes = {}
        self.get_groupes()
        self.get_historique_groupes_senat()
        self.parlementaires = {}
        if load_parls:
            self.get_parlementaires()

    def get_procedure(self):
        try:
            with open(os.path.join(self.sourcedir, 'viz', 'procedure.json'), "r") as procedure:
                return json.load(procedure)
        except Exception as e:
            sys.stderr.write('ERROR: could not find procedure data in directory %s\n' % self.sourcedir)
            raise e

    def get_parlementaires(self):
        for f in os.listdir(os.path.join(self.sourcedir, '..')):
            if f.endswith('.parlementaires.json'):
                url = f.replace('.parlementaires.json', '').lower()
                try:
                    with open(os.path.join(self.sourcedir, '..', f), "r") as parls:
                        self.parlementaires[url] = {}
                        typeparl = "depute" if "depute" in url else "senateur"
                        for parl in json.load(parls)[typeparl+"s"]:
                            p = parl[typeparl]
                            self.parlementaires[url][p["slug"]] = p
                except Exception as e:
                    sys.stderr.write('WARNING: could not read parlementaires file %s in data\n' % f)
                    sys.stderr.write('%s: %s\n' % (type(e), e))

    def get_parlementaire(self, urlapi, slug):
        try:
            return self.parlementaires[urlapi][slug]
        except:
            typeparl = "depute" if "deputes" in urlapi else "senateur"
            if urlapi not in self.parlementaires:
                self.parlementaires[urlapi] = {}
            self.parlementaires[urlapi][slug] = requests.get(parl_link(slug, urlapi)+"/json").json()[typeparl]
            return self.parlementaires[urlapi][slug]

    def get_groupes(self):
        for f in os.listdir(os.path.join(self.sourcedir, '..')):
            if f.endswith('-groupes.json'):
                url = f.replace('-groupes.json', '').lower()
                try:
                    with open(os.path.join(self.sourcedir, '..', f), "r") as gpes:
                        self.allgroupes[url] = {}
                        for gpe in json.load(gpes)['organismes']:
                            if not gpe["organisme"]["acronyme"]:
                                continue
                            acro = slug_groupe(gpe["organisme"]["acronyme"])
                            self.allgroupes[url][acro] = {
                                "nom": gpe["organisme"]['nom'],
                                "order": int(gpe["organisme"]['order']),
                                "color": "rgb(%s)" % gpe["organisme"]['couleur']}
                except Exception as e:
                    sys.stderr.write('WARNING: could not read groupes file %s in data\n' % f)
                    sys.stderr.write('%s: %s\n' % (type(e), e))

    def get_historique_groupes_senat(self):
        senateurs = {}
        gfile = os.path.join(self.sourcedir, '..', 'historique-groupes-senat.json')
        for row in open_json(gfile)["results"]:
            sid = row['Matricule'].lower()
            if sid not in senateurs:
                senateurs[sid] = []
            st = row.get('Date_de_debut_de_la_fonction') or row.get('Date_de_debut_d_appartenance') or '0000-00-00'
            ed = row.get('Date_de_fin_de_la_fonction') or row.get('Date_de_fin_d_appartenance') or '9999-99-99'
            senateurs[sid].append({
                'debut': st[:10].replace('/', '-'),
                'fin': ed[:10].replace('/', '-'),
                'groupe': slug_groupe(row['Code_du_groupe_politique'])
            })
        for sid in senateurs:
            senateurs[sid] = sorted(senateurs[sid], key=lambda x: (x['debut'], x['fin']))
        self.groupes_senateurs = senateurs

    def get_senateur_groupe(self, slug, object_date, urlapi):
        senator = self.get_parlementaire(urlapi, slug)
        senid = senator["id_institution"][-6:].lower()
        if senid not in self.groupes_senateurs:
            print('WARNING - cannot find %s in OpenData Sénat' % slug)
        else:
            for period in self.groupes_senateurs[senid]:
                if period["debut"] <= object_date <= period["fin"]:
                    return period["groupe"]
            print('WARNING - cannot find groupe of %s in OpenData Sénat for date %s' % (slug, object_date))
            for period in self.groupes_senateurs[senid]:
                print(' > ', period['debut'], period['fin'], period['groupe'])
        return None

    def add_groupe(self, groupes, gpe, urlapi):
        gpid = upper_first(gpe.lower())
        acro = slug_groupe(gpid)
        if acro in self.allgroupes[urlapi]:
            gpid = acro
        if gpid not in groupes:
            groupes[gpid] = {'nom': upper_first(gpe),
                             'link': ''}
            if gpid in self.allgroupes[urlapi]:
                groupes[gpid]['nom'] = self.allgroupes[urlapi][gpid]['nom']
                groupes[gpid]['order'] = 10 + self.allgroupes[urlapi][gpid]['order']
                groupes[gpid]['color'] = self.allgroupes[urlapi][gpid]['color']
                groupes[gpid]['link'] = groupe_link({'slug': gpid}, urlapi)
            elif gpid == "Présidence":
                groupes[gpid]['color'] = "#bfbbcc"
                groupes[gpid]['order'] = 0
            elif gpid == "Rapporteurs":
                groupes[gpid]['color'] = "#b9ccc0"
                groupes[gpid]['order'] = 50
            elif gpid == "Gouvernement":
                groupes[gpid]['color'] = "#cccbb3"
                groupes[gpid]['order'] = 60
            elif gpid == "Auditionnés":
                groupes[gpid]['color'] = "#ccb7b6"
                groupes[gpid]['order'] = 70
            else:
                groupes[gpid]['color'] = "#bfbfbf"
                groupes[gpid]['order'] = 100
        return gpid


def get_text_id(texte_url):
    if "nationale.fr" in texte_url:
        textid_match = re.search(r'fr\/(\d+)\/.*[^0-9]0*([1-9][0-9]*)(-a\d)?\.asp$', texte_url, re.I)
        nosdeputes_id = textid_match.group(2)
        if '/ta/ta' in texte_url:
            nosdeputes_id = 'TA' + nosdeputes_id
        return nosdeputes_id
    elif "senat.fr" in texte_url:
        textid_match = re.search(r"(\d{2})-(\d+)(/|rec|(_mono)?\.html$)", texte_url, re.I)
        return '20%s20%s-%s' % (textid_match.group(1).zfill(2),
            str(int(textid_match.group(1))+1).zfill(2),
            textid_match.group(2))
