import os, sys

from tlfp.tools.common import *


def list_get_or_none(arr, i):
    if 0 <= i < len(arr):
        return arr[i]

def process(OUTPUT_DIR, procedure):
    context = Context(OUTPUT_DIR)
    steps = procedure['steps']
    for step_i, step in enumerate(steps):

        if 'intervention_files' not in step:
            continue

        interventions_files_moved = []
        for interv_file in step['intervention_files']:
            interv_dirpath = os.path.join(context.sourcedir, 'procedure', step['directory'], 'interventions')
            interv = open_json(interv_dirpath, "%s.json" % interv_file)['seance'][0]['intervention']
            date = interv['date']

            prev_step = list_get_or_none(steps, step_i-1)
            next_step = list_get_or_none(steps, step_i+1)

            # if step date is later than intervention date, use intervention date
            if step.get('date') and step['date'] > date:
                if not prev_step or prev_step['date'] <= date:
                    step['date'] = date
                    print('INFO: change beginning date of', step_i, 'thanks to', interv_file)
                else:
                    print('ERROR: PB date of', interv_file, ', step begins', step['date'], 'and prev date ends', prev_step['enddate'])

            # if enddate is earlier than end of interventions, use interventions date
            if step.get('enddate') and step['enddate'] < date:
                # check that next step start_date is later than this intervention date
                if not next_step or next_step.get('in_discussion') or next_step['date'] >= date:
                    step['enddate'] = date
                    print('INFO: change end date of', step_i, 'thanks to', interv_file)
                else:
                    # the intervention is for a later step, we find the matching step and move the file
                    for test_step_i in range(step_i, len(steps)):
                        test_step = steps[test_step_i]

                        test_prev_step = list_get_or_none(steps, test_step_i - 1)
                        test_next_step = list_get_or_none(steps, test_step_i + 1)
                        if test_prev_step['stage'] == test_step['stage']:
                            test_prev_step = list_get_or_none(steps, test_step_i - 2)

                        # if the intervention date is between:
                        #    - previous step enddate
                        #    - next step start_date
                        #  => then move the intervention to the current step
                        # + check if we are still in the same chamber
                        if (not test_prev_step or test_prev_step['enddate'] <= date) \
                                and (not test_next_step or test_next_step.get('in_discussion') or date <= test_next_step['date']) \
                                and test_step['institution'] == step['institution']:
                            interventions_files_moved.append(interv_file)
                            print('INFO: moves ', interv_file,' from step', step_i, 'to step', test_step_i)

                            test_interv_dirpath = os.path.join(context.sourcedir, 'procedure', test_step['directory'], 'interventions')
                            if 'intervention_files' not in test_step:
                                test_step['has_interventions'] = True
                                test_step['intervention_files'] = []
                                os.makedirs(test_interv_dirpath)

                            test_step['intervention_files'].append(interv_file)
                            test_step['intervention_files'].sort()
                            os.rename(interv_dirpath + '/' + interv_file + '.json', test_interv_dirpath + '/' + interv_file + '.json')
                            break

        # replace step intervention files
        new_interventions_files = [file for file in step['intervention_files'] if file not in interventions_files_moved]
        step['has_interventions'] = len(new_interventions_files) > 0
        if new_interventions_files:
            step['intervention_files'] = new_interventions_files
        else:
            del step['intervention_files']
            os.rmdir(interv_dirpath)

    return procedure

if __name__ == '__main__':
    process(sys.argv[1], open_json(os.path.join(sys.argv[1], 'viz', 'procedure.json')))
