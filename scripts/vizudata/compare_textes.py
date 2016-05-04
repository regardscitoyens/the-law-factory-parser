#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from common import *
from difflib import SequenceMatcher


def read_text(path):
    articles = open_json(os.path.dirname(path), os.path.basename(path))['articles']
    texte = []
    for art in articles:
        for key in sorted(art['alineas'].keys()):
            if art['alineas'][key] != '':
                texte.append(art['alineas'][key])
    return texte


def compare(textA, textB):
    lenA = len(textA)
    lenB = len(textB)

    matcher = SequenceMatcher(None, textA, textB)
    blocks = matcher.get_matching_blocks()

    return {
        'changed': (1 - float(sum([m[2] for m in blocks])) / max(blocks[-1][0], blocks[-1][1])),
        'growth': float(lenB - lenA) / float(lenA),
        'lenA': lenA,
        'lenB': lenB,
        'similarity': matcher.ratio()
    }


def compare_paths(pathA, pathB):
    textA = "\n".join(read_text(pathA))
    textB = "\n".join(read_text(pathB))

    return compare(textA, textB)


def output_result(result, indent=''):
    sys.stdout.write('%sDissimilarity (from SequenceMatcher): %.2f%%\n' % (indent, 100 * (1 - result['similarity'])))
    sys.stdout.write('%sChange ratio: %.2f%%\n' % (indent, 100 * result['changed']))
    sys.stdout.write('%sText A length: %d\n' % (indent, result['lenA']))
    sys.stdout.write('%sText B length: %d\n' % (indent, result['lenB']))
    sys.stdout.write('%sText growth: %.2f%%\n' % (indent, 100 * result['growth']))


def process_text(datadir, force=False, output=False):
    # Read procedure and loop over steps
    proc = open_json(os.path.join(datadir, 'viz'), 'procedure.json')
    first_step = proc['steps'][0]
    prev_step = first_step
    for step in proc['steps']:
        # Load step text
        textefile = os.path.join(datadir, 'procedure', step['directory'], 'texte', 'texte.json')
        if not os.path.exists(textefile):
            if output:
                sys.stdout.write('No text for step %s, aborting\n' % step['directory'])
            break

        step['texte'] = "\n".join(read_text(textefile))

        # Nothing to compare first step to
        if step == first_step:
            continue

        # If stats file exists, computation already done
        statsfile = os.path.join(datadir, 'procedure', step['directory'], 'stats.json')

        if not force and os.path.exists(statsfile):
            step['texte_stats'] = open_json(os.path.join(datadir, 'procedure', step['directory']), 'stats.json')
        else:
            # Compute & save stats
            stats = { 'previous': compare(prev_step['texte'], step['texte']) }
            if prev_step == first_step:
                stats['total'] = stats['previous']
            else:
                stats['total'] = compare(first_step['texte'], step['texte'])
            print_json(stats, statsfile)
            step['texte_stats'] = stats

        if output:
            sys.stdout.write('Step %s\n' % step['directory'])
            sys.stdout.write('  Compared to previous step:\n')
            output_result(step['texte_stats']['previous'], '    ')
            sys.stdout.write('  From start of procedure:\n')
            output_result(step['texte_stats']['total'], '    ')

        prev_step = step


if __name__ == '__main__':
    if len(sys.argv) == 3:
        output_result(compare_paths(sys.argv[1], sys.argv[2]))

    elif len(sys.argv) == 2:
        process_text(sys.argv[1], False, True)

    else:
        sys.stderr.write('Usage:\n')
        sys.stderr.write('  %s a/texte.json b/texte.json : compares two arbitrary texts\n' % sys.argv[0])
        sys.stderr.write('  %s datadir : compares versions of a text in a datadir\n' % sys.argv[0])
        exit(1)
