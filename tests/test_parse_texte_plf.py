"""
Test PLF 2nd part for year 2018 retrieval

Usage: python tests_parse_texte_plf.py
"""
import sys

from tlfp.tools import parse_texte


if "--enable-cache" in sys.argv:
    from lawfactory_utils.urls import enable_requests_cache

    enable_requests_cache()

print("> testing parse_texte.parse for PLF 2 (2018)")
result = parse_texte.parse("http://www.assemblee-nationale.fr/15/projets/pl0235.asp" )#, DEBUG=True)

print("  > correct number of articles")
assert len(result) == 67, len(result)
print("     > OK")

print("  > correct content of article 19")
article_19 = result[22]
assert article_19["type"] == "article", article_19["type"]
assert article_19["titre"] == "19", article_19["titre"]
print("     > OK")

print("  > correct content of article 19 alineas")
assert len(article_19["alineas"]) == 67, len(article_19["alineas"])
assert article_19["alineas"]["001"].startswith("I. - L'article 46 de la loi")
assert article_19["alineas"]["067"].startswith("31 décembre de chaque année.")
print("     > OK")
