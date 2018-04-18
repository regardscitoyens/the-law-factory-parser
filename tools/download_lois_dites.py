import sys, os, time, json

from legipy.services import LawService


def process(output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    yesterday = time.time() - 86400
    dfile = 'lois_dites.json'
    destfile = os.path.join(output_directory, dfile)
    if not os.path.exists(destfile) or os.path.getmtime(destfile) < yesterday:
        common_laws = {l.id_legi: l.common_name for l in LawService().common_laws()}
        with open(destfile, 'w') as f:
            json.dump(common_laws, f)
    else:
        with open(destfile) as f:
            common_laws = json.load(f)
    return common_laws


if __name__ == '__main__':
    process(sys.argv[1])
