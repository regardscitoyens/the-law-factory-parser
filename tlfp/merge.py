import copy

from tlfp.tools.detect_anomalies import find_anomalies
from tlfp.tools._step_logic import should_ignore_commission_text, use_old_procedure

from lawfactory_utils.urls import validate_link_CC_decision


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


def merge_promulgation_steps(senat_step, an_step):
    step = {**senat_step}
    senat_url = senat_step.get('source_url')
    if not senat_url or 'jo_pdf' in senat_url and an_step.get('source_url'):
        step['source_url'] = an_step['source_url']
    if not senat_step.get('date') and an_step.get('date'):
        step['date'] = an_step['date']
    return step


def merge_senat_with_an(senat, an):
    """Takes a senat dosleg and an AN dosleg and returns a merged version"""
    dos = copy.deepcopy(senat)

    dos['url_dossier_assemblee'] = an['url_dossier_assemblee']
    dos['assemblee_slug'] = an['assemblee_slug']
    dos['assemblee_id'] = an['assemblee_id']
    dos['assemblee_legislature'] = an['assemblee_legislature']

    if ('url_jo' not in dos or 'jo_pdf' in dos['url_jo']) and 'url_jo' in an:
        dos['url_jo'] = an['url_jo']
        if not dos.get('end') and an.get('end'):
            dos['end'] = an['end']

    dos['steps'] = []
    an['steps'] = [s for s in an['steps'] if not should_ignore_commission_text(s, an)]

    def same_stage_step_instit(a, b):
        return a.get('stage') == b.get('stage') and a.get('step') == b.get('step') \
            and a.get('institution') == b.get('institution')

    empty_last_step = False
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
                    if an_step.get('source_url') and (
                      # In lecture définitive's dépot, if one source_url is an AN TA, it is probably the good one and should be kept if the other one is a PL
                      not (step.get('stage') == 'l. définitive' and step.get('step') == 'depot' and '/projets/pl' in an_step.get('source_url') and '/ta/ta' in step['source_url'])):
                        common_step['source_url'] = an_step.get('source_url')
                    if not common_step.get('date'):
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
            for an_index, an_step in enumerate(an['steps']):
                if same_stage_step_instit(an_step, step) and an_step.get('source_url'):
                    an_offset = an_index - i
                    if 'cmp_commission_other_url' in an_step:
                        if an_step['cmp_commission_other_url'] == step['source_url']:
                            step['cmp_commission_other_url'] = an_step['source_url']
                        else:
                            step['cmp_commission_other_url'] = an_step['cmp_commission_other_url']
                    elif step.get('source_url'):
                        if step['source_url'] != an_step['source_url']:
                            step['cmp_commission_other_url'] = an_step['source_url']
                    else:
                        step['source_url'] = an_step['source_url']
            if dos.get('url_jo') and not step.get('source_url'):
                print('[warning] [merge] empty CMP steps announced in Senate in a promulgated text but missing in the AN-side', dos['url_dossier_assemblee'])
                continue

        # Choose best CC url available
        if step.get('stage') == 'constitutionnalité' and not validate_link_CC_decision(step.get('source_url')):
            cc_an = [s.get('source_url') for s in an['steps'] if s.get('stage') == 'constitutionnalité']
            if validate_link_CC_decision(cc_an[0]):
                step['source_url'] = cc_an[0]

        # Choose best JO url available
        if step.get('stage') == 'promulgation':
            an_step_promulgation = [(i, s) for i, s in enumerate(an['steps']) if s.get('stage') == 'promulgation']
            if an_step_promulgation:
                an_index, an_step = an_step_promulgation[0]
                an_offset = an_index - i
                step = merge_promulgation_steps(step, an_step)

        # Only keep first empty consecutive step as next one to come
        if not dos.get('url_jo'):
            if step.get('source_url'):
                empty_last_step = False
            elif empty_last_step:
                break
            else:
                if not step.get('step') == 'commission' and use_old_procedure(step, dos):
                    empty_last_step = True

        if len(steps_to_add) == 0:
            steps_to_add = [step]

        dos['steps'] += steps_to_add

    dos = fix_an_cmp_step_url(dos, an)

    # ## SANITY CHECKS ## #

    # detect AN leftovers we didn't merge
    if len(an['steps']) > i + an_offset + 1:
        leftovers = an['steps'][an_index:]
        if not dos.get('url_jo'):
            dos['steps'] += leftovers
        else:
            print('[warning] [merge] some AN steps didn\'t get merged ( the last', len(leftovers), ')')

    # compare the number of anomalies before and after merging
    if find_anomalies([senat], verbose=False) < find_anomalies([dos], verbose=False) or \
       find_anomalies([an], verbose=False) < find_anomalies([dos], verbose=False):
        print('[warning] [merge] more anomalies in the steps after the merge:', dos['url_dossier_senat'])

    # verify number of the CMP steps didn't move while merging
    cmp_steps_in_merged_dos = len([1 for step in dos['steps'] if step.get('stage') == 'CMP'])
    cmp_steps_in_senat_dos = len([1 for step in senat['steps'] if step.get('stage') == 'CMP'])
    if cmp_steps_in_merged_dos != cmp_steps_in_senat_dos:
        # since we remove the Senate predicted CMP steps, CMP steps can disappear for live texts
        if dos.get('url_jo') or cmp_steps_in_merged_dos > cmp_steps_in_senat_dos:
            print('[warning] [merge] number of CMP steps changed', dos['url_dossier_senat'],
                  '(before:', cmp_steps_in_senat_dos, ', after:', cmp_steps_in_merged_dos, ')')

    return dos
