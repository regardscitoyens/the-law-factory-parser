import sys, io, os, traceback

from senapy.dosleg.parser import parse as senapy_parse
from anpy.dossier_like_senapy import parse as anpy_parse
from lawfactory_utils.urls import download, enable_requests_cache, parse_national_assembly_url

from . import format_data_for_frontend
from . import parse_doslegs_texts
from .tools.detect_anomalies import find_anomalies
from .tools.json2arbo import mkdirs
from .tools.download_groupes import process as download_groupes
from .tools.download_lois_dites import process as download_lois_dites
from .tools.download_AN_opendata import process as download_AN_opendata
from .tools.common import debug_file, log_print
from .merge import merge_senat_with_an


class ParsingFailedException(Exception):
    def __init__(self, exception, logfile):
        super().__init__()
        self.root_exception = exception
        self.logfile = logfile


def download_senat(url, log=sys.stderr):
    print('  [] download SENAT version')
    resp = download(url)
    if resp.status_code != 200:
        print('WARNING: Invalid response -', resp.status_code)
        return
    html = resp.text
    print('  [] parse SENAT version')
    senat_dos = senapy_parse(html, url, logfile=log)
    debug_file(senat_dos, 'senat_dos.json')
    return senat_dos


def download_an(url, cached_opendata_an, url_senat=False, log=sys.stderr):
    print('  [] download AN version')
    print('  [] parse AN version')
    # TODO: do both instead of first
    results = anpy_parse(url, logfile=log, cached_opendata_an=cached_opendata_an)
    if not results:
        print('     WARNING: AN DOS NOT FOUND', url)
        return
    an_dos = results[0]
    if len(results) > 1:
        if url_senat:
            for result in results:
                if result.get('url_dossier_senat') == url_senat:
                    an_dos = result
                    break
        print('     WARNING: TOOK FIRST DOSLEG BUT THERE ARE %d OF THEM' % len(results))

    debug_file(an_dos, 'an_dos.json')
    return an_dos


def are_same_doslegs(senat_dos, an_dos):
    # same dosleg url ?
    if an_dos['url_dossier_senat'] == senat_dos['url_dossier_senat']:
        return True
    elif download(an_dos['url_dossier_senat']).status_code == 404:
        return True
    # same first text  ?
    if senat_dos.get('steps') and an_dos.get('steps') \
        and senat_dos['steps'][0].get('source_url') == an_dos['steps'][0].get('source_url'):
        return True
    # it's not the same dosleg !
    return False


def download_merged_dos(url, cached_opendata_an, log=sys.stderr):
    """find dossier from url and returns (the_merged_dosleg, AN_dosleg, SENAT_dosleg)"""
    if not url.startswith('http') and ('pjl' in url or 'ppl' in url or 'plfss' in url):
        url = "http://www.senat.fr/dossier-legislatif/%s.html" % url

    print(' -= DOSLEG URL:', url, '=-')

    dos = None
    an_dos = None
    senat_dos = None

    if 'senat.fr' in url:
        senat_dos = download_senat(url, log=log)
        if not senat_dos:
            print('  /!\ INVALID SENAT DOS')
            return None, None, None
        # Add AN version if there's one
        if 'url_dossier_assemblee' in senat_dos:
            an_dos = download_an(senat_dos['url_dossier_assemblee'], cached_opendata_an, senat_dos['url_dossier_senat'], log=log)
            if not an_dos:
                return senat_dos, None, senat_dos
            if 'url_dossier_senat' in an_dos:
                assert are_same_doslegs(senat_dos, an_dos)
            dos = merge_senat_with_an(senat_dos, an_dos)
        else:
            dos = senat_dos
    elif 'assemblee-nationale.fr' in url:
        dos = an_dos = download_an(url, cached_opendata_an, log=log)
        # Add senat version if there's one
        if an_dos and 'url_dossier_senat' in an_dos:
            senat_dos = download_senat(an_dos['url_dossier_senat'], log=log)
            if senat_dos:
                dos = merge_senat_with_an(senat_dos, an_dos)
    else:
        print(' INVALID URL:', url)
    return dos, an_dos, senat_dos


def dump_error_log(url, exception, api_dir, logdir, log):
    url_id = url.replace('/', '')
    if 'assemblee-nationale' in url:
        url_id = "%s-%s" % parse_national_assembly_url(url)
    elif 'senat.fr' in url:
        url_id = url.split('/')[-1].replace('.html', '')

    abs_dir = os.path.join(api_dir, logdir)
    mkdirs(abs_dir)
    abs_file = os.path.join(abs_dir, url_id)

    with open(abs_file, 'w') as f:
        f.write(log.getvalue())

    print('[error] parsing of', url, 'failed. Details in', abs_file)

    raise ParsingFailedException(exception, os.path.join(logdir, url_id))


def process(API_DIRECTORY, url):
    only_promulgated = '--only-promulgated' in sys.argv
    quiet = '--quiet' in sys.argv
    if '--enable-cache' in sys.argv:
        enable_requests_cache()

    dos = None
    with log_print(only_log=quiet) as log:
        try:
            print('======')
            print(url)

            # download the AN open data or just retrieve the last stored version
            opendata_an = download_AN_opendata(API_DIRECTORY)

            dos, an_dos, senat_dos = download_merged_dos(url, opendata_an, log=log)
            if not dos:
                raise Exception('Nothing found at %s' % url)

            find_anomalies([dos])

            if not dos.get('url_jo') and only_promulgated:
                print('    ----- passed: no JO link')
                return

            print('        title:', dos.get('long_title'))

            debug_file(dos, 'dos.json')

            # download the groupes in case they are not there yet
            download_groupes(API_DIRECTORY)

            # Add potential common name from Legifrance's "Lois dites"
            common_laws = download_lois_dites(API_DIRECTORY)
            if dos.get('legifrance_cidTexte') in common_laws and common_laws[dos['legifrance_cidTexte']].lower() not in dos['short_title'].lower():
                dos['loi_dite'] = common_laws[dos['legifrance_cidTexte']]

            print('  [] parse the texts')
            dos_with_texts = parse_doslegs_texts.process(dos)

            print('  [] format data for the frontend')
            format_data_for_frontend.process(dos_with_texts, API_DIRECTORY, log=log)
            return dos
        except KeyboardInterrupt as e:  # bypass the error log dump when doing Ctrl-C
            raise e
        except Exception as e:
            print(*traceback.format_tb(e.__traceback__), e, sep='', file=log)
            # dump log for each failed doslegs in logs/
            logdir = 'logs'
            if dos and not dos.get('url_jo'):
                logdir = 'logs-encours'
            dump_error_log(url, e, API_DIRECTORY, logdir, log)


if __name__ == '__main__':
    args = [arg for arg in sys.argv[1:] if '--' not in arg]
    url = args[0]
    API_DIRECTORY = args[1] if len(args) > 1 else 'data'
    process(API_DIRECTORY, url)
