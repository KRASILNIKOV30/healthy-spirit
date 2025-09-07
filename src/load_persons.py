import os
import api
import remap

persons_dir = './res/2025'

tree = list(os.walk(persons_dir))
files = tree[0][2]

i = len(remap.tag_to_name)

for file in files:
    print(api.set(i, f"{persons_dir}/{file}"))
    name = os.path.splitext(file)[0].replace('_', ' ').title()
    remap.tag_to_name[f"person{i}"] = name
    i += 1

# Записываем обновленный словарь обратно в файл
with open('src/remap.py', 'w', encoding='utf-8') as f:
    f.write('tag_to_name = {\n')
    for key, value in remap.tag_to_name.items():
        f.write(f'    "{key}": "{value}",\n')
    f.write('}\n')
