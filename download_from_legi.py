#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import click
import json
import sys
import itertools
import os

from legipy.services import LawService, LegislatureService


for legislature in LegislatureService().legislatures():
    if legislature.number < 13:
        continue

    for project in itertools.chain(LawService().published_laws(legislature.number),
        LawService().pending_laws(legislature.number, True),
        LawService().pending_laws(legislature.number, False)):
        print(project.id_legi)
        filepath = 'legifrance_dossiers/' + project.id_legi + '.json'
        if os.path.exists(filepath):
            continue
        details = LawService().get_law(project.id_legi)
        json.dump(details.to_json(), open(filepath, 'w'), sort_keys=True, indent=2, ensure_ascii=False)
