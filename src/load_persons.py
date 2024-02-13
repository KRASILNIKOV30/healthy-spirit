import os
import api

tree = list(os.walk('../res/persons'))
files = tree[0][2]

i = 2
for file in files:
    print(api.set(i, f"../res/persons/{file}"))
    i += 1
