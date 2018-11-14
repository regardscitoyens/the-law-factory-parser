import os, shutil, io

from .tools import json2arbo, prepare_articles, update_procedure, \
    prepare_amendements, prepare_interventions, reorder_interventions_and_correct_procedure, \
    compute_stats, add_links
from .tools.common import debug_file, print_json


def project_header_template(procedure):
    return """
<h1>Les données pour: "{long_title}"</h1>
<p>Les données mises à disposition dans ces répertoires sont celles utilisées par <a href="https://lafabriquedelaloi.fr/">La Fabrique de la Loi</a> pour visualiser "<a href="https://lafabriquedelaloi.fr/lois.html?loi={dos_id}">{long_title}</a>".</p>
<p>Elles ont été constituées par <a href="https://regardscitoyens.org">Regards Citoyens</a> à partir de <a href="https://nosdeputes.Fr/">NosDéputés.fr</a>, <a href="https://NosSénateurs.fr">NosSénateurs.fr<a/> et les sites du <a href="https://www.senat.fr/">Sénat</a> et de l'<a href="http://www.assemblee-nationale.fr">Assemblée nationale</a>. Elles sont réutilisables librement en <img src="https://www.nosdeputes.fr/images/opendata.png" alt="Open Data"/> sous la licence <a href="https://opendatacommons.org/licenses/odbl/">ODBL</a>.</p>
<p>Le répertoire <a href="procedure/"><img src="/icons/folder.gif"/>&nbsp;procedure/</a> contient un dossier par étape de la procédure parlementaire pour ce projet, avec pour chacun lorsqu'elle existe la version finale du texte de loi à cette étape. Le répertoire <a href="viz/"><img src="/icons/folder.gif"/>&nbsp;viz/</a> contient les fichiers utilisés par l'application.</p>
""".format(long_title=procedure.get('long_title'), dos_id=procedure['id'])


def dump_success_log(output_dir, log):
    log = log.getvalue()
    logfile = os.path.join(output_dir, "parsing.log")
    with open(logfile, 'w') as f:
        f.write(log)
    textid = output_dir.split('/')[-1]
    api_dir = output_dir.replace('/' + textid, '')

    for err_dir in ('logs', 'logs-encours'):
        err_log = os.path.join(api_dir, err_dir, textid)
        if os.path.exists(err_log):
            os.remove(err_log)


def process(dos, OUTPUT_DIR, log=io.StringIO()):
    dos['id'] = dos.get('senat_id', dos.get('assemblee_id'))

    output_dir = os.path.join(OUTPUT_DIR, dos['id'] + '_tmp')
    final_output_dir = os.path.join(OUTPUT_DIR, dos['id'])
    print('     writing to:', dos['id'] + '_tmp')

    shutil.rmtree(output_dir, ignore_errors=True)

    # avoid duplicate titles
    if 'short_title' in dos:
        if " de loi organique" in dos['long_title']:
            dos['short_title'] += " (texte organique)"
    # AN doslegs have no short_titles
    else:
        dos['short_title'] = dos['long_title']

    debug_file(dos, 'before_add_links.json')
    dos = add_links.process(dos)

    # add texte.json and write all the text files tree
    debug_file(dos, 'before_json2arbo.json')
    dos = json2arbo.process(dos, output_dir + '/procedure')

    print(' - process article versions')
    json2arbo.mkdirs(os.path.join(output_dir, 'viz'))
    debug_file(dos, 'before_prepare_articles.json')
    articles_etapes = prepare_articles.process(dos)
    print_json(articles_etapes, os.path.join(output_dir, 'viz', 'articles_etapes.json'))

    procedure = update_procedure.process(dos, articles_etapes)

    print(' - process amendements & interventions')
    procedure = prepare_amendements.process(output_dir, procedure)

    print(' - re-order interventions and correct procedure dates')
    procedure = reorder_interventions_and_correct_procedure.process(output_dir, procedure)

    print(' - prepare interventions.json')
    prepare_interventions.process(output_dir, procedure)

    print(' - compute stats')
    debug_file(dos, 'before_stats.json')
    procedure['stats'] = compute_stats.process(output_dir, procedure)

    # remove temporary data
    for step in procedure['steps']:
        for key in 'articles_completed', 'articles', 'texte.json':
            try:
                step.pop(key)
            except KeyError:
                pass

    # remove temporary interventions files
    for step in procedure['steps']:
        step_directory = os.path.join(output_dir, 'procedure', step['directory'])
        shutil.rmtree(os.path.join(step_directory, 'interventions'), ignore_errors=True)
        # remove empty step directory
        if os.path.exists(step_directory) and not os.listdir(step_directory):
            os.rmdir(step_directory)

    print_json(procedure, os.path.join(output_dir, 'viz', 'procedure.json'))

    with open(os.path.join(output_dir, 'HEADER.html'), 'w') as f:
        f.write(project_header_template(procedure))

    if 'assemblee_id' in dos:
        an_output_dir = os.path.join(OUTPUT_DIR, dos['assemblee_id'])
        shutil.rmtree(an_output_dir, ignore_errors=True)
    shutil.rmtree(final_output_dir, ignore_errors=True)
    os.rename(output_dir, final_output_dir)

    print('  FINISHED -', dos['id'])

    dump_success_log(final_output_dir, log)
