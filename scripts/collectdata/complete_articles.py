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
                olddepot = line['depot']
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

null_reg = re.compile(r'^$')
re_mat_uno = re.compile(r'[I1]$')
re_mat_simple = re.compile(r'[IVXDCLM\d]')
re_mat_complex = re.compile(r'L[O.\s]*[IVXDCLM\d]')
re_clean_art = re.compile(r'^"?Art\.?\s*', re.I)
make_sta_reg = lambda x: re.compile(r'^("?Art[\s\.]*)?%s\s*(([\.°\-]+\s*)+)' % re_clean_art.sub('', x.encode('utf-8')))
make_end_reg = lambda x, rich: re.compile(r'^%s[IVXDCLM\d\-]+([\-\.\s]+\d*)*((%s|[A-Z])\s*)*(\(|et\s|%s)' % ('("?[LA][LArRtTO\.\s]+)?' if rich else "", bister, x))
re_sect_chg = re.compile(r'^((chap|t)itre|volume|livre|tome|(sous-)?section)\s+[1-9IVXDC]', re.I)
def get_mark_from_last(text, s, l="", sep="", force=False):
    log("- GET Extract from " + s + " to " + l)
    res = []
    try:
        start = make_sta_reg(s)
    except Exception as e:
        print >> sys.stderr, 'ERROR', type(e), e, s.encode('utf-8'), l.encode('utf-8')
        exit()
    rich = re_mat_complex.match(s) or not re_mat_simple.match(s)
    if l:
        last = make_sta_reg(l)
    re_end = None
    record = False
    for n, i in enumerate(text):
        matc = start.match(i)
        log("    TEST: " + i[:50])
        if re_end and (re_end.match(i) or re_sect_chg.match(i)):
            if l:
                re_end = make_end_reg(sep, rich)
                l = ""
            else:
                log("  --> END FOUND")
                record = False
                break
        elif matc:
            sep = matc.group(2).strip()
            log("  --> START FOUND " + sep)
            record = True
            if l:
                re_end = last
            else:
                re_end = make_end_reg(sep, rich)
        elif force:
            record = True
            re_end = null_reg
            if n == 0:
                i = "%s%s %s" % (s, ". -" if re_mat_simple.match(s) else sep, i)
        if record:
            log("     copy alinea")
            res.append(i)
    # retry and get everything as I before II added if not found
    if not res:
        if not l and re_mat_uno.match(s):
            log("   nothing found, grabbing all article now...")
            return get_mark_from_last(text, s, l, sep=sep, force=True)
        print >> sys.stderr, 'ERROR: could not retrieve', s.encode('utf-8')
        exit()
    return res

re_alin_sup = re.compile(ur'supprimés?\)$', re.I)
re_clean_alin = re.compile(r'^"?([IVXCDLM]+|\d+|[a-z]|[°)\-\.\s]+)+\s*((%s|[A-Z]+)[°)\-\.\s]+)*' % bister)
re_clean_et = re.compile(r'(\s*[\&,]\s*|\s+et\s+)+', re.I)
re_clean_virg = re.compile(r'\s*,\s*')
re_suppr = re.compile(r'\W*suppr(ess|im)', re.I)
re_confo = re.compile(r'\W*(conforme|non[\s\-]*modifi)', re.I)
re_confo_with_txt = re.compile(r'\s*\(\s*(conforme|non[\s\-]*modifié)\s*\)\s*([\W]*\w+)', re.I)
re_clean_subsec_space = re.compile(r'^("?[IVX0-9]{1,4}(\s+[a-z]+)?(\s+[A-Z]{1,4})?)\s*([\.°\-]+)\s*([^\s\)])', re.I)
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
            from difflib import SequenceMatcher
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
                        c, a = oldarts.pop(0)
                        oldartids.remove(c)
                        if olddepot:
                            log("DEBUG: Marking art %s as supprimé" % c.encode('utf-8'))
                            a["order"] = order
                            order += 1
                            write_json(a)
                    else:
                        goon = False
            except:
                print >> sys.stderr, "ERROR: Problem while renumbering articles", line, "\n", oldart
                exit()
            oldtxt = [re_clean_alin.sub('', v) for v in oldart["alineas"].values() if not re_alin_sup.search(v)]
            txt = [re_clean_alin.sub('', v) for v in line["alineas"].values() if not re_alin_sup.search(v)]
            a = SequenceMatcher(None, oldtxt, txt).get_matching_blocks()
            similarity = float(sum([m[2] for m in a])) / max(a[-1][0], a[-1][1])
            if similarity < 0.75 and not olddepot:
                print >> sys.stderr, "WARNING BIG DIFFERENCE BETWEEN RENUMBERED ARTICLE", oldart["titre"], "<->", line["titre"], len("".join(txt)), "diffchars, similarity;", similarity
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
                        a = grdoldarts[a['titre']]
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
        if alineas and re_confo.match(alineas[0].encode('utf-7')) and alineas[0].endswith(')'):
            if not line['titre'] in oldstep[oldid]:
                sys.stderr.write("WARNING: found repeated article %s missing from previous step %s: %s\n" % (line['titre'], FILE, line['alineas']))
            else:
                log("DEBUG: get back Art %s" % line['titre'])
                alineas = oldstep[oldid][line['titre']]
        gd_text = []
        oldid = 1 if grdoldarts else 0
        for j, text in enumerate(alineas):
            text = text.encode('utf-8')
            if "(Non modifi" in text and not line['titre'] in oldstep[oldid]:
                sys.stderr.write("WARNING: found repeated article missing %s from previous step %s: %s\n" % (line['titre'], FILE, text))
            elif re_confo_with_txt.search(text):
                text = re_confo_with_txt.sub(r' \2', text)
                text = re_clean_subsec_space.sub(r'\1\4 \5', text)
                gd_text.append(text)
            elif "(Non modifi" in text:
                part = re.split("\s*([\.°\-]+\s*)+\s*\(Non", text)
                if not part:
                    log("ERROR trying to get non-modifiés")
                    exit()
                pieces = re_clean_et.sub(',', part[0])
                log("EXTRACT non-modifiés for "+line['titre']+": " + pieces)
                piece = []
                for todo in pieces.split(','):
    # Extract series of non-modified subsections of articles from previous version.
                    if " à " in todo:
                        start = re.split(" à ", todo)[0]
                        end = re.split(" à ", todo)[1]
                        piece.extend(get_mark_from_last(oldstep[oldid][line['titre']], start, end, sep=part[1:]))
    # Extract set of non-modified subsections of articles from previous version.
                    elif todo:
                        piece.extend(get_mark_from_last(oldstep[oldid][line['titre']], todo, sep=part[1:]))
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
    #exit()

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

