import re

from lawfactory_utils.urls import download
from senapy.dosleg.parser import parse as senapy_parse

from .tools import parse_texte, complete_articles
from .tools._step_logic import get_previous_step, use_old_procedure, is_one_of_the_initial_depots, should_ignore_commission_text
from .tools.common import debug_file


def test_status(url):
    resp = download(url)
    if resp.status_code != 200:
        return False
    # TODO: do this in download()
    if 'assemblee-nationale.fr' in url:
        resp.encoding = 'Windows-1252'
    return resp


def is_step_in_discussion(steps, step_index):
    for s in steps[step_index + 1:]:
        if 'source_url' in s and s.get('step') in (
            'hemicycle',
            'commission',
            'constitutionnalité'
        ):
            return False
    return True


def find_good_url_resp(url):
    if 'senat.fr' in url:
        # Depot steps can sometime link a previous abandonned dosleg
        # ex: http://www.senat.fr/dossier-legislatif/ppl09-338.html
        if '/dossier-legislatif/' in url:
            resp = test_status(url)
            if resp:
                dos = senapy_parse(resp.text, url)
                return find_good_url_resp(dos['steps'][0]['source_url'])

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
                    or re.search(r'>PROJET DE LOI ', text) \
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


def parse_url_for_step(url, step, step_index, retry=True):
    fixed_url_resp = find_good_url_resp(url)
    if fixed_url_resp:
        fixed_url = fixed_url_resp.url
        if fixed_url != url:
            print('        ^ text url fixed:', fixed_url)

        if step.get('stage') != 'constitutionnalité':
            step['source_url'] = fixed_url

        articles = parse_texte.parse(fixed_url, resp=fixed_url_resp)
        debug_file(articles, 'parsed_text_step_%d.json' % step_index)

        if (not articles or len(articles) < 2):
            if retry:
                if 'ta-commission' in fixed_url:
                    fixed_url = fixed_url.replace('ta-commission', 'rapports').replace('-a0', '')
                    print('        ^ empty parsing, trying url rapport :', fixed_url)
                    return parse_url_for_step(fixed_url, step, step_index, retry=False)
                if 'assemblee-nationale' in fixed_url and 'rapports' in fixed_url:
                    fixed_url = fixed_url.replace('rapports', 'ta-commission').replace('.asp', '-a0.asp')
                    print('        ^ empty parsing, trying url TA :', fixed_url)
                    return parse_url_for_step(fixed_url, step, step_index, retry=False)

            raise Exception('[parse_texts] Empty parsing %s' % url)

        step['articles'] = articles
        text = articles[0]
        text['depot'] = step.get('step') == 'depot'

        # echec detected ? we update the step
        echec_line = [article for article in articles if article.get('type') == 'echec']
        if echec_line:
            assert step.get('step') != 'depot'
            echec_line = echec_line[0]
            if step.get('stage') == 'CMP':
                step['echec'] = 'échec'
            else:
                step['echec'] = 'rejet'

        if not step.get('echec') and len(articles) == 1:
            re_rapport_senat = re.compile(r'(senat.fr/rap/([^/]+)/\2)\d.html')
            if re_rapport_senat.search(fixed_url):
                fixed_url = re_rapport_senat.sub(r'\1_mono.html', fixed_url)
                print('        ^ empty parsing, trying url mono :', fixed_url)
                return parse_url_for_step(fixed_url, step, step_index)

            raise Exception('parsing failed for %s (no text)' % fixed_url)
    elif 'ta-commission' in url:
        fixed_url = url.replace('ta-commission', 'rapports').replace('-a0', '')
        print('        ^ empty response, trying url rapport :', fixed_url)
        parse_url_for_step(fixed_url, step, step_index)
    else:
        raise Exception('[parse_texts] Invalid response %s' % url)


def parse_texts(dos):
    print('** parsing texts')

    steps = dos['steps']

    # first parse the texts
    for step_index, step in enumerate(steps):
        url = step.get('source_url')
        print('    ^ text: ', url)

        if should_ignore_commission_text(step, dos):
            continue

        # we parse the JO texte only if there's a CC decision
        if step.get('stage') == 'constitutionnalité':
            url = dos.get('url_jo')
        if step.get('stage') == 'promulgation':
            continue


        try:
            if url is None:
                if step.get('echec') is None:
                    raise Exception('[parse_texts] Empty url for step: %s.%s.%s' % (step.get('institution'), step.get('stage'), step.get('step')))
                continue
            else:
                parse_url_for_step(url, step, step_index)
        except Exception as e:
            if step.get('step') == 'depot' and not is_one_of_the_initial_depots(steps, step_index):
                print('     * ignore missing intermediary depot', url)
                continue

            if not dos.get('url_jo') and is_step_in_discussion(steps, step_index):
                step['in_discussion'] = True
                print('     * ignore step in discussion')
                break

            raise e


def re_order_cmp(dos):
    # re-order CMPs via texte définitif detection
    steps = dos['steps']

    cmp_hemi_steps = [i for i, step in enumerate(dos['steps']) if
        step.get('stage') == 'CMP' and step.get('step') == 'hemicycle']

    if cmp_hemi_steps and len(cmp_hemi_steps) == 2:
        first_i, second_i = cmp_hemi_steps
        first = dos['steps'][first_i]
        if first.get('articles', [{}])[0].get('definitif') or first.get('echec'):
            print('     * re-ordered CMP steps')
            steps = dos['steps']
            steps[first_i], steps[second_i] = steps[second_i], steps[first_i]


def complete_texts(dos):
    steps = dos['steps']
    for step_index, step in enumerate(steps):
        print('    ^ complete text: ', step.get('source_url'))

        if 'articles' in step:
            old_proc = use_old_procedure(step, dos)
            prev_step_index = get_previous_step(steps, step_index, old_proc)
            if prev_step_index is not None and not step.get('echec'):
                if is_one_of_the_initial_depots(steps, step_index):
                    step['articles_completed'] = step['articles']
                else:
                    # get ante-previous step for hemicycle text where an alinea
                    # can reference the depot step instead of the commission text
                    anteprevious = None
                    if step.get('step') == 'hemicycle' and steps[prev_step_index].get('step') == 'commission':
                        antestep_index = get_previous_step(steps, prev_step_index, old_proc, get_depot_step=True)
                        if antestep_index is not None and steps[antestep_index].get('step') == 'depot':
                            anteprevious = steps[antestep_index].get(
                                'articles_completed',
                                steps[antestep_index].get('articles', [])
                            )

                    prev_step = steps[prev_step_index]
                    real_prev_step = steps[step_index-1]
                    real_prev_step_arts = real_prev_step.get(
                        'articles_completed',
                        real_prev_step.get('articles',
                            [{"type": "texte",
                             "id": real_prev_step.get("source_url", "").replace('.asp', '').replace('.html', ''),
                             "skip": old_proc or real_prev_step.get("echec")}]
                        )
                    )
                    real_prev_step_metas = real_prev_step_arts[0] if real_prev_step_arts else {}
                    complete_args = {
                        'current': step.get('articles', []),
                        'previous': prev_step.get(
                            'articles_completed',
                            prev_step.get('articles', [])
                        ),
                        'step': step,
                        'previous_step_metas': real_prev_step_metas,
                        'table_concordance': dos.get('table_concordance', {}),
                        'anteprevious': anteprevious,
                    }
                    debug_file(complete_args, 'complete_args_step_%d.json' % step_index)
                    step['articles_completed'] = complete_articles.complete(**complete_args)
                    debug_file(step.get('articles_completed'), 'completed_text_step_%d.json' % step_index)


def process(dos):
    # TODO(cleanup): articles_completed/articles attributes are hacky
    parse_texts(dos)
    re_order_cmp(dos)
    complete_texts(dos)
    return dos
