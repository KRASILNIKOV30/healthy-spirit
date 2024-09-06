import os
import api
import remap

persons_dir = '../res/2024'

tree = list(os.walk(persons_dir))
files = tree[0][2]

i = len(remap.tag_to_name)

for file in files:
    print(api.set(i, f"{persons_dir}/{file}"))
    i += 1
