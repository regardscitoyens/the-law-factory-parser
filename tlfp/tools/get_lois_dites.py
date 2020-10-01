import os
from tlfp.tools.common import open_json


def get_lois_dites():
	file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/lois_dites.json')
	return open_json(file)