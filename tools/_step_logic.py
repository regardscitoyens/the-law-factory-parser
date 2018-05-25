
def use_old_procedure(step, dos=None):
    if dos and dos.get('use_old_procedure'):
        return True
    return (step.get("enddate", step.get("date", "9999-99-99")) or "9999-99-99") < "2009-03-01"


def should_ignore_commission_text(step, dos):
    return step.get('step') == 'commission' and (
        step.get('stage') == 'l. définitive' or (
        use_old_procedure(step, dos) and step['institution'] in ('senat', 'assemblee'))
    )


def is_one_of_the_initial_depots(steps, step_index):
    # Detect if the step is one of the multiple initial depot
    return step_index == 0 or (steps[step_index - 1].get('step') == steps[step_index].get('step') == 'depot')


def get_previous_step(steps, curr_step_index, is_old_procedure=False, get_depot_step=False):
    # is_old_procedure: Budget, Financement Sécurité Sociale, lois organique
    # get_depot_step: get the step the amendments are done on (including the depot steps)

    curr_step = steps[curr_step_index]

    if curr_step.get('stage') == 'l. définitive' and (
            (curr_step.get('step') == 'hemicycle' and not get_depot_step) or
            curr_step.get('step') == 'depot'
        ):
        # cf Constitution Article 45 alinéa 4 https://www.legifrance.gouv.fr/affichTexteArticle.do?idArticle=LEGIARTI000006527521&dateTexte=&categorieLien=cid
        print('[step_logic] l. définitive / %s: fetching last AN hemi or last CMP commission' % curr_step.get('step'))
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

        # the amendments are done on the depot text for a renvoi en commission
        if step.get('echec') == 'renvoi en commission':
            i -= 1 # we skip the commission step
            continue

        if not step.get('echec'):
            # for the old procedure, there's no text produced during the commission
            if (is_old_procedure or use_old_procedure(step)) and step.get('step') == 'commission' and step.get('stage') != 'CMP':
                continue

            # if a CMP hemi fail, we ignore the CMP commission
            if cmp_hemi_failed and step.get('stage') == 'CMP' and step.get('step') == 'commission' and curr_step.get('stage') != 'CMP':
                continue

            # do not take previous depot if it's not one of the initial depot
            if not get_depot_step and step.get('step') == 'depot' and not is_one_of_the_initial_depots(steps, i):
                continue

            return i
