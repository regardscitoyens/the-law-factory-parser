#!/usr/bin/env python
# -*- coding: utf-8 -*-


def detect_auteur_depot_from_url(url):
    if '/propositions/' in url:
        return "Députés"
    elif '/leg/ppl' in url:
        return "Sénateurs"
    return "Gouvernement"


def add_auteur_depot(step):
    if step.get('step', '') == 'depot' and step['debats_order'] is not None:
        step['auteur_depot'] = detect_auteur_depot_from_url(step.get('source_url', ''))


def remove_interventions_too_small(step, intervs):
    # TODO: this warning is never triggered, maybe this code is obsolete ?
    if step.get('has_interventions') and step['directory'] not in intervs:
        print("[warning] [update_procedure] removing nearly empty interventions steps for", step['directory'])
        step['has_interventions'] = False


def process(procedure, articles, intervs={}):
    """
    Process procedure to
        - add a fake `enddate` where it's useful
        - detect the steps we want to display
            (add a `debats_order` to those steps)
        - add `auteur_depot`
        - remove extra predicted steps
    """
    articles = articles['articles']

    good_steps = {}
    for _, a in articles.items():
        for s in a['steps']:
            stepid = s['directory']
            if stepid not in good_steps:
                good_steps[stepid] = int(s['directory'].split('_')[0])

    if not good_steps:
        raise Exception('[update_procedure] no steps to display, parsing must have failed')

    currently_debated_step = None
    for s in procedure['steps']:
        if s.get('in_discussion'):
            currently_debated_step = s

        if 'enddate' not in s and currently_debated_step is None:
            s['enddate'] = s.get('date')

        s['debats_order'] = None
        if 'directory' in s:
            if currently_debated_step == s and good_steps:
                s['debats_order'] = max(good_steps.values()) + 1
            elif not currently_debated_step:
                s['debats_order'] = good_steps.get(s['directory'], None)

        remove_interventions_too_small(s, intervs)
        add_auteur_depot(s)

    # remove predicted steps after the one in discussion
    if not procedure.get('url_jo'):
        steps_to_keep = []
        for s in procedure['steps']:
            if s.get('stage') == 'promulgation':
                break
            steps_to_keep.append(s)
            if s.get('in_discussion'):
                break
        else:
            raise Exception("[update_procedure] no step in discussion for live text")
        procedure['steps'] = steps_to_keep

    return procedure


if __name__ == "__main__":
    # test: do not mark promulgation step as visible step even for
    #       unfinished texts (#95)
    result = process(
        {
            "url_jo": None,
            "steps": [
                {
                    "date": "2011-12-01",
                    "directory": "00_",
                    "enddate": "2011-12-01",
                    "institution": "senat",
                    "stage": "1ère lecture",
                    "step": "depot",
                },
                {
                    "date": "2011-12-13",
                    "directory": "02_",
                    "institution": "senat",
                    "stage": "1ère lecture",
                    "step": "hemicycle",
                },
                {
                    "date": None,
                    "directory": "03_",
                    "institution": "gouvernement",
                    "stage": "promulgation",
                },
            ],
        },
        {
            "articles": {
                "1er": {
                    "steps": [
                        {"directory": "00_"},
                        {"directory": "01_"},
                        {"directory": "02_"},
                    ]
                }
            }
        },
    )

    try:
        assert result == {
            "steps": [
                {
                    "auteur_depot": "Gouvernement",
                    "date": "2011-12-01",
                    "debats_order": 0,
                    "directory": "00_",
                    "enddate": "2011-12-01",
                    "institution": "senat",
                    "stage": "1ère lecture",
                    "step": "depot",
                },
                {
                    "date": "2011-12-13",
                    "debats_order": 2,
                    "directory": "02_",
                    "enddate": "2011-12-13",
                    "institution": "senat",
                    "stage": "1ère lecture",
                    "step": "hemicycle",
                }
            ],
            "url_jo": None,
        }
    except Exception as e:
        import pprint
        pprint.pprint(result)
        raise e
    print("[update_procedure] TESTS OK")
