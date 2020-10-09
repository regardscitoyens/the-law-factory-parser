# takes all doslegs in previous data folder not in the new data folder
# and copy them to the new data folder
# usage: python migrate_old_doslegs <old_data_folder> <data_folder> > script && . script
import sys
import os
import glob

old_data_folder = sys.argv[1]
data_folder = sys.argv[2]

old_doslegs = set(glob.glob(os.path.join(old_data_folder, '*')))
doslegs = set(glob.glob(os.path.join(data_folder, '*')))
doslegs_dirnames = set([dosleg.split('/')[-1] for dosleg in doslegs])

for dosleg in old_doslegs:
    dirname = dosleg.split('/')[-1]
    if "_tmp" in dirname:
        continue
    if dirname not in doslegs_dirnames:
        print("cp -r", dosleg, dosleg.replace(old_data_folder, data_folder))
