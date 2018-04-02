import sys, json, re

from lawfactory_utils.urls import download
from tools import parse_texte, complete_articles, _step_logic


def _dump_json(data, filename):
    json.dump(data, open(filename, 'w'), ensure_ascii=False, indent=2, sort_keys=True)
    print('   DEBUG - dumped', filename)


def test_status(url):
    resp = download(url)
    if resp.status_code != 200:
        return False
    return resp


def find_good_url_resp(url):
    if 'senat.fr' in url:
        if '/leg/' in url and url.endswith('.html'):
            resp = test_status(url)
            if resp:
                return resp
        if '/rap/' in url:
            # we try to use the last page to get a clean text
            clean_url_resp = None
            for page in '0123456789':
                new_url = url.replace('.html', page + '.html')
                resp = test_status(new_url)
                if not resp:
                    break
                text = resp.text.replace('<br>', '\n')
                # look for the "TEXTE ÉLABORÉ PAR .."" TITLE
                if re.match(r'.*TEXTE\s+&Eacute;LABOR&Eacute;\s+PAR.*', text, re.M | re.DOTALL) \
                    or re.match(r'.*EXAMEN\s+EN\s+COMMISSION.*', text, re.M | re.DOTALL):
                    # if the previous page was valid also, then the text is multi-page
                    if clean_url_resp:
                        clean_url_resp = None
                        break
                    clean_url_resp = resp

            if clean_url_resp:
                return clean_url_resp
            else:
                # use _mono as last resort
                mono_url = url.replace('.html', '_mono.html')
                resp = test_status(mono_url)
                if resp:
                    return resp

    if 'assemblee-nationale.fr' in url:
        if '/cr-' in url:
            return False
        if '/dossiers/' in url:
            return False

        if 'documents/notice/' in url:
            url = url.replace('www2', 'www').replace('documents/notice/', '').split('/(index)')[0] + '.asp'

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
            return resp

    resp = test_status(url)
    if resp:
        return resp
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

        if (dos.get('use_old_procedure') or _step_logic.use_old_procedure(step) )\
            and step.get('institution') in ('senat', 'assemblee') \
            and step.get('step') == 'commission':
            continue

        # we do not parse CC / JO texte for now
        if step.get('stage') in ('constitutionnalité', 'promulgation'):
            continue

        if url is None:
            if step == steps[-1] and not dos.get('url_jo'):
                print('     * ignore empty last step since the law is not yet promulgated')
                continue
            if step.get('echec') is None:
                raise Exception('[parse_texts] Empty url for step: %s.%s.%s' % (step.get('institution'), step.get('stage'), step.get('step')))
            # TODO: texte retire
            continue
        else:
            fixed_url_resp = find_good_url_resp(url)
            if fixed_url_resp:
                fixed_url = fixed_url_resp.url
                if fixed_url != url:
                    print('        ^ text url fixed:', fixed_url)

                step['source_url'] = fixed_url

                step['articles'] = parse_texte.parse(fixed_url, resp=fixed_url_resp)
                assert step['articles']

                step['articles'][0]['depot'] = step.get('step') == 'depot'

                # echec detected ? we update the step
                echec_line = [article for article in step['articles'] if article.get('type') == 'echec']
                if echec_line:
                    assert step.get('step') != 'depot'
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
                raise Exception('[parse_texts] Invalid response %s' % url)

        if debug_intermediary_files:
            _dump_json(step.get('articles'), 'debug_parsed_text_step_%d.json' % step_index)

    # re-order CMPs via texte définitif detection
    cmp_hemi_steps = [i for i, step in enumerate(dos['steps']) if
        step.get('stage') == 'CMP' and step.get('step') == 'hemicycle']
    if cmp_hemi_steps and len(cmp_hemi_steps) == 2:
        first, second = [dos['steps'][i] for i in cmp_hemi_steps]
        first_i, second_i = cmp_hemi_steps
        if first.get('articles', [{}])[0].get('definitif'):
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
                    # get ante-previous step for hemicycle text where an alinea
                    # can reference the depot step instead of the commission text
                    anteprevious = None
                    if step.get('step') == 'hemicycle':
                        antestep_index = _step_logic.get_previous_step(steps, prev_step_index, dos.get('use_old_procedure', False), get_depot_step=True)
                        if antestep_index is not None and steps[antestep_index].get('step') == 'depot':
                            anteprevious = steps[antestep_index].get(
                                'articles_completed',
                                steps[antestep_index].get('articles', [])
                            )

                    complete_args = {
                        'current': step.get('articles', []),
                        'previous': steps[prev_step_index].get(
                            'articles_completed',
                            steps[prev_step_index].get('articles', [])
                        ),
                        'step': step,
                        'table_concordance': dos.get('table_concordance', {}),
                        'anteprevious': anteprevious,
                    }
                    if debug_intermediary_files:
                        _dump_json(complete_args, 'debug_complete_args_step_%d.json' % step_index)
                    step['articles_completed'] = complete_articles.complete(**complete_args)

        if debug_intermediary_files:
            _dump_json(step.get('articles_completed'), 'debug_completed_text_step_%d.json' % step_index)

    return dos


"""
A gerer:
 - Votre commission vous propose d'adopter le projet de loi sans modification.
    - https://www.senat.fr/rap/l07-372/l07-3722.html#toc16
 - http://www.assemblee-nationale.fr/13/rapports/r1151.asp
    "Suivant les conclusions du rapporteur, la commission adopte les projets de loi (nos 1038, 1039 et 1040)."
 - tableaux comparatif - http://www.assemblee-nationale.fr/13/rapports/r0771.asp
 - tomes: http://www.assemblee-nationale.fr/13/rapports/r1211.asp
 - plf - https://www.senat.fr/rap/l08-162/l08-162_mono.html#toc40
 - revenir au sommaire depuis une page - https://www.senat.fr/rap/l11-038/l11-0389.html#toc50
 - alineas bis non modifiés - https://www.senat.fr/leg/tas11-064.html
"""
