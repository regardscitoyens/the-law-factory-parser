import sys, os

from lawfactory_utils.urls import download, enable_requests_cache, clean_url
enable_requests_cache()

API_DIRECTORY = sys.argv[1]

# TODO: 1942 + 5*legislature
for url in "2007-2012.nosdeputes", "2012-2017.nosdeputes", "2017-2022.nosdeputes", "www.nosdeputes", "www.nossenateurs":
    print('downloading from', url)
    open(os.path.join(API_DIRECTORY, '%s-groupes.json' % url), 'w').write(
        download("https://%s.fr/organismes/groupe/json" % url).text)
    open(os.path.join(API_DIRECTORY, '%s.parlementaires.json' % url), 'w').write(
        download("http://%s.fr/%s/json" % (url, 'deputes' if 'deputes' in url else 'senateurs')).text)
