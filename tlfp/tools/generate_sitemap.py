import datetime
from lys import L, render, raw
import os

def generate_sitemap(doslegs, api_directory):
    urls = [
            L.url / [
                L.loc / f"https://www.lafabriquedelaloi.fr/articles.html?loi={dos['id']}",
                L.lastmod / datetime.datetime.now().strftime('%Y-%m-%d'), # TODO: use directory last modified date
                L.changefreq / ("monthly" if dos.get('url_jo') else "daily"),
                L.priority / "1.0",
            ]
          for dos, _ in doslegs
    ]

    other_urls = [
        ("https://www.lafabriquedelaloi.fr/", "daily"),
        ("https://www.lafabriquedelaloi.fr/a-propos.html", "monthly"),
        ("https://www.lafabriquedelaloi.fr/lois.html", "daily"),
        ("https://www.lafabriquedelaloi.fr/lois.html?encours", "daily"),
    ]

    urls += [
            L.url / [
                L.loc / url,
                L.lastmod / datetime.datetime.now().strftime('%Y-%m-%d'),
                L.changefreq / changefreq,
                L.priority / "1.0",
            ]
          for url, changefreq in other_urls
    ]

    result = render([
        raw("""<?xml version="1.0" encoding="UTF-8"?>"""),
        L.urlset(xmlns="http://www.sitemaps.org/schemas/sitemap/0.9") / urls
    ])
    open(os.path.join(api_directory, 'sitemap.xml'), 'w').write(result)