# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

__version__ = '0.0.1'

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read()

with open(path.join(here, 'requirements.txt')) as f:
    requirements = []
    dependency_links = []
    for req in f.read().splitlines():
        if '-e ' in req:
            req = req.replace('-e ', '').replace('git+', '')
            if '@' in req:
                if 'framagit' in req:
                    # ex: https://framagit.org/parlement-ouvert/metslesliens/-/archive/1.1.1/metslesliens-1.1.1.tar.bz2
                    version = re.search('.git@(.*)#', req).group(1)
                    name = req.split('=')[1]
                    req = req.replace('.git@%s' % version, '/-/archive/{version}/{name}-{version}.zip'.format(version=version, name=name))
                else:
                    raise Exception('Dependency link not supported', req)
            else:
                if 'github' in req:
                    req = req.replace('.git', '/tarball/master')
                else:
                    raise Exception('Dependency link not supported', req)
            dependency_links.append(req + '-0.0.42') # add a random version because pip...
            requirements.append(req.split('egg=')[1].split('-')[0])
        else:
            requirements.append(req)


setup(
    name='tlfp',
    version=__version__,

    description='Data generator for the-law-factory project lafabriquedelaloi.fr',
    long_description=LONG_DESC,
    license="GPL",

    url='https://github.com/regardscitoyens/the-law-factory-parser',
    author='Regards Citoyens',
    author_email='contact@regardscitoyens.org',
    include_package_data=True,

    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    keywords='scraping politics data',

    packages=find_packages(),

    install_requires=requirements,
    dependency_links=dependency_links,

    scripts=[
        'bin/tlfp-parse-text',
        'bin/tlfp-parse',
        'bin/tlfp-parse-many',
    ],
)
