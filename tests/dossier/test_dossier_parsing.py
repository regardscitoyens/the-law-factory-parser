# -*- coding: utf-8 -*-

import codecs

from lawfactory.dossier.parser import parse_dossier_senat


def test_dossier_pjl14_424():
    url = 'http://www.senat.fr/dossier-legislatif/pjl14-424.html'
    html = codecs.open('tests/dossier/resources/pjl14-424.html', encoding='iso-8859-1')

    data = parse_dossier_senat(url, html)

    assert data['legislature'] == '14'
    assert data['short_title'] == 'Renseignement'
    assert data['title'] == 'projet de loi relatif au renseignement'

    assert data['steps'][0]['date'] == '19/03/15'
    assert data['steps'][0]['name'] == u'1ère lecture'
    assert data['steps'][0]['items'][0]['name'] == 'Texte'
    assert data['steps'][0]['items'][0]['url'] == 'http://www.assemblee-nationale.fr/14/projets/pl2669.asp'