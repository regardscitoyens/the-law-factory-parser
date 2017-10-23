the-law-factory-parser
======================

**WIP: rewrite of the parser**

To get the parsed doslegs:

```
# let's install senapy, anpy and a few other things
# NOTE: this is python 3 only for now
pip install -r requirements.txt

# download the senat pages
senapy-cli download_from_csv downloads/html_senat_csv/
senapy-cli download_recent downloads/senat_recent/
# then parse them
senapy-cli parse_directory "downloads/senat_*/" parsed/senat/

# download the AN pages
python download_from_AN.py downloads/an_index/
python download_from_AN_json.py downloads/an_json/
# and parse them
python parse_AN_directory.py "downloads/an_*/" parsed/an/

# now it's the big merge (consolidate data from both sources)
python merge.py "parsed/senat/*" "parsed/an/*" parsed/merged/

# fun stuff
python steps_as_dot.py parsed/merged/all.json | dot -Tsvg > steps_senat.svg
```