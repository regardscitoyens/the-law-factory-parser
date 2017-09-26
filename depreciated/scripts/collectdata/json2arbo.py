#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Create file arborescence corresponding to a law json output from parse_texte.py

Run with python json2arbo.py JSON_FILE PROJECT
where LAW_FILE results from perl download_loi.pl URL > LAW_FILE
Outputs results to stdout

Dependencies :
simplejson"""

import os, sys, re
try:
    import json
except:
    import simplejson as json

def mkdirs(d):
    if not os.path.exists(d):
        os.makedirs(d)

re_sec_path = re.compile(r"(\de?r?)([TCVLS])")
def sec_path(s):
    return re_sec_path.sub(r"\1/\2", s)

def write_json(j, p):
    write_text(json.dumps(j, sort_keys=True, indent=1, ensure_ascii=False), p)

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

try:
    FILE = sys.argv[1]
    f = open(FILE, "r")
except:
    sys.stderr.write("ERROR: Cannot open json file %s\n" % FILE)
    sys.exit(1)

def log_err(txt, arg=None):
    txt = "ERROR: %s" % txt
    if arg:
        txt += " %s" % arg
    txt = "%s while working on %s\n" % (txt, FILE)
    sys.stderr.write(txt)

def write_text(t, p):
    try:
        f = open(p, "w")
    except:
        log_err("Cannot write to file %s" % p)
        return
    f.write(t.encode("utf-8"))
    f.close()

try:
    project = sys.argv[2]
    mkdirs(project)
    os.chdir(project)
except:
    log_err("Cannot create dir for project %s" % project)
    sys.exit(1)

textid = ""
for l in f:
    if not l.strip():
        continue
    data = json.loads(l)
    if not data or not "type" in data:
        log_err("JSON %s badly formatted, missing field type: %s" % (f, data))
        sys.exit(1)
    if data["type"] == "texte":
        textid = data["id"]
#   textid = date_formatted+"_"+data["id"]
        write_text(clean_text(data["titre"]), textid+".titre")
        alldata = dict(data)
        alldata['sections'] = []
        alldata['articles'] = []
    elif textid == "":
        log_err("JSON missing first line with text infos")
        sys.exit(1)
    elif data["type"] == "section":
        path = sec_path(data["id"])
        mkdirs(path)
        alldata['sections'].append(data)
        write_json(data, path+"/"+textid+".json")
        write_text(clean_text(data["titre"]), path+"/"+textid+".titre")
    elif data["type"] == "article":
        path = ""
        if "section" in data:
            path = sec_path(data["section"])+"/"
        path += "A"+orderabledir(data["titre"])+"/"
        mkdirs(path)
        alldata['articles'].append(data)
        write_json(data, path+textid+".json")
        text = ""
        for i in range(len(data["alineas"])):
            if text != "":
                text += "\n"
            text += clean_text(data["alineas"]["%03d" % (i+1)])
        write_text(text, path+textid+".alineas")

f.close()
write_json(alldata, "texte.json")
