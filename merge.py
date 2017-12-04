import glob, json, sys, copy, os

from lawfactory_utils.urls import clean_url
from tools.detect_anomalies import find_anomalies

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


def is_after_13_legislature(dos):
    try:
        legislature = int(dos['url_dossier_assemblee'].split('.fr/')[1].split('/')[0])
        return legislature >= 13
    except:
        pass
    return False


def date_is_after_2008_reform(date):
    # https://www.legifrance.gouv.fr/affichTexte.do?cidTexte=JORFTEXT000019237256&dateTexte=&categorieLien=id
    year, month, *rest = date.split('-')
    year, month = int(year), int(month)
    # return year >= 1996 and year <= 2016
    return year >= 2008
    # return year > 2008 or (year == 2008 and month >= 9) # we take september 2008


def merge_previous_works_an(doslegs):
    """
    Takes the AN doslegs and merge those that goes over multiple legislature with
    the previous ones
    """
    all_an_hash_an = {an['url_dossier_assemblee']: an for an in all_an if 'url_dossier_assemblee' in an and an['url_dossier_assemblee']}
    
    merged_dos_urls = set()
    for dos in doslegs:
        if dos['url_dossier_assemblee'] not in merged_dos_urls:
            try:
                legislature = int(dos['url_dossier_assemblee'].split('.fr/')[1].split('/')[0])
            except:
                print("INVALID URL AN -", dos['url_dossier_assemblee'])
                continue

            current_last_dos = dos
            for i in (1, 2, 3, 4):
                if dos.get('previous_works'):
                    older_url = dos['url_dossier_assemblee'].replace(str(legislature), str(legislature - i))
                    if older_url in all_an_hash_an:
                        older_dos = all_an_hash_an[older_url]

                        # remove promulgation step
                        if older_dos['steps'] and older_dos['steps'][-1].get('stage') == 'promulgation':
                            older_dos['steps'] = older_dos['steps'][:-1]

                        if dos['steps'] and older_dos['steps'] and older_dos['steps'][-1]['source_url'] == dos['steps'][0]['source_url']:
                            dos['steps'] = older_dos['steps'][:-1] + dos['steps']
                        elif dos['steps'] and len(older_dos['steps']) > 1 and older_dos['steps'][-2]['source_url'] == dos['steps'][0]['source_url']:
                            dos['steps'] = older_dos['steps'][:-2] + dos['steps']
                        else:
                            dos['steps'] = older_dos['steps'] + dos['steps']
                        merged_dos_urls.add(older_url)

                        if 'url_dossier_senat' in older_dos and not 'url_dossier_senat' in dos:
                            dos['url_dossier_senat'] = older_dos['url_dossier_senat']

                        current_last_dos = older_dos

    print(len(merged_dos_urls), 'AN doslegs merged with previous ones')

    return [dos for dos in doslegs if dos.get('url_dossier_assemblee') not in merged_dos_urls]


def merge(senat, an):
    """Takes a senat dosleg and an AN dosleg and returns a merged version"""
    dos = copy.deepcopy(senat)

    dos['url_dossier_assemblee'] = an['url_dossier_assemblee']

    dos['steps'] = []

    def same_stage_step_instit(a, b):
        return a.get('stage') == b.get('stage') and a.get('step') == b.get('step') \
            and a.get('institution') == b.get('institution')

    # TODO: detect CMP.hemicycle and do re-ordering as a pre-processing step
    # also detect missing AN CMP step in senat data

    an_offset = 0
    for i, step in enumerate(senat['steps']):
        steps_to_add = []

        # generate an offset when steps are missing on the AN side
        if step.get('institution') == 'senat':
            an_index = i + an_offset
            if len(an['steps']) > an_index and an_index > 0:
                an_step = an['steps'][an_index]
                if not same_stage_step_instit(an_step, step):
                    found_same_step_at = None
                    for j, next_senat in enumerate(senat['steps'][i:]):
                        if same_stage_step_instit(next_senat, an_step) \
                            and next_senat.get('source_url') == an_step.get('source_url'):
                            found_same_step_at = j
                            break
                    if found_same_step_at:
                        an_offset -= found_same_step_at

        # complete senat data from AN
        if step.get('institution') == 'assemblee':
            an_index = i + an_offset
            if len(an['steps']) > an_index and an_index > 0:
                an_step = an['steps'][an_index]

                # get data from AN even if there's data on the senat side
                if same_stage_step_instit(an_step, step):
                    # only take source_url from the AN, we've got better infos for now
                    # from the senat
                    common_step = copy.deepcopy(step)
                    common_step['source_url'] = an_step.get('source_url')
                    steps_to_add.append(common_step)

                    """
                    try to find "holes":
                        - we are in an AN step
                        - next step is different
                        - a few steps later, it's the same !
                    """
                    if len(an['steps']) > an_index+1 and len(senat['steps']) > i+1:
                        next_step_an = an['steps'][an_index+1]
                        next_step = senat['steps'][i+1]
                        if not same_stage_step_instit(next_step_an, next_step):
                            found_same_step_at = None
                            for j, next_an in enumerate(an['steps'][an_index+1:]):
                                if next_an.get('institution') != 'senat' and same_stage_step_instit(next_an, next_step):
                                    found_same_step_at = j
                                    break

                            if found_same_step_at is not None:
                                steps_to_add = an['steps'][an_index:an_index+j+1]
                                an_offset += found_same_step_at

        if len(steps_to_add) == 0:
            steps_to_add = [step]

        dos['steps'] += steps_to_add

    if find_anomalies([senat], verbose=False) < find_anomalies([dos], verbose=False) or \
        find_anomalies([an], verbose=False) < find_anomalies([dos], verbose=False):
        print('REGRESSION DURING MERGE:', dos['url_dossier_senat'])
    return dos


""" TODO: proper test for merging
from pprint import pprint as pp

# strange CMP.commission double
pp(merge(json.load(open('data/parsed/senat/pjl13-215')), json.load(open('data/parsed/an/14-collectif-budgetaire-2013'))))

# strange CMP.hemicycle overwrite: assemblee CMP url stay void
pp(merge(json.load(open('data/parsed/senat/pjl11-187')), json.load(open('data/parsed/an/13-limite-age-magistrats-ordre-judiciaire'))))

# complete AN urls
# pp(merge(json.load(open('data/parsed/senat/pjl11-497')), json.load(open('data/parsed/an/14-accord-serbie-cooperation-policiere'))))

# complete AN steps
# pp(merge(json.load(open('data/parsed/senat/pjl08-248')), json.load(open('data/parsed/an/13-kenya-imposition-fraude'))))
# pp(merge(json.load(open('data/parsed/senat/pjl10-515')), json.load(open('data/parsed/an/13-accord-fiscal-dominique'))))

sys.exit()
# """


SENAT_GLOB = sys.argv[1] # ex: 'senat_dossiers/*
AN_GLOB = sys.argv[2] # ex: 'an_dossiers/*'
OUTPUT_DIR = sys.argv[3]

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print('loading senat...')
all_senat = [json.load(open(f)) for f in glob.glob(SENAT_GLOB)]
all_senat = [x for x in all_senat if x and date_is_after_2008_reform(x.get('beginning','1900-0-0'))]
all_senat = [dos for dos in dedup_by_key(all_senat, 'url_dossier_senat')]

print('senat loaded', len(all_senat))
print('  - anomalies', find_anomalies(all_senat, verbose=False)) 
print()


print('loading AN...')
all_an = [json.load(open(f)) for f in glob.glob(AN_GLOB)]
all_an = [x for x in all_an if x]
# all_an = [x for x in all_an if x and date_is_after_2008_reform(x.get('beginning','1900-0-0'))]
# TODO: dedup by url_dossier_assemblee but multiple doslegs in assemblee pages
all_an = merge_previous_works_an(all_an)
all_an = [dos for dos in all_an if is_after_13_legislature(dos)]
all_an = [dos for dos in dedup_by_key(all_an, 'url_dossier_senat')]

print('an loaded', len(all_an))
print('  - anomalies', find_anomalies(all_an, verbose=False)) 
print()


print('merging....')
all_an_hash_an = {clean_url(an['url_dossier_assemblee']): an for an in all_an if 'url_dossier_assemblee' in an and an['url_dossier_assemblee']}
all_an_hash_se = {clean_url(an['url_dossier_senat']): an for an in all_an if 'url_dossier_senat' in an and an['url_dossier_senat']}
all_an_hash_legifrance = {clean_url(an['url_jo']): an for an in all_an if 'url_jo' in an and an['url_jo']}
matched, not_matched = [], []
not_matched_and_assemblee_id = []
an_not_matched = all_an

for dos in all_senat:
    clean_senat = clean_url(dos['url_dossier_senat'])
    clean_an = clean_url(dos['url_dossier_assemblee']) if 'url_dossier_assemblee' in dos else None
    clean_legi = clean_url(dos['url_jo']) if 'url_jo' in dos else None

    def merge_an_dos(dos, an):
        global an_not_matched
        matched.append(merge(dos, an))
        an_not_matched = [an2 for an2 in an_not_matched if an != an2]

    if clean_senat in all_an_hash_se:
        merge_an_dos(dos, all_an_hash_se[clean_senat])
    # look at a common url for AN after senat since the senat individualize their doslegs
    elif clean_an and clean_an in all_an_hash_an:
        merge_an_dos(dos, all_an_hash_an[clean_an])
    elif clean_legi and clean_legi in all_an_hash_legifrance:
        merge_an_dos(dos, all_an_hash_legifrance[clean_legi])
    else:
        not_matched.append(dos)
        if 'assemblee_id' in dos:
            not_matched_and_assemblee_id.append(dos)

ALL = matched + not_matched + an_not_matched

print()
print('match (senat)', len(matched))
print('no match (senat)', len(not_matched))
print('no match (senat) && assemblee_id', len(not_matched_and_assemblee_id))
print('  - anomalies (senat merged)', find_anomalies(matched+not_matched, verbose=False)) 
print('no match (AN)', len(an_not_matched))
print('  - anomalies (AN)', find_anomalies(an_not_matched, verbose=False)) 
print('all (matched and not matched)', len(ALL))
print('  - anomalies (ALL)', find_anomalies(ALL, verbose=False)) 

json.dump(all_senat, open(OUTPUT_DIR + 'all_senat.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(all_an, open(OUTPUT_DIR + 'all_an.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(ALL, open(OUTPUT_DIR + 'all.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(matched, open(OUTPUT_DIR + 'matched.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(not_matched, open(OUTPUT_DIR + 'not_matched.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
json.dump(not_matched_and_assemblee_id, open(OUTPUT_DIR + 'not_matched_and_assemblee_id.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

print()
print('output in', OUTPUT_DIR, 'have fun !')