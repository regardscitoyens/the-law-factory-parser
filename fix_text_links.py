import sys, json

from lawfactory_utils.urls import clean_url

from bs4 import BeautifulSoup
import requests, requests_cache

requests_cache.install_cache('texts_cache')

"""
Proto écrit à l'arrache pour voir l'étendu du boulot à faire

"""

def test(url):
    resp = requests.get(url)

    if resp.status_code != 200:
        return False

    smoke_testers = [
        'Article',
        'REJETÉ',
        'adopter le projet de loi',
        'SESSION ORDINAIRE DE',
    ]

    if not [1 for x in smoke_testers if x in resp.text]:

        def find_line_and_take_link(toc_title):
            if toc_title in resp.text:
                for line in resp.text.split('\n'):
                    if toc_title in line:
                        cmp_href = None
                        link = BeautifulSoup(line, 'lxml').find('a')
                        if link:
                            cmp_href = BeautifulSoup(line, 'lxml').find('a').attrs.get('href')
                        if not cmp_href and 'senat.fr' in url:
                            # maybe "page suivante button ?"
                            cmp_href = BeautifulSoup(resp.text, 'lxml').select_one('a.link-next').attrs.get('href')
                        if cmp_href:
                            new_url = '/'.join(url.split('/')[:-1]) + '/' + cmp_href
                            new_url = clean_url(new_url)
                            if test(new_url):
                                print('url fixed:', new_url)
                                return new_url
                        break

        new_url = find_line_and_take_link('TRAVAUX DE LA COMMISSION MIXTE PARITAIRE')
        if new_url: return new_url
        new_url = find_line_and_take_link('PROJET DE LOI</A><br>')
        if new_url: return new_url
        new_url = find_line_and_take_link('PROJET DE LOI </A><br>') # TODO: regex
        if new_url: return new_url
        new_url = find_line_and_take_link('divisé en deux tomes') # TODO: regex
        if new_url: return new_url

        return False

    return url
try:
    doslegs = json.load(open(sys.argv[1]))
    ok, nok = 0, 0
    for dos in doslegs:
        for step in dos['steps']:
            url = step.get('source_url')
            if url is None:
                continue
                print(step)
            elif '/dossiers/' in url or '.pdf' in url or '/cr-' in url:
                print('INVALID URL', url)
            else:
                fixed_url = test(url)
                if fixed_url:
                    ok += 1
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