import sys, json, time

from lawfactory_utils.urls import clean_url

from bs4 import BeautifulSoup
import requests, requests_cache

requests_cache.install_cache('texts_cache')


sys.path.append('deprecated/scripts/collectdata')
import parse_texte


def download(url, retry=5):
    try:
        return requests.get(url)
    except requests.exceptions.ConnectionError as e:
        if retry:
            time.sleep(1)
            return download(url, retry-1)
        raise e


def test_status(url):
    resp = download(url)

    if resp.status_code != 200:
        return False

    return resp


def find_good_url(url):
    # TODO: clean /textes/ urls

    if 'senat.fr' in url:
        if '/leg/' in url and url.endswith('.html'):
            resp = test_status(url)
            if resp:
                return url
        if '/rap/' in url: # and step.get('institution') == 'CMP':
            for page in '_mono', '3', '2', '1', '0':
                new_url = url.replace('.html', page + '.html')
                if test_status(new_url):
                    return new_url

    if 'assemblee-nationale.fr' in url:
        if '/cr-' in url:
            return False
        if '/dossiers/' in url:
            return False
        if url.endswith('.pdf'):
            url = url.replace('/pdf/', '/propositions/').replace('.pdf', '.asp')
        resp = test_status(url)
        if not resp or "n'est pas encore édité" in resp.text:
            return False
        else:
            return url

    resp = test_status(url)
    if resp:
        return url
    return False


if __name__ == '__main__':
    ### some tests
    # AN .pdf
    assert find_good_url('http://www.assemblee-nationale.fr/13/pdf/pion1895.pdf') == 'http://www.assemblee-nationale.fr/13/propositions/pion1895.asp'
    # senat simple
    assert find_good_url('https://www.senat.fr/leg/tas11-040.html') == 'https://www.senat.fr/leg/tas11-040.html'
    # senat multi-page
    assert find_good_url('https://www.senat.fr/rap/l08-584/l08-584.html') == 'https://www.senat.fr/rap/l08-584/l08-584_mono.html'


    try:
        doslegs = json.load(open(sys.argv[1]))
        ok, nok = 0, 0
        for dos in doslegs:
            for step in dos['steps']:
                url = step.get('source_url')

                if url is None:
                    # TODO: stats of None urls
                    continue
                    print(step)
                # we do not parse CC texts
                elif 'conseil-constitutionnel' in url:
                    continue
                else:
                    fixed_url = find_good_url(url)
                    if fixed_url:
                        ok += 1
                        try:
                            parse_texte.parse(fixed_url)
                        except Exception as e:
                            print('parsing failed for', fixed_url)
                            print('   ', e)
                        if ok % 100 == 0:
                            print('ok..100')
                        continue
                    else:
                        print('INVALID RESP', url, '\t\t-->', dos.get('url_dossier_senat'))
                nok += 1
    except KeyboardInterrupt:
        pass
    print('ok', ok)
    print('nok', nok)
    print(r'%%%', ok/(nok+ok) * 100)
    json.dump(doslegs, open(sys.argv[2], 'w'), indent=2, ensure_ascii=False, sort_keys=False)


"""
A gerer:
 - https://www.legifrance.gouv.fr/jo_pdf.do?numJO=0&dateJO=20131230&numTexte=2&pageDebut=21910&pageFin=22188

Non-géré par parse_texte:
 - _mono /rap/
 - Votre commission vous propose d'adopter le projet de loi sans modification.
    - https://www.senat.fr/rap/l07-372/l07-3722.html#toc16
 - http://www.assemblee-nationale.fr/13/rapports/r1151.asp
    "Suivant les conclusions du rapporteur, la commission adopte les projets de loi (nos 1038, 1039 et 1040)."
 - PLF - https://www.legifrance.gouv.fr/eli/loi/2016/7/22/FCPX1613153L/jo/texte

Cas difficiles:
 - tomes: http://www.assemblee-nationale.fr/13/rapports/r1211.asp
 - plf - https://www.senat.fr/rap/l08-162/l08-162_mono.html#toc40
"""