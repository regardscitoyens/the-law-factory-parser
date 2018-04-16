coverage run --include="./*.py" tools/sort_articles.py
coverage run -a --include="./*.py" tools/parse_texte.py --test
coverage run -a --include="./*.py" tests/test_steps.py
coverage run -a --include="./*.py" tests/test_regressions.py the-law-factory-parser-test-cases
coverage html
