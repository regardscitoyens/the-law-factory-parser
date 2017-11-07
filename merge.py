import glob, json, sys, copy, os


def dedup_by_key(list, key, alt_key=None, alt_key2=None, verbose=False):
    uniqs = set()
    for el in list:
        v = el.get(key)
        if not v and alt_key:
            v = el.get(alt_key)
            if not v and alt_key2:
                v = el.get(alt_key2)
        if not v:
            yield el
            continue
        if v not in uniqs:
            yield el
            uniqs.add(v)
        elif verbose:
            print('dedup', v)


def date_is_after_2008_reform(date):
    # https://www.legifrance.gouv.fr/affichTexte.do?cidTexte=JORFTEXT000019237256&dateTexte=&categorieLien=id
    year, month, *rest = date.split('-')
    year, month = int(year), int(month)
    # return year >= 1996 and year <= 2016
    return year >= 2008
    # return year > 2008 or (year == 2008 and month >= 9) # we take september 2008


def merge(senat, an):
    dos = copy.deepcopy(senat)
    dos['steps'] = []
    for i, step in enumerate(senat['steps']):
        steps_to_add = []
        # get source_url from AN in priority
        if step.get('institution') == 'assemblee':
            if len(an['steps']) > i:
                an_step = an['steps'][i]
                if an_step.get('stage') == step.get('stage') \
                    and an_step.get('step') == step.get('step'):
                    steps_to_add.append(an['steps'][i])

                """
                try to find "holes":
                    - we are in an AN step
                    - next step is different
                    - a few steps later, it's the same !
                """
                if len(an['steps']) > i+1 and len(senat['steps']) > i+1:
                    next_step_an = an['steps'][i+1]
                    next_step = senat['steps'][i+1]
                    if next_step_an.get('stage') != next_step.get('stage') \
                        or next_step_an.get('step') != next_step.get('step'):

                        found_same_step_at = None
                        for j, next_an in enumerate(an['steps'][i+1:]):
                            if next_an.get('institution') != 'senat' and next_an.get('stage') == next_step.get('stage') \
                                and next_an.get('step') == next_step.get('step'):
                                found_same_step_at = j

                        if found_same_step_at is not None:
                            steps_to_add += an['steps'][i+1:i+1+j]

        if len(steps_to_add) == 0:
            steps_to_add = [step]

        dos['steps'] += steps_to_add
    return dos

""" TODO: proper test for merging
from pprint import pprint as pp
pp(merge(json.load(open('data/parsed/senat/pjl10-515')), json.load(open('data/parsed/an/13-accord-fiscal-dominique'))))
"""


SENAT_GLOB = sys.argv[1] # ex: 'senat_dossiers/*
AN_GLOB = sys.argv[2] # ex: 'an_dossiers/*'
OUTPUT_DIR = sys.argv[3]

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

all_senat = [json.load(open(f)) for f in glob.glob(SENAT_GLOB)]
all_senat = [x for x in all_senat if x and date_is_after_2008_reform(x.get('beginning','1900-0-0'))]
all_senat = [dos for dos in dedup_by_key(all_senat, 'url_dossier_senat')]

print('senat loaded', len(all_senat))

all_an = [json.load(open(f)) for f in glob.glob(AN_GLOB)]
all_an = [x for x in all_an if x]
# all_an = [x for x in all_an if x and date_is_after_2008_reform(x.get('beginning','1900-0-0'))]
# TODO: dedup by url_dossier_assemblee but multiple doslegs in assemblee pages
all_an = [dos for dos in dedup_by_key(all_an, 'url_dossier_senat')]

print('an loaded', len(all_an))

json.dump(all_senat, open(OUTPUT_DIR + 'all_senat.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(all_an, open(OUTPUT_DIR + 'all_an.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

"""
ALL = all_an + all_senat
print('ALL (before dedup)', len(ALL))
ALL = [x for x in dedup_by_key(ALL, 'url_dossier_assemblee')]
ALL = [x for x in dedup_by_key(ALL, 'url_dossier_senat')]
print('ALL (basic dedup)', len(ALL))
"""

all_an_hash_an = {an['url_dossier_assemblee']: an for an in all_an if 'url_dossier_assemblee' in an and an['url_dossier_assemblee']}
all_an_hash_se = {an['url_dossier_senat']: an for an in all_an if 'url_dossier_senat' in an and an['url_dossier_senat']}
matched, not_matched = [], []
not_matched_and_assemblee_id = []
for dos in all_senat:
    if dos['url_dossier_senat'] in all_an_hash_se:
        matched.append(merge(dos, all_an_hash_se[dos['url_dossier_senat']]))
    # look at a common url for AN after senat since the senat individualize their doslegs
    elif 'url_dossier_assemblee' in dos and dos['url_dossier_assemblee'] in all_an_hash_an:
        matched.append(merge(dos, all_an_hash_an[dos['url_dossier_assemblee']]))
    else:
        not_matched.append(dos)
        if 'assemblee_id' in dos:
            not_matched_and_assemblee_id.append(dos)

print()
print('match', len(matched))
print('no match', len(not_matched))
print('no match && assemblee_id', len(not_matched_and_assemblee_id))

json.dump(matched + not_matched, open(OUTPUT_DIR + 'all.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(matched, open(OUTPUT_DIR + 'matched.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(not_matched, open(OUTPUT_DIR + 'not_matched.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(not_matched_and_assemblee_id, open(OUTPUT_DIR + 'not_matched_and_assemblee_id.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)


"""
# only on senat => find all doslegs from all_senat that are not in all_an

all_an_urls = set([x['assemblee_id'] for x in all_an_converted])
all_senat_an_urls = set([x.get('assemblee_id') for x in all_senat])
print('strange stuff', len(all_senat_an_urls - all_an_urls))

# for x in all_senat_an_urls - all_an_urls: print(x)


# legislature seems not unique, assemblee id can change


json.dump(all_senat, open('all_senat.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
# json.dump(all_legi, open('all_legi.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(all_an, open('all_an.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(ALL, open('all.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(all_an_converted, open('all_an_converted.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

all_senat_jo = [dos for dos in all_senat if dos.get('end_jo')]

print('all_senat_jo', len(all_senat_jo))
json.dump(all_senat_jo, open('all_senat_jo.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
"""
