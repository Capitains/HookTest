import os
from glob import glob

try:
    with open('manifest.txt') as f:
        passing = f.read().split('\n')
except FileNotFoundError:
    print('There is no manifest.txt file to load.\nStopping build.')


files = glob('data/*/*/*.xml')
files += glob('data/*/*.xml')
for file in files:
    if file not in passing:
        os.remove(file)

dirs = [x for x in glob('data/*/*') if os.path.isdir(x)]
for d in dirs:
    try:
        os.removedirs(d)
    except OSError:
        continue