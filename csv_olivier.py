import json, glob, os, sys, csv

# step 1 - get senat CSV
senat_csv = list(csv.DictReader(open(sys.argv[1], encoding='iso-8859-1'), delimiter=';'))

# filter non-promulgués
senat_csv = [dos for dos in senat_csv if dos['Date de promulgation']]
# filter after 1998
senat_csv = [dos for dos in senat_csv if int(dos['Date de promulgation'].split('/')[-1]) >= 1996]

# step 2 - complete the fields

# get our data via dossiers_json for now
API_DIRECTORY = sys.argv[2]
dossiers_json = {}
for path in glob.glob(os.path.join(API_DIRECTORY, 'dossiers_*.json')):
    for dos in json.load(open(path))['dossiers']:
        if dos.get('senat_id'):
            dossiers_json[dos['senat_id']] = dos


def custom_number_of_steps(steps):
    # count the number of coulumns minus CMP hemicycle
    c = 0
    for step in steps:
        if step.get('debats_order') and not (step['stage'] == 'CMP' and step['step'] == 'hemicycle'):
            c += 1
    return c


sample_for_header = None
c = 0
for dos in senat_csv:
    senat_id = dos['URL du dossier'].split('/')[-1].replace('.html', '')
    if senat_id in dossiers_json:
        c += 1
        parsed_dos = dossiers_json[senat_id]
        dos['Initial size of the law'] = parsed_dos['input_text_length2']
        dos['Final size of the law'] = parsed_dos['output_text_length2']
        dos['Private/Gvmt bill'] = 'private' if 'proposition de loi' in dos['Titre'] else 'gov'
        dos['Steps in the legislative procedures'] = custom_number_of_steps(parsed_dos['steps'])
        dos['Amendments'] = sum([step.get('nb_amendements', 0) for step in parsed_dos['steps']])
        sample_for_header = dos
print(c, 'matched')

senat_csv.sort(key=lambda x: ''.join(reversed(x['Date de promulgation'].split('/'))))

# step 3 - output the new CSV
out = sys.argv[1] + '.test.csv'
print(out)
writer = csv.DictWriter(open(out, 'w'), fieldnames=sorted(list(sample_for_header.keys())))
writer.writeheader()
for dos in senat_csv:
    writer.writerow(dos)
