"""
Make one Git repo per bill and optionally upload it to gitlab
"""

"""
find .procedure -name 'A*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/A|/Article_|')'"' ; done |sh
find .procedure -name 'SS*' -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/SS|/SousSection_|')'"' ; done |sh
find .procedure -name 'S*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/S|/Section_|')'"' ; done |sh
find .procedure -name 'C*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/C|/Chapitre_|')'"' ; done |sh
find .procedure -name 'T*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/T|/Titre_|')'"' ; done |sh
find .procedure -name 'L*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/L|/Livre_|')'"' ; done |sh
find .procedure -name 'V*'  -type d | while read dir ; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/V|/Volume_|')'"' ; done |sh
"""

import glob
import os
import sys
import shutil
import shlex
from pathlib import Path

from tlfp.tools.common import open_json


def read_text(path):
    # TODO: format tables
    try:
        articles = open_json(os.path.dirname(path), os.path.basename(path))["articles"]
    except FileNotFoundError:
        return ""

    texte = ""
    for art in articles:
        texte += "# Article " + art["titre"] + "\n\n"
        for key in sorted(art["alineas"].keys()):
            if art["alineas"][key] != "":
                texte += art["alineas"][key] + "\n"
        texte += "\n"
    return texte


def call(cmd):
    code = os.system(cmd)
    if code != 0:
        raise Exception('"{}"" returned {}'.format(cmd, code))


def call_bash(cmd):
    call("bash -c " + shlex.quote(cmd))


GIT_REPOS_DIRECTORY = sys.argv[1]

for procedure_file in glob.glob("data/**/procedure.json", recursive=True):
    procedure = open_json(procedure_file)
    project_dir = os.path.dirname(os.path.dirname(procedure_file))

    git_dir = Path(GIT_REPOS_DIRECTORY) / procedure["id"]

    shutil.rmtree(str(git_dir), ignore_errors=True)
    os.makedirs(str(git_dir))

    remote_url = "http://git.regardscitoyens.org/parlement/{bill}.git)".format(
        bill=procedure["id"]
    )
    call_bash(
        "(cd %s;" % git_dir.absolute()
        + "; git init"
        + "; git remote add origin %s" % shlex.quote(remote_url)
    )

    for step in procedure["steps"]:
        # MSG=$(echo $line | awk -F ';' '{if ($8 == 1) print "Dépot du texte"; if ($8 != 1 && $11 != "depot" && $7 != "XX") print "Travaux en "$11", "$9;}');
        if step.get("step") == "depot":
            msg = "Dépot du texte"
        elif step.get("step") == "commission":
            msg = "Travaux en commission"
        elif step.get("step") == "hemicycle":
            msg = "Travaux en hemicycle"
        elif step.get("stage") == "promulgation":
            msg = "Promulgation"
        elif step.get("stage") == "constitutionnalité":
            msg = "Constitutionnalité"
        else:
            raise Exception("Unknown step: %s" % (str(step)))

        # AUTEUR=$(echo $line | awk -F ';' '{if ($8 == 1 && $6 ~ /pjl/) print "gouv"; else print $10;}');
        instit = step.get("institution")
        author_depot = step.get("auteur_depot")
        if instit == "gouvernement" or author_depot == "Gouvernement":
            author = "Gouvernement"
            author_email = "contact@pm.gouv.fr"
            gituser = "gouv"
        elif instit == "assemblee":
            author = author_depot or "Assemblée nationale"
            author_email = "contact@assemblee-nationale.fr"
            gituser = "assemblee"
        elif instit == "senat":
            author = author_depot or "Sénat"
            author_email = "contact@senat.fr"
            gituser = "senat"
        elif instit == "CMP":
            author = "Commission mixte paritaire"
            author_email = "contact@parlement.fr"
            gituser = "cmp"
        elif instit == "conseil constitutionnel":
            author = "Conseil Constitutionnel"
            author_email = " contact@conseil-constitutionnel.fr "
            gituser = "conseil_constitutionnel"
        elif instit == "congrès":
            author = "Congrès"
            author_email = "contact@assemblee-nationale.fr"  # ?
            gituser = "congrès"
        else:
            raise Exception("Unknown author: %s" % instit)

        # ID=$(echo $line | awk -F ';' '{print $7}')

        # DATE=$(echo $line | awk -F ';' '{print $14}')
        #  DATE=$(date --date="$DATE" -R);
        date = step.get("date")

        if "directory" not in step or "debats_order" not in step:
            continue

        texte_path = os.path.join(
            project_dir, "procedure", step.get("directory"), "texte/texte.json"
        )
        texte = read_text(texte_path)
        if texte:
            text_dest = git_dir / "texte"
            open(str(text_dest), "w").write(texte)

            #  echo $line | awk -F ';' '{print $2}' > texte/titre.txt

            r"""
            find texte -name *json -exec rm '{}' ';'
            find texte -name '*alineas' | sed 's/\(.*\)/mv "\1" "\1"/' | sed 's|[^/]*$|article.txt"|' | sh
            find texte -name 'article.txt' | while read dir; do echo mv '"'$dir'"' '"'$(echo $dir | sed 's|/article||')'"'; done | sh
            find texte -name '*titre' | sed 's/\(.*\)/mv "\1" "\1"/' | sed 's|[^/]*$|titre.txt"|' | sh
            find texte -size 0 -exec rm '{}' ';'
            """

            GIT_AUTHOR_NAME = GIT_COMMITER_NAME = author
            GIT_AUTHOR_EMAIL = GIT_COMMITER_EMAIL = author_email

            call_bash(
                "(cd %s" % git_dir.absolute()
                + "; git add -A .;"
                + "git config --local user.name %s;" % shlex.quote(GIT_AUTHOR_NAME)
                + "git config --local user.email %s;" % shlex.quote(GIT_AUTHOR_EMAIL)
                + " git commit --date=format:short:{} --author={} -m {} --allow-empty -q )".format(
                    shlex.quote(date),
                    shlex.quote(author + " <" + author_email + ">"),
                    shlex.quote(msg),
                )
            )

# TODO: GitLab API calls

# Upload to GitLab as a second step
# GITLAB_GROUP=$($GITLAB group list | grep -B 1 parlement | head -n 1 | sed 's/.* //')
# echo $GITLAB project create $(head -n 1 .procedure/procedure.csv  | awk -F ';' '{print " --description=\""$2"\" --name='$BILL'"}') --namespace-id=$GITLAB_GROUP --public=true | sh
# git push -u origin master
