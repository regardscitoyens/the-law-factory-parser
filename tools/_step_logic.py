

def get_previous_step(steps, curr_step_index, is_old_procedure=False, get_depot_step=False):
    # is_old_procedure: Budget, Financement Sécurité Sociale, lois organique
    # get_depot_step: Instead of real last step, get the step the amendements are done on

    curr_step = steps[curr_step_index]

    if curr_step.get('stage') == 'l. définitive' and curr_step.get('step') == 'hemicycle' and not get_depot_step:
        print('[step_logic] l. définitive / hemicycle: fetching last AN hemi or last CMP commission')
        for i in reversed(range(curr_step_index)):
            step = steps[i]
            if step.get('echec'):
                continue
            if step.get('stage') == 'CMP' and step.get('step') == 'commission':
                return i
            if step.get('institution') == 'assemblee' and step.get('stage') == 'nouv. lect.' and step.get('step') == 'hemicycle':
                return i
        else:
            raise Exception('[step_logic] l. définitive / depot: no good text found, this should never happen !')


    cmp_hemi_failed = False
    i = curr_step_index
    while i > 0:
        i -= 1
        step = steps[i]

        if step.get('stage') == 'CMP' and step.get('step') == 'hemicycle':
            # a CMP hemicycle previous step is the CMP commission
            if curr_step.get('stage') == 'CMP' and curr_step.get('step') == 'hemicycle':
                continue
            # if a CMP hemi fail, we mark it to ignore the commission text and the other CMP hemi
            if step.get('echec'):
                print('[step_logic] CMP hemicycle failed, we ignore the CMP commission')
                cmp_hemi_failed = True
            if cmp_hemi_failed:
                continue

        if not step.get('echec') or step.get('echec') == 'renvoi en commission':
            # the amendments are done on the depot text for a renvoi en commission
            if step.get('echec') == 'renvoi en commission':
                i -= 1 # we skip the commission step
                continue

            # for the old procedure, there's no text produced during the commission
            if is_old_procedure and step.get('step') == 'commission' and step.get('stage') != 'CMP':
                continue

            # if a CMP hemi fail, we ignore the CMP commission
            if cmp_hemi_failed and step.get('stage') == 'CMP' and step.get('step') == 'commission' and curr_step.get('stage') != 'CMP':
                continue

            # do not take previous depot if it's not one of the initial depot
            if not get_depot_step:
                if i > 0 and steps[i].get('step') == 'depot' and steps[i-1].get('step') != 'depot':
                    continue

            return i
