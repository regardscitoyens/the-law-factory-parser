# quick script to produce a DOT file of the steps from a list of dosleg
# use "python steps_as_dot.py <data_directory>| dot -Tpng > steps.png" to produce the diagram

# the XKCD font is available here: https://github.com/ipython/xkcd-font/tree/master/xkcd/build
import json, sys, os, random, glob


if len(sys.argv) < 2:
    print('USAGE: `steps_as_dot.py <path_to_json>`')
    sys.exit()

procedure_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'doc/valid_procedure.json')
procedure = json.load(open(procedure_file))

API_DIRECTORY = sys.argv[1]
all_senat_jo = [json.load(open(path)) for path \
                in glob.glob(os.path.join(API_DIRECTORY, '*/viz/procedure.json'))]
all_senat_jo = [dos for dos in all_senat_jo if dos.get('end_jo')]
# all_senat_jo = [x for x in json.load(open(sys.argv[1])) if len(x['steps']) > 2]
# all_senat_jo = random.sample(all_senat_jo, 5)

nodes_names_size = {}
step_trans = {}
steps_logs = ""
for dos in all_senat_jo:
    prev_step = None
    last_step = ''
    for step_i, step in enumerate(dos.get('steps', [])):
        step_name = ' • '.join((x for x in (step.get('stage'), step.get('institution')) if x))
        if "CMP" in step_name:
            step_name = "CMP"
        # step_name = step.get('stage')
        # step_name = step.get('institution')
        if step_name:
            if not (prev_step and prev_step.get('step') == 'depot' and step.get('step') == 'depot'):
                if last_step not in step_trans:
                    step_trans[last_step] = {}
                step_trans[last_step][step_name] = step_trans[last_step].get(step_name, 0) + 1
                nodes_names_size[step_name] = nodes_names_size.get(step_name, set()).union(set([dos.get('url_dossier_senat')]))
                steps_logs += '%s->%s:%s\n' % (last_step, step_name, dos.get('url_dossier_assemblee'))
            last_step = step_name
            prev_step = step

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
            if next_id == prev_id: continue

            incorrect = False #procedure.get(prev, {}).get(next, False) is False
            color = '#F44336' if incorrect else '#a5a5a5'

            dot_result += '\n   %s -> %s [label="%s", penwidth="%d", color="%s", fontcolor="%s"];' % (
                prev_id, next_id, next_v, next_v // 100 + 1, color, color)

def xpos(n):
    if "senat" in n:
        return 0
    if "assemblee" in n:
        return 2
    return 1

def ypos(n):
    if "promulgation" in n:
        return 0
    if "constitutionnalité" in n:
        return 1
    if "définitive" in n:
        if "hemicycle" in n:
            return 2
        return 3
    if "nouv." in n:
        res = 4
    elif "3ème" in n:
        res = 7
    elif "2ème" in n:
        res = 10
    elif "1ère" in n:
        res = 13
    elif "CMP" in n:
        res = 8.5
    if "commission" in n:
        return res + 1
    if "depot" in n:
        return res + 2
    return res

def clean(n):
    if "assemblee" in n:
        n = n.replace("assemblee", "AN")
    if "senat" in n:
        n = n.replace("senat", "Sénat")
    if "nouv. lect" in n:
        n = n.replace("nouv. lect.", "Nouvelle lecture")
    if "définitive" in n:
        n = n.replace("l. définitive", "Lecture définitive")
    if n == "CMP • CMP":
        return "CMP • commission"
    if n == "constitutionnalité • conseil constitutionnel":
        return "Conseil Constitutionnel"
    if "promulgation" in n:
        return "Promulgation JO"
    if "congrès" in n:
        return "Congrès"
    return n

for name, id in nodes_names.items():
    # add previous step, mockup
    # prev_id = id-1 if id > 0 else id + 1
    # dot_result += '\n   %s -> %s [label="prec", penwidth="1", color="green", fontcolor="green"];' % (
    #    id, prev_id)

    # generate node
    fillcolor = "#f3f3f3"
    if 'assemblee' in name:
        fillcolor = '#ced6ff6d'
    if 'senat' in name:
        fillcolor = '#f99b906d'
    if 'CMP' in name:
        fillcolor = '#e7dd9e6d'
    if 'constitutionnalité' in name:
        fillcolor = '#aeeaaa6d'
    if 'congrès' in name:
        fillcolor = '#dfb3f36d'
    dot_result += '\n %s [label="%s • %s", penwidth="%d", fillcolor="%s"];' % (
        id,
        clean(name),
        len(nodes_names_size[name]),
        len(nodes_names_size[name]) // 600 + 1,
        fillcolor)

if '1ère lecture • assemblee' in nodes_names:
    dot_result += ("""
      {
        rank=source; %s; %s;
      }
    """ % (get_node_id('1ère lecture • assemblee'), get_node_id('1ère lecture • senat')))

for stage in ['1ère lecture', '2ème lecture']:
    dot_result += ("""
      {
        rank=same; %s; %s;
      }
    """ % (get_node_id('%s • assemblee' % stage), get_node_id('%s • senat' % stage)))

dot_result += """
{
    rank=same; %s; %s; %s;
}
""" % (get_node_id('CMP'), get_node_id('3ème lecture • assemblee'), get_node_id('3ème lecture • senat'))

dot_result += """
{
    rank=same; %s; %s;
}
""" % (get_node_id('congrès • congrès'), get_node_id('constitutionnalité • conseil constitutionnel'))

dot_result += '\n}'

open('_steps.log', 'w').write(steps_logs)
open('steps_transitions.json', 'w').write(json.dumps(step_trans, ensure_ascii=False, indent=2, sort_keys=True))

print(dot_result)
# open('steps.dot','w').write(dot_result)


# improve layout: https://stackoverflow.com/questions/11588667/how-to-influence-layout-of-graph-items
