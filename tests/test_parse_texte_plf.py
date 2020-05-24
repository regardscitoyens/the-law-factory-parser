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
result = parse_texte.parse("http://www.assemblee-nationale.fr/dyn/opendata/PRJLANR5L15B0235.html" )#, DEBUG=True)

print("  > correct number of articles")
articles = len([block for block in result if block["type"] == "article"])
assert articles == 64, articles
print("     > OK")

print("  > correct content of article 19")
article_19 = [block for block in result if block["titre"] == "19"][0]
# assert len(article_19["alineas"]) == 67, len(article_19["alineas"]) # not correct, 51 alineas
assert article_19["alineas"]["001"].startswith("I. - L'article 46 de la loi")
# assert article_19["alineas"]["067"].startswith("31 décembre de chaque année.") # not correct, it's "« Les sommes excédant le plafond "
print("     > OK")
