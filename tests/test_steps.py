"""
Tests all the little subtilities of the steps
"""

import sys, os, json
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tlfp.tools._step_logic import get_previous_step


def name(i):
    if i is None:
        return None
    return '_'.join((x for x in (str(i).zfill(2), steps[i].get('stage'), steps[i].get('institution'), steps[i].get('step','')) if x))


proc = json.load(open(os.path.join(TESTS_DIR, 'ressources/pjl12-688.json')))
steps = proc['steps']

# simple commission -> depot initial
assert get_previous_step(steps, 1) == 0

# lect. def. hemi -> nouv. lect AN hemicycle text
assert get_previous_step(steps, 16) == 11
# lect. def. hemi -> lect. def. depot (we want the real text number)
assert get_previous_step(steps, 16, get_depot_step=True) == 15
# lect. def. depot -> nouv. lect AN hemicycle text
assert get_previous_step(steps, 15) == 11
# lect. def. depot -> nouv. lect AN hemicycle text
assert get_previous_step(steps, 15, get_depot_step=True) == 11

# Aprés l'échec en commission qui a suivi le renvoi en commission, les amendements sont posés
# sur le texte de depot (le texte voté a l'AN)
assert get_previous_step(steps, 7, get_depot_step=True) == 3
# Pour la complétion des articles, il faut prendre le texte voté à l'AN ou celui du renvoi en comm
assert get_previous_step(steps, 7) == 2


proc = json.load(open(os.path.join(TESTS_DIR, 'ressources/ppl09-682.json')))
steps = proc['steps']

# (CMP hemicycle echec) Nouv. lect. AN com -> 2eme lect. AN hemi
assert get_previous_step(steps, 16, get_depot_step=True) == 15
assert get_previous_step(steps, 16) == 11

"""
# debug utils
correct = {name(i): name(get_previous_step(steps, i, is_old_procedure=False)) for i, step in enumerate(steps)}
print(json.dumps(correct, indent=2, sort_keys=True, ensure_ascii=False))
correct = {name(i): name(get_previous_step(steps, i, is_old_procedure=False, get_depot_step=True)) for i, step in enumerate(steps)}
print(json.dumps(correct, indent=2, sort_keys=True, ensure_ascii=False))
"""
