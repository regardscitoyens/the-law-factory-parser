#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, re, copy
import json
from .sort_articles import bister, article_is_lower

def complete(current, previous, anteprevious, step, table_concordance):
    current = copy.deepcopy(current)
    previous = copy.deepcopy(previous)
    anteprevious = copy.deepcopy(anteprevious)

    DEBUG = True if len(sys.argv) > 4 else False
    def log(text):
        if DEBUG:
            print(text, file=sys.stderr)

    def exit():
        raise Exception('oops, parsing exploded')

    find_num = re.compile(r'-[a-z]*(\d+)\D?$')
    oldnum = 0
    oldstep = [{}, {}]
    oldjson =  []
    oldstatus = {}
    oldartids = []
    oldarts = []
    oldsects = []
    try:
        for line in previous:
            if not line or not "type" in line:
                log("JSON %s badly formatted, missing field type: %s" % (source, line))
                exit()
            if line["type"] != "texte":
                oldjson.append(line)
            else:
                oldnum = int(find_num.search(line['id']).group(1))
                olddepot = line['depot']
            if line["type"] == "article":
                keys = list(line['alineas'].keys())
                keys.sort()
                oldstep[0][line["titre"]] = [line['alineas'][k] for k in keys]
                oldstatus[line["titre"]] = line['statut']
                oldartids.append(line["titre"])
                oldarts.append((line["titre"], line))
            elif line["type"] == "section":
                oldsects.append(line)
    except Exception as e:
        print(type(e), e, file=sys.stderr)
        log("No previous step found at %s" % sys.argv[2])
        exit()


    grdoldarts = {}
    if '/ta' in step.get('source_url', ''):
        for line in anteprevious:
            if line["type"] == "article":
                keys = list(line['alineas'].keys())
                keys.sort()
                oldstep[1][line["titre"]] = [line['alineas'][k] for k in keys]
                grdoldarts[line["titre"]] = line

    ALL_ARTICLES = []
    def write_json(data):
        nonlocal ALL_ARTICLES
        ALL_ARTICLES.append(data)

    null_reg = re.compile(r'^$')
    re_mat_uno = re.compile(r'[I1]$')
    re_mat_simple = re.compile(r'[IVXDCLM\d]')
    re_mat_complex = re.compile(r'L[O.\s]*[IVXDCLM\d]')
    re_clean_art = re.compile(r'^"?Art\.?\s*', re.I)
    make_sta_reg = lambda x: re.compile(r'^("?Art[\s\.]*)?%s\s*(([\.°\-]+\s*)+)' % re_clean_art.sub('', x))
    make_end_reg = lambda x, rich: re.compile(r'^%s[IVXDCLM\d\-]+([\-\.\s]+\d*)*((%s|[A-Z])\s*)*(\(|et\s|%s)' % ('("?[LA][LArRtTO\.\s]+)?' if rich else "", bister, x))
    re_sect_chg = re.compile(r'^((chap|t)itre|volume|livre|tome|(sous-)?section)\s+[1-9IVXDC]', re.I)
    def get_mark_from_last(text, s, l="", sep="", force=False):
        log("- GET Extract from " + s + " to " + l)
        res = []
        try:
            start = make_sta_reg(s)
        except Exception as e:
            print('ERROR', type(e), e, s, l, file=sys.stderr)
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
            print('ERROR: could not retrieve', s, file=sys.stderr)
            exit()
        return res

    re_alin_sup = re.compile(r'supprimés?\)$', re.I)
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
    for line in current:
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
                    print("ERROR: Problem while renumbering sections", line['titre'], "\n", cursec, file=sys.stderr)
                    exit()
                if line["id"] != cursec["id"]:
                    line["newid"] = line["id"]
                    line["id"] = cursec["id"]
            write_json(line)
          else:
            keys = list(line['alineas'].keys())
            keys.sort()
            alineas = [line['alineas'][k] for k in keys]
            mult = line['titre'].split(' à ')
            is_mult = (len(mult) > 1)
            oldid = 1 if grdoldarts and ("conforme" in line['statut'].lower() or (alineas and "conforme" in alineas[0].lower())) else 0
            if is_mult:
                st = mult[0].strip()
                ed = mult[1].strip()
                if re_suppr.match(line['statut']) or (len(alineas) == 1 and re_suppr.match(alineas[0])):
                    if (st not in oldartids and ed not in oldartids) or (st in oldstatus and re_suppr.match(oldstatus[st]) and ed in oldstatus and re_suppr.match(oldstatus[ed])):
                        log("DEBUG: SKIP already deleted articles %s to %s" % (st, ed))
                        continue
                    log("DEBUG: Marking as deleted articles %s à %s" % (st, ed))
                    mult_type = "sup"
                elif re_confo.match(line['statut']) or (len(alineas) == 1 and re_confo.match(alineas[0])):
                    log("DEBUG: Recovering art conformes %s à %s" % (st, ed))
                    mult_type = "conf"
                else:
                    print("ERROR: Found multiple article which I don't know what to do with", line['titre'], line, file=sys.stderr)
                    exit()
                line['titre'] = st
            cur = ""
            if texte['definitif']:
                try:
                    goon = True
                    while goon:
                        _, oldart = oldarts[0]

                        if oldart['titre'].lower() in table_concordance:
                            new_art = table_concordance[oldart['titre'].lower()]
                            if 'suppr' in new_art:
                                c, a = oldarts.pop(0)
                                oldartids.remove(c)
                                if olddepot:
                                    log("DEBUG: Marking art %s as supprimé (thanks to concordance table)" % c)
                                    a["order"] = order
                                    order += 1
                                    write_json(a)
                                continue

                        if re_suppr.match(oldart['statut']):
                            c, a = oldarts.pop(0)
                            oldartids.remove(c)
                            if olddepot:
                                log("DEBUG: Marking art %s as supprimé" % c)
                                a["order"] = order
                                order += 1
                                write_json(a)
                        else:
                            goon = False
                except:
                    print("ERROR: Problem while renumbering articles", line, "\n", oldart, file=sys.stderr)
                    exit()
                oldtxt = [re_clean_alin.sub('', v) for v in list(oldart["alineas"].values()) if not re_alin_sup.search(v)]
                txt = [re_clean_alin.sub('', v) for v in list(line["alineas"].values()) if not re_alin_sup.search(v)]
                a = SequenceMatcher(None, oldtxt, txt).get_matching_blocks()
                similarity = float(sum([m[2] for m in a])) / max(a[-1][0], a[-1][1])
                if similarity < 0.75 and not olddepot:
                    print("WARNING BIG DIFFERENCE BETWEEN RENUMBERED ARTICLE", oldart["titre"], "<->", line["titre"], len("".join(txt)), "diffchars, similarity; %.2f" % similarity, file=sys.stderr)
                
                log("DEBUG: concordance detected between '%s' et '%s'" % (line['titre'], oldart['titre']))
                if oldart['titre'].lower() in table_concordance:
                    new_art = table_concordance[oldart['titre'].lower()]
                    if new_art != line['titre']:
                        log("DEBUG: true concordance is different: '%s' instead of '%s'" % (new_art, line['titre']))
                        exit()

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
                        log("DEBUG: Recovering art conforme %s" % cur)
                        a["statut"] = "conforme"
                        a["order"] = order
                        order += 1
                        write_json(a)
                    elif not re_suppr.match(a["statut"]):
                        log("DEBUG: Marking art %s as supprimé" % cur)
                        a["statut"] = "supprimé"
                        a["alineas"] = dict()
                        a["order"] = order
                        order += 1
                        write_json(a)
            if is_mult:
                if ed not in oldartids or cur != line['titre']:
                    if mult_type == "sup":
                        print("WARNING: could not find first or last part of multiple article to be removed:", line['titre'], "to", ed, "(last found:", cur+")", file=sys.stderr)
                        continue
                    print("ERROR: dealing with multiple article", line['titre'], "to", ed, "Could not find first or last part in last step (last found:", cur+")", file=sys.stderr)
                    exit()
                while True:
                    if mult_type == "sup" and not re_suppr.match(a["statut"]):
                        log("DEBUG: Marking art %s as supprimé" % cur)
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
            if alineas and re_confo.match(alineas[0]) and alineas[0].endswith(')'):
                if not line['titre'] in oldstep[oldid]:
                    sys.stderr.write("WARNING: found repeated article %s missing from previous step: %s\n" % (line['titre'], line['alineas']))
                else:
                    log("DEBUG: get back Art %s" % line['titre'])
                    alineas = oldstep[oldid][line['titre']]
            gd_text = []
            oldid = 1 if grdoldarts else 0
            for j, text in enumerate(alineas):
                text = text
                if "(Non modifi" in text and not line['titre'] in oldstep[oldid]:
                    sys.stderr.write("WARNING: found repeated article missing %s from previous step: %s\n" % (line['titre'], text))
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
                    # log("EXTRACT non-modifiés for "+line['titre']+": " + pieces)
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
                    gd_text.append(text)
            line['alineas'] = dict()
            line['order'] = order
            order += 1
            for i, t in enumerate(gd_text):
                line['alineas']["%03d" % (i+1)] = t
            write_json(line)

    if texte['definitif'] and oldsects and oldarts:
        print("ERROR: %s sections left:\n%s" % (len(oldsects), oldsects), file=sys.stderr)
        #exit()

    while oldarts:
        cur, a = oldarts.pop(0)
        oldartids.remove(cur)
        if texte['definitif'] and not re_suppr.match(a["statut"]):
            print("ERROR: %s articles left:\n%s %s" % (len(oldarts)+1, cur, oldartids), file=sys.stderr)
            exit()
        if not texte.get('echec', '') and a["statut"].startswith("conforme"):
            log("DEBUG: Recovering art conforme %s" % cur)
            a["statut"] = "conforme"
            a["order"] = order
            order += 1
            write_json(a)
        elif not re_suppr.match(a["statut"]) or texte.get('echec', ''):
            log("DEBUG: Marking art %s as supprimé" % cur)
            a["statut"] = "supprimé"
            a["alineas"] = dict()
            a["order"] = order
            order += 1
            write_json(a)

    return ALL_ARTICLES

if __name__ == '__main__':
    print(json.dump(json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), indent=2, sort_keys=True, ensure_ascii=False))
