the-law-factory-parser
======================
[![Build Status](https://travis-ci.org/regardscitoyens/the-law-factory-parser.svg?branch=parser-refactor)](https://travis-ci.org/regardscitoyens/the-law-factory-parser)

Data generator for [the-law-factory project](https://github.com/RegardsCitoyens/the-law-factory) (http://www.LaFabriqueDeLaLoi.fr)

Code used to generate the API available at: http://www.LaFabriqueDeLaLoi.fr/api/

## Install the dependencies ##

You can install them with the following:
```
virtualenv -p=/usr/bin/python3 venv
source venv/bin/activate
pip install --upgrade setuptools pip # not necessary but always a good idea
pip install --upgrade -r requirements.txt
```
NOTE: You must have Python 3.5+ for now

## Generate data for one bill ##

- search for the [bill procedure page on senat.fr](http://www.senat.fr/dossiers-legislatifs/index-general-projets-propositions-de-lois.html)

- execute *parse_one.py* script using the procedure page :

`python parse_one.py <url>`

The data is generated in the "*data*" directory.

For example, to generate data about the "*Enseignement supérieur et recherche*" bill:

```
python parse_one.py http://www.senat.fr/dossier-legislatif/pjl12-614.html
ls data/pjl12-614/
```

## Generate data for many bills

To generate all bills from 2008, you can use [senapy](https://github.com/regardscitoyens/senapy)

    senapy-cli doslegs_urls --min-year=2008 | python parse_many.py data/

See `senapy-cli doslegs_urls` help for more options. You can also use [anpy](https://github.com/regardscitoyens/anpy) with `anpy-cli doslegs_urls`

## Serve bills locally for the [law factory website](https://github.com/regardscitoyens/the-law-factory)

First, you need to generate the files

    python generate_dossiers_csv.py data/ # generate the home.json and the .csv to
    python tools/assemble_procedures.py data/

To be used in the law factory app, we need to enable cors. Just install *http-server* nodejs lib and run it in data directory on a given port (8002 in the example) :

    npm install -g http-server
    cd data & http-server -p 8002 --cors

## Generate git version for a bill

(coming back soon)

### Other things you can do

 - parse a sénat dosleg: `senapy-cli parse pjl15-610`
 - parse all the sénat doslegs: `senapy-cli doslegs_urls | senapy-cli parse_many senat_doslegs/`
 - parse all the AN doslegs `anpy-cli doslegs_urls | anpy-cli parse_many_doslegs an_doslegs/`
 - parse an AN dosleg: `anpy-cli show_dossier_like_senapy http://www.assemblee-nationale.fr/13/dossiers/deuxieme_collectif_2009.asp`
 - generate a graph of the steps: `python tools/steps_as_dot.py data/ | dot -Tsvg > steps.svg`

### Tests

To run the tests, you can follow the `.travis.yml` file.

    - git clone https://github.com/regardscitoyens/the-law-factory-parser-test-cases.git
    - python tests/test_regressions.py the-law-factory-parser-test-cases

If you modify something, best in to re-generate the test-cases with the `--regen` flag:

    - python tests/test_regressions.py the-law-factory-parser-test-cases --regen

To make the tests faster, you can also use the `--enable-cache` flag.


### Credits

This work is supported by a public grant overseen by the French National Research Agency (ANR) as part of the "Investissements d'Avenir" program within the framework of the LIEPP center of excellence (ANR11LABX0091, ANR 11 IDEX000502).
More details at https://lafabriquedelaloi.fr/a-propos.html