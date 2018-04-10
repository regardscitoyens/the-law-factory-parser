""""
Generate final directories as the ones we use in the
live website and compare it with previously
a previously generated version

Usage: python tests_regressions.py <tests_cases_directory>

Optional: There's a `--regen` flag to generate the tests cases
"""

import glob, shutil, os, filecmp, sys, difflib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parse_one
from parse_doslegs_texts import find_good_url_resp
from tools import parse_texte

# use `test_regressions.py <directory> --regen` to update the tests directory
REGEN_TESTS = '--regen' in sys.argv
TEST_DIR = sys.argv[1]

if '--enable-cache' in sys.argv:
    from lawfactory_utils.urls import enable_requests_cache;enable_requests_cache()

print('****** testing url fixing... ******')
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
print('****** => url fixing OK ******')

print()
print('*** testing parse_texte ****')
assert len(parse_texte.parse('http://www.assemblee-nationale.fr/13/rapports/r2568.asp')) == 5
assert len(parse_texte.parse('https://www.senat.fr/leg/ppl08-039.html')) == 2
print('****** => parse_texte OK ******')

""" test full data generation """

# https://stackoverflow.com/questions/4187564/recursive-dircmp-compare-two-directories-to-ensure-they-have-the-same-files-and
filecmp.cmpfiles.__defaults__ = (False,)
def _is_same_helper(dircmp):
    assert not dircmp.funny_files
    if dircmp.left_only or dircmp.right_only or dircmp.diff_files or dircmp.funny_files:
        for name in dircmp.diff_files:
            left_file = os.path.join(dircmp.left, name)
            right_file = os.path.join(dircmp.right, name)
            print('TWO FILES ARES DIFFERENT:', left_file, 'AND', right_file)
            diff = list(difflib.unified_diff(open(left_file).readlines(),
                open(right_file).readlines()))
            for line in diff[:20]:
                print(line, end='')
            if len(diff) > 20:
                print('-- diff too long, it was truncated')
        else:
            dircmp.report_full_closure()
        return False
    for sub_dircmp in dircmp.subdirs.values():
       if not _is_same_helper(sub_dircmp):
           return False
    return True

output_dir = 'tests_tmp'
if REGEN_TESTS:
    output_dir = TEST_DIR
    for f in glob.glob(os.path.join(TEST_DIR, '*es.json')):
        os.remove(f)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for directory in sorted(glob.glob(TEST_DIR + '/p*')):
    if '_tmp' in directory:
        continue
    senat_id = directory.split('/')[-1]
    print()
    print('****** testing', senat_id, '*******')
    print()

    parse_one.process(output_dir, senat_id)
    comp = filecmp.dircmp(directory, output_dir + '/' + senat_id)
    if _is_same_helper(comp):
        print()
        print('  -> test passed')
    else:
        print()
        print('   -> test failed, details in tests_tmp')
        raise Exception()

if not REGEN_TESTS:
    shutil.rmtree('tests_tmp')
else:
    print('TESTS REGEN OK')
