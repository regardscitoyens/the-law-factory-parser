import sys

from legipy.services.law_service import LawService

from .common import download_daily


def download_lois_dites():
    return {l.id_legi: l.common_name for l in LawService().common_laws()}


def process(output_directory):
    return download_daily(download_lois_dites, 'lois_dites', output_directory)


if __name__ == '__main__':
    process(sys.argv[1])
