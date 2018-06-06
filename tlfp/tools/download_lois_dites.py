import sys, os, time

from legipy.services.law_service import LawService

from .common import open_json, print_json


def process(output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    yesterday = time.time() - 86400
    dfile = 'lois_dites.json'
    destfile = os.path.join(output_directory, dfile)
    if not os.path.exists(destfile) or os.path.getmtime(destfile) < yesterday:
        common_laws = {l.id_legi: l.common_name for l in LawService().common_laws()}
        print_json(common_laws, destfile)
    else:
        common_laws = open_json(destfile)
    return common_laws


if __name__ == '__main__':
    process(sys.argv[1])
