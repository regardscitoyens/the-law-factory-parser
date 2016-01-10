# -*- coding: utf-8 -*-

from lawfactory.dossier.parser import parse_date


def test_parse_date():
    assert parse_date('Commission mixte paritaire (27 octobre 2015)') == '2015-10-27'
    assert parse_date(u'Commission mixte paritaire le 27 décembre 2015') == '2015-12-27'