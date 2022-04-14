import os

from pathlib import Path

import cv2

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
device_name = 'hello'
print(rf"static/image uploads/{device_name}/" +"haha.txt")

# original_img = cv2.imread(os.path.join(os.getcwd(), 'static', 'image uploads', '2021-07-15 16-18-18xxxelephant_annotated.jpg'))

device_name = 'end device 2'
original_img = cv2.imread(f'static/image uploads/{device_name}/2021-07-15 16-18-18xxxelephant_annotated.jpg')

# Jsonpath = rf'static/image uploads/{device_name}/2021-08-15 16-18-18-x-babyy - Copy - Copy - Copy.json'
# print(os.path.exists(Jsonpath))

# annotationStr = open(Jsonpath, "r").read()



str11 = "['eee','rrr']"
print(str11.replace("\'", "\""))