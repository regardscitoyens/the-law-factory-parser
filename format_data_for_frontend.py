import os, glob, sys, json, csv, random, shutil

from tools import json2arbo, prepare_articles, update_procedure, \
    prepare_amendements, prepare_interventions, reorder_interventions_and_correct_procedure


def project_header_template(dos_id, procedure):
    return """
<h1>Les données pour: "{long_title}"</h1>
<p>Les données mises à disposition dans ces répertoires sont celles utilisées par <a href="http://lafabriquedelaloi.fr/">La Fabrique de la Loi</a> pour visualiser "<a href="http://lafabriquedelaloi.fr/lois.html?loi={dos_id}">{long_title}</a>".</p>
<p>Elles ont été constituées par <a href="http://regardscitoyens.org">Regards Citoyens</a> à partir de <a href="http://nosdeputes.Fr/">NosDéputés.fr</a>, <a href="http://NosSénateurs.fr">NosSénateurs.fr<a/> et les sites du <a href="http://senat.fr/">Sénat</a> et de l'<a href="http://assemblee-nationale.fr">Assemblée nationale</a>. Elles sont réutilisables librement en <img src="http://www.nosdeputes.fr/images/opendata.png" alt="Open Data"/> sous la licence <a href="http://opendatacommons.org/licenses/odbl/">ODBL</a>.</p>
<p>Le répertoire <a href="procedure/"><img src="http://www.lafabriquedelaloi.fr/icons/folder.gif"/>&nbsp;procedure/</a> contient les données brutes au format JSON sur les textes, les interventions et les amendements à chaque étape de la procédure. Le répertoire <a href="viz/"><img src="http://www.lafabriquedelaloi.fr/icons/folder.gif"/>&nbsp;viz/</a> contient les fichiers utilisés par l'application.</p>
""".format(long_title=procedure.get('long_title'), dos_id=dos_id)


def process(dos, OUTPUT_DIR, skip_already_done=False):
    dos_id = dos.get('senat_id', dos.get('assemblee_id'))
    
    output_dir = os.path.join(OUTPUT_DIR, dos_id + '_tmp')
    final_output_dir = os.path.join(OUTPUT_DIR, dos_id)
    print('     writing to:', output_dir)

    if skip_already_done and os.path.exists(final_output_dir):
        print(' - already done')
        return

    shutil.rmtree(output_dir, ignore_errors=True)

    # add texte.json and write all the text files tree
    dos = json2arbo.process(dos, output_dir + '/procedure')

    json2arbo.mkdirs(output_dir + '/viz')
    articles_etapes = prepare_articles.process(dos)
    open(output_dir + '/viz/articles_etapes.json', 'w').write(json.dumps(articles_etapes, indent=2, sort_keys=True, ensure_ascii=True))

    procedure = update_procedure.process(dos, articles_etapes)

    print(' - process amendements')
    procedure = prepare_amendements.process(output_dir, procedure)

    print(' - re-order interventions and correct procedure dates')
    procedure = reorder_interventions_and_correct_procedure.process(output_dir, procedure)

    print(' - prepare interventions.json')
    prepare_interventions.process(output_dir, procedure)

    # remove intermediate data
    for step in procedure['steps']:
        for key in 'articles_completed', 'articles', 'texte.json':
            try:
                step.pop(key)
            except KeyError:
                pass

    # avoid duplicate titles
    if " de loi organique" in procedure['long_title']:
        procedure['short_title'] += " (texte organique)"

    open(os.path.join(output_dir, 'viz/procedure.json'), 'w').write(
        json.dumps(procedure, indent=2, sort_keys=True, ensure_ascii=False))

    open(os.path.join(output_dir, 'HEADER.html'), 'w').write(
        project_header_template(dos_id, procedure))

    shutil.rmtree(final_output_dir, ignore_errors=True)
    os.rename(output_dir, final_output_dir)

    print('  FINISHED -', final_output_dir)
