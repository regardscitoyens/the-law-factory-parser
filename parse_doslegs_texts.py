import sys, json, time, random, os

from lawfactory_utils.urls import clean_url, download, enable_requests_cache

enable_requests_cache()

from bs4 import BeautifulSoup
import requests

from tools import parse_texte, complete_articles, _step_logic


def test_status(url):
    resp = download(url)

    if resp.status_code != 200:
        return False

    return resp


def find_good_url(url):
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

        """
        # /textes/ URL are not supported yet in parse_text
        if '/ta-commission/' in url:
            text_id = url.split('/')[-1].split('-')[0].replace('r', '')
            new_url = url.split('/ta-commission/')[0] + '/textes/' + text_id + '.asp'
            if test_status(new_url):
                return new_url

        if '/projets/' in url:
            new_url = url.replace('/projets/pl', '/textes/')
            if test_status(new_url):
                return new_url

        if '/propositions/' in url:
            new_url = url.replace('/propositions/pion', '/textes/')
            if test_status(new_url):
                return new_url

        if '/ta/' in url:
            new_url = url.replace('/ta/ta', '/textes/')
            if test_status(new_url):
                return new_url
        """

        resp = test_status(url)
        if not resp or "n'est pas encore édité" in resp.text:
            return False
        else:
            return url

    resp = test_status(url)
    if resp:
        return url
    return False


def _dos_id(dos):
    return dos.get('senat_id', dos.get('assemblee_id'))


def process(dos):
    dos_id = _dos_id(dos)
    print('** parsing texts of', dos_id)

    steps = dos['steps']

    # first parse the texts
    for step_index, step in enumerate(steps):
        url = step.get('source_url')
        print('    ^ text: ', url)

        if url is None:
            if step.get('echec') == 'renvoi en commission':
                step['articles_completed'] = steps[step_index-2].get('articles_completed',
                    steps[step_index-2].get('articles'))
            # TODO: texte retire
            # TODO: stats of None urls
            continue
            print(step)
        # we do not parse CC
        elif 'conseil-constitutionnel' in url:
            continue
        # also ignore legifrance for now
        elif 'legifrance' in url:
            continue
        else:
            fixed_url = find_good_url(url)

            if fixed_url:
                try:
                    step['articles'] = parse_texte.parse(fixed_url)
                    step['articles'][0]['depot'] = step.get('step') == 'depot'

                    # echec detected in the text content ? we update the step then
                    if any([1 for article in step['articles'] if article.get('type') == 'echec']):
                        if step.get('stage') == 'CMP':
                            step['echec'] = 'echec'
                        else:
                            step['echec'] = 'rejet'

                except Exception as e:
                    print('parsing failed for', fixed_url)
                    print('   ', e)

                prev_step_index = _step_logic.get_previous_step(steps, step_index)
                if prev_step_index is not None and not step.get('echec'):
                    # multiple-depots
                    if step_index == 0 or (step_index > 0 and steps[step_index-1].get('step') == 'depot' and step.get('step') == 'depot'):
                        step['articles_completed'] = step['articles']
                    else:
                        ante_step_index = _step_logic.get_previous_step(steps, prev_step_index)
                        if ante_step_index is None:
                            ante_step_articles = []
                        else:
                            ante_step_articles = steps[ante_step_index].get('articles_completed', steps[ante_step_index].get('articles', []))
                        try:
                            step['articles_completed'] = complete_articles.complete(
                                step.get('articles', []),
                                steps[prev_step_index].get('articles_completed', steps[prev_step_index].get('articles', [])),
                                ante_step_articles,
                                step,
                            )

                            assert 'Non modifié' not in str(step['articles_completed'])
                            print('             complete OK')
                        except Exception as e:
                            print('             complete FAIL', e)
                            break
                continue
            else:
                print('INVALID RESP', url, '\t\t-->', dos.get('url_dossier_senat'))
    
    # re-order CMPs via texte définitif detection
    cmp_hemi_steps = [i for i, step in enumerate(dos['steps']) if
        step.get('stage') == 'CMP' and step.get('step') == 'hemicycle']
    if cmp_hemi_steps and len(cmp_hemi_steps) == 2:
        first, second = [dos['steps'][i] for i in cmp_hemi_steps]
        first_i, second_i = cmp_hemi_steps
        if first.get('articles',{}).get('definitif'):
            steps = dos['steps']
            steps[first_i], steps[second_i] = steps[second_i], steps[first_i]

    # TODO complete articles after re-order here to get the completion right

    return dos


if __name__ == '__main__':
    ### some tests
    # AN .pdf
    assert find_good_url('http://www.assemblee-nationale.fr/13/pdf/pion1895.pdf') == 'http://www.assemblee-nationale.fr/13/propositions/pion1895.asp'
    # senat simple
    assert find_good_url('https://www.senat.fr/leg/tas11-040.html') == 'https://www.senat.fr/leg/tas11-040.html'
    # senat multi-page
    assert find_good_url('https://www.senat.fr/rap/l08-584/l08-584.html') == 'https://www.senat.fr/rap/l08-584/l08-584_mono.html'

    # AN improve link
    """
    assert find_good_url('http://www.assemblee-nationale.fr/15/ta-commission/r0268-a0.asp') == 'http://www.assemblee-nationale.fr/15/textes/0268.asp'
    assert find_good_url('http://www.assemblee-nationale.fr/15/projets/pl0315.asp') == 'http://www.assemblee-nationale.fr/15/textes/0315.asp'
    assert find_good_url('http://www.assemblee-nationale.fr/14/propositions/pion4347.asp') == 'http://www.assemblee-nationale.fr/14/textes/4347.asp'
    assert find_good_url('http://www.assemblee-nationale.fr/15/ta/ta0021.asp') == 'http://www.assemblee-nationale.fr/15/textes/0021.asp'
    """

    print("tests passed..let's fix some links !")

    doslegs = json.load(open(sys.argv[1]))
    if type(doslegs) is not list:
        doslegs = [doslegs]

    output_dir = sys.argv[2]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # random.shuffle(doslegs)
    for dos in doslegs:
        filepath = os.path.join(output_dir, _dos_id(dos))
        print('generating', filepath)

        if os.path.exists(filepath):
            print('  - already done')
            continue

        json.dump(process(dos), open(filepath, 'w'),
            ensure_ascii=False, indent=2, sort_keys=True)


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
 - tableaux comparatif - http://www.assemblee-nationale.fr/13/rapports/r0771.asp
 - old proc

Cas difficiles:
 - tomes: http://www.assemblee-nationale.fr/13/rapports/r1211.asp
 - plf - https://www.senat.fr/rap/l08-162/l08-162_mono.html#toc40
"""
