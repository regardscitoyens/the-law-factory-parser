# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

__version__ = '0.0.3'

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read()

with open(path.join(here, 'requirements.txt')) as f:
    requirements = [line.strip() for line in f.read().splitlines()]

setup(
    name='tlfp',
    version=__version__,

    description='Data generator for the-law-factory project lafabriquedelaloi.fr',
    long_description=LONG_DESC,
    long_description_content_type='text/markdown',
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

    scripts=[
        'bin/tlfp-parse-text',
        'bin/tlfp-parse',
        'bin/tlfp-parse-many',
    ],
)
