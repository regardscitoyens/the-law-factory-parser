import sys, json, time, random, os, re

from lawfactory_utils.urls import clean_url, download, enable_requests_cache

enable_requests_cache()

from bs4 import BeautifulSoup
import requests

from tools import parse_texte, complete_articles, _step_logic, common


def _dump_json(data, filename):
    json.dump(data, open(filename, 'w'), ensure_ascii=False, indent=2, sort_keys=True)
    print('   DEBUG - dumped', filename)


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
            # we try to use the last page to get a clean text
            clean_url = None
            for page in '9', '8', '7', '6', '5', '4', '3', '2', '1', '0':
                new_url = url.replace('.html', page + '.html')
                resp = test_status(new_url)
                if resp:
                    text = resp.text.replace('<br>', '\n')
                    # look for the "TEXTE ÉLABORÉ PAR .."" TITLE
                    if re.match(r'.*TEXTE\s+&Eacute;LABOR&Eacute;\s+PAR.*', text, re.M | re.DOTALL) \
                        or re.match(r'.*EXAMEN\s+EN\s+COMMISSION.*', text, re.M | re.DOTALL):
                        # if the previous page was valid also, then the text is multi-page
                        if clean_url:
                            clean_url = None
                            break
                        clean_url = new_url

            if clean_url:
                return clean_url
            else:
                # use _mono as last resort
                mono_url = url.replace('.html', '_mono.html')
                if test_status(mono_url):
                    return mono_url

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
        if not resp \
            or "n'est pas encore édité" in resp.text \
            or ">Cette division n'est pas encore distribuée<" in resp.text:
            return False
        else:
            return url

    resp = test_status(url)
    if resp:
        return url
    return False


def _dos_id(dos):
    return dos.get('senat_id', dos.get('assemblee_id'))


def process(dos, debug_intermediary_files=False):
    dos_id = _dos_id(dos)
    print('** parsing texts of', dos_id)

    steps = dos['steps']

    # first parse the texts
    for step_index, step in enumerate(steps):
        url = step.get('source_url')
        print('    ^ text: ', url)

        if dos.get('use_old_procedure') \
            and step.get('institution') in ('senat', 'assemblee') \
            and step.get('step') == 'commission':
            continue

        if url is None:
            if step == steps[-1] and not dos.get('url_jo'):
                print('     * ignore empty last step since the law is not yet promulgated')
                continue
            if step.get('echec') is None:
                raise Exception('empty url for step: %s.%s.%s' % (step.get('institution'), step.get('stage'), step.get('step')))
            # TODO: texte retire
            # TODO: stats of None urls
            continue
        # we do not parse CC
        elif 'conseil-constitutionnel' in url:
            continue
        # also ignore legifrance for now
        elif 'legifrance' in url:
            continue
        else:
            fixed_url = find_good_url(url)
            if fixed_url:
                if fixed_url != url:
                    print('        ^ text url fixed:', fixed_url)

                step['articles'] = parse_texte.parse(fixed_url)
                assert step['articles']
                
                step['articles'][0]['depot'] = step.get('step') == 'depot'

                # echec detected in the text content ? we update the step then
                echec_line = [article for article in step['articles'] if article.get('type') == 'echec']
                if echec_line:
                    echec_line = echec_line[0]
                    if step.get('stage') == 'CMP':
                        step['echec'] = 'echec'
                    else:
                        step['echec'] = 'rejet'

                if not step.get('echec') and len(step['articles']) < 2:
                    raise Exception('parsing failed for %s (no text)' % fixed_url)
            else:
                # ignore missing intermediate depot
                if step.get('step') == 'depot':
                    if step_index > 0:
                        last_step = steps[step_index-1]
                        if not last_step.get('echec') and last_step.get('step') == 'hemicycle':
                            print('     * ignore missing depot', url)
                            continue
                raise Exception('INVALID RESPONSE %s' % url)

        if debug_intermediary_files:
            _dump_json(step.get('articles'), 'debug_parsed_text_step_%d.json' % step_index)
    

    # re-order CMPs via texte définitif detection
    cmp_hemi_steps = [i for i, step in enumerate(dos['steps']) if
        step.get('stage') == 'CMP' and step.get('step') == 'hemicycle']
    if cmp_hemi_steps and len(cmp_hemi_steps) == 2:
        first, second = [dos['steps'][i] for i in cmp_hemi_steps]
        first_i, second_i = cmp_hemi_steps
        if first.get('articles',[{}])[0].get('definitif'):
            print('     * re-ordered CMP steps')
            steps = dos['steps']
            steps[first_i], steps[second_i] = steps[second_i], steps[first_i]


    for step_index, step in enumerate(steps):
        print('    ^ complete text: ', step.get('source_url'))
        
        if step.get('echec') == 'renvoi en commission':
            step['articles'] = steps[step_index-2].get('articles')
            # TODO: texte retire
            # TODO: stats of None urls
        if 'articles' in step:
            prev_step_index = _step_logic.get_previous_step(steps, step_index, dos.get('use_old_procedure', False))
            if prev_step_index is not None and not step.get('echec'):
                # multiple-depots
                if step_index == 0 or (step_index > 0 and steps[step_index-1].get('step') == 'depot' and step.get('step') == 'depot'):
                    step['articles_completed'] = step['articles']
                else:
                    complete_args = {
                        'current': step.get('articles', []),
                        'previous': steps[prev_step_index].get('articles_completed', steps[prev_step_index].get('articles', [])),
                        'step': step,
                        'table_concordance':dos.get('table_concordance', {}),
                    }
                    if debug_intermediary_files:
                        _dump_json(complete_args, 'debug_complete_args_step_%d.json' % step_index)
                    step['articles_completed'] = complete_articles.complete(**complete_args)
                    assert 'Non modifié' not in str(step['articles_completed'])

        if debug_intermediary_files:
            _dump_json(step.get('articles_completed'), 'debug_completed_text_step_%d.json' % step_index)

    return dos


if __name__ == '__main__':
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
