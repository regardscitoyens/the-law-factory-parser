# quick script to produce a DOT file of the steps from a list of dosleg
# use "python steps_as_dot.py <path_to_json>| dot -Tpng > steps.png" to produce the diagram
import json, sys, os, random


if len(sys.argv) < 2:
    print('USAGE: `steps_as_dot.py <path_to_json>`')
    os.exit()

all_senat_jo = [x for x in json.load(open(sys.argv[1])) if len(x['steps']) > 2]
# all_senat_jo = random.sample(all_senat_jo, 5)

nodes_names_size = {}
step_trans = {}
steps_logs = ""
for dos in all_senat_jo:
    last_step = ''
    for step_i, step in enumerate(dos.get('steps', [])):
        step_name = ' • '.join((x for x in (step.get('stage'), step.get('institution'), step.get('step','')) if x))
        # step_name = step.get('stage')
        if step_name:
            # step_name = step['institution']
            if step_name != last_step or True:
                if last_step not in step_trans:
                    step_trans[last_step] = {}
                step_trans[last_step][step_name] = step_trans[last_step].get(step_name, 0) + 1
                nodes_names_size[step_name] = nodes_names_size.get(step_name, set()).union(set([dos.get('url_dossier_senat')]))
                steps_logs += '%s->%s:%s\n' % (last_step, step_name, dos.get('url_dossier_assemblee'))
            last_step = step_name

dot_result = """digraph g {
    node  [style="rounded,filled,bold", shape=box, fontname="xkcd"];
    edge  [style=bold, fontname="xkcd"];
    ranksep=0;
"""

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
                prev_id, next_id, next_v, next_v // 400 + 1)

for name, id in nodes_names.items():
    fillcolor = "#f3f3f3"
    if 'assemblee' in name:
        fillcolor = '#B3E5FD'
    if 'senat' in name:
        fillcolor = '#f48fb1'
    if 'CMP' in name:
        fillcolor = '#FFD54F'
    dot_result += '\n %s [label="%s %s", penwidth="%d", fillcolor="%s"];' % (
        id, name, len(nodes_names_size[name]),
        len(nodes_names_size[name]) // 600 + 1,
        fillcolor)

if '1ère lecture • assemblee • depot' in nodes_names:
    dot_result += ("""
      {
        rank=source; %s; %s;
      }
    """ % (get_node_id('1ère lecture • assemblee • depot'), get_node_id('1ère lecture • senat • depot')))

dot_result += '\n}'

open('_steps.log', 'w').write(steps_logs)
open('steps_transitions.json', 'w').write(json.dumps(step_trans, ensure_ascii=False, indent=2, sort_keys=True))

print(dot_result)
# open('steps.dot','w').write(dot_result)


# improve layout: https://stackoverflow.com/questions/11588667/how-to-influence-layout-of-graph-items
