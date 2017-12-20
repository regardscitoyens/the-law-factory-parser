import sys

from senapy.dosleg.parser import parse as senapy_parse
from anpy.dossier_like_senapy import parse as anpy_parse
from lawfactory_utils.urls import download, enable_requests_cache, clean_url

from merge import merge_senat_with_an
import parse_doslegs_texts
import format_data_for_frontend


def download_senat(url):
    print('  [] download SENAT version')
    html = download(url).text
    print('  [] parse SENAT version')
    return senapy_parse(html, url)


def download_an(url):
    print('  [] download AN version')
    html = download(url).text
    print('  [] parse AN version')
    # TODO: do both instead of first
    return anpy_parse(html, url)[0]


def process(API_DIRECTORY, url, disable_cache=False):
    # Download senat version
    if not disable_cache:
        enable_requests_cache()
    if not url.startswith('http') and ('pjl' in url or 'ppl' in url):
        url = "http://www.senat.fr/dossier-legislatif/%s.html" % url

    print(' -= DOSLEG URL:', url, '=-')

    if 'senat.fr' in url:
        senat_dos = download_senat(url)
        if not senat_dos:
            print('  /!\ INVALID SENAT DOS')
            return
        # Add AN version if there's one
        if 'url_dossier_assemblee' in senat_dos:
            an_dos = download_an(senat_dos['url_dossier_assemblee'])
            dos = merge_senat_with_an(senat_dos, an_dos)
        else:
            dos = senat_dos
    elif 'assemblee-nationale.fr' in url:
        an_dos = download_an(url)
        # Add senat version if there's one
        if 'url_dossier_senat' in an_dos:
            senat_dos = download_senat(an_dos['url_dossier_senat'])
            dos = merge_senat_with_an(senat_dos, an_dos)
        else:
            dos = an_dos
    else:
        print(' INVALID URL:', url)
        return

    if not dos.get('url_jo'):
        print('    ----- passed: no JO link')
        return
    if dos.get('use_old_procedure'):
        print('    ----- passed: budget law')
        return

    print('  [] parse the texts')
    dos_with_texts = parse_doslegs_texts.process(dos)

    print('  [] format data for the frontend')
    format_data_for_frontend.process(dos_with_texts, API_DIRECTORY)

if __name__ == '__main__':
    API_DIRECTORY = sys.argv[1]
    url = sys.argv[2]
    disable_cache = sys.argv[3] == '--disable-cache' if len(sys.argv) > 3 else False
    process(API_DIRECTORY, url, disable_cache)
