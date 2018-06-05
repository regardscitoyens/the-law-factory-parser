import sys, os, time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from anpy.dossier_from_opendata import download_open_data_doslegs

from common import print_json, open_json


def process(output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    all_data = {}

    yesterday = time.time() - 86400
    for legislature in 14, 15:
        dfile = 'opendata_AN_dossiers_%d.json' % legislature
        destfile = os.path.join(output_directory, dfile)
        if not os.path.exists(destfile) or os.path.getmtime(destfile) < yesterday:
            print('downloading', dfile)
            data = download_open_data_doslegs(legislature)
            print_json(data, destfile)
        else:
            data = open_json(destfile)
        all_data[legislature] = data
    return all_data


if __name__ == '__main__':
    process(sys.argv[1])
