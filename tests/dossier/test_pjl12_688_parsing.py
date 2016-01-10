# -*- coding: utf-8 -*-

import codecs

from lawfactory.dossier.parser import parse_dossier_senat


def get_dossier_pjl12_688():
    url = 'http://www.senat.fr/dossier-legislatif/pjl12-688.html'
    html = codecs.open('tests/dossier/resources/pjl12-688.html', encoding='iso-8859-1')

    return parse_dossier_senat(url, html)


def test_global_params():
    data = get_dossier_pjl12_688()

    assert data['legislature'] == '12'
    assert data['dossier_id'] == 'pjl12-688'
    assert data['short_title'] == 'Transparence de la vie publique'
    assert data['title'] == u'projet de loi organique relatif à la transparence de la vie publique'
    assert len(data['steps']) == 20


def test_first_lecture():
    data = get_dossier_pjl12_688()

    assemblee = {
        'place': 'assemblee',
        'step': 'depot',
        'stage': u'1ère lecture',
        'documents': [{
            'url': 'http://www.assemblee-nationale.fr/14/projets/pl1004.asp',
            'date': '2013-04-24',
            'type': 'texte'
        }]
    }
    assert data['steps'][0] == assemblee


def test_cmp():
    data = get_dossier_pjl12_688()

    cmp = {
        'place': 'CMP',
        'step': 'commission',
        'stage': 'CMP',
        'documents': [{
            'url': 'http://www.senat.fr/compte-rendu-commissions/20130715/cmp.html#toc3',
            'date': '2013-07-16',
            'type': ''
        }, {
            'url': 'http://www.senat.fr/rap/l12-770/l12-770.html',
            'date': '2013-07-16',
            'type': 'rapport'
        }, {
            'url': 'http://www.senat.fr/leg/pjl12-771.html',
            'date': '2013-07-16',
            'type': ''
        }]
    }

    assert data['steps'][8] == cmp