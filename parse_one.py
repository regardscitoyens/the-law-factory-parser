import sys

from senapy.dosleg.parser import parse as senapy_parse
from anpy.dossier_like_senapy import parse as anpy_parse
from lawfactory_utils.urls import download, enable_requests_cache, clean_url

from merge import merge_senat_with_an
import parse_doslegs_texts
import format_data_for_frontend

def process(url, API_DIRECTORY):
    # Download senat version
    enable_requests_cache() # TODO: make this optional
    if not url.startswith('http'):
        url = "http://www.senat.fr/dossier-legislatif/%s.html" % url

    print('  [] download SENAT version')
    html = download(url).text
    print('  [] parse SENAT version')
    senat_dos = senapy_parse(html, url)

    # Add AN version if there's one
    if 'url_dossier_assemblee' in senat_dos:
        an_url = senat_dos['url_dossier_assemblee']
        print('  [] download AN version')
        html = download(an_url).text
        print('  [] parse AN version')
        an_dos = anpy_parse(html, an_url)
        an_dos = an_dos[0] # TODO: detect which dos is the good one
        print('  [] merge AN and SENAT version')
        dos = merge_senat_with_an(senat_dos, an_dos)
    else:
        dos = senat_dos

    print('  [] parse the texts')
    dos_with_texts = parse_doslegs_texts.process(dos)

    print('  [] format data for the frontend')
    format_data_for_frontend.process(dos_with_texts, API_DIRECTORY)

if __name__ == '__main__':
    url = sys.argv[1]
    API_DIRECTORY = sys.argv[2]
    process(url, API_DIRECTORY)
