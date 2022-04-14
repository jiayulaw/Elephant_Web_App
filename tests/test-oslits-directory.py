import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(BASE_DIR)
file_path = os.path.join('static/img/', "bigpicture.png")
file_path = 'static/img/bigpicture.png'
absolute_file_path = os.path.join(BASE_DIR, file_path)
directory2 = os.path.join(BASE_DIR, absolute_file_path)
print(directory2)

#print(os.listdir(directory2))
