import glob, shutil, os, filecmp

import parse_one
from parse_doslegs_texts import find_good_url

""" test url fixing """

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


""" test full data generation """

# https://stackoverflow.com/questions/4187564/recursive-dircmp-compare-two-directories-to-ensure-they-have-the-same-files-and
filecmp.cmpfiles.__defaults__ = (False,)
def _is_same_helper(dircmp):
    assert not dircmp.funny_files
    if dircmp.left_only or dircmp.right_only or dircmp.diff_files or dircmp.funny_files:
        return False
    for sub_dircmp in dircmp.subdirs.values():
       if not _is_same_helper(sub_dircmp):
           return False
    return True


for directory in glob.glob('tests/*'):
    senat_id = directory.split('/')[1]
    print()
    print('****** testing', senat_id, '*******')
    print()
    parse_one.process('tests_tmp', senat_id)
    comp = filecmp.dircmp(directory, 'tests_tmp/' + senat_id)
    if _is_same_helper(comp):
        print()
        print('  -> test passed')
    else:
        print()
        comp.report_full_closure()
        print()
        print('   -> test failed, details in tests_tmp')
        raise Exception()

shutil.rmtree('tests_tmp')
