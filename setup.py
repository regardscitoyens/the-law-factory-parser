# -*- coding: utf-8 -*-
from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

__version__ = '0.0.1'

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read()


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
    ],

    keywords='scraping politics data',

    packages=['tlfp'],

    install_requires=[
        "lawfactory_utils",
        "beautifulsoup4==4.6.0",
        "diff-match-patch==20121119",
        "html5lib==1.0.1",
    ],

    scripts=['bin/parse-texte'],
)
