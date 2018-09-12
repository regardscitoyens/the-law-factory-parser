import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tlfp.tools.common import log_print
from tlfp.tools import complete_articles


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

with log_print() as log:
    case = json.load(open(os.path.join(TESTS_DIR, 'ressources/complete_me.json')))
    result = complete_articles.complete(**case)
    assert len(result[1]['alineas']) == 6
    assert log.getvalue() == ''
