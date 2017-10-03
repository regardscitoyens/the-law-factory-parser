import glob, json, sys

def dedup_by_key(list, key):
    uniqs = set()
    for el in list:
        if key not in el:
            print(el)
            continue
        v = el.get(key)
        if v not in uniqs:
            yield el
            uniqs.add(v)

def date_is_after_2008_reform(date):
    # https://www.legifrance.gouv.fr/affichTexte.do?cidTexte=JORFTEXT000019237256&dateTexte=&categorieLien=id
    year, month, day = (int(x) for x in date.split('-'))
    return year > 2008 or (year == 2008 and month >= 9) # we take september 2008

SENAT_GLOB = sys.argv[1] # ex: '/home/mel/prog/repos/senapy/scratch/2_*/*
LEGI_GLOB = sys.argv[2] # ex: '/home/mel/prog/repos/legipy/legifrance_dossiers/*'
AN_GLOB = sys.argv[3] # ex: '/home/mel/prog/repos/anpy/an_dossiers/*'

all_senat = [json.load(open(f)) for f in glob.glob(SENAT_GLOB)]
all_senat = [x for x in all_senat if x and date_is_after_2008_reform(x.get('beginning','1900-0-0'))]
all_senat = [dos for dos in dedup_by_key(all_senat, 'url_dossier_senat')]

print('senat loaded', len(all_senat))

all_legi = [json.load(open(f)) for f in glob.glob(LEGI_GLOB)]
all_legi = [x for x in all_legi if x]

print('legi loaded', len(all_legi))

all_an = [json.loads(open(f).read()) for f in glob.glob(AN_GLOB)]
all_an = [x for x in all_an if x]

print('an loaded', len(all_an))

json.dump(all_senat, open('all_senat.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
# json.dump(all_legi, open('all_legi.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
# json.dump(all_an, open('all_an.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
# json.dump(all_senat + all_legi + all_an, open('all.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

all_senat_jo = [dos for dos in dedup_by_key(all_senat, 'url_dossier_senat') if dos.get('end_jo')]

print('all_senat_jo', len(all_senat_jo))
json.dump(all_senat_jo, open('all_senat_jo.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
