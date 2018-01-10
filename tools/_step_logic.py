def get_previous_step(steps, curr_step_index):
    curr_step = steps[curr_step_index]

    # if 'nouv. lect depot' and last step failed, take last depot
    if curr_step.get('stage') == 'nouv. lect.' and curr_step.get('step') == 'depot' and \
        steps[curr_step_index-1].get('echec'):
        print('[parse_doslegs_texts] fetching last depot instead of last non-failed text')
        for i in reversed(range(curr_step_index)):
            if steps[i].get('step') == 'depot':
                return i

    if curr_step.get('stage') == 'l. définitive' and curr_step.get('step') == 'depot':
        print('[parse_doslegs_texts] l. définitive / depot: fetching last AN hemi or last CMP hemi')
        for i in reversed(range(curr_step_index)):
            step = steps[i]
            if step.get('echec'):
                continue
            if step.get('stage') == 'CMP' and step.get('step') == 'hemicycle':
                return i
            if step.get('institution') == 'assemblee' and step.get('stage') == 'nouv. lect.' and step.get('step') == 'hemicycle':
                return i
        else:
            raise Exception('[parse_doslegs_texts] l. définitive / depot: no good text found, this should never happen !')

    for i in reversed(range(curr_step_index)):
        if not steps[i].get('echec') or steps[i].get('echec') == 'renvoi en commission':
            # do not take previous depot but hemicycle version instead if in the
            # middle of the procedure
            # TODO: this is not working well, find why and enable it
            # if i > 0 and steps[i].get('step') == 'depot' and steps[i-1].get('step') != 'depot':
            #    return i-1
            return i
