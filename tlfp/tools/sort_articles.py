#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from functools import cmp_to_key

# Handle all bis-ter words until 27 included
# (adding 28 duodetrecies creates more complexity)
# cf http://fr.wikipedia.org/wiki/Adverbe_multiplicatif
# 27 is actually the biggest used case in all texts analyzed so far back to 2009
# cf http://www.assemblee-nationale.fr/13/ta-commission/r3604-a0.asp
# TODO: support multiple spellings in tests + more values than continuous
#       ex: quatervecies/quatervicies, novies/nonies
bis_27 = ['bis', 'ter', 'quater', 'quinquies', 'sexies', 'septies', 'octies', 'novies',
'decies', 'undecies', 'duodecies', 'terdecies', 'quaterdecies', 'quindecies', 'sexdecies', 'septdecies', 'octodecies', 'novodecies',
'vicies', 'unvicies', 'duovicies', 'tervicies', 'quatervicies', 'quinvicies', 'sexvicies', 'septvicies', 'duodetrecies', 'undetricies', 'tricies']

# support 1 to 99, from https://framagit.org/parlement-ouvert/metslesliens/blob/master/docs/l%C3%A9gistique.md
bister = '(' + \
  '(?:un|duo|ter|quater|quin|sex?|sept|octo|novo|unde?|duode)?' + \
  '(?:dec|v[ie]c|tr[ie]c|quadrag|quinquag|sexag|septuag|octog|nonag)' + \
  'ies|semel|bis|ter|quater|' + \
  '(?:quinqu|sex|sept|oct|no[nv])ies' + \
  ')'
re_bister = re.compile(bister)

re_article = re.compile(r'(\d+)e?r?(( ([A-Z]+|%s))*)' % bister)

re_clean_befaft = re.compile(r"^(a(vant|près)\s*l'|article\s*)+", re.I)

re_add_spaces = re.compile(r'([A-Z])\s*')
add_spaces = lambda x: re_add_spaces.sub(r'\1 ', x)
def split_article(a):
    if not re_article.match(re_clean_befaft.sub('', a)):
        return [0, a]
    m = re_article.search(a)
    res = [int(m.group(1))]
    if m.group(2):
        res += add_spaces(m.group(2)).strip().split(' ')
    return res

hash_bis = {'u': 1, 'b': 2, 't': 3, 'o': 8, 'n': 9,
  'qua': 4, 'qui': 5, 'sex': 6, 'sep': 7, 'du': 2, 'de': 0, 'tri': 0, 'v': 0}
def quantify_bis(b):
    u = 0
    if b.startswith("und") and b != 'undecies':
        u = -1
    elif b.startswith("duode") and b != 'duodecies':
        u = -2
    else:
        for i in [3, 2, 1]:
            if b[:i] in hash_bis:
                u = hash_bis[b[:i]]
                break
    if 'decies' in b:
        u += 10
    elif 'vicies' in b or 'vecies' in b:
        u += 20
    elif 'tricies' in b or 'trecies' in b:
        u += 30
    elif 'quadragies' in b:
        u += 40
    elif 'quinquagies' in b:
        u += 50
    elif 'sexagies' in b:
        u += 60
    elif 'septuagies' in b:
        u += 70
    elif 'octogies' in b:
        u += 80
    elif 'nonagies' in b:
        u += 90
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
    res = compare_details(na[1:], nb[1:])
    if res != 0:
        return res
    ia = na[0]
    if 'avant' in a.lower():
        ia -= 1
    elif 'après' in a.lower():
        ia += 1
    ib = nb[0]
    if 'avant' in b.lower():
        ib -= 1
    elif 'après' in b.lower():
        ib += 1
    return ia - ib

def article_is_lower(a, b):
    return compare_articles(a, b) < 0

if __name__ == "__main__":
    # Test split articles
    print("[TEST] Splitting article 1er A bis AA'")
    assert(split_article('1er A bis AA') == [1, 'A', 'bis', 'A', 'A'])
    print(" -> Success!")

    print("[TEST] Splitting article 1er A duodetrecies AA'")
    assert(split_article('1er A duodetrecies AA') == [1, 'A', 'duodetrecies', 'A', 'A'])
    print(" -> Success!")

    # Test convert bis to numbers for 2 to 27
    print("[TEST] Converting bis expressions to numbers for 2 to 27:")
    for i, v in enumerate(bis_27):
        try:
            assert(quantify_bis(v) == i + 2)
        except Exception as e:
            print("Wrong quantifying of '%s': %s" % (v, quantify_bis(v)))
            raise e
    print(" -> Success!")

    # Test sorting an array of articles
    print("[TEST] Sorting randomized array of articles:")
    sorted_arts = [
      "liminaire",
      "wrong name 1",
      "wrong name 2",
      "1er A",
      "1er A bis AA",
      "1er A bis A",
      "1er A bis",
      "1er B",
      "Après l'article 1er B",
      "Avant l'article 1er C",
      "1er C",
      "Après l'article 1er D",
      "avant l'article 1er",
      "1er",
      "Avant l'article 10 quater",
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
    new_sorted_arts = list(sorted(random_arts, key=cmp_to_key(compare_articles)))

    if new_sorted_arts != sorted_arts:
        print("- Randomized array:")
        pprint(new_sorted_arts)
        print("- Sorted array:")
        pprint(sorted_arts)
    assert new_sorted_arts == sorted_arts
    print(" -> Success!")
