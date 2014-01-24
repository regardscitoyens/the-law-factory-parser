#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, re
import simplejson as json

FILE = sys.argv[1]
DEBUG = True if len(sys.argv) > 3 else False
def log(text):
    if DEBUG:
        print >> sys.stderr, text

try:
    f = open(FILE, "r")
except:
    log("ERROR: Cannot open json file %s" % FILE)
    sys.exit()

try:
    oldstep = {}
    oldjson =  []
    oldstatus = {}
    oldarts = []
    oldartids = []
    with open(sys.argv[2], 'r') as f2:
        for l in f2:
            if not l.strip():
                continue
            line = json.loads(l)
            if not line or not "type" in line:
                log("JSON %s badly formatted, missing field type: %s" % (source, line))
                sys.exit()
            if line["type"] != "texte":
                oldjson.append(line)
            if line["type"] == "article":
                keys = line['alineas'].keys()
                keys.sort()
                alineas = [line['alineas'][k] for k in keys]
                oldstep[line["titre"]] = [line['alineas'][k] for k in keys]
                oldstatus[line["titre"]] = line['statut']
                oldartids.append(line["titre"])
                oldarts.append((line["titre"], line))


except Exception as e:
    print type(e), e
    log("No previous step found at %s" % sys.argv[2])
    sys.exit()

def write_json(data):
    print json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")

def get_mark_from_last(text, start, last=""):
    log("- GET Extract from " + start + " to " + last)
    res = []
    start = re.compile(r'^%s([\)\.°\-\s]+)' % start)
    if last:
        last = re.compile(r'^%s([\)\.°\-\s]+)' % last)
    re_end = None
    record = False
    for i in text:
        sep = start.match(i)
        log("   TEST: " + i[:15])
        if re_end and re_end.match(i):
            log("  --> END FOUND")
            if last:
                re_end = re.compile(r'^[IVX0-9]{1,4}%s' % sep)
                last = ""
            else:
                record = False
                break
        elif sep:
            sep = sep.group(1)
            log("  --> START FOUND " + sep)
            record = True
            if last:
                re_end = last
            else:
                re_end = re.compile(r'^[IVX0-9]{1,4}%s' % sep)
        if record:
            log("    copy alinea")
            res.append(i)
    return res

order = 1
done_titre = False
for l in f:
    if not l.strip():
        continue
    line = json.loads(l)
    if not line or not "type" in line:
        sys.stderr.write("JSON %s badly formatted, missing field type: %s" % (FILE, line))
        sys.exit()
    if line["type"] == "echec":
        texte["echec"] = True
        texte["expose"] = line["texte"]
        write_json(texte)
        for a in oldjson:
            write_json(a)
        break
    elif line["type"] == "texte":
        texte = dict(line)
    else:
      if not done_titre:
        write_json(texte)
        done_titre = True
      if line["type"] != "article":
        write_json(line)
      else:
        mult = line['titre'].split(u' à ')
        if len(mult) > 1:
            line['titre'] = mult[0].strip()
        if line['titre'] in oldartids:
            cur = ""
            while cur != line['titre'] and oldarts:
                cur, a = oldarts.pop(0)
                if a["statut"].startswith("conforme"):
                    log("DEBUG: Recovering art conforme %s\n" % cur)
                    a["order"] = order
                    order += 1
                    write_json(a)
        if len(mult) > 1:
            cur = ""
            end = mult[1].strip
            run = True
            while run and oldarts:
                cur, a = oldarts.pop(0)
                a["statut"] = "conforme"
                log("DEBUG: Recovering art conforme %s\n" % cur)
                a["order"] = order
                order += 1
                write_json(a)
                if cur == end:
                    run = False
            continue
        if line["statut"].startswith("suppr") and (line['titre'] not in oldstatus or oldstatus[line['titre']].startswith("suppr")):
           continue
        keys = line['alineas'].keys()
        keys.sort()
        alineas = [line['alineas'][k] for k in keys]
        if len(alineas) == 1:
            text = alineas[0].encode('utf-8')
        # Clean empty articles with only "Non modifié" and include text from previous step
            if text.startswith("(Non modifié)"):
                if not line['titre'] in oldstep:
                    sys.stderr.write("WARNING: found repeated article %s missing from previous step %s: %s\n" % (line['titre'], FILE, line['alineas']))
                else:
                    log("DEBUG: get back Art %s" % line['titre'])
                    alineas.pop(0)
                    alineas.extend(oldstep[line['titre']])
        gd_text = []
        for j, text in enumerate(alineas):
            text = text.encode('utf-8')
            if "(non modifié" in text and not line['titre'] in oldstep:
                sys.stderr.write("WARNING: found repeated article missing %s from previous step %s: %s\n" % (line['titre'], FILE, line['alineas']))
            elif "(non modifié" in text:
                part = re.split("\s*([\)\.°\-]+\s*)+", text)
                if not part:
                    log("ERROR trying to get non-modifiés")
                    exit(1)
                todo = part[0]
                log("EXTRACT non-modifiés: " + todo)
    # Extract series of non-modified subsections of articles from previous version.
                if " à " in todo:
                    start = re.split(" à ", todo)[0]
                    end = re.split(" à ", todo)[1]
                    piece = get_mark_from_last(oldstep[line['titre']], start, end)
    # Extract set of non-modified subsections of articles from previous version.
                elif "," in todo or " et " in todo or " & " in todo:
                    piece = []
                    for i, mark in enumerate(re.split("(?:\s*(,|&|et)\s*)", todo)):
                        if i % 2 == 1:
                            continue
                        piece.extend(get_mark_from_last(oldstep[line['titre']], mark))
    # Extract single non-modified subsection of articles from previous version.
                else:
                    piece = get_mark_from_last(oldstep[line['titre']], todo)
                gd_text.extend(piece)
            else:
                gd_text.append(text.decode('utf-8'))
        line['alineas'] = dict()
        line['order'] = order
        order += 1
        for i, t in enumerate(gd_text):
            line['alineas']["%03d" % (i+1)] = t
        write_json(line)

f.close()

