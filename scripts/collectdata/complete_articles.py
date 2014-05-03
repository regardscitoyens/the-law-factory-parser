#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, re
import simplejson as json
from sort_articles import bister, article_is_lower

FILE = sys.argv[1]
DEBUG = True if len(sys.argv) > 4 else False
def log(text):
    if DEBUG:
        print >> sys.stderr, text

try:
    f = open(FILE, "r")
except:
    log("ERROR: Cannot open json file %s" % FILE)
    sys.exit(1)

def exit():
    f.close()
    sys.exit(1)

find_num = re.compile(r'-[a-z]*(\d+)\D?$')
oldnum = 0
oldstep = [{}, {}]
oldjson =  []
oldstatus = {}
oldartids = []
oldarts = []
oldsects = []
try:
    with open(sys.argv[2], 'r') as f2:
        for l in f2:
            if not l.strip():
                continue
            line = json.loads(l)
            if not line or not "type" in line:
                log("JSON %s badly formatted, missing field type: %s" % (source, line))
                exit()
            if line["type"] != "texte":
                oldjson.append(line)
            else:
                oldnum = int(find_num.search(line['id']).group(1))
            if line["type"] == "article":
                keys = line['alineas'].keys()
                keys.sort()
                oldstep[0][line["titre"]] = [line['alineas'][k] for k in keys]
                oldstatus[line["titre"]] = line['statut']
                oldartids.append(line["titre"])
                oldarts.append((line["titre"], line))
            elif line["type"] == "section":
                oldsects.append(line)
except Exception as e:
    print >> sys.stderr, type(e), e
    log("No previous step found at %s" % sys.argv[2])
    exit()

grdoldarts = {}
if "%2Fta" in FILE and len(sys.argv) > 3 and sys.argv[3]:
  try:
    with open(sys.argv[3], 'r') as f3:
        for l in f3:
            if not l.strip():
                continue
            line = json.loads(l)
            if not line or not "type" in line:
                log("JSON %s badly formatted, missing field type: %s" % (source, line))
                exit()
            if line["type"] == "article":
                keys = line['alineas'].keys()
                keys.sort()
                oldstep[1][line["titre"]] = [line['alineas'][k] for k in keys]
                grdoldarts[line["titre"]] = line
  except Exception as e:
    print >> sys.stderr, type(e), e
    log("No grand previous step found at %s" % sys.argv[2])
    exit()

def write_json(data):
    print json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")

make_sta_reg = lambda x: re.compile(r'^"?(?:Art[\s\.]*)?%s\s*(([\.°\-]+\s*)+)' % x)
make_end_reg = lambda x: re.compile(r'^"?([LA][LArRtTO\.\s]+)?[IVX0-9\-]{1,6}([\-\.]+\d+)*(\s*%s)?%s' % (bister, x))
re_sect_chg = re.compile(r'^"?((chap|t)itre|volume|livre|tome|(sous-)?section)\s+[1-9IVX]', re.I)
def get_mark_from_last(text, start, last=""):
    log("- GET Extract from " + start + " to " + last)
    res = []
    try:
        start = make_sta_reg(start)
    except:
        print >> sys.stderr, 'ERROR', start.encode('utf-8'), text.encode('utf-8'), last.encode('utf-8')
        exit()
    if last:
        last = make_sta_reg(last)
    re_end = None
    record = False
    for i in text:
        matc = start.match(i)
        log("    TEST: " + i[:50])
        if re_end and (re_end.match(i) or re_sect_chg.match(i)):
            if last:
                re_end = make_end_reg(sep)
                last = ""
            else:
                log("  --> END FOUND")
                record = False
                break
        elif matc:
            sep = matc.group(1).strip()
            log("  --> START FOUND " + sep)
            record = True
            if last:
                re_end = last
            else:
                re_end = make_end_reg(sep)
        if record:
            log("     copy alinea")
            res.append(i)
    return res

re_alin_sup = re.compile(ur'supprimés?\)$', re.I)
re_clean_alin = re.compile(r'^"?[IVXCDLMa-z\d]+[°)-\.\s]*(\s(%s|[A-Z]+)[°)-\.\s]+)*' % bister)
re_clean_virg = re.compile(r'\s*,\s*')
re_suppr = re.compile(r'\W*suppr(ess|im)', re.I)
re_confo = re.compile(r'\W*(conforme|non[\s\-]*modifi)', re.I)
re_confo_with_txt = re.compile(r'\s*\(\s*(conforme|non[\s\-]*modifié)\s*\)\s*([\W]*\w+)', re.I)
order = 1
cursec = {'id': ''}
done_titre = False
for l in f:
    if not l.strip():
        continue
    line = json.loads(l)
    if not line or not "type" in line:
        sys.stderr.write("JSON %s badly formatted, missing field type: %s\n" % (FILE, line))
        exit()
    if oldnum and 'source_text' in line and oldnum != line['source_text']:
        continue
    if line["type"] == "echec":
        texte["echec"] = True
        texte["expose"] = line["texte"]
        write_json(texte)
        for a in oldjson:
            write_json(a)
        break
    elif line["type"] == "texte":
        texte = dict(line)
        if texte["definitif"]:
            from difflib import ndiff, SequenceMatcher
    else:
      if not done_titre:
        write_json(texte)
        done_titre = True
      if line["type"] != "article":
        if texte['definitif']:
            try:
                cursec = oldsects.pop(0)
                assert(cursec["type_section"] == line["type_section"])
            except:
                print >> sys.stderr, "ERROR: Problem while renumbering sections", line, "\n", cursec
                exit()
            if line["id"] != cursec["id"]:
                line["newid"] = line["id"]
                line["id"] = cursec["id"]
        write_json(line)
      else:
        keys = line['alineas'].keys()
        keys.sort()
        alineas = [line['alineas'][k] for k in keys]
        mult = line['titre'].split(u' à ')
        is_mult = (len(mult) > 1)
        oldid = 1 if grdoldarts and ("conforme" in line['statut'].lower() or (alineas and "conforme" in alineas[0].lower())) else 0
        if is_mult:
            st = mult[0].strip()
            ed = mult[1].strip()
            if re_suppr.match(line['statut']) or (len(alineas) == 1 and re_suppr.match(alineas[0])):
                if (st not in oldartids and ed not in oldartids) or (st in oldstatus and re_suppr.match(oldstatus[st]) and ed in oldstatus and re_suppr.match(oldstatus[ed])):
                    log("DEBUG: SKIP already deleted articles %s to %s" % (st.encode('utf-8'), ed.encode('utf-8')))
                    continue
                log("DEBUG: Marking as deleted articles %s à %s" % (st.encode('utf-8'), ed.encode('utf-8')))
                mult_type = "sup"
            elif re_confo.match(line['statut']) or (len(alineas) == 1 and re_confo.match(alineas[0])):
                log("DEBUG: Recovering art conformes %s à %s" % (st.encode('utf-8'), ed.encode('utf-8')))
                mult_type = "conf"
            else:
                print >> sys.stderr, "ERROR: Found multiple article which I don't knwo what to do with", line['titre'].encode('utf-8'), line
                exit()
            line['titre'] = st
        cur = ""
        if texte['definitif']:
            try:
                goon = True
                while goon:
                    _, oldart = oldarts[0]
                    if re_suppr.match(oldart['statut']):
                        c, _ = oldarts.pop(0)
                        oldartids.remove(c)
                    else:
                        goon = False
            except:
                print >> sys.stderr, "ERROR: Problem while renumbering articles", line, "\n", oldart
                exit()
            oldtxt = [re_clean_alin.sub('', v) for v in oldart["alineas"].values() if not re_alin_sup.search(v)]
            txt = [re_clean_alin.sub('', v) for v in line["alineas"].values()]
            compare = list(ndiff(txt, oldtxt))
            mods = {'+': 0, '-': 0 ,'?': 0, ' ': 0}
            for l in compare:
                mod = l[0]
                if mod == '?':
                    mods[mod] += l.count('^')
                    mods[mod] += l.count('-')
                    mods[mod] += l.count('+')
                else:
                    mods[mod] += 1
            if mods['+'] or mods['-']:
                mods['?'] = mods['?'] / (mods['+'] + mods['-'])
            diff = float(mods['?'])/max(len("".join(txt)), len("".join(oldtxt)))
            if diff > 0.15:
                print >> sys.stderr, "WARNING BIG DIFFERENCE BETWEEN RENUMBERED ARTICLE", oldart["titre"], line["titre"], mods['?'], len("".join(txt)), diff
                log("------------------")
                log("\n".join(compare))
                log("------------------")
            if line['titre'] != oldart['titre']:
                line['newtitre'] = line['titre']
                line['titre'] = oldart['titre']
            if "section" in line and cursec['id'] != line["section"]:
                line["section"] = cursec["id"]
        if oldarts:
            while oldarts:
                cur, a = oldarts.pop(0)
                if line['titre'] in oldartids or article_is_lower(cur, line['titre']):
                    oldartids.remove(cur)
                else:
                    oldarts.insert(0, (cur, a))
                    break
                if cur == line['titre']:
                    break
                #print >> sys.stderr, cur, line['titre'], a["statut"]
                if a["statut"].startswith("conforme"):
                    log("DEBUG: Recovering art conforme %s" % cur.encode('utf-8'))
                    a["statut"] = "conforme"
                    a["order"] = order
                    order += 1
                    write_json(a)
                elif not re_suppr.match(a["statut"]):
                    log("DEBUG: Marking art %s as supprimé" % cur.encode('utf-8'))
                    a["statut"] = "supprimé"
                    a["alineas"] = dict()
                    a["order"] = order
                    order += 1
                    write_json(a)
        if is_mult:
            if ed not in oldartids or cur != line['titre']:
                if mult_type == "sup":
                    print >> sys.stderr, "WARNING: could not find first or last part of multiple article to be removed:", line['titre'].encode('utf-8'), "to", ed.encode('utf-8'), "(last found:", cur+")"
                    continue
                print >> sys.stderr, "ERROR: dealing with multiple article", line['titre'].encode('utf-8'), "to", ed.encode('utf-8'), "Could not find first or last part in last step (last found:", cur+")"
                exit()
            while True:
                if mult_type == "sup" and not re_suppr.match(a["statut"]):
                    log("DEBUG: Marking art %s as supprimé" % cur.encode('utf-8'))
                    a["statut"] = "supprimé"
                    a["alineas"] = dict()
                    a["order"] = order
                    order += 1
                    write_json(a)
                elif mult_type == "conf":
                    if oldid:
                        a = grdoldarts[line['titre']]
                    log("DEBUG: Recovering art conforme %s" % cur)
                    a["statut"] = "conforme"
                    a["order"] = order
                    order += 1
                    write_json(a)
                if cur == ed or not oldarts:
                    break
                cur, a = oldarts.pop(0)
            continue
        if (re_suppr.match(line["statut"]) or (len(alineas) == 1 and re_suppr.match(alineas[0]))) and (line['titre'] not in oldstatus or re_suppr.match(oldstatus[line['titre']])):
           continue
        # Clean empty articles with only "Non modifié" and include text from previous step
        if len(alineas) == 1 and re_confo.match(alineas[0].encode('utf-8')):
            if not line['titre'] in oldstep[oldid]:
                sys.stderr.write("WARNING: found repeated article %s missing from previous step %s: %s\n" % (line['titre'], FILE, line['alineas']))
            else:
                log("DEBUG: get back Art %s" % line['titre'])
                alineas.pop(0)
                alineas.extend(oldstep[oldid][line['titre']])
        gd_text = []
        for j, text in enumerate(alineas):
            text = text.encode('utf-8')
            if "(Non modifi" in text and not line['titre'] in oldstep[0]:
                sys.stderr.write("WARNING: found repeated article missing %s from previous step %s: %s\n" % (line['titre'], FILE, text))
            elif re_confo_with_txt.search(text):
                text = re_confo_with_txt.sub(r' \2', text)
                gd_text.append(text)
            elif "(Non modifi" in text:
                part = re.split("\s*([\.°\-]+\s*)+\s*\(Non", text)
                if not part:
                    log("ERROR trying to get non-modifiés")
                    exit()
                todo = part[0]
                log("EXTRACT non-modifiés: " + str(part))
    # Extract series of non-modified subsections of articles from previous version.
                if " à " in todo:
                    start = re.split(" à ", todo)[0]
                    end = re.split(" à ", todo)[1]
                    piece = get_mark_from_last(oldstep[0][line['titre']], start, end)
    # Extract set of non-modified subsections of articles from previous version.
                elif "," in todo or " et " in todo or " & " in todo:
                    piece = []
                    for i, mark in enumerate(re.split("(?:\s*(,|&|et)\s*)", todo)):
                        if i % 2 == 1:
                            continue
                        piece.extend(get_mark_from_last(oldstep[0][line['titre']], mark))
    # Extract single non-modified subsection of articles from previous version.
                else:
                    piece = get_mark_from_last(oldstep[0][line['titre']], todo)
                gd_text.extend(piece)
            else:
                gd_text.append(text.decode('utf-8'))
        line['alineas'] = dict()
        line['order'] = order
        order += 1
        for i, t in enumerate(gd_text):
            line['alineas']["%03d" % (i+1)] = t
        write_json(line)

if texte['definitif'] and oldsects and oldarts:
    print >> sys.stderr, "ERROR: %s sections left:\n%s" % (len(oldsects), oldsects)
    exit()

while oldarts:
    cur, a = oldarts.pop(0)
    oldartids.remove(cur)
    if texte['definitif'] and not re_suppr.match(a["statut"]):
        print >> sys.stderr, "ERROR: %s articles left:\n%s %s" % (len(oldarts)+1, cur, oldartids)
        exit()
    if not texte.get('echec', '') and a["statut"].startswith("conforme"):
        log("DEBUG: Recovering art conforme %s" % cur.encode('utf-8'))
        a["statut"] = "conforme"
        a["order"] = order
        order += 1
        write_json(a)
    elif not re_suppr.match(a["statut"]) or texte.get('echec', ''):
        log("DEBUG: Marking art %s as supprimé" % cur.encode('utf-8'))
        a["statut"] = "supprimé"
        a["alineas"] = dict()
        a["order"] = order
        order += 1
        write_json(a)

f.close()

