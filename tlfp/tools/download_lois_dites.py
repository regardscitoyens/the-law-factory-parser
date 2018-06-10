import sys

from legipy.services.law_service import LawService

from tlfp.tools.common import download_daily


def process(output_directory):
    return download_daily(
        lambda : {l.id_legi: l.common_name for l in LawService().common_laws()},
        'lois_dites',
        output_directory
    )


if __name__ == '__main__':
    process(sys.argv[1])
