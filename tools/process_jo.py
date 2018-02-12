import re
import sys

from lawfactory_utils.urls import download, enable_requests_cache

re_br = re.compile(r"[\s\n\r]*</?br[^>]*>[\s\n\r]*|<div[^>]*>\s*</div>")
clean_br = lambda x: re_br.sub("\n", x)
re_signataires = re.compile(r"^.*>\s*Fait (?:(?:à|au) [^,]+, )?le \d.*?<\/p>(.*?)<(font|div|!--).*$", re.S)
signataires = lambda x: re_signataires.sub(r"\1", x)
re_ministre = re.compile(r"le Président de la République|L[ea] (Premi[eè]re?|ministre|garde|secrétaire|haut-commissaire) ")
count_ministres = lambda x: len(re_ministre.findall(x))

def extract_signataires(url):
    text_src = download(url).text
    text_src = clean_br(text_src)
    if not re_signataires.search(text_src):
        print("ERROR: could not find signature in texte JO", url, file=sys.stderr)
        return None
    text_src = signataires(text_src)
    return text_src

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
                print()
                print(url, ':', count_signataires(url))
    else:
        print(extract_signataires(sys.argv[1]), count_signataires(sys.argv[1]))
