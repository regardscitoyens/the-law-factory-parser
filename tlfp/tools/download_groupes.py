import sys

from lawfactory_utils.urls import download, enable_requests_cache

from .common import download_daily


def process(output_directory):
    for url in "2007-2012.nosdeputes", "2012-2017.nosdeputes", "2017-2022.nosdeputes", "www.nosdeputes", "www.nossenateurs":
        download_daily(
            "https://%s.fr/organismes/groupe/json" % url,
            '%s-groupes' % url,
            output_directory
        )
        download_daily(
            "https://%s.fr/%s/json" %
                (url, 'deputes' if 'deputes' in url else 'senateurs'),
            '%s.parlementaires' % url,
            output_directory
        )
    download_daily(
        'http://data.senat.fr/data/senateurs/ODSEN_HISTOGROUPES.json',
        'historique-groupes-senat',
        output_directory
    )


if __name__ == '__main__':
    enable_requests_cache()
    process(sys.argv[1])
