"""
Test annexes retrieval

Usage: python tests_parse_annexes.py
"""
import sys

from tlfp.tools import parse_texte


if "--enable-cache" in sys.argv:
    from lawfactory_utils.urls import enable_requests_cache

    enable_requests_cache()

print("> testing parse_texte without annexes (default)")
result = parse_texte.parse(
    "http://www.assemblee-nationale.fr/15/ta-commission/r1056-a0.asp"
)
article = result[-1]
assert article["type"] == "article"
print("     > OK")

print("> testing parse_texte annexes from AN")
result = parse_texte.parse(
    "http://www.assemblee-nationale.fr/15/ta-commission/r1056-a0.asp",
    include_annexes=True,
)
assert len(result) == 93, len(result)
annexe = result[-1]
assert annexe["type"] == "annexe", annexe["type"]
assert annexe["order"] == 82, annexe["order"]
assert annexe["statut"] == "none", annexe["statut"]
assert (
    annexe["titre"] == "Stratégie nationale d'orientation de l'action publique"
), annexe["titre"]
assert len(annexe["alineas"]) == 28, len(annexe["alineas"])
print("     > OK")

