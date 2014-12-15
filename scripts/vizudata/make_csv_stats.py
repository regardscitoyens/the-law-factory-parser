#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, json

sourcedir = os.path.join(sys.argv[1], 'data')
if not sourcedir:
    sys.stderr.write('ERROR: no input directory given\n')
    exit(1)

formatt = lambda x: x.encode("utf-8") if type(x) == unicode else str(x)
cleanquotes = lambda x: '"' + x.replace('"', '""') + '"' if "," in x else x
safediv = lambda x, y: 0 if not int(y) else int(x)/float(y)

headers = [
  "id",
  "short_title",
  "procedure",
  "type",
  "beginning",
  "end",
  "decision_cc",
  "themes",
  "input_text_length2",
  "output_text_length2",
  "ratio_text_size",
  "ratio_texte_modif",
  "total_articles",
  "total_articles_modified",
  "ratio_article_modif",
  "total_days",
  "total_accident_procedure",
  "total_intervenant",
  "total_mots2",
  "total_amendements",
  "total_amendements_adoptes",
  "taux_amendements_adoptes",
  "total_amendements_parlementaire",
  "total_amendements_parlementaire_adoptes"
  "taux_amendements_parlementaire_adoptes"
]
print ",".join(headers)

for fil in os.listdir(sourcedir):
    if not fil.startswith("dossiers_") or not fil.endswith(".json"):
        continue
    with open(os.path.join(sourcedir, fil)) as f:
        dset = json.load(f)["dossiers"]
    for text in dset:
        text["decision_cc"] = ""
        for s in text["steps"]:
            if "decision" in s:
                text["decision_cc"] = s["decision"]
                break
        text["themes"] = "|".join(text["themes"])
        text["ratio_text_size"] = safediv(int(text["output_text_length2"])-int(text["input_text_length2"]), text["input_text_length2"])
        text["taux_amendements_adoptes"] = safediv(text["total_amendements_adoptes"], text["total_amendements"])
        text["taux_amendements_parlementaire_adoptes"] = safediv(text["total_amendements_parlementaire_adoptes"], text["total_amendements_parlementaire"])

        print ",".join([cleanquotes(formatt(text.get(h, 0))) for h in headers])

