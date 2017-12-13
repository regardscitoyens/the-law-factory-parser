import glob, shutil, os, filecmp

import parse_one

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
