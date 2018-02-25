import sys, os

from lawfactory_utils.urls import download, enable_requests_cache


def process(output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    for url in "2007-2012.nosdeputes", "2012-2017.nosdeputes", "2017-2022.nosdeputes", "www.nosdeputes", "www.nossenateurs":
        dfile = '%s-groupes.json' % url
        destfile = os.path.join(output_directory, dfile)
        if not os.path.exists(destfile):
            print('downloading', dfile)
            open(destfile, 'w').write(download("https://%s.fr/organismes/groupe/json" % url).text)
        dfile = '%s.parlementaires.json' % url
        destfile = os.path.join(output_directory, dfile)
        if not os.path.exists(destfile):
            print('downloading', dfile)
            open(destfile, 'w').write(download("http://%s.fr/%s/json" %
                (url, 'deputes' if 'deputes' in url else 'senateurs')).text)


if __name__ == '__main__':
    enable_requests_cache()
    process(sys.argv[1])
