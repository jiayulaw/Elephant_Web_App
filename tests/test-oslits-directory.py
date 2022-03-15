import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(BASE_DIR)
directory = rf "static/img/bigpicture.png"
directory2 = os.path.join("C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2", directory)

print(os.listdir(directory2))
