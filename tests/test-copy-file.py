
import shutil
import os
 

 

 
path = 'static/image uploads/end device 2/2021-09-15 16-18-18-x-whale.jpg'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_absolute_path = os.path.join(BASE_DIR, path)
device = 'end device 3'
dest_absolute_path = os.path.join(BASE_DIR, f'NodeRed/{device}/new_image.jpg')
shutil.copy2(src_absolute_path, dest_absolute_path)