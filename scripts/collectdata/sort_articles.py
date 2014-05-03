#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

# Handle all bis-ter words until 27 included
# (adding 28 duodetrecies creates more complexity)
# cf http://fr.wikipedia.org/wiki/Adverbe_multiplicatif
# 27 is actually the biggest used case in all texts analyzed so far back to 2009
# cf http://www.assemblee-nationale.fr/13/ta-commission/r3604-a0.asp
bis_27 = ['bis', 'ter', 'quater', 'quinquies', 'sexies', 'septies', 'octies', 'novies',
'decies', 'undecies', 'duodecies', 'terdecies', 'quaterdecies', 'quindecies', 'sexdecies', 'septdecies', 'octodecies', 'novodecies',
'vicies', 'unvicies', 'duovicies', 'tervicies', 'quatervicies', 'quinvicies', 'sexvicies', 'septvicies']

bister = '(un|duo|tre|bis|qua|quin[tqu]*|sex|sept|octo?|novo?|non|dec|vic|ter|ies)+'
re_bister = re.compile(bister)

re_article = re.compile(r'(\d+)e?r?(( ([A-Z]+|%s))*)' % bister)

re_add_spaces = re.compile(r'([A-Z])\s*')
add_spaces = lambda x: re_add_spaces.sub(r'\1 ', x)
def split_article(a):
    if not re_article.match(a):
        return [0, a]
    m = re_article.search(a)
    res = [int(m.group(1))]
    if m.group(2):
        res += add_spaces(m.group(2)).strip().split(' ')
    return res

hash_bis = {'u': 1, 'b': 2, 't': 3, 'o': 8, 'n': 9,
  'qua': 4, 'qui': 5, 'sex': 6, 'sep': 7, 'du': 2, 'de': 0, 'v': 0}
def quantify_bis(b):
    u = 0
    for i in [1, 2, 3]:
        if b[:i] in hash_bis:
            u = hash_bis[b[:i]]
            break
    if 'decies' in b:
        u += 10
    if 'vicies' in b:
        u += 20
    return u

def type_detail(d):
    if not d:               # nothing
        return 0
    if len(d) == 1:         # A-Z
        return -1
    if re_bister.match(d):  # bis-ter
        return 1
    return -2               # junk text

def compare_details(a, b):
    if a == b:
        return 0
    # recursive if same first detail
    if a[0] == b[0]:
        return compare_details(a[1:], b[1:])
    # classify type details
    qa = type_detail(a[0])
    qb = type_detail(b[0])
    # order by A-Z < _ < bis-ter
    if qa != qb:
        return qa - qb
    # if both A-Z or junk text
    if qa < 0:
        if a[0] < b[0]: # use alpha order
            return -1
        return 1
    # necessarily both bis-ter now
    return quantify_bis(a[0]) - quantify_bis(b[0])

def compare_articles(a, b):
    if a == b:
        return 0
    na = split_article(a)
    nb = split_article(b)
    # compare numbers
    if na[0] != nb[0]:
        return na[0] - nb[0]
    # equalize array lengths
    if len(na) > len(nb):
        nb += [None] * (len(na) - len(nb))
    elif len(na) < len(nb):
        na += [None] * (len(nb) - len(na))
    # compare details
    return compare_details(na[1:], nb[1:])

def article_is_lower(a, b):
    return compare_articles(a, b) < 0

if __name__ == "__main__":

    # Test split articles
    print "[TEST] Splitting article 1er A bis AA'"
    assert(split_article('1er A bis AA') == [1, 'A', 'bis', 'A', 'A'])
    print " -> Success!"

    # Test convert bis to numbers for 2 to 27
    print "[TEST] Converting bis expressions to numbers for 2 to 27:"
    for i, v in enumerate(bis_27):
        assert(quantify_bis(v) == i + 2)
    print " -> Success!"

    # Test sorting an array of articles
    print "[TEST] Sorting randomized array of articles:"
    sorted_arts = [
      "wrong name 1",
      "wrong name 2",
      "1er A",
      "1er A bis AA",
      "1er A bis A",
      "1er A bis",
      "1er B",
      "1er C",
      "1er",
      "13",
      "14 AAA",
      "14 AA",
      "14 AB",
      "14 A",
      "14 A bis A",
      "14 A ter",
      "14 B",
      "14 CA",
      "14 C",
      "14",
      "14 bis A",
      "14 bis",
      "14 ter",
      "14 quater",
      "14 duodecies CA",
      "14 duodecies CC",
      "14 duodecies C",
      "14 duodecies G",
      "14 duodecies ZY",
      "14 duodecies ZZ",
      "14 duodecies Z",
      "14 duodecies",
    ]
    from pprint import pprint
    import random

    random_arts = list(sorted_arts)
    random.shuffle(random_arts)

    print "- Randomized array:"
    pprint(random_arts)
    random_arts.sort(compare_articles)
    pprint(random_arts)
    print "- Sorted array:"
    assert(random_arts == sorted_arts)
    print " -> Success!"

