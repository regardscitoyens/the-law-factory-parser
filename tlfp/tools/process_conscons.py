import re
import sys

from lawfactory_utils.urls import download, enable_requests_cache

from .common import strip_text

# TODO:
# - parse by <p>
# - return ID ECLI
# - return list of signataires saisine
# - return list of signataires décision
# - return list of visa
# - return list of considerants
# - return list of decision articles

re_delibere = re.compile(r"<p>\s*(Jug|Délibér)é par le Conseil constitutionnel .*$", re.S)
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
    return strip_text(decision_txt)

def get_decision_length(url):
    decision_txt = extract_full_decision(url)
    if not decision_txt:
        return -1
    return len(decision_txt)

if __name__ == "__main__":
    enable_requests_cache()
    if len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            for url in f.readlines():
                url = url.strip()
                print(url, ':', get_decision_length(url))
    else:
        print(extract_full_decision(sys.argv[1]))
