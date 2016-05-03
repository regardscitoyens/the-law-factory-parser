#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from common import *
from difflib import SequenceMatcher


if len(sys.argv) < 3:
    sys.stderr.write('Usage: %s a/texte.json b/texte.json\n' % sys.argv[0])
    exit(1)


def read_text(path):
    articles = open_json(os.path.dirname(path), os.path.basename(path))['articles']
    texte = []
    for art in articles:
        for key in sorted(art['alineas'].keys()):
            if art['alineas'][key] != '':
                texte.append(art['alineas'][key])
    return texte


textA = "\n".join(read_text(sys.argv[1]))
textB = "\n".join(read_text(sys.argv[2]))

lenA = len(textA)
lenB = len(textB)

matcher = SequenceMatcher(None, textA, textB).get_matching_blocks()
changed = (1 - float(sum([m[2] for m in matcher])) / max(matcher[-1][0], matcher[-1][1]))
growth = float(lenB - lenA) / float(lenA)

sys.stdout.write('Change ratio: %f\n' % changed)
sys.stdout.write('Text A length: %d\n' % lenA)
sys.stdout.write('Text B length: %d\n' % lenB)
sys.stdout.write('Text growth: %f\n' % growth)
