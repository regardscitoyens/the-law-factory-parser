# -*- coding: utf-8 -*-

import codecs

from lawfactory.dossier.senat_parser import parse_dossier_senat


def get_dossier_pjl14_424():
    url = 'http://www.senat.fr/dossier-legislatif/pjl14-424.html'
    html = codecs.open('tests/dossier/resources/pjl14-424.html', encoding='iso-8859-1')

    return parse_dossier_senat(url, html)


def test_global_params():
    data = get_dossier_pjl14_424()

    assert data['legislature'] == '14'
    assert data['dossier_id'] == 'pjl14-424'
    assert data['short_title'] == 'Renseignement'
    assert data['title'] == 'projet de loi relatif au renseignement'
    assert len(data['steps']) == 10


def test_first_lecture():
    data = get_dossier_pjl14_424()

    expected_steps = [{
        'place': 'assemblee', 
        'step': 'depot',
        'stage': u'1ère lecture',
        'documents': [{
            'url': 'http://www.assemblee-nationale.fr/14/projets/pl2669.asp',
            'date': '2015-03-19',
            'type': 'texte'
        }]
    }, {
        'place': 'assemblee',
        'step': 'commission',
        'stage': u'1ère lecture',
        'documents': [{
            'url': 'http://www.assemblee-nationale.fr/14/rapports/r2697.asp',
            'date': '2015-04-02',
            'type': 'rapport'
        }, {
            'url': 'http://www.assemblee-nationale.fr/14/ta-commission/r2697-a0.asp',
            'date': '2015-04-01',
            'type': 'texte'
        }, {
            'url': 'http://www.assemblee-nationale.fr/14/rapports/r2691.asp',
            'date': '2015-03-31',
            'type': 'avis'
        }]
    }, {
        'place': 'assemblee',
        'step': 'hemicycle',
        'stage': u'1ère lecture',
        'documents': [{
            'url': 'http://www.assemblee-nationale.fr/14/ta/ta0511.asp',
            'date': '2015-05-05',
            'type': 'texte'
        }]
    }, {
        'place': 'senat',
        'step': 'depot',
        'stage': u'1ère lecture',
        'documents': [{
            'url': 'http://www.senat.fr/leg/pjl14-424.html',
            'date': '2015-05-05',
            'type': 'texte'
        }]
    }]

    assert data['steps'][:4] == expected_steps