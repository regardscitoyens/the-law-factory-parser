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
    "https://web.archive.org/web/20191104051233/http://www.assemblee-nationale.fr/15/ta-commission/r1056-a0.asp"
)
article = result[-1]
assert article["type"] == "article"
print("     > OK")

print("> testing parse_texte annexes from AN")
result = parse_texte.parse(
    "https://web.archive.org/web/20191104051233/http://www.assemblee-nationale.fr/15/ta-commission/r1056-a0.asp",
    include_annexes=True,
)
assert len(result) == 94, len(result)
annexe = result[-1]
assert annexe["type"] == "annexe", annexe["type"]
assert annexe["order"] == 82, annexe["order"]
assert annexe["statut"] == "none", annexe["statut"]
assert (
    annexe["titre"] == "Stratégie nationale d'orientation de l'action publique"
), annexe["titre"]
assert len(annexe["alineas"]) == 29, len(annexe["alineas"])
print("     > OK")

print("> testing parse_texte annexes from Senat")
result = parse_texte.parse(
    "http://www.senat.fr/leg/pjl17-063.html", include_annexes=True
)
assert len(result) == 103, len(result)

annexe_a = result[-3]
assert annexe_a["type"] == "annexe", annexe_a["type"]
assert annexe_a["order"] == 78, annexe_a["order"]
assert annexe_a["statut"] == "none", annexe_a["statut"]
assert annexe_a["titre"] == "A", annexe_a["titre"]
assert len(annexe_a["alineas"]) == 19, len(annexe_a["alineas"])

annexe_b = result[-2]
assert annexe_b["type"] == "annexe", annexe_b["type"]
assert annexe_b["order"] == 79, annexe_b["order"]
assert annexe_b["statut"] == "none", annexe_b["statut"]
assert annexe_b["titre"] == "B", annexe_b["titre"]
assert len(annexe_b["alineas"]) == 52, len(annexe_b["alineas"])

annexe_c = result[-1]
assert annexe_c["type"] == "annexe", annexe_c["type"]
assert annexe_c["order"] == 80, annexe_c["order"]
assert annexe_c["statut"] == "none", annexe_c["statut"]
assert annexe_c["titre"] == "C", annexe_c["titre"]
assert len(annexe_c["alineas"]) == 13, len(annexe_c["alineas"])

print("     > OK")
