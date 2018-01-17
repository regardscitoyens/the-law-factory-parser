import glob, shutil, os, filecmp, sys, difflib

import parse_one
from parse_doslegs_texts import find_good_url
from tools import parse_texte
import download_groupes

# use `test_regressions.py <directory> --regen` to update the tests directory
REGEN_TESTS = '--regen' in sys.argv
TEST_DIR = sys.argv[1]

print('****** testing url fixing... ******')
# AN .pdf
assert find_good_url('http://www.assemblee-nationale.fr/13/pdf/pion1895.pdf') == 'http://www.assemblee-nationale.fr/13/propositions/pion1895.asp'
# senat simple
assert find_good_url('https://www.senat.fr/leg/tas11-040.html') == 'https://www.senat.fr/leg/tas11-040.html'
# senat multi-page but not last page
assert find_good_url('https://www.senat.fr/rap/l07-485/l07-485.html') == 'https://www.senat.fr/rap/l07-485/l07-4851.html'
# senat multi-page but not mono
assert find_good_url('http://www.senat.fr/rap/l09-654/l09-654.html') == 'http://www.senat.fr/rap/l09-654/l09-6542.html'
# senat multi-page text
assert find_good_url('https://www.senat.fr/rap/l08-584/l08-584.html') == 'https://www.senat.fr/rap/l08-584/l08-584_mono.html'
# senat multipage examen en commission
assert find_good_url('https://www.senat.fr/rap/l09-535/l09-535.html') == 'https://www.senat.fr/rap/l09-535/l09-5358.html'
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
            diff = difflib.unified_diff(open(os.path.join(dircmp.left, name)).readlines(),
                open(os.path.join(dircmp.right, name)).readlines())
            for line in diff:
                print(line)
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
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
download_groupes.process(output_dir)

for directory in glob.glob(TEST_DIR + '/p*'):
    senat_id = directory.split('/')[-1]
    print()
    print('****** testing', senat_id, '*******')
    print()

    parse_one.process(output_dir, senat_id, disable_cache=True)
    comp = filecmp.dircmp(directory, output_dir + '/' + senat_id)
    if _is_same_helper(comp):
        print()
        print('  -> test passed')
    else:
        print()
        print('   -> test failed, details in tests_tmp')
        raise Exception()

shutil.rmtree('tests_tmp')
