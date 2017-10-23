the-law-factory-parser
======================

**WIP: rewrite of the parser**

To get the parsed doslegs:

```
# let's install senapy, anpy and a few other things
# NOTE: this is python 3 only for now
pip install -r requirements.txt

# download the senat pages
senapy-cli download_from_csv data/html/senat/
senapy-cli download_recent data/html/senat/
# then parse them
senapy-cli parse_directory "data/html/senat/*" data/parsed/senat/

# download the AN pages
python download_from_AN.py data/html/an/
python download_from_AN_json.py data/html/an/
# and parse them
python parse_AN_directory.py "data/html/an/*" data/parsed/an/

# now it's the big merge (consolidate data from both sources)
python merge.py "data/parsed/senat/*" "data/parsed/an/*" data/parsed/merged/

# fun stuff
python steps_as_dot.py data/parsed/merged/all.json | dot -Tsvg > steps.svg
```