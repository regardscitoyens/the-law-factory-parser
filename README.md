the-law-factory-parser
======================

[![Build Status](https://travis-ci.org/regardscitoyens/the-law-factory-parser.svg?branch=parser-refactor)](https://travis-ci.org/regardscitoyens/the-law-factory-parser) [![Coverage Status](https://coveralls.io/repos/github/regardscitoyens/the-law-factory-parser/badge.svg?branch=master)](https://coveralls.io/github/regardscitoyens/the-law-factory-parser?branch=master)

Data generator for [the-law-factory project](https://github.com/RegardsCitoyens/the-law-factory) (http://www.LaFabriqueDeLaLoi.fr)

Code used to generate the API available at: http://www.LaFabriqueDeLaLoi.fr/api/


## Install the dependencies ##

You can install them with the following:

```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install --upgrade setuptools pip # not necessary but always a good idea
pip install --process-dependency-links -e .
```
NOTE: You must have Python 3.5+ for now


## Generate data for one bill ##

- search for the [bill's procedure page on Senat.fr](http://www.senat.fr/dossiers-legislatifs/index-general-projets-propositions-de-lois.html) or [Assemblee-nationale.fr](http://www.assemblee-nationale.fr/15/documents/index-dossier.asp).

- execute *tlfp-parse* script using the procedure page:

`tlfp-parse <url>`

The data is generated in the "*data*" directory. You can change this default behavior by inputting a data path as extra argument: `tlfp-parse <url> <dataDir>`.

For example, to generate data about the "*Enseignement supérieur et recherche*" bill:

    tlfp-parse http://www.senat.fr/dossier-legislatif/pjl12-614.html
    ls data/pjl12-614/

You can also use directly Senate's ids such as: `tlfp-parse pjl12-614`

Development options `--debug`, `--enable-cache` and `--only-promulgated` can also be used.


## Generate data for many bills

To generate all bills from 2008, you can pipe a list of ids or urls into `tlfp-parse-many`.

A convenient way to do so is to use [senapy](https://github.com/regardscitoyens/senapy):

   senapy-cli doslegs_urls --min-year=2008 | tlfp-parse-many data/

See `senapy-cli doslegs_urls` help for more options. You can also use [anpy](https://github.com/regardscitoyens/anpy) with `anpy-cli doslegs_urls`.


## Serve bills locally for [The Law Factory website](https://github.com/regardscitoyens/the-law-factory)

First, you need to build data for all desired bills.

Then generate the files required by the frontend:

    python tlfp/generate_dossiers_csv.py data/       # generates home.json and dossiers_promulgues.csv used by the searchbar
    python tlfp/tools/assemble_procedures.py data/   # generates dossiers_n.json files used by the Navettes viz

Finally, serve the data directory however you like. For instance, you can serve it on a specific port with a simple http server like nodeJs', in which case, you'll need to enable cors: just install *http-server* with npm and run it in data directory on a given port (8002 in the example):

    npm install -g http-server
    cd data & http-server -p 8002 --cors


## Generate git version for a bill

(coming back soon)


## Other things you can do

 - parse a sénat dosleg: `senapy-cli parse pjl15-610`
 - parse all the sénat doslegs: `senapy-cli doslegs_urls | senapy-cli parse_many senat_doslegs/`
 - parse all the AN doslegs `anpy-cli doslegs_urls | anpy-cli parse_many_doslegs an_doslegs/`
 - parse an AN dosleg: `anpy-cli show_dossier_like_senapy http://www.assemblee-nationale.fr/13/dossiers/deuxieme_collectif_2009.asp`
 - generate a graph of the steps: `python tools/steps_as_dot.py data/ | dot -Tsvg > steps.svg`


## Tests

To run the tests, you can follow the `.travis.yml` file.

    git clone https://github.com/regardscitoyens/the-law-factory-parser-test-cases.git
    python tests/test_regressions.py the-law-factory-parser-test-cases

If you modify something, best is to regenerate the test-cases with the `--regen` flag:

    python tests/test_regressions.py the-law-factory-parser-test-cases --regen

To make the tests faster, you can also use the `--enable-cache` flag.

You can also watch for parts of the code not yet covered by the tests:

   - First, install `coverage`: `pip install coverage`
   - Then, you can execute `bash coverage.sh`
   - Then, the report is in `htmlcov/index.html`

## Credits

This work, a collaboration between [Regard Citoyens](https://www.regardscitoyens.org), [médialab Sciences Po](https://medialab.sciencespo.fr/fr/) and [CEE Sciences Po](http://www.sciencespo.fr/centre-etudes-europeennes/fr), is supported by a public grant overseen by the French National Research Agency (ANR) as part of the "Investissements d'Avenir" program within the framework of the LIEPP center of excellence (ANR11LABX0091, ANR 11 IDEX000502).

More details at https://lafabriquedelaloi.fr/a-propos.html
