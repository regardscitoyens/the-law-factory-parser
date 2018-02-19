import sys, json, contextlib, io, os, traceback

from senapy.dosleg.parser import parse as senapy_parse
from anpy.dossier_like_senapy import parse as anpy_parse
from lawfactory_utils.urls import download, enable_requests_cache, clean_url

from tools.detect_anomalies import find_anomalies
from tools.json2arbo import mkdirs
from tools.download_groupes import process as download_groupes
from merge import merge_senat_with_an
import parse_doslegs_texts
import format_data_for_frontend


def download_senat(url):
    print('  [] download SENAT version')
    html = download(url).text
    print('  [] parse SENAT version')
    return senapy_parse(html, url)


def download_an(url, url_senat=False):
    print('  [] download AN version')
    resp = download(url)
    resp.encoding = 'Windows-1252'
    html = resp.text
    print('  [] parse AN version')
    # TODO: do both instead of first
    results = anpy_parse(html, url)
    if len(results) > 1:
        if url_senat:
            for result in results:
                if result.get('url_dossier_senat') == url_senat:
                    return result
        print('     WARNING: TOOK FIRST DOSLEG BUT THERE ARE %d OF THEM' % len(results))
    return results[0]


def are_same_doslegs(senat_dos, an_dos):
    # same dosleg url ?
    if an_dos['url_dossier_senat'] == senat_dos['url_dossier_senat']:
        return True
    # same first text  ?
    if senat_dos.get('steps') and an_dos.get('steps') \
        and senat_dos['steps'][0].get('source_url') == an_dos['steps'][0].get('source_url'):
        return True
    # it's not the same dosleg !
    return False


def _dump_json(data, filename):
    json.dump(data, open(filename, 'w'), ensure_ascii=False, indent=2, sort_keys=True)
    print('   DEBUG - dumped', filename)


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

    url_id = None
    if 'assemblee-nationale' in url:
        legi = url.split('.fr/')[1].split('/')[0]
        url_id = legi + url.split('/')[-1].replace('.asp', '')
    elif 'senat.fr' in url:
        url_id = url.split('/')[-1].replace('.html', '')

    mkdirs(os.path.join(api_dir, 'logs/'))
    logfile = os.path.join(api_dir, 'logs/' + url_id)

    print('[error] parsing', url, 'failed. Details in', logfile)
    open(logfile, 'w').write(log)


def process(API_DIRECTORY, url, disable_cache=True,
        debug_intermediary_files=False, only_promulgated=False):
    with log_print(io.StringIO()) as log:
        try:
            # Download senat version
            if not disable_cache:
                enable_requests_cache()
            if not url.startswith('http') and ('pjl' in url or 'ppl' in url):
                url = "http://www.senat.fr/dossier-legislatif/%s.html" % url

            print(' -= DOSLEG URL:', url, '=-')

            an_dos = None
            senat_dos = None

            if 'senat.fr' in url:
                senat_dos = download_senat(url)
                if not senat_dos:
                    print('  /!\ INVALID SENAT DOS')
                    return
                # Add AN version if there's one
                if 'url_dossier_assemblee' in senat_dos:
                    an_dos = download_an(senat_dos['url_dossier_assemblee'], senat_dos['url_dossier_senat'])
                    if 'url_dossier_senat' in an_dos:
                        assert are_same_doslegs(senat_dos, an_dos)
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

            print('        title:', dos.get('long_title'))
            find_anomalies([dos])

            if not dos.get('url_jo') and only_promulgated:
                print('    ----- passed: no JO link')
                return
            if dos.get('use_old_procedure') and False:
                print('    ----- passed: budget law')
                return

            if debug_intermediary_files:
                if an_dos:
                    _dump_json(an_dos, 'debug_an_dos.json')
                if senat_dos:
                    _dump_json(senat_dos, 'debug_senat_dos.json')
                _dump_json(dos, 'debug_dos.json')

            # download the groupes in case they are not there yet
            download_groupes(API_DIRECTORY)

            print('  [] parse the texts')
            dos_with_texts = parse_doslegs_texts.process(dos, debug_intermediary_files=debug_intermediary_files)

            print('  [] format data for the frontend')
            format_data_for_frontend.process(dos_with_texts, API_DIRECTORY)
        except Exception as e:
            # dump log for each failed doslegs in logs/
            dump_log(url, e, API_DIRECTORY, log)
            raise e

if __name__ == '__main__':
    API_DIRECTORY = sys.argv[1]
    url = sys.argv[2]
    disable_cache = '--enable-cache' not in sys.argv
    debug_intermediary_files = '--debug' in sys.argv
    only_promulgated = '--only-promulgated' in sys.argv
    process(API_DIRECTORY, url, disable_cache, debug_intermediary_files, only_promulgated)
