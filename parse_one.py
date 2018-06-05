import sys, contextlib, io, os, traceback

from senapy.dosleg.parser import parse as senapy_parse
from anpy.dossier_like_senapy import parse as anpy_parse
from lawfactory_utils.urls import download, enable_requests_cache

from tools.detect_anomalies import find_anomalies
from tools.json2arbo import mkdirs
from tools.download_groupes import process as download_groupes
from tools.download_lois_dites import process as download_lois_dites
from tools.download_AN_opendata import process as download_AN_opendata
from tools.common import debug_file
from merge import merge_senat_with_an
import parse_doslegs_texts
import format_data_for_frontend


def download_senat(url, log=sys.stderr, verbose=True):
    if verbose: print('  [] download SENAT version')
    html = download(url).text
    if verbose: print('  [] parse SENAT version')
    return senapy_parse(html, url, logfile=log)


def download_an(url, cached_opendata_an, url_senat=False, log=sys.stderr, verbose=True):
    if verbose: print('  [] download AN version')
    if verbose: print('  [] parse AN version')
    # TODO: do both instead of first
    results = anpy_parse(url, logfile=log, verbose=verbose, cached_opendata_an=cached_opendata_an)
    if not results:
        if verbose: print('     WARNING: AN DOS NOT FOUND', url)
        return
    if len(results) > 1:
        if url_senat:
            for result in results:
                if result.get('url_dossier_senat') == url_senat:
                    return result
        if verbose: print('     WARNING: TOOK FIRST DOSLEG BUT THERE ARE %d OF THEM' % len(results))
    return results[0]


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


def download_merged_dos(url, cached_opendata_an, log=sys.stderr, verbose=True):
    """find dossier from url and returns (the_merged_dosleg, AN_dosleg, SENAT_dosleg)"""
    if not url.startswith('http') and ('pjl' in url or 'ppl' in url or 'plfss' in url):
        url = "http://www.senat.fr/dossier-legislatif/%s.html" % url

    if verbose: print(' -= DOSLEG URL:', url, '=-')

    dos = None
    an_dos = None
    senat_dos = None

    if 'senat.fr' in url:
        senat_dos = download_senat(url, verbose=verbose, log=log)
        if not senat_dos:
            if verbose: print('  /!\ INVALID SENAT DOS')
            return None, None, None
        # Add AN version if there's one
        if 'url_dossier_assemblee' in senat_dos:
            an_dos = download_an(senat_dos['url_dossier_assemblee'], cached_opendata_an, senat_dos['url_dossier_senat'], verbose=verbose, log=log)
            if not an_dos:
                return senat_dos, None, senat_dos
            if 'url_dossier_senat' in an_dos:
                assert are_same_doslegs(senat_dos, an_dos)
            dos = merge_senat_with_an(senat_dos, an_dos)
        else:
            dos = senat_dos
    elif 'assemblee-nationale.fr' in url:
        an_dos = download_an(url, cached_opendata_an, verbose=verbose, log=log)
        # Add senat version if there's one
        if 'url_dossier_senat' in an_dos:
            senat_dos = download_senat(an_dos['url_dossier_senat'], log=log)
            dos = merge_senat_with_an(senat_dos, an_dos)
        else:
            dos = an_dos
    else:
        if verbose: print(' INVALID URL:', url)
    return dos, an_dos, senat_dos


@contextlib.contextmanager
def log_print(file):
    # capture all outputs to a log file while still printing it
    class Logger:
        def __init__(self, file):
            self.terminal = sys.stdout
            self.log = file
            self.only_log = False

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)

        def __getattr__(self, attr):
            return getattr(self.terminal, attr)

    logger = Logger(file)

    _stdout = sys.stdout
    _stderr = sys.stderr
    sys.stdout = logger
    sys.stderr = logger
    yield logger.log
    sys.stdout = _stdout
    sys.stderr = _stderr


def dump_error_log(url, exception, api_dir, log):
    log = log.getvalue() + '\n' + ''.join(traceback.format_tb(exception.__traceback__))

    url_id = url.replace('/', '')
    if 'assemblee-nationale' in url:
        legi = url.split('.fr/')[1].split('/')[0]
        url_id = legi + url.split('/')[-1].replace('.asp', '')
    elif 'senat.fr' in url:
        url_id = url.split('/')[-1].replace('.html', '')

    mkdirs(os.path.join(api_dir, 'logs'))
    logfile = os.path.join(api_dir, 'logs', url_id)

    print('[error] parsing', url, 'failed. Details in', logfile)
    open(logfile, 'w').write(log)


def process(API_DIRECTORY, url):
    disable_cache = '--enable-cache' not in sys.argv
    only_promulgated = '--only-promulgated' in sys.argv
    verbose = '--quiet' not in sys.argv
    if not disable_cache:
        enable_requests_cache()
    with log_print(io.StringIO()) as log:
        try:
            if verbose:
                print('======')
                print(url)

            # download the groupes in case they are not there yet
            opendata_an = download_AN_opendata(API_DIRECTORY)

            dos, an_dos, senat_dos = download_merged_dos(url, opendata_an, log=log, verbose=verbose)
            if not dos:
                return

            if verbose:
                print('        title:', dos.get('long_title'))
            find_anomalies([dos], verbose=verbose)

            if not dos.get('url_jo') and only_promulgated:
                if verbose:
                    print('    ----- passed: no JO link')
                return

            if not verbose:
                print()
                print('======')
                print(url)

            debug_file(an_dos, 'debug_an_dos.json')
            debug_file(senat_dos, 'debug_senat_dos.json')
            debug_file(dos, 'debug_dos.json')

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
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            # dump log for each failed doslegs in logs/
            dump_error_log(url, e, API_DIRECTORY, log)
            raise e


if __name__ == '__main__':
    args = [arg for arg in sys.argv[1:] if '--' not in arg]
    url = args[0]
    API_DIRECTORY = args[1] if len(args) > 1 else 'data'
    process(API_DIRECTORY, url)
