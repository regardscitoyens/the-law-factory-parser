# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

import re

legislature_re = re.compile('dossier-legislatif/\w+(\d\d)-\d+.html')


def parse_dossier_senat(url, html):
    soup = BeautifulSoup(html)

    return {
        'url': url,
        'legislature': legislature_re.search(url).groups()[0],
        'short_title': soup.find('title').text.split(' - ')[0],
        'title': soup.find('meta', attrs={'name': 'Description'})['content'],
        'steps': [parse_timeline_li(soup, li) for li in soup.find(id='block-timeline').find_all('li')]
    }


def parse_timeline_li(soup, li):
    a = li.find('a')
    step_id = a['href'].replace('#', '')

    items = [parse_timeline_li_item(item_) for item_ in soup.find(id=step_id).find_all('li')]

    ems = li.find_all('em')

    return {
        'date': ems[-1].text,
        'title': a['title'].split('| ')[1],
        'items': items,
        'name': ems[0].text if len(ems) > 1 else ''
    }


def parse_timeline_li_item(item):
    links = [link for link in item.find_all('a') if link.has_attr('href')]

    if not links:
        return

    return {
        'url': links[0]['href'] if len(links) > 0 else '',
        'text': item.text,
        'name': links[0].text
    }

