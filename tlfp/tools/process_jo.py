import re
import sys

from lawfactory_utils.urls import download, enable_requests_cache

from .common import strip_text

# TODO:
# - count articles
# - count alineas

re_br = re.compile(r"[\s\n\r]*</?br[^>]*>[\s\n\r]*", re.S)
clean_br = lambda x: re_br.sub("\n", x)
re_fioritures = re.compile(r"(<div[^>]*>[\s\n]*</div>|<a[^>]*>En savoir plus sur [^<]*</a>|Fait à [^,]+, le \d[^.,]*, en double exemplaire\.)")
clean_fioritures = lambda x: re_fioritures.sub("", x)
re_texte = re.compile(r"^.*Le Président (?:de la République (?:française )?)?promulgue la loi dont la teneur suit :(.*?)(La présente loi sera exécutée comme loi de l'Etat\.|<!-- end texte -->|Fait(?: (?:à|au) [^,]+,)? le \d.*?<[^>]*>).*$", re.S|re.I)
extract_contenu = lambda x: re_texte.sub(r"\1", x)
re_reorder = re.compile(r"(Fait(?: (?:à|au) [^,]+,)? le \d.*?<[^>]*>)(.*)(<!-- end texte -->.*Par le Président de la République :)", re.S)
reorder = lambda x: re_reorder.sub(r"\2\1\3", x)
re_signataires = re.compile(r"^.*?((<!-- end texte -->|Fait(?: (?:à|au) [^,]+,)? le \d.*?<[^>]*>).*?)<(font|!-- end signataires).*$", re.S)
signataires = lambda x: re_signataires.sub(r"\1", x)
re_ministre = re.compile(r"le Président de la République|L[ea] (Premi[eè]re?|ministre|garde|secrétaire|haut-commissaire) ")
count_ministres = lambda x: len(re_ministre.findall(x))

def download_texte(url):
    text = download(url).text
    return clean_fioritures(clean_br(text))

def extract_texte(url):
    text = download_texte(url)
    if not re_texte.search(text):
        print("ERROR: could not find texte in JO", url, file=sys.stderr)
        return None
    return strip_text(extract_contenu(text))

def get_texte_length(url):
    text = extract_texte(url)
    if not text:
        return -1
    return len(text)

def extract_signataires(url):
    text_src = reorder(download_texte(url))
    if not re_signataires.search(text_src):
        print("ERROR: could not find signature in texte JO", url, file=sys.stderr)
        return None
    text_src = signataires(text_src)
    return strip_text(text_src)

def count_signataires(url):
    signataires_text = extract_signataires(url)
    if not signataires_text:
        return -1
    return count_ministres(signataires_text)

if __name__ == "__main__":
    enable_requests_cache()
    if len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            for url in f.readlines():
                url = url.strip()
                print(url, ':', get_texte_length(url), '|', count_signataires(url))
    else:
        print(extract_texte(sys.argv[1]), get_texte_length(sys.argv[1]))
        print(extract_signataires(sys.argv[1]), count_signataires(sys.argv[1]))
