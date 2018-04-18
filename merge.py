import copy

from tools.detect_anomalies import find_anomalies

# TODO: unused but can be useful in the futur
"""
def merge_previous_works_an(doslegs):
    # Takes the AN doslegs and merge those that goes over multiple legislature with
    # the previous ones
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
"""

def fix_an_cmp_step_url(senat, an):
    # detect missing AN CMP step in senat data
    dos = copy.deepcopy(senat)

    # if CMP.assemblee.hemicycle is empty in senat data but ok in AN data
    # complete from AN data
    an_cmp_step_from_senat = [i for i, step in enumerate(senat['steps']) if
        step.get('stage') == 'CMP' and step.get('institution') == 'assemblee']
    an_cmp_step_from_an = [i for i, step in enumerate(an['steps']) if
        step.get('stage') == 'CMP' and step.get('institution') == 'assemblee']
    if an_cmp_step_from_an:
        if an_cmp_step_from_senat:
            dos['steps'][an_cmp_step_from_senat[0]]['source_url'] = \
                an['steps'][an_cmp_step_from_an[0]].get('source_url')

    return dos


def merge_senat_with_an(senat, an):
    """Takes a senat dosleg and an AN dosleg and returns a merged version"""
    dos = copy.deepcopy(senat)

    dos['url_dossier_assemblee'] = an['url_dossier_assemblee']

    if ('url_jo' not in dos or 'jo_pdf' in dos['url_jo']) and 'url_jo' in an:
        dos['url_jo'] = an['url_jo']

    dos['steps'] = []

    def same_stage_step_instit(a, b):
        return a.get('stage') == b.get('stage') and a.get('step') == b.get('step') \
            and a.get('institution') == b.get('institution')

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
            if len(an['steps']) > an_index and an_index >= 0:
                an_step = an['steps'][an_index]

                # get data from AN even if there's data on the senat side
                if same_stage_step_instit(an_step, step):
                    # only take source_url from the AN, we've got better infos for now
                    # from the senat
                    common_step = copy.deepcopy(step)
                    common_step['source_url'] = an_step.get('source_url')
                    if 'date' not in common_step:
                        common_step['date'] = an_step.get('date')
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

        # CMP commission: get extra urls from AN side if there's a different one
        if step.get('stage') == 'CMP' and step.get('step') == 'commission':
            an_index = i + an_offset
            if len(an['steps']) > an_index and an_index > 0:
                an_step = an['steps'][an_index]
                if same_stage_step_instit(an_step, step):
                    if 'cmp_commission_other_url' in an_step:
                        if an_step['cmp_commission_other_url'] == step['source_url']:
                            step['cmp_commission_other_url'] = an_step['source_url']
                        else:
                            step['cmp_commission_other_url'] = an_step['cmp_commission_other_url']
                    elif step.get('source_url'):
                        if step['source_url'] != an_step['source_url']:
                            step['cmp_commission_other_url'] = an_step['source_url']
                    elif an_step['source_url']:
                        step['source_url'] = an_step['source_url']

        if step.get('stage') == 'promulgation' and (not step.get('source_url') or 'jo_pdf' in step['source_url']):
            an_step_promulgation = [s for s in an['steps'] if s.get('stage') == 'promulgation']
            if an_step_promulgation and an_step_promulgation[0]['source_url']:
                step['source_url'] = an_step_promulgation[0]['source_url']

        if len(steps_to_add) == 0:
            steps_to_add = [step]

        dos['steps'] += steps_to_add

    dos = fix_an_cmp_step_url(dos, an)

    if find_anomalies([senat], verbose=False) < find_anomalies([dos], verbose=False) or \
        find_anomalies([an], verbose=False) < find_anomalies([dos], verbose=False):
        print('REGRESSION DURING MERGE (ANOMALIES NUMBER):', dos['url_dossier_senat'])
    if len([1 for step in dos['steps'] if step.get('stage') == 'CMP']) \
        != len([1 for step in senat['steps'] if step.get('stage') == 'CMP']):
        print('REGRESSION DURING MERGE (MORE CMP STEPS):', dos['url_dossier_senat'])
    return dos
