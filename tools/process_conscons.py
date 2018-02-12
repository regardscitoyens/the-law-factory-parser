import re
import sys

from lawfactory_utils.urls import download

# TODO:
# - parse by <p>
# - return ID ECLI
# - return list of signataires saisine
# - return list of signataires décision
# - return list of visa
# - return list of considerants
# - return list of decision articles

re_clean_spaces = re.compile(r"[\s\n]+")
clean_spaces = lambda x: re_clean_spaces.sub(" ", x)
re_clean_balises = re.compile(r"<\/?[a-z][^>]*>", re.I)
clean_balises = lambda x: re_clean_balises.sub("", x)
re_delibere = re.compile(r"<p>\s*(Jug|Délibér)é par le Conseil constitutionnel .*$", re.M)
clean_delib = lambda x: re_delibere.sub("", x)

def extract_full_decision(url):
    decision_src = download(url).text
    if '<a name=\'visa\' id="visa"></a>' not in decision_src:
        print("ERROR: could not find visa in decision CC", url, file=sys.stderr)
        return None
    decision_txt = decision_src.split('<a name=\'visa\' id="visa"></a>')[1]
    if not re_delibere.search(decision_txt):
        print("ERROR: could not find siège in décision CC", url, file=sys.stderr)
        return None
    decision_txt = clean_delib(decision_txt)
    return clean_spaces(clean_balises(decision_txt))

def get_decision_length(url):
    try:
        return len(extract_full_decision(url))
    except:
        return -1

if __name__ == "__main__":
    print(extract_full_decision(sys.argv[1]))
