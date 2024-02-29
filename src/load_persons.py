import os
import api

tree = list(os.walk('../res/additional_photos'))
files = tree[0][2]

#i = 2
#for file in files:

    #print(api.set(i, f"../res/persons/{file}"))
    #i += 1

#print(api.set(28, '../res/additional_photos/Атюлов Игнат Васильевич.png'))
print(api.recognize('../res/old_persons/bogdan_krasilnikov.png'))
