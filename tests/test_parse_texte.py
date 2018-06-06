from tlfp.tools.parse_texte import (
    clean_article_name, clean_html, normalize_1, re_clean_conf, re_mat_sec
)


def assert_eq(x, y):
    if x != y:
        print(repr(x), "!=", repr(y))
        raise Exception()


# keep the dots
assert_eq(clean_html('<i>....................</i>'), '<i>....................</i>')
# but remove them for status
assert_eq(clean_html('...........Conforme.........'), 'Conforme')
assert_eq(clean_html('...……......……..Conforme....……...…….'), 'Conforme')
# even with spaces
assert_eq(clean_html('...........  Conforme   .........'), 'Conforme')
# or for alineas
assert_eq(clean_html('II. - <i>Conforme</i>...............'), 'II. - <i>Conforme</i>')
# even midway alineas
assert_eq(clean_html('II. - <i>Conforme</i>............... ;'), 'II. - <i>Conforme</i> ;')

# clean empty <a> tags
assert_eq(clean_html('<b><a name="P302_55065"></a>ANNEXE N° 1 :<a name="P302_55081"><br/> </a>TEXTE ADOPTÉ PAR LA COMMISSION</b>'), '<b>ANNEXE N° 1 : TEXTE ADOPTÉ PAR LA COMMISSION</b>')

# clean status
assert_eq(re_clean_conf.sub(r'\1(Non modifié)', 'IV. - Non modifié'), 'IV. - (Non modifié)')
assert_eq(re_clean_conf.sub(r'\1(Non modifié)', 'III et IV. - Non modifié'), 'III et IV. - (Non modifié)')

assert_eq(normalize_1('1', '1er'), '1er')
assert_eq(normalize_1('17', '1er'), '17')
assert_eq(normalize_1('1 bis', '1er'), '1er bis')

assert_eq(clean_article_name('Article 5.'), 'Article 5')

assert_eq(re_mat_sec.match('<b>Titre Ier - Cuire un oeuf</b>').group('titre').strip(), 'Cuire un oeuf')
