import os

from pathlib import Path

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# print(BASE_DIR)

# JsonFileName = '2021-08-15 16-18-18-x-babyy' + ".json"
# print(JsonFileName)
# # JsonFilePath = os.path.join(directory, JsonFileName)
# # JsonFilePath = rf"static/image uploads/end device 2/"+JsonFileName
# JsonFilePath = os.path.join(rf"static/image uploads/end device 2", JsonFileName)
# print(JsonFilePath)
# JsonFilePath = os.path.join(BASE_DIR, JsonFilePath)

# print(JsonFilePath)
# # Record to database the new image    

# if os.path.exists(JsonFilePath):
#     print("yes")
# else:
#     print("no")

# filepath = "static/img/xxx.png"
# dirname = os.path.dirname(filepath)
# print(dirname)

print(os.path.abspath('.'))
username = 'kk'

import pathlib
print(pathlib.Path(f"~/{username}.txt"))

p1 = os.path.dirname('static/img/img.txt')
print(p1)
print(Path(p1))

print(p1[1:])

print(os.path.basename('static/img/img.txt'))