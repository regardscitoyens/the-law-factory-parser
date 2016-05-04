#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Common law parser for AN/Sénat

Run with python parse_texte.py LAW_FILE
where LAW_FILE results from perl download_loi.pl URL > LAW_FILE
Outputs results to stdout

Dependencies :
html5lib, beautifulsoup4, simplejson"""

import sys, re, html5lib
import simplejson as json
from bs4 import BeautifulSoup
from sort_articles import bister

# Warning changing parenthesis in this regexp has multiple consequences throughout the code
section_titles = "((chap|t)itre|volume|livre|tome|(sous-)?section)"

re_definitif = re.compile(ur'<p[^>]*align[=:\s\-]*center"?>\(?<(b|strong)>\(?texte d[^f]*finitif\)?</(b|strong)>\)?</p>', re.I)

clean_texte_regexps = [
    (re.compile(r'[\n\t\r\s]+'), ' '),
    (re.compile(r'(<t[rdh][^>]*>) ?<p [^>]*> ?'), r'\1'),
    (re.compile(r' ?</p> ?(</t[rdh]>)'), r'\1'),
    (re.compile(r'(>%s\s*[\dIVXLCDM]+(<sup>[eE][rR]?</sup>)?)\s+-\s+([^<]*?)\s*</p>' % section_titles.upper()), r'\1</p><p><b>\6</b></p>'),
]

re_clean_title_legif = re.compile("[\s|]*l[eé]gifrance(.gouv.fr)?$", re.I)
clean_legifrance_regexps = [
    (re.compile(r'[\n\t\r\s]+'), ' '),
    (re.compile(r'<a[^>]*>\s*En savoir plus sur ce[^<]*</a>', re.I), ''),
    (re.compile(r'<a/?[^>]*>', re.I), ''),
    (re.compile(r'\s*<br/>\s*', re.I), '</p><p>'),
    (re.compile(r'<div[^>]*class="titreSection[^>]*>\s*(%s\s+[\dIVXLCDM]+e?r?)\s*:\s*([^<]*?)\s*</div>' % section_titles, re.I), r'<p>\1</p><p><b>\5</b></p>'),
    (re.compile(r'<div[^>]*class="titreArt[^>]*>(.*?)\s*</div>', re.I), r'<p><b>\1</b></p>'),
]

FILE = sys.argv[1]
try:
    with open(FILE, 'r') as f:
        string = f.read()
        try:
            string = string.decode('utf-8')
        except:
            try:
                string = string.decode('iso-8859-15')
            except:
                pass
        if 'legifrance.gouv.fr' in FILE:
            for reg, res in clean_legifrance_regexps:
                string = reg.sub(res, string)
        else:
            for reg, res in clean_texte_regexps:
                string = reg.sub(res, string)

    definitif = re_definitif.search(string) is not None
    soup = BeautifulSoup(string, "html5lib")
except:
    sys.stderr.write("ERROR: Cannot open file %s" % FILE)
    exit(1)

if (len(sys.argv) > 2) :
    ORDER = "%02d_" % int(sys.argv[2])
else:
    ORDER = ''

url = re.sub(r"^.*/http", "http", FILE)
url = re.sub(r"%3A", ":", re.sub(r"%2F", "/", url))
texte = {"type": "texte", "source": url, "definitif": definitif}
# Generate Senat or AN ID from URL
if "legifrance.gouv.fr" in url:
    m = re.search(r"cidTexte=(JORFTEXT\d+)(\D|$)", url, re.I)
    texte["id"] = ORDER + m.group(1)
elif re.search(r"assemblee-?nationale", url, re.I):
    m = re.search(r"/(\d+)/.+/(ta)?[\w\-]*(\d{4})[\.\-]", url, re.I)
    numero = int(m.group(3))
    texte["id"] = ORDER+"A" + m.group(1) + "-"
    if m.group(2) is not None:
        texte["id"] += m.group(2)
    texte["id"] += str(numero)
else:
    m = re.search(r"(ta|l)?s?(\d\d)-(\d{1,3})\d?\.", url, re.I)
    if m is None:
        m = re.search(r"/(-)?20(\d+)-\d+/(\d+).html", url, re.I)
    numero = int(m.group(3))
    texte["id"] = ORDER+"S" + m.group(2) + "-"
    if m.group(1) is not None:
        texte["id"] += m.group(1)
    texte["id"] += "%03d" % numero

texte["titre"] = re_clean_title_legif.sub('', soup.title.string.strip()) if soup.title else ""
texte["expose"] = ""
expose = False

# Convert from roman numbers
re_mat_romans = re.compile(r"[IVXCLDM]+", re.I)
romans_map = zip(
    (1000,  900, 500, 400 , 100,  90 , 50 ,  40 , 10 ,   9 ,  5 ,  4  ,  1),
    ( 'M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
)


def romans(n):
    n = n.upper()
    i = res = 0
    for d, r in romans_map:
        while n[i:i + len(r)] == r:
            res += d
            i += len(r)
    return res

upcase_accents = "ÇÀÂÄÉÈÊËÎÏÔÖÙÛÜ"
locase_accents = "çàâäéèêëîïôöùûü"


def real_lower(text):
    for a in upcase_accents:
        text = text.replace(a, locase_accents[upcase_accents.find(a)])
    return text.lower()


def lower_but_first(text):
    return text[0].upper() + real_lower(text[1:])


re_fullupcase = re.compile("^([\W0-9]*)([A-Z%s][\W0-9A-Z%s]*)$" % (upcase_accents, upcase_accents), re.U)


def clean_full_upcase(text):
    mat = re_fullupcase.match(text)
    if mat:
        text = mat.group(1) + lower_but_first(mat.group(2))
    return text

re_clean_premier = re.compile(r'((PREM)?)(1|I)ER?')
re_clean_bister = re.compile(r'([IXV\d]+e?r?)\s+(%s)' % bister, re.I)
re_clean_subsec_space = re.compile(r'^("?[IVX0-9]{1,4}(\s+[a-z]+)?(\s+[A-Z]{1,4})?)\s*([\.°\-]+)\s*([^\s\)])', re.I)
re_clean_subsec_space2 = re.compile(r'^("?[IVX0-9]{1,4})\s*([a-z]*)\s*([A-H]{1,4})([\.°\-])', re.I)
re_clean_punc_space = re.compile(u'([°«»:;,\.!\?\]\)%€&\$])([^\s\)\.,\d"])')
re_clean_spaces = re.compile(r'\s+')
re_clean_coord = re.compile(r'^["\(]*(pour)?\s*coordination[\)\s\.]*$', re.I)
# Clean html and special chars
lower_inner_title = lambda x: x.group(1)+lower_but_first(x.group(3))+" "
html_replace = [
    (re.compile(r"−"), "-"),
    (re.compile(r" "), " "),
    (re.compile(r"<!--.*?-->", re.I), ""),
    (re.compile(r"</?br/?>[«\"\s]+", re.I), " "),
    (re.compile(r'(«\s+|\s+»)'), '"'),
    (re.compile(r'(«|»|“|”|„|‟|❝|❞|＂|〟|〞|〝)'), '"'),
    (re.compile(r"(’|＇|’|ߴ|՚|ʼ|❛|❜)"), "'"),
    (re.compile(r"(‒|–|—|―|⁓|‑|‐|⁃|⏤)"), "-"),
    (re.compile(r"(</?\w+)[^>]*>"), r"\1>"),
    (re.compile(r"(</?)em>", re.I), r"\1i>"),
    (re.compile(r"(</?)strong>", re.I), r"\1b>"),
    (re.compile(r"<(![^>]*|/?(p|span))>", re.I), ""),
    (re.compile(r"\s*\n+\s*"), " "),
    (re.compile(r"<[^>]*></[^>]*>"), ""),
    (re.compile(r"^<b><i>", re.I), "<i><b>"),
    (re.compile(r"</b>(\s*)<b>", re.I), r"\1"),
    (re.compile(r"</?sup>", re.I), ""),
    (re.compile(r"^((<[bi]>)*)\((S|AN)[12]\)\s*", re.I), r"\1"),
    (re.compile(r"^(<b>Article\s*)\d+\s*<s>\s*", re.I), r"\1"),
    (re.compile(r"<s>(.*)</s>", re.I), ""),
    (re.compile(r"</?s>", re.I), ""),
    (re.compile(r"\s*</?img>\s*", re.I), ""),
    (re.compile(r"œ([A-Z])"), r"OE\1"),
    (re.compile(r"œ\s*", re.I), "oe"),
    (re.compile(r'^((<[^>]*>)*")%s ' % section_titles, re.I), lower_inner_title),
    (re.compile(r' pr..?liminaire', re.I), ' préliminaire'),
    (re.compile(r'<strike>[^<]*</strike>', re.I), ''),
    (re.compile(r'^<a>(\w)', re.I), r"\1"),
    (re_clean_spaces, " ")
]


def clean_html(t):
    for regex, repl in html_replace:
        t = regex.sub(repl, t)
    return t.strip()

re_clean_et = re.compile(r'(,|\s+et)\s+', re.I)


def pr_js(dic):
    # Clean empty articles with only "Supprimé" as text
    if not dic:
        return
    if 'alineas' in dic:
        if len(dic['alineas']) == 1 and dic['alineas']['001'].startswith("(Supprimé)"):
            dic['statut'] = "supprimé"
            dic['alineas'] = {'001': ''}
        elif dic['statut'].startswith('conforme') and not len(dic['alineas']):
            dic['alineas'] = {'001': '(Non modifié)'}
        multiples = re_clean_et.sub(',', dic['titre']).split(',')
        if len(multiples) > 1:
            for d in multiples:
                new = dict(dic)
                new['titre'] = d
                print json.dumps(new, sort_keys=True, ensure_ascii=False).encode("utf-8")
            return
    print json.dumps(dic, sort_keys=True, ensure_ascii=False).encode("utf-8")


def save_text(txt):
    if "done" not in txt:
        pr_js(txt)
    txt["done"] = True
    return txt


blank_none = lambda x: x if x else ""
re_cl_html = re.compile(r"<[^>]+>")
re_cl_html_except_tables = re.compile(r"</?[^t/][^>]*>", re.I)
re_fix_missing_table = re.compile(r'(<td>\W*)$', re.I)
cl_html_except_tables = lambda x: re_fix_missing_table.sub(r'\1</td></tr></tbody></table>', re_cl_html_except_tables.sub('', x)).strip().replace('> ', '>').replace(' <', '<').replace('<td><tr>', '<td></td></tr><tr>')
re_cl_par  = re.compile(r"[()]")
re_cl_uno  = re.compile(r"(premie?r?|unique?)", re.I)
re_cl_sec_uno = re.compile(r"^[Ii1][eE][rR]?")
re_mat_sec = re.compile(r"%s(\s+(.+)e?r?)" % section_titles, re.I)
re_mat_n = re.compile(r"((pr..?)?limin|unique|premier|[IVX\d]+)", re.I)
re_mat_art = re.compile(r"articles?\s*([^(]*)(\([^)]*\))?$", re.I)
re_mat_ppl = re.compile(r"(<b>)?pro.* loi", re.I)
re_mat_tco = re.compile(r"\s*<b>\s*(ANNEXE[^:]*:\s*|\d+\)\s+)?TEXTES?\s*(ADOPTÉS?\s*PAR|DE)\s*LA\s*COMMISSION.*</b>\s*$")
re_mat_exp = re.compile(r"(<b>)?expos[eéÉ]", re.I)
re_mat_end = re.compile(r"((<i>)?Délibéré en|(<i>)?NB[\s:<]+|(<b>)?RAPPORT ANNEX|Fait à .*, le|\s*©|\s*N.?B.?\s*:|(</?i>)*<a>[1*]</a>\s*(</?i>)*\(\)(</?i>)*|<i>\(1\)\s*Nota[\s:]+|<a>\*</a>\s*(<i>)?1)", re.I)
re_mat_ann = re.compile(r"\s*<b>\s*ANNEXES?[\s<]+")
re_mat_dots = re.compile(r"^(<i>)?[.…]+(</i>)?$")
re_mat_st = re.compile(r"(<i>|\()+\s*(conform|non[\s\-]*modif|suppr|nouveau).{0,10}$", re.I)
re_mat_new = re.compile(r"\s*\(\s*nouveau\s*\)\s*", re.I)
re_mat_texte = re.compile(r'\(texte (modifié|élaboré|d(u|e l))', re.I)
re_mat_single_char = re.compile(r'^\s*[LMN]\s*$')
re_clean_idx_spaces = re.compile(r'^([IVXLCDM0-9]+)\s*\.\s*')
re_clean_art_spaces = re.compile(r'^\s*("?)\s+')
re_clean_art_spaces2 = re.compile(r'\s+\.\s*-\s+')
re_clean_conf = re.compile(r"\((conforme|non[\s-]*modifi..?)s?\)", re.I)
re_clean_supr = re.compile(r'\((dispositions?\s*d..?clar..?es?\s*irrecevable.*article 4.*Constitution.*|(maintien de la )?suppr(ession|im..?s?)(\s*(conforme|maintenue|par la commission mixte paritaire))*)\)["\s]*$', re.I)
re_echec_hemi = re.compile(r"L('Assemblée nationale|e Sénat) (a rejeté|n'a pas adopté)[, ]+", re.I)
re_echec_hemi2 = re.compile(r"de loi a été rejetée par l('Assemblée nationale|e Sénat)\.$", re.I)
re_echec_com = re.compile(r" la commission .*(effet est d'entraîner le rejet|demande de rejeter|a rejeté|n'a pas adopté)[dleau\s]*(projet|proposition|texte)[.\s]", re.I)
re_echec_cmp = re.compile(r" (a conclu à l'échec de ses travaux|(ne|pas) .*parven(u[es]?|ir) à (élaborer )?un texte commun)", re.I)
re_rap_mult = re.compile(r'[\s<>/ai]*N[°\s]*\d+\s*(,|et)\s*[N°\s]*\d+', re.I)
re_src_mult = re.compile(r'^- L(?:A PROPOSITION|E PROJET) DE LOI n°\s*(\d+)\D')
re_clean_mult_1 = re.compile(r'\s*et\s*', re.I)
re_clean_mult_2 = re.compile(r'[^,\d]', re.I)
re_clean_footer_notes = re.compile(r"[\.\s]*\(*\d*\([\d\*]+[\)\d\*\.\s]*$")
re_sep_text = re.compile(r'\s*<b>\s*(article|%s)\s*(I|uniqu|pr..?limina|1|prem)[ier]*\s*</b>\s*$' % section_titles, re.I)
re_stars = re.compile(r'^[\s*_]+$')
re_art_uni = re.compile(r'\s*article\s*unique\s*$', re.I)
read = art_num = ali_num = 0
section_id = ""
article = None
indextext = -1
curtext = -1
srclst = []
section = {"type": "section", "id": ""}

for text in soup.find_all("p"):
    line = clean_html(str(text))

    if re_stars.match(line):
        continue
    if line == "<b>RAPPORT</b>" or line == "Mesdames, Messieurs,":
        read = -1
    if (srclst or indextext != -1) and re_sep_text.match(line):
        curtext += 1
        art_num = 0
    srcl = re_src_mult.search(line)
    cl_line = re_cl_html.sub("", line).strip()
    if srcl and read < 1:
        srclst.append(int(srcl.group(1)))
        continue
    elif re_rap_mult.match(line):
        line = cl_line
        line = re_clean_mult_1.sub(",", line)
        line = re_clean_mult_2.sub("", line)
        cl_line = re_cl_html.sub("", line).strip()
        for n_t in line.split(','):
            indextext += 1
            if int(n_t) == numero:
                break
    elif re_mat_ppl.match(line) or re_mat_tco.match(line):
        read = 0
        texte = save_text(texte)
    elif re_mat_exp.match(line):
        read = -1 # Deactivate description lecture
        expose = True
    elif re_echec_cmp.search(cl_line) or re_echec_com.search(cl_line) or re_echec_hemi.match(cl_line) or re_echec_hemi2.search(cl_line):
        texte = save_text(texte)
        pr_js({"type": "echec", "texte": cl_line})
        break
    elif read == -1 or (indextext != -1 and curtext != indextext):
        continue

    # Identify section zones
    m = re_mat_sec.match(line)
    if m:
        read = 1 # Activate titles lecture
        section["type_section"] = real_lower(m.group(1))
        section_typ = m.group(1).upper()[0]
        if m.group(3) is not None:
            section_typ += "S"

        if " LIMINAIRE" in line:
            section_num = "L"
        else:
            section_num = re_cl_uno.sub('1', re_cl_sec_uno.sub('1', re_cl_html.sub('', m.group(5).strip())).strip())
            section_num = re_clean_bister.sub(lambda m: m.group(1)+" "+real_lower(m.group(2)), section_num)
            section_num = re_mat_new.sub('', section_num).strip()
            m2 = re_mat_romans.match(section_num)
            if m2:
                rest = section_num.replace(m2.group(0), '')
                section_num = romans(m2.group(0))
                if rest: section_num = str(section_num) + rest
        # Get parent section id to build current section id
        section_par = re.sub(r""+section_typ+"[\dL].*$", "", section["id"])
        section["id"] = section_par + section_typ + str(section_num)

    # Identify titles and new article zones
    elif (not expose and re_mat_end.match(line)) or (read == 2 and re_mat_ann.match(line)):
        break
    elif re.match(r"(<i>)?<b>", line) or re_art_uni.match(line) or re.match(r"^Articles? ", line):
        line = cl_line
        # Read a new article
        if re_mat_art.match(line):
            if article is not None:
                texte = save_text(texte)
                pr_js(article)
            read = 2 # Activate alineas lecture
            expose = False
            art_num += 1
            ali_num = 0
            article = {"type": "article", "order": art_num, "alineas": {}, "statut": "none"}
            if srclst:
                article["source_text"] = srclst[curtext]
            m = re_mat_art.match(line)
            article["titre"] = re_cl_uno.sub("1er", re_cl_sec_uno.sub("1er", m.group(1).strip())).strip(" -'")
            if m.group(2) is not None:
                article["statut"] = re_cl_par.sub("", real_lower(m.group(2))).strip()
            if section["id"] != "":
                article["section"] = section["id"]
        # Read a section's title
        elif read == 1:
            texte = save_text(texte)
            section["titre"] = lower_but_first(line)
            if article is not None:
                pr_js(article)
                article = None
            pr_js(section)
            read = 0

    # Read articles with alineas
    if read == 2 and not m:
        # Find extra status information
        if ali_num == 0 and re_mat_st.match(line):
            article["statut"] = re_cl_html.sub("", re_cl_par.sub("", real_lower(line)).strip())
            continue
        if re_mat_dots.match(line):
            continue
        if "<table>" in line:
            cl_line = cl_html_except_tables(line)
        line = re_clean_art_spaces2.sub('. - ', re_clean_art_spaces.sub(r'\1', re_clean_idx_spaces.sub(r'\1. ', re_mat_new.sub(" ", cl_line).strip())))
        # Clean low/upcase issues with BIS TER etc.
        line = line.replace("oeUVRE", "OEUVRE")
        line = clean_full_upcase(line)
        line = re_clean_premier.sub(lambda m: (real_lower(m.group(0)) if m.group(1) else "")+m.group(3)+"er", line)
        line = re_clean_bister.sub(lambda m: m.group(1)+" "+real_lower(m.group(2)), line)
        # Clean different versions of same comment.
        line = re_clean_supr.sub('(Supprimé)', line)
        line = re_clean_conf.sub('(Non modifié)', line)
        line = re_clean_coord.sub('', line)
        line = re_clean_subsec_space.sub(r'\1\4 \5', line)
        line = re_clean_subsec_space2.sub(r'\1 \2 \3\4', line)
        try:
            tmp = line.decode('utf-8')
        except:
            try:
                tmp = line.decode('iso-8859-1')
            except:
                tmp = line
        line = re_clean_punc_space.sub(r'\1 \2', tmp).encode('utf-8')
        line = re_clean_spaces.sub(' ', line)
        line = re_mat_sec.sub(lambda x: lower_but_first(x.group(1))+x.group(4) if re_mat_n.match(x.group(4)) else x.group(0), line)
        line = re_clean_footer_notes.sub(".", line)
        # Clean comments (Texte du Sénat), (Texte de la Commission), ...
        if ali_num == 0 and re_mat_texte.match(line):
            continue
        line = re_mat_single_char.sub("", line)
        line = line.strip()
        if line:
            ali_num += 1
            article["alineas"]["%03d" % ali_num] = line
    else:
        #metas
        continue

save_text(texte)
pr_js(article)
