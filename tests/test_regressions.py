""""
Generate final directories as the ones we use in the
live website and compare it with previously
a previously generated version

Usage: python tests_regressions.py <tests_cases_directory>

Optional: There's a `--regen` flag to generate the tests cases
"""
# TODO(cleanup): test.sh/test runner to run all the small tests before the big ones (like travis)

import glob, shutil, os, filecmp, sys, difflib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tlfp import parse_one
from tlfp.parse_one import download_merged_dos
from tlfp.parse_doslegs_texts import find_good_url_resp
from tlfp.tools.detect_anomalies import find_anomalies
from tlfp.tools.common import log_print
from tlfp.tools import parse_texte, download_groupes, download_lois_dites, download_AN_opendata

REGEN_TESTS = '--regen' in sys.argv
# directory with the test-cases
TEST_DIR = sys.argv[1] if len(sys.argv) > 1 else 'tests_tmp'
# directory where we generate the output to be tested for regression
OUTPUT_DIR = TEST_DIR if REGEN_TESTS else 'tests_tmp'

if '--enable-cache' in sys.argv:
    from lawfactory_utils.urls import enable_requests_cache
    enable_requests_cache()

print('> testing url fixing')
# AN .pdf
assert find_good_url_resp('http://www.assemblee-nationale.fr/13/pdf/pion1895.pdf').url == 'http://www.assemblee-nationale.fr/13/propositions/pion1895.asp'
# senat simple
assert find_good_url_resp('https://www.senat.fr/leg/tas11-040.html').url == 'https://www.senat.fr/leg/tas11-040.html'
# senat multi-page but not last page
assert find_good_url_resp('https://www.senat.fr/rap/l07-485/l07-485.html').url == 'https://www.senat.fr/rap/l07-485/l07-4851.html'
# senat multi-page but not mono
assert find_good_url_resp('http://www.senat.fr/rap/l09-654/l09-654.html').url == 'http://www.senat.fr/rap/l09-654/l09-6542.html'
# senat multi-page text
assert find_good_url_resp('https://www.senat.fr/rap/l08-584/l08-584.html').url == 'https://www.senat.fr/rap/l08-584/l08-584_mono.html'
# senat multipage examen en commission
assert find_good_url_resp('https://www.senat.fr/rap/l09-535/l09-535.html').url == 'https://www.senat.fr/rap/l09-535/l09-5358.html'
print('     > OK ')
print('> testing parse_texte')
assert len(parse_texte.parse('http://www.assemblee-nationale.fr/13/rapports/r2568.asp')) == 5
assert len(parse_texte.parse('https://www.senat.fr/leg/ppl08-039.html')) == 2
print('     > OK')


if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

download_groupes.process(OUTPUT_DIR)
download_lois_dites.process(OUTPUT_DIR)
opendata_an = download_AN_opendata.process(OUTPUT_DIR)

print('> testing merge')
# complete AN urls
with log_print(only_log=True) as log:
    print('wtf', file=sys.stderr)
    dos, *_ = download_merged_dos('pjl11-497', opendata_an, log=log)
    anomalies = find_anomalies([dos])
    assert anomalies == 0
    for step in dos['steps']:
        if step.get('institution') == 'assemblee':
            assert step['source_url']
print('     > OK')

print('> test full data generation')
# https://stackoverflow.com/questions/4187564/recursive-dircmp-compare-two-directories-to-ensure-they-have-the-same-files-and
filecmp.cmpfiles.__defaults__ = (False,)
def _is_same_helper(dircmp):
    assert not dircmp.funny_files
    if dircmp.left_only or dircmp.right_only or dircmp.diff_files or dircmp.funny_files:
        for name in dircmp.diff_files:
            left_file = os.path.join(dircmp.left, name)
            right_file = os.path.join(dircmp.right, name)
            print('>>> Two files are different:', left_file, 'AND', right_file)
            diff = list(difflib.unified_diff(open(left_file).readlines(),
                        open(right_file).readlines()))
            for line in diff[:20]:
                print(line, end='')
            if len(diff) > 20:
                print('-- diff too long, it was truncated')
            print()
        else:
            print('>>> Full file-tree diff:')
            dircmp.report_full_closure()
        return False
    for sub_dircmp in dircmp.subdirs.values():
        if not _is_same_helper(sub_dircmp):
            return False
    return True


for directory in sorted(glob.glob(TEST_DIR + '/p*')):
    if '_tmp' in directory:
        continue
    senat_id = directory.split('/')[-1]
    print('  - test regressions for', senat_id)

    with log_print(only_log=True) as log:
        parse_one.process(OUTPUT_DIR, senat_id)
    comp = filecmp.dircmp(directory, OUTPUT_DIR + '/' + senat_id)
    if _is_same_helper(comp):
        print('     > OK')
    else:
        print(log.getvalue().replace('\n', '\nlog: '))
        print('     > Output different to the verified output: '
              'https://github.com/regardscitoyens/'
              'the-law-factory-parser-test-cases/tree/master/%s' % senat_id)
        sys.exit(1)

if not REGEN_TESTS:
    shutil.rmtree(OUTPUT_DIR)
else:
    print('>> the regressions cases have been correctly re-generated')
