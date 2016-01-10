# -*- coding: utf-8 -*-

import codecs

from lawfactory.dossier.parser import parse_dossier_senat


def test_dossier_pjl14_424():
    url = 'http://www.senat.fr/dossier-legislatif/pjl14-424.html'
    html = codecs.open('tests/dossier/resources/pjl14-424.html', encoding='iso-8859-1')

    data = parse_dossier_senat(url, html)

    assert data['legislature'] == '14'
    assert data['dossier_id'] == 'pjl14-424'
    assert data['short_title'] == 'Renseignement'
    assert data['title'] == 'projet de loi relatif au renseignement'
    assert len(data['steps']) == 10

    expected_first_step = {
        'place': 'assemblee', 
        'step': 'depot',
        'stage': u'1ère lecture',
        'documents': [{
            'url': 'http://www.assemblee-nationale.fr/14/projets/pl2669.asp',
            'date': '2015-03-19',
            'type': 'texte'
        }]
    }

    expected_second_step = {
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
    }

    assert data['steps'][0] == expected_first_step
    assert data['steps'][1] == expected_second_step