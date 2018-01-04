def get_previous_step(steps, curr_step_index):
    curr_step = steps[curr_step_index]

    # if 'nouv. lect depot' and last step failed, take last depot
    if curr_step.get('stage') == 'nouv. lect.' and curr_step.get('step') == 'depot' and \
        steps[curr_step_index-1].get('echec') == 'renvoi en commission':
        print('[parse_doslegs_texts] fetching last depot instead of last non-failed text')
        for i in reversed(range(curr_step_index)):
            if steps[i].get('step') == 'depot':
                return i

    for i in reversed(range(curr_step_index)):
        if not steps[i].get('echec') or steps[i].get('echec') == 'renvoi en commission':
            # do not take previous depot but hemicycle version instead if in the
            # middle of the procedure
            # TODO: this is not working well, find why and enable it
            # if i > 0 and steps[i].get('step') == 'depot' and steps[i-1].get('step') != 'depot':
            #    return i-1
            return i
