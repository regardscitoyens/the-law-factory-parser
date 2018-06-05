"""
Debugging tool to compare between the old parser and the new one
"""

import sys

from .common import open_json


def compare(proc, me, verbose=True):
    score_ok = 0
    score_nok = 0

    myprint = print
    if not verbose:
        myprint = lambda *args: None

    # i like to write cryptic function sometimes also
    def test_test(proc, me):
        def test(a, b=None, a_key=lambda a: a, ok_if_correct_is_none=False):
            nonlocal score_nok, score_ok

            def clean(obj):
                if type(obj) is str:
                    # http == https
                    obj = obj.replace('https://', 'http://')
                    obj = obj.replace('/www.legifrance.gouv.fr', '/legifrance.gouv.fr')
                    # old senat url
                    obj = obj.replace('/dossierleg/', '/dossier-legislatif/')
                    obj = obj.replace('&categorieLien=id', '')
                    obj = obj.replace('/./', '/')
                    # 1ère lecture VS 1ere lecture, should be standardized
                    return obj.replace('è', 'e')
                return obj

            if b is None:
                b = a
            a_val = clean(a_key(proc.get(a)))
            b_val = clean(me.get(b))
            if a_val != b_val and not (not a_val and not b_val) and not (not a_val and ok_if_correct_is_none):
                # rapport/ta-commission can be guessed
                if not (type(a_val) is str and type(b_val) is str and \
                    (a_val.replace('/rapports/', '/ta-commission/') \
                        == b_val.replace('/rapports/', '/ta-commission/')
                    )):
                    print('!! NOK !!', a,' diff:', a_val, 'VS', b_val)
                    score_nok += 1
                    return
            print('OK', a, '(', a_val, ')')
            score_ok += 1
        return test

    test = test_test(proc, me)
    #test('beginning')
    #test('short_title', a_key=lambda x: x.replace('(texte organique)','').strip())
    #test('long_title', 'long_title_descr')
    #test('end')
    test('url_dossier_assemblee')
    test('url_dossier_senat')
    test('url_jo', ok_if_correct_is_none=True)
    test('type', 'urgence', lambda type: type == 'urgence')

    myprint()
    myprint('STEPS:')
    if len(proc['steps']) != len(me['steps']):
        myprint('!! NOK !! DIFFERENT NUMBER OF STEPS:', len(proc['steps']), 'VS', len(me['steps']))
    myprint()

    for i, step_proc in enumerate(proc['steps']):
        myprint(' - step', i + 1)

        step_me = {}
        if len(me['steps']) > i:
            step_me = me['steps'][i]
        else:
            myprint('  - step not in mine')

        test = test_test(step_proc, step_me)

        # test('date')
        test('institution')
        test('stage')
        test('step')
        test('source_url')
        myprint()

    myprint('NOK:', score_nok)
    myprint('OK:', score_ok)
    return score_nok, score_ok

if __name__ == '__main__':
    import glob

    sum_ok = 0
    sum_nok = 0
    missing = 0
    perfect = 0
    less_than_1 = 0

    all_doslegs = open_json(sys.argv[2])
    lafabrique_doslegs = list(sorted(glob.glob(sys.argv[1])))
    scored = []
    for file in lafabrique_doslegs:
        print('======')
        print('======')
        print(file)
        me = None
        proc = open_json(file)
        proc_url_senat = proc.get('url_dossier_senat', '').replace('http://', 'https://').replace('/dossierleg/', '/dossier-legislatif/')
        for dos in all_doslegs:
            dos_url_senat = dos.get('url_dossier_senat', '').replace('http://', 'https://').replace('/dossierleg/', '/dossier-legislatif/')
            if dos_url_senat == proc_url_senat:
                me = dos
                break
        # look at a common url for AN after senat since the senat individualize their doslegs
        if not me:
            for dos in all_doslegs:
                if dos.get('url_dossier_assemblee') == proc.get('url_dossier_assemblee'):
                    me = dos
                    break
        if not me:
            missing += 1
            print(file)
            print('NO DOSLEGS FOUND:', proc['url_dossier_senat'])
            continue
        nok, ok = compare(proc, me)
        sum_ok += ok
        sum_nok += nok
        scored.append([file, nok, ok])

        if nok == 0:
            perfect += 1
        if nok <= 1:
            less_than_1 += 1

    print('-----')
    print('TOTAL:')
    print('MISSING DOSLEGS', missing, '/', len(lafabrique_doslegs))
    print('** PERFECT **', perfect, '/', len(lafabrique_doslegs))
    print('** NOK <= 1 **', less_than_1, '/', len(lafabrique_doslegs))
    print('NOK',sum_nok)
    print('OK', sum_ok)
    print('=>', (sum_ok/(sum_nok+sum_ok))*100)
    print()
    print('worst:')
    for file, nok, ok in sorted(scored, key=lambda x:x[1])[-5:]:
        print(file, nok, ok)


# missing steps
# /pjl09-113

# double cmp hemi
# pjl10-784
# pjl11-187 (ordering wtf)

# NOK 11
# ppl08-454
# ppl09-191
