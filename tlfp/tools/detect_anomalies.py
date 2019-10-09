import sys, os

from .common import open_json


procedure_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valid_procedure.json')
procedure = open_json(procedure_file)

def find_anomalies(dossiers, verbose=True):
    anomalies = 0
    for dos in dossiers:
        prev_step = ''
        for step in dos['steps']:
            step_name = ' • '.join((x for x in (step.get('stage'), step.get('institution'), step.get('step','')) if x))
            if procedure.get(prev_step, {}).get(step_name, False) is False:
                if verbose:
                    print('INCORRECT', prev_step, '->', step_name)
                    print(dos.get('url_dossier_senat'), '|',dos.get('url_dossier_assemblee'))
                    print()
                anomalies += 1

            #print(step_name, '      \t\t\t\t===>>', procedure.get(prev_step, {}).get(step_name))

            prev_step = step_name

    if verbose and anomalies:
        print(anomalies, 'anomalies (', len(dossiers), 'doslegs)')
    return anomalies

"""
TODO:
 - anomalies liens: /leg/tas for textes sénat
"""

if __name__ == '__main__':
    if not os.isatty(0):
        import json
        dossiers = json.loads(sys.stdin.read())
        if type(dossiers) is not list:
            dossiers = [dossiers]
    else:
        dossiers = open_json(sys.argv[1])
    find_anomalies(dossiers)
