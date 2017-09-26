# quick script to produce a DOT file of the steps from a list of dosleg
# use "python steps_as_dot.py <path_to_json>| dot -Tpng > steps.png" to produce the diagram
import json, sys, os

if len(sys.argv) < 2:
    print('USAGE: `steps_as_dot.py <path_to_json>`')
    os.exit()

all_senat_jo = json.load(open(sys.argv[1]))

nodes_names_size = {}
step_trans = {}
steps_logs = ""
for dos in all_senat_jo:
    last_step = ''
    for step in dos.get('steps', []):
        step_name = '%s %s %s' % (step['stage'], step.get('institution'), step.get('step',''))
        # step_name = step['stage']
        # step_name = step['institution']
        if step_name != last_step:
            if last_step not in step_trans:
                step_trans[last_step] = {}
            step_trans[last_step][step_name] = step_trans[last_step].get(step_name, 0) + 1
            nodes_names_size[step_name] = nodes_names_size.get(step_name, set()).union(set([dos['url_dossier_senat']]))
            steps_logs += '%s->%s:%s\n' % (last_step, step_name, dos['url_dossier_senat'])
        last_step = step_name

dot_result = 'digraph g { '

nodes_names_i = 0
nodes_names = {}
def get_node_id(node):
    global nodes_names_i, nodes_names
    if node not in nodes_names:
        nodes_names[node] = nodes_names_i
        nodes_names_i += 1
    return nodes_names[node]

for prev, nexts in step_trans.items():
    if prev:
        prev_id = get_node_id(prev)
        for next, next_v in nexts.items():
            next_id = get_node_id(next)
            dot_result += '\n   %s -> %s [label="%s", penwidth="%d"];' % (
                prev_id, next_id, next_v, next_v // 150 + 1)

for name, id in nodes_names.items():
    dot_result += '\n %s [label="%s - %d", penwidth="%d"];' % (id, name, len(nodes_names_size[name]), len(nodes_names_size[name]) // 100 + 1)

dot_result += '\n}'

open('steps.log', 'w').write(steps_logs)

print(dot_result)
# open('steps.dot','w').write(dot_result)
